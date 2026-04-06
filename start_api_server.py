#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动Flask API服务器并捕获错误
"""

import sys
import os
import traceback

try:
    # 导入api_server.py中的app
    from api_server import app
    
    print("正在启动Flask API服务器...")
    print("访问地址: http://localhost:5000")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except Exception as e:
    print(f"启动失败: {str(e)}")
    print("错误详情:")
    traceback.print_exc()
    
    # 检查是否缺少依赖
    print("\n检查依赖...")
    try:
        import flask
        print("✓ flask 已安装")
    except ImportError:
        print("✗ flask 未安装")
    
    try:
        from flask_cors import CORS
        print("✓ flask_cors 已安装")
    except ImportError:
        print("✗ flask_cors 未安装")
    
    try:
        from sizhu_engine import get_sizhu
        print("✓ sizhu_engine 已安装")
    except ImportError:
        print("✗ sizhu_engine 未安装")
    
    input("按任意键退出...")
