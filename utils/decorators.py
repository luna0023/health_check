# -*- coding:utf-8 -*-
"""
模块：decorators.py
作用：定义通用的函数装饰器，如接口耗时统计
知识点：闭包、装饰器语法、*args/**kwargs
"""

import time
import logging
from functools import wraps


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # perf_counter是干嘛的？
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logging.info(f"⏱️  {func.__name__} took {elapsed_ms:.2f} ms")
        return result
    return wrapper
