#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试导入 api_server 模块
"""

import sys
print("开始导入 api_server 模块...")

try:
    import api_server
    print("✅ 导入成功！")
except Exception as e:
    import traceback
    print(f"❌ 导入失败：{e}")
    print(f"\n详细错误:\n{traceback.format_exc()}")
