#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试天将计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from sike_sanchuan_engine import SiKeSanChuanCalculator

calc = SiKeSanChuanCalculator()

# 测试甲子日 子将子时
ri_gan = '甲'
ri_zhi = '子'
yue_jiang = '子'
shi_chen = '子'

print(f"测试：{ri_gan}{ri_zhi}日 {yue_jiang}将{shi_chen}时")
print("=" * 60)

# 计算天地盘
tiandi_pan = calc.get_tiandi_pan(yue_jiang, shi_chen)
print(f"天地盘：子 -> {tiandi_pan.get('子', 'N/A')}")

# 计算天将盘
print("\n计算天将盘...")
try:
    tian_jiang_map = calc.get_tian_jiang_pan(ri_gan, tiandi_pan, shi_chen)
    print(f"天将映射：{tian_jiang_map}")
    print(f"寅的天将：{tian_jiang_map.get('寅', 'NOT FOUND')}")
    print(f"子的天将：{tian_jiang_map.get('子', 'NOT FOUND')}")
except Exception as e:
    print(f"天将计算错误：{e}")
    import traceback
    traceback.print_exc()

# 起四课
print("\n起四课...")
try:
    sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan, shi_chen)
    for ke in sike:
        print(f"  {ke[0]}: 上{ke[1]} 下{ke[2]} ({ke[3]})")
except Exception as e:
    print(f"四课计算错误：{e}")
    import traceback
    traceback.print_exc()
