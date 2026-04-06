#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大六壬禄马贵人到山到向完整模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules', 'engine'))

from daliuren_luma_guiren import DaLiuRenLuMaGuiRen
from sizhu_engine import get_sizhu

print("=" * 100)
print("测试大六壬禄马贵人到山到向完整模块")
print("=" * 100)

# 创建计算器
calculator = DaLiuRenLuMaGuiRen()

# 测试日期：2026-04-01 卯时
year = 2026
month = 4
day = 1
shichen = '卯'

print(f"\n测试日期: {year}年{month}月{day}日 {shichen}时")

# 获取四柱
sizhu_result = get_sizhu(year, month, day, shichen)
sizhu = {
    '年柱': sizhu_result.get('年柱', ''),
    '月柱': sizhu_result.get('月柱', ''),
    '日柱': sizhu_result.get('日柱', ''),
    '时柱': sizhu_result.get('时柱', '')
}

nian_gan = sizhu['年柱'][0]
nian_zhi = sizhu['年柱'][1]
yue_gan = sizhu['月柱'][0]
yue_zhi = sizhu['月柱'][1]
ri_gan = sizhu['日柱'][0]
ri_zhi = sizhu['日柱'][1]

print(f"\n四柱: 年{sizhu['年柱']} 月{sizhu['月柱']} 日{sizhu['日柱']} 时{sizhu['时柱']}")

# 测试壬山
print("\n" + "=" * 100)
print("测试 1: 壬山")
print("=" * 100)
result = calculator.analyze_full('壬', shichen, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi)
calculator.print_analysis(result)

# 测试丙山
print("\n" + "=" * 100)
print("测试 2: 丙山")
print("=" * 100)
result = calculator.analyze_full('丙', shichen, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi)
calculator.print_analysis(result)

# 测试子山
print("\n" + "=" * 100)
print("测试 3: 子山")
print("=" * 100)
result = calculator.analyze_full('子', shichen, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi)
calculator.print_analysis(result)

print("\n" + "=" * 100)
print("测试完成！")
print("=" * 100)
