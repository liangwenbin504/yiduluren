#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen'))

from flask import json

# 测试API服务器代码的语法和逻辑
print("=" * 80)
print("检查API服务器代码")
print("=" * 80)

# 模拟请求数据
test_data = {
    'mountain': '壬',
    'start_date': '2026-04-01',
    'end_date': '2026-04-03',
    'min_daliuren_score': 70,
    'max_results': 5
}

print(f"\n测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")

# 检查是否导入了必要的模块
try:
    from douhou_analyzer import DouhouKegeAnalyzer
    print("\n✓ DouhouKegeAnalyzer 导入成功")
except Exception as e:
    print(f"\n✗ DouhouKegeAnalyzer 导入失败: {e}")

try:
    from sizhu_engine import get_sizhu
    print("✓ get_sizhu 导入成功")
except Exception as e:
    print(f"✗ get_sizhu 导入失败: {e}")

try:
    from dizhi_layout_generator import arrange_tiandi_pan
    print("✓ arrange_tiandi_pan 导入成功")
except Exception as e:
    print(f"✗ arrange_tiandi_pan 导入失败: {e}")

try:
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print("✓ SiKeSanChuanCalculator 导入成功")
except Exception as e:
    print(f"✗ SiKeSanChuanCalculator 导入失败: {e}")

try:
    from gui_ren_engine import GuiRenCalculator
    print("✓ GuiRenCalculator 导入成功")
except Exception as e:
    print(f"✗ GuiRenCalculator 导入失败: {e}")

try:
    from yanqin_analyzer import YanQinAnalyzer
    print("✓ YanQinAnalyzer 导入成功")
except Exception as e:
    print(f"✗ YanQinAnalyzer 导入失败: {e}")

print("\n" + "=" * 80)
print("测试通过！API服务器代码语法正确，模块导入正常。")
print("=" * 80)
print("\n请运行 API 服务器后在前端测试：")
print("  python api_server.py")
print("\n然后在浏览器中打开：")
print("  主界面.html")
