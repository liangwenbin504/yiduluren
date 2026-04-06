#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比分析2026年和2027年吉课的六壬评分"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from daliuren_luma_guiren import DaLiuRenLuMaGuiRen
from kejing_scoring import KeJingScoring
from sike_sanchuan_engine import SiKeSanChuanCalculator
from data.斗首择日规则 import DIZHI

print("=" * 70)
print("对比分析2026年和2027年吉课的六壬评分")
print("=" * 70)

# 2026年丙午年的课
print("\n【2026年丙午年】2026-09-22 寅时")
sizhu_2026 = {'年柱': '丙午', '月柱': '丁酉', '日柱': '辛巳', '时柱': '庚寅'}
shan = '壬'
shichen = '寅'

# 计算六壬评分
luma_calc = DaLiuRenLuMaGuiRen()
kejing_scorer = KeJingScoring()
sike_calc = SiKeSanChuanCalculator()

# 禄马贵人评分
nian_gan = sizhu_2026['年柱'][0]
nian_zhi = sizhu_2026['年柱'][1]
yue_gan = sizhu_2026['月柱'][0]
yue_zhi = sizhu_2026['月柱'][1]
ri_gan = sizhu_2026['日柱'][0]
ri_zhi = sizhu_2026['日柱'][1]

luma_result = luma_calc.analyze_full(shan, shichen, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi)
print(f"禄马贵人评分: {luma_result.get('score')}")
print(f"状态: {luma_result.get('status')}")
print(f"合格数: {luma_result.get('qualified_count')}/3")

# 课格评分
shi_index = DIZHI.index(shichen)
tiandi_pan = {}
for i, dz in enumerate(DIZHI):
    tiandi_pan[dz] = DIZHI[(i + shi_index) % 12]

sike = sike_calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
sanchuan = sike_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
keti = sanchuan.get('课体', '')
keti_name = keti.replace('课', '') if keti else ''
kejing_score = kejing_scorer.calculate_score(keti_name) * 10
print(f"课体: {keti}")
print(f"课格评分: {kejing_score}")

# 六壬总分
daliuren_score = int(kejing_score * 0.4 + luma_result.get('score', 0) * 0.6)
print(f"六壬总分: {daliuren_score}")

print("\n" + "=" * 70)
print("【2027年丁未年】2027-09-09 申时")
sizhu_2027 = {'年柱': '丁未', '月柱': '己酉', '日柱': '辛卯', '时柱': '丙申'}
shichen = '申'

# 禄马贵人评分
nian_gan = sizhu_2027['年柱'][0]
nian_zhi = sizhu_2027['年柱'][1]
yue_gan = sizhu_2027['月柱'][0]
yue_zhi = sizhu_2027['月柱'][1]
ri_gan = sizhu_2027['日柱'][0]
ri_zhi = sizhu_2027['日柱'][1]

luma_result = luma_calc.analyze_full(shan, shichen, nian_gan, nian_zhi, yue_gan, yue_zhi, ri_gan, ri_zhi)
print(f"禄马贵人评分: {luma_result.get('score')}")
print(f"状态: {luma_result.get('status')}")
print(f"合格数: {luma_result.get('qualified_count')}/3")

# 课格评分
shi_index = DIZHI.index(shichen)
tiandi_pan = {}
for i, dz in enumerate(DIZHI):
    tiandi_pan[dz] = DIZHI[(i + shi_index) % 12]

sike = sike_calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
sanchuan = sike_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
keti = sanchuan.get('课体', '')
keti_name = keti.replace('课', '') if keti else ''
kejing_score = kejing_scorer.calculate_score(keti_name) * 10
print(f"课体: {keti}")
print(f"课格评分: {kejing_score}")

# 六壬总分
daliuren_score = int(kejing_score * 0.4 + luma_result.get('score', 0) * 0.6)
print(f"六壬总分: {daliuren_score}")

print("\n" + "=" * 70)
print("【结论】")
print("=" * 70)
print("""
问题根源：
1. 六壬评分 = 课格分×40% + 禄马贵人分×60%
2. 禄马贵人评分占比过高（60%）
3. 2027年的课禄马贵人评分更高，导致六壬总分更高

建议：
- 调整评分权重，降低禄马贵人评分占比
- 或者将斗首评分权重提高
""")
