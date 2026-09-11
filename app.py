# -*- coding: utf-8 -*-
import os
import sys
import atexit  # 用于注册退出回调
import logging
from flask import Flask, request, jsonify
from utils.decorators import timer
from services.price_fetcher import get_best_price, get_failure_count, shutdown_executor
from config import LOG_FILE


atexit.register(shutdown_executor)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding='utf-8')
        ]
    )


setup_logging()


@app.route('/price', methods=['GET'])
@timer
def get_best_price_api():
    product_id = request.args.get('product_id')
    if not product_id:
        return jsonify({"error": "缺少 product_id 参数"}), 400

    # 调用优化后的函数，传入总超时 2.5 秒
    best_price, failed_list = get_best_price(product_id, total_timeout=2.5)

    if best_price is None:
        return jsonify({
            "error": "所有供应商均不可用",
            "product_id": product_id,
            "failed_suppliers": failed_list
        }), 503

    return jsonify({
        "product_id": product_id,
        "best_price": best_price,
        "failed_suppliers": failed_list,
        "total_failures_since_start": get_failure_count()
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


# print("\n===== 已注册的路由 =====")
# for rule in app.url_map.iter_rules():
#     print(rule)
# print("========================\n")

if __name__ == '__main__':
    # 注意：debug=True 会启动子进程，atexit 可能在子进程中执行两次，但影响不大
    app.run(debug=True, host='0.0.0.0', port=5000)
