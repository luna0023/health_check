# -*- coding: utf-8 -*-
import time
import logging
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import REQUEST_TIMEOUT, SUPPLIERS, MAX_WORKERS

# ---------- 优化点1：全局线程池（复用线程，避免每次请求创建/销毁）----------
# 为什么这么写？线程创建开销大（约1ms/个），高并发下频繁创建会拖垮CPU。
# 全局池子只创建一次，所有请求共享，符合“池化”思想（类似数据库连接池）。
_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# ---------- 优化点2：全局失败计数器（演示锁）----------
_total_failures = 0
_fail_lock = threading.Lock()


def reset_failure_counter():
    global _total_failures
    with _fail_lock:
        _total_failures = 0


def get_failure_count():
    with _fail_lock:
        return _total_failures


def fetch_price(supplier_id, url, product_id):
    """
    请求单个供应商。
    优化点：日志里带上 product_id，方便追踪是哪个商品的请求失败了。
    """
    global _total_failures
    try:
        params = {'product_id': product_id}
        # 第一层超时，防止网络请求无限期等待
        response = requests.get(url, timeout=REQUEST_TIMEOUT, params=params)
        response.raise_for_status()
        data = response.json()
        price = data.get('price', float('inf'))

        logging.info(f"✅ [商品{product_id}] 供应商{supplier_id} 返回价格: {price}")
        return price
    except Exception as e:
        logging.warning(f"❌ [商品{product_id}] 供应商{supplier_id} 请求失败: {e}")
        with _fail_lock:
            _total_failures += 1
        return float('inf')


def get_best_price(product_id, total_timeout=2.5):
    """
    并发请求所有供应商，取最低价。
    优化点：
    1. 使用全局线程池（_executor）
    2. 引入总超时控制（total_timeout），防止因某个供应商卡死导致接口无限等待
    3. future.result(timeout) 确保单个任务不无限阻塞
    """
    reset_failure_counter()
    local_failures = []
    start_time = time.perf_counter()  # 记录整个请求的开始时间

    # 提交任务（使用全局线程池）
    # future_to_supplier = {FutureA: "supplier_0", FutureB: "supplier_1", FutureC: "supplier_2"}
    future_to_supplier = {
        _executor.submit(fetch_price, supplier_id, url, product_id): supplier_id
        for supplier_id, url in SUPPLIERS.items()
    }

    prices = []
    for future in as_completed(future_to_supplier):
        supplier_id = future_to_supplier[future]

        # 计算剩余超时时间（总超时 - 已消耗时间）
        elapsed = time.perf_counter() - start_time
        remaining_time = total_timeout - elapsed

        # 如果剩余时间 <= 0，说明总超时已到，不再等待后续任务
        if remaining_time <= 0:
            logging.warning(f"⏰ [商品{product_id}] 总超时已到 ({total_timeout}s)，放弃等待供应商{supplier_id}")
            # 把还没返回的供应商标记为失败（虽然我们没拿到结果，但程序不能卡死）
            local_failures.append(supplier_id)
            continue

        try:
            # 第二层超时：
            # 给 result() 加 timeout，防止单个任务无限阻塞
            # 如果这个供应商在 remaining_time 内没返回，抛出 TimeoutError
            price = future.result(timeout=remaining_time)
            if price == float('inf'):
                local_failures.append(supplier_id)
            else:
                prices.append(price)
        except TimeoutError:
            # 单个任务超时（可能是网络抖动或服务慢）
            logging.warning(f"⏰ [商品{product_id}] 供应商{supplier_id} 单任务超时 (>{remaining_time:.2f}s)")
            local_failures.append(supplier_id)
        except Exception as e:
            logging.error(f"❌ [商品{product_id}] 供应商{supplier_id} 结果异常: {e}")
            local_failures.append(supplier_id)

    if not prices:
        return None, local_failures

    best = min(prices)
    # 额外日志：记录最终选中的供应商（方便追踪）
    logging.info(f"🏆 [商品{product_id}] 最终最低价: {best}，失败供应商: {local_failures}")
    return best, local_failures


# ---------- 优化点3：优雅关闭（应用退出时释放线程池资源）----------
def shutdown_executor():
    """应用退出时调用，释放线程池资源"""
    _executor.shutdown(wait=True)
    logging.info("🛑 全局线程池已关闭")
