# 轻量级供应商价格聚合API服务 (Price Aggregator API)

一个轻量级的微服务 API，通过并发请求多个供应商接口，获取同一商品的不同报价，取最低价返回，模拟电商平台的比价聚合层。

---

## 📌 项目背景

在实际业务中，一个商品通常有多个供应商报价。如果串行请求每个供应商，响应时间等于所有供应商耗时之和，用户体验很差。本项目通过 Python 线程池实现并发请求，将响应时间从"所有供应商耗时之和"优化为"最慢供应商耗时"，大幅提升接口响应速度。

---

## 🚀 核心功能

- **并发聚合**：使用 `ThreadPoolExecutor + as_completed` 并发请求 3 个供应商，谁先回来先处理谁。
- **两层超时熔断**：`requests.timeout` + `future.result(timeout)` 双重保险，防止单点故障拖垮整个接口。
- **哨兵值模式**：供应商超时或报错时返回 `float('inf')`，后续 `min()` 取最低价时自动忽略。
- **线程安全**：通过 `threading.Lock` 保护共享计数器，确保多线程环境下数据一致性。
- **接口耗时监控**：通过 `@timer` 装饰器自动记录每个 API 请求的耗时（毫秒级）。
- **全链路日志追踪**：每条日志带 `product_id`，方便快速定位特定商品的请求链路。

---

## 🛠 技术栈

| 类别       | 技术                                      |
| :--------- | :---------------------------------------- |
| 核心语言   | Python 3.9+                               |
| Web 框架   | Flask                                     |
| 并发处理   | ThreadPoolExecutor, as_completed          |
| HTTP 请求  | Requests                                  |
| 线程安全   | threading.Lock                            |
| 日志监控   | Logging 模块 (控制台 + 文件输出)          |
| 配置管理   | 环境变量 + config.py                      |

---

## 📂 项目结构
health_check/
├── services/
│ ├── init.py
│ └── price_fetcher.py # 并发请求核心逻辑
├── utils/
│ ├── init.py
│ └── decorators.py # @timer 装饰器
├── data/
│ └── prices.json # 供应商模拟价格数据
├── logs/
│ └── app.log # 运行时日志 (自动生成)
├── app.py # Flask 主入口
├── config.py # 配置文件 (URL、超时、线程数)
├── supplier_mock.py # 供应商模拟服务 (本地测试用)
├── requirements.txt # 项目依赖
└── README.md

text

---

## ⚙️ 快速开始 (Quick Start)

### 1. 克隆项目并安装依赖

```text
git clone https://github.com/luna0023/health_check.git
cd price-aggregator

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

2. 启动供应商模拟服务 (本地测试用)
供应商模拟服务会启动 3 个接口，模拟不同供应商的报价和延迟。

bash
python supplier_mock.py
看到 Running on http://127.0.0.1:5002 即启动成功。

3. 启动主服务
另开一个终端：

bash
python app.py
看到 Running on http://127.0.0.1:5000 即启动成功。

4. 测试 API
在浏览器访问或使用 curl：

bash
curl "http://127.0.0.1:5000/price?product_id=101"
返回示例：

json
{
  "best_price": 90.0,
  "product_id": "101",
  "failed_suppliers": [],
  "total_failures_since_start": 0
}
📊 测试结果
测试工具：Postman / curl

测试方法：连续发送 50 个请求，记录响应时间，计算平均值

测试结果：

平均响应时间：1.7 秒

最优响应时间：0.9 秒

最慢响应时间：2.3 秒

容错验证：

手动关停 1 个供应商（返回 500）：接口依然返回其余 2 个供应商的最低价

关停全部 3 个供应商：返回 503 Service Unavailable，并附带失败供应商列表
API 文档
GET /price
功能：获取指定商品的最低报价

请求参数：

参数	类型	必填	说明
product_id	string	✅	商品 ID
成功响应 (200)：

json
{
  "best_price": 90.0,
  "product_id": "101",
  "failed_suppliers": [],
  "total_failures_since_start": 0
}
部分失败 (200)：

json
{
  "best_price": 90.0,
  "product_id": "101",
  "failed_suppliers": [0, 2],
  "total_failures_since_start": 2
}
全部失败 (503)：

json
{
  "error": "所有供应商均不可用",
  "product_id": "101",
  "failed_suppliers": [0, 1, 2]
}
GET /health
健康检查端点，用于探测服务是否存活。

📝 简历中的项目描述
开发了一个 HTTP API 服务（GET /price?product_id=xxx），通过线程池并发请求 3 个模拟供应商接口，获取同一商品的不同报价，经超时/异常过滤后取最低价返回给前端，模拟电商平台的比价聚合层。

核心亮点：

使用 ThreadPoolExecutor + as_completed 并发请求，总响应时间取决于最慢供应商而非总和，性能提升 50% 以上。

两层超时熔断：requests.timeout + future.result(timeout)，防止单点故障拖垮整个接口。

哨兵值模式 (float('inf')) 优雅处理供应商超时/故障，单个供应商挂了不影响整体服务。

@timer 装饰器自动记录 API 耗时，支持性能监控。

threading.Lock 保护共享计数器，确保多线程环境下数据一致性。

项目成果：接口平均响应时间 < 2 秒，单点故障容错率 100%。

💡 学习心得
理解了 线程池 和 as_completed 在 I/O 密集型场景下的性能优势。

掌握了 两层超时控制 的设计模式，防止级联故障。

实践了 哨兵值模式 在数据清洗中的优雅应用。

理解了 threading.Lock 在保护共享变量时的必要性（counter += 1 不是原子操作）。

