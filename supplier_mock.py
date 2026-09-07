# -*- coding:utf-8 -*-
"""
供应商模拟服务（数据驱动版）
从 data/prices.json 读取价格数据，支持不同 product_id 返回不同价格。
"""
import json
import logging
import os
import random
import time
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'prices.json')


def load_prices():
    # 从JSON文件加载价格数据，如果文件不存在或格式错误则返回空字典
    if not os.path.exists(DATA_FILE):
        print(f"⚠️ 警告: 数据文件 {DATA_FILE} 不存在，使用空数据")
        logging.warning(f"⚠️ 警告: 数据文件 {DATA_FILE} 不存在，使用空数据")
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # json.load(f)什么意思来着？
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ 警告: {DATA_FILE} 格式错误，使用空数据")
        logging.warning(f"️ 警告: {DATA_FILE} 格式错误，使用空数据")
        return {}


PRICE_DATA = load_prices()


@app.route('/supplier/<int:supplier_id>', methods=['GET'])
def get_price(supplier_id):
    """
        供应商接口：根据供应商ID和查询参数 product_id 返回价格
        模拟真实场景：随机延迟、偶发500错误、数据缺失处理
        """
    # 1. 模拟随机延迟（0.2~1.5秒，让并发效果明显）
    time.sleep(random.uniform(0.2, 1.5))

    # 2. 模拟10%概率的服务内部错误(锻炼主服务的容错能力)
    if random.random() < 0.1:
        return jsonify({"error": "Internal SERVER ERROR"}), 500

    # 3. 获取商品id
    product_id = request.args.get('product_id')
    if not product_id:
        return jsonify({"error": "No product_id"}), 400

    # 4. 从数据中查找价格
    supplier_key = f"supplier_{supplier_id}"
    supplier_data = PRICE_DATA.get(supplier_key, {})

    # 如果该供应商没有这个商品数据，返回一个超大值（模拟无库存或报错）
    if product_id not in supplier_data:
        print(f"⚠️ 供应商 {supplier_id} 没有商品 {product_id} 的数据")
        logging.warning(f"⚠️ 供应商 {supplier_id} 没有商品 {product_id} 的数据")
        return jsonify({"price": 9999.0}), 200

    price = supplier_data[product_id]
    print(f"✅ 供应商 {supplier_id} 为商品 {product_id} 报价: {price}")
    logging.warning(f"✅ 供应商 {supplier_id} 为商品 {product_id} 报价: {price}")
    return jsonify({"price": price}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
