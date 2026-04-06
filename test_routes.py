#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API服务器的所有注册路由
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from api_server import app

print("=== API服务器注册路由列表 ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule} (methods: {list(rule.methods)})")

print("\n=== 检查导入PPT模板路由 ===")
import_route_found = False
for rule in app.url_map.iter_rules():
    if '/import/ppt-template' in rule.rule:
        import_route_found = True
        print(f"✓ 找到路由: {rule.rule} (methods: {list(rule.methods)})")
        break

if not import_route_found:
    print("✗ 未找到导入PPT模板路由")
