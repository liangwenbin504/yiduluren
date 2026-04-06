#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试旬遁法计算
"""

# 导入函数
import sys
sys.path.append('d:\\新建文件夹\\仪度六壬择日\\yiduluren\\zongmen')

from http_api_server import get_xun_shou, get_stem_for_branch

# 测试 1：甲子日（甲子旬，戌亥空）
print("测试 1：甲子日（甲子旬，戌亥空）")
print("=" * 60)
ri_gan, ri_zhi = '甲', '子'
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)
print(f"日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")
print(f"旬遁排布：子 (甲)、丑 (乙)、寅 (丙)、卯 (丁)、辰 (戊)、巳 (己)、午 (庚)、未 (辛)、申 (壬)、酉 (癸)、戌 (甲)、亥 (乙)")
print()

# 测试各地支的遁干
branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    kw_mark = " [空亡]" if branch in kong_wang else ""
    print(f"  {branch}: {stem}{kw_mark}")

print()
print()

# 测试 2：乙丑日（甲子旬，戌亥空）
print("测试 2：乙丑日（甲子旬，戌亥空）")
print("=" * 60)
ri_gan, ri_zhi = '乙', '丑'
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)
print(f"日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")
print(f"旬遁排布：子 (癸)、丑 (甲)、寅 (乙)、卯 (丙)、辰 (丁)、巳 (戊)、午 (己)、未 (庚)、申 (辛)、酉 (壬)、戌 (癸)、亥 (甲)")
print()

for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    kw_mark = " [空亡]" if branch in kong_wang else ""
    print(f"  {branch}: {stem}{kw_mark}")

print()
print()

# 测试 3：丙寅日（甲子旬，戌亥空）
print("测试 3：丙寅日（甲子旬，戌亥空）")
print("=" * 60)
ri_gan, ri_zhi = '丙', '寅'
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)
print(f"日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")
print()

for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    kw_mark = " [空亡]" if branch in kong_wang else ""
    print(f"  {branch}: {stem}{kw_mark}")

print()
print()

# 测试 4：甲戌日（甲戌旬，申酉空）
print("测试 4：甲戌日（甲戌旬，申酉空）")
print("=" * 60)
ri_gan, ri_zhi = '甲', '戌'
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)
print(f"日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")
print(f"旬遁排布：戌 (甲)、亥 (乙)、子 (丙)、丑 (丁)、寅 (戊)、卯 (己)、辰 (庚)、巳 (辛)、午 (壬)、未 (癸)、申 (甲)、酉 (乙)")
print()

for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    kw_mark = " [空亡]" if branch in kong_wang else ""
    print(f"  {branch}: {stem}{kw_mark}")
