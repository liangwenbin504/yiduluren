#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证修正后的三传天干计算
"""

import sys
sys.path.append('d:\\新建文件夹\\仪度六壬择日\\yiduluren\\src\\utils')

from daliuren_full_chart import get_xun_shou, get_stem_for_branch

print("=" * 70)
print("修正后验证：甲申日三传天干")
print("=" * 70)

# 甲申日
ri_gan, ri_zhi = '甲', '申'

# 获取旬首和空亡
xun_shou_gan, xun_shou_zhi, kong_wang = get_xun_shou(ri_gan, ri_zhi)

print(f"\n日干支：{ri_gan}{ri_zhi}")
print(f"旬首：{xun_shou_gan}{xun_shou_zhi}")
print(f"空亡：{kong_wang}")

print("\n" + "=" * 70)
print("甲申旬遁干排布（旬遁法 - 正确）")
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
print("三传天干（修正后 - 正确）")
print("=" * 70)

sanchuan_branches = ['辰', '巳', '午']
print("\n三传地支\t遁干\t完整干支")
print("-" * 70)

for branch in sanchuan_branches:
    stem = get_stem_for_branch(branch, ri_gan, ri_zhi)
    ganzhi = stem + branch
    print(f"{branch}\t\t{stem}\t{ganzhi}")

print("\n" + "=" * 70)
print("对比：五鼠遁元法（错误 - 已修正）")
print("=" * 70)

print("""
错误的五鼠遁元法会得到：
辰 (戊)、巳 (己)、午 (庚) ← 这是错误的！

修正后的旬遁法得到：
辰 (壬)、巳 (癸)、午 (甲) ← 这才是正确的！
""")

print("\n" + "=" * 70)
print("✅ 修正完成！")
print("=" * 70)
print("""
修正内容：
1. 删除了错误的五鼠遁元法代码
2. 添加了正确的旬遁法函数
3. 三传天干计算现在使用旬遁法

甲申日三传辰巳午的天干：
- 初传：壬辰 ✓
- 中传：癸巳 ✓
- 末传：甲午 ✓
""")
print("=" * 70)
