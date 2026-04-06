#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Waitress 启动 API 服务器（Windows 兼容）
"""

from waitress import serve
from api_server import app

print("=" * 60)
print("仪度六壬择日系统 API 服务器（Waitress 生产模式）")
print("=" * 60)
print("服务地址：http://localhost:5000")
print("线程数：4")
print("日志级别：INFO")
print("=" * 60)

# 使用 Waitress 启动
serve(
    app,
    host='0.0.0.0',
    port=5000,
    threads=4,
    url_scheme='http',
    channel_timeout=120,
    cleanup_interval=30,
)
