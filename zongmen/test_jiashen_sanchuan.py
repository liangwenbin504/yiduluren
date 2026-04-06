#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证甲申日的三传天干
"""

import sys
sys.path.append('d:\\新建文件夹\\仪度六壬择日\\yiduluren\\zongmen')

from http_api_server import get_xun_shou, get_stem_for_branch

print("=" * 70)
print("甲申日三传天干验证")
print("=" * 70)

# 甲申日
ri_gan, ri_zhi = '甲', '申'

# 获取旬首和空亡
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)

print(f"\n日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")

print("\n" + "=" * 70)
print("甲申旬遁干排布（正确的旬遁法）")
print("=" * 70)

branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
print("\n地支\t遁干\t说明")
print("-" * 70)

for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    is_kw = branch in kong_wang
    kw_mark = " [空亡]" if is_kw else ""
    
    # 标注三传辰巳午
    if branch in ['辰', '巳', '午']:
        print(f"{branch}\t{stem}\t← 三传地支 {kw_mark}")
    else:
        print(f"{branch}\t{stem}\t{kw_mark}")

print("\n" + "=" * 70)
print("三传天干分析")
print("=" * 70)

sanchuan_branches = ['辰', '巳', '午']
print("\n三传地支\t遁干\t完整干支")
print("-" * 70)

for branch in sanchuan_branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    ganzhi = stem + branch
    print(f"{branch}\t\t{stem}\t{ganzhi}")

print("\n" + "=" * 70)
print("对比：如果是戊己庚（错误的五子遁元法）")
print("=" * 70)

print("""
五子遁元法（日上起时法）- 错误的方法：
甲己还加甲（甲己日起甲子时）

从子位开始：
子 (甲)、丑 (乙)、寅 (丙)、卯 (丁)、辰 (戊)、巳 (己)、午 (庚)

这样会得到：
辰 (戊)、巳 (己)、午 (庚) ← 这是错误的！

错误原因：使用了五子遁元法，而不是旬遁法！
""")

print("\n" + "=" * 70)
print("正确的旬遁法排布")
print("=" * 70)

print("""
甲申旬，旬首甲申：
申 (甲)、酉 (乙)、戌 (丙)、亥 (丁)、子 (戊)、丑 (己)、
寅 (庚)、卯 (辛)、辰 (壬)、巳 (癸)、午 (甲)、未 (乙)

正确的三传天干：
辰 (壬)、巳 (癸)、午 (甲) ← 这才是正确的！
""")

print("=" * 70)
