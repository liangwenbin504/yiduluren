#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - PythonAnywhere WSGI 配置文件
"""

import os
import sys

# 添加项目路径（优先从 engine/ 目录导入）
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)
    sys.path.insert(0, os.path.join(project_home, 'engine'))
    sys.path.insert(0, os.path.join(project_home, 'core_modules'))

# 设置环境变量
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TZ'] = 'Asia/Shanghai'

# 导入 Flask 应用
from api_server import app as application
