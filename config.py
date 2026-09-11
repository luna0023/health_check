# -*- coding:utf-8 -*-
"""
模块：config.py
作用：存放所有配置常量，如超时时间、供应商接口地址等
好处：将配置与代码分离，便于在不同环境（开发/测试/生产）中修改，无需改动业务代码
"""
import os

REQUEST_TIMEOUT = 1.5

MAX_WORKERS = 3

SUPPLIERS = {
    "supplier_0": "http://127.0.0.1:5001/supplier/0",
    "supplier_1": "http://127.0.0.1:5001/supplier/1",
    "supplier_2": "http://127.0.0.1:5001/supplier/2",
}

LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "app.log")

