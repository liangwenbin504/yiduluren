#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - 启动脚本（使用 Waitress WSGI 服务器）
"""

import os
import sys
from waitress import serve

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

# 导入 Flask 应用
from api_server import app

def start_with_waitress():
    """使用 Waitress 启动服务器"""
    print("=" * 80)
    print("仪度六壬择日系统 - 生产服务器")
    print("=" * 80)
    print("使用 Waitress WSGI 服务器启动...")
    print("服务配置:")
    print(f"- 主机: 0.0.0.0")
    print(f"- 端口: 5000")
    print("=" * 80)
    
    # 启动 Waitress 服务器
    serve(app, host='0.0.0.0', port=5000, threads=4)

if __name__ == '__main__':
    start_with_waitress()