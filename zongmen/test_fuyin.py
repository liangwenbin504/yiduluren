#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接测试伏吟课三传计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from sike_sanchuan_engine import SiKeSanChuanCalculator

calc = SiKeSanChuanCalculator()

# 测试甲子日 子将子时（伏吟课）
ri_gan = '甲'
ri_zhi = '子'
yue_jiang = '子'
shi_chen = '子'

print(f"测试：{ri_gan}{ri_zhi}日 {yue_jiang}将{shi_chen}时")
print("=" * 60)

# 计算天地盘
tiandi_pan = calc.get_tiandi_pan(yue_jiang, shi_chen)
print(f"天地盘：")
for dizhi in calc.DIZHI:
    print(f"  {dizhi} -> {tiandi_pan[dizhi]}")

# 起四课
sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
print(f"\n四课:")
for ke in sike:
    print(f"  {ke[0]}: 上{ke[1]} 下{ke[2]}")

# 发三传
sanchuan = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
print(f"\n三传:")
print(f"  起法：{sanchuan.get('起法', '')}")
print(f"  课体：{sanchuan.get('课体', '')}")
print(f"  初传：{sanchuan.get('初传', '')}")
print(f"  中传：{sanchuan.get('中传', '')}")
print(f"  末传：{sanchuan.get('末传', '')}")
print(f"  三传列表：{sanchuan.get('三传', [])}")

print("\n完整三传数据:")
import json
print(json.dumps(sanchuan, ensure_ascii=False, indent=2))
