#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
甲申旬空亡验证
"""

import sys
sys.path.append('d:\\新建文件夹\\仪度六壬择日\\yiduluren\\zongmen')

from http_api_server import get_xun_shou, get_stem_for_branch

print("=" * 70)
print("甲申旬空亡验证")
print("=" * 70)

# 甲申旬的日干支
ri_gan, ri_zhi = '甲', '申'

# 获取旬首和空亡
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)

print(f"\n日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"地支空亡：{kong_wang}")

print("\n" + "=" * 70)
print("甲申旬遁干排布")
print("=" * 70)

branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
print("\n地支\t遁干\t空亡标记")
print("-" * 70)

for branch in branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    is_kw = branch in kong_wang
    kw_mark = " [空亡]" if is_kw else ""
    print(f"{branch}\t{stem}\t{kw_mark}")

print("\n" + "=" * 70)
print("三传辰巳午的天干分析")
print("=" * 70)

sanchuan_branches = ['辰', '巳', '午']
print("\n三传地支\t遁干\t完整干支")
print("-" * 70)

for branch in sanchuan_branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    ganzhi = stem + branch
    is_kw = branch in kong_wang
    kw_mark = " [空亡]" if is_kw else ""
    print(f"{branch}\t\t{stem}\t{ganzhi}{kw_mark}")

print("\n" + "=" * 70)
print("壬癸空亡的理论分析")
print("=" * 70)

print("""
1. 旬遁规则：
   - 甲申旬：申 (甲)、酉 (乙)、戌 (丙)、亥 (丁)、子 (戊)、丑 (己)、
            寅 (庚)、卯 (辛)、辰 (壬)、巳 (癸)、午 (甲)、未 (乙)
   
2. 地支空亡：
   - 午、未为空亡（旬后两位）
   
3. 三传辰巳午：
   - 初传：壬辰（水库）
   - 中传：癸巳（火之临官）
   - 末传：甲午（火之帝旺）
   
4. 壬癸空亡的含义：
   a) 旬尾说：壬辰、癸巳是旬尾，有交接之意
   b) 火局说：辰巳午为火局，壬癸水被火蒸干
   c) 纳音说：壬辰癸巳长流水，在火局中被蒸发
   
5. 实际占断：
   - 初传壬辰空：开始虚诈
   - 中传癸巳空：中间有阻
   - 末传甲午实：最终能成
   
6. 填实应期：
   - 壬空：逢壬日、壬时、辰年填实
   - 癸空：逢癸日、时、巳年填实
""")

print("=" * 70)
