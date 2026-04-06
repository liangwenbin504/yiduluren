#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试大六壬 API 函数（不通过 HTTP）
"""

import sys
import os

# 添加所有路径
paths_to_add = [
    os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'),
    os.path.join(os.path.dirname(__file__), 'src', 'utils'),
    os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'),
    os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine')
]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

print("导入模块...")
from sike_sanchuan_engine import SiKeSanChuanCalculator
from gui_ren_engine import GuiRenCalculator
from dizhi_layout_generator import arrange_tiandi_pan

print("✅ 模块导入成功！")

print("\n测试排天地盘...")
try:
    tiandi_pan = arrange_tiandi_pan('亥', '寅')
    print(f"✅ 成功！天地盘：{len(tiandi_pan)} 个")
except Exception as e:
    import traceback
    print(f"❌ 失败：{e}")
    print(traceback.format_exc())

print("\n测试起四课...")
try:
    calc = SiKeSanChuanCalculator()
    sike = calc.qi_sike('甲', '子', tiandi_pan)
    print(f"✅ 成功！四课：{len(sike)} 个")
except Exception as e:
    import traceback
    print(f"❌ 失败：{e}")
    print(traceback.format_exc())

print("\n测试发三传...")
try:
    sanchuan = calc.fa_sanchuan(sike, '甲', '子', tiandi_pan)
    print(f"✅ 成功！课体：{sanchuan.get('课体', '无')}")
except Exception as e:
    import traceback
    print(f"❌ 失败：{e}")
    print(traceback.format_exc())

print("\n测试贵人...")
try:
    gui_ren_calc = GuiRenCalculator()
    guiren_info = gui_ren_calc.arrange_gui_ren_pan('甲', {'天地对应': tiandi_pan}, '寅')
    print(f"✅ 成功！贵人：{guiren_info}")
except Exception as e:
    import traceback
    print(f"❌ 失败：{e}")
    print(traceback.format_exc())
