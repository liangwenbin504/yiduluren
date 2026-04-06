#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比分析丙午年与丁未年的斗首格局"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer

print("=" * 70)
print("对比分析：丙午年 vs 丁未年 的斗首格局")
print("=" * 70)

analyzer = DouhouKegeAnalyzer()

# 壬山
shan = '壬'

print(f"\n【壬山斗首五行】")
print(f"  山家五行: {analyzer.get_shan_jia_wuxing(shan)}")
print(f"  （壬山属土，斗首以土为山家）")

print(f"\n【天干化气与六亲关系】")
for gan in ['丙', '丁', '己', '辛']:
    huaqi = analyzer.get_tiangan_huaqi(gan)
    liuqin = analyzer.get_liuqin('土', huaqi)
    print(f"  {gan} -> 化{huaqi} -> {liuqin}")

print("\n" + "=" * 70)
print("方案一：丁未年（原课）")
print("=" * 70)

sizhu1 = {
    '年柱': '丁未',
    '月柱': '己酉',
    '日柱': '辛卯',
    '时柱': '丙申'
}

result1 = analyzer.analyze_kege(shan, sizhu1)
print(f"四柱: {sizhu1['年柱']} {sizhu1['月柱']} {sizhu1['日柱']} {sizhu1['时柱']}")
print(f"综合评分: {result1.get('综合评分')}")
print(f"吉凶等级: {result1.get('吉凶等级')}")

print(f"\n四柱分析:")
for pillar, info in result1.get('四柱分析', {}).items():
    print(f"  {pillar}: {info.get('干支')} 化气={info.get('化气五行')} 星曜={info.get('斗首星曜')}")

print(f"\n六相统计: {result1.get('六相六替分析', {}).get('六相统计', {})}")
print(f"课格格局:")
for pattern in result1.get('课格格局', []):
    print(f"  - {pattern.get('格局名称')}: {pattern.get('描述')}")

print("\n" + "=" * 70)
print("方案二：丙午年（假设）")
print("=" * 70)

sizhu2 = {
    '年柱': '丙午',
    '月柱': '己酉',
    '日柱': '辛卯',
    '时柱': '丙申'
}

result2 = analyzer.analyze_kege(shan, sizhu2)
print(f"四柱: {sizhu2['年柱']} {sizhu2['月柱']} {sizhu2['日柱']} {sizhu2['时柱']}")
print(f"综合评分: {result2.get('综合评分')}")
print(f"吉凶等级: {result2.get('吉凶等级')}")

print(f"\n四柱分析:")
for pillar, info in result2.get('四柱分析', {}).items():
    print(f"  {pillar}: {info.get('干支')} 化气={info.get('化气五行')} 星曜={info.get('斗首星曜')}")

print(f"\n六相统计: {result2.get('六相六替分析', {}).get('六相统计', {})}")
print(f"课格格局:")
for pattern in result2.get('课格格局', []):
    print(f"  - {pattern.get('格局名称')}: {pattern.get('描述')}")

print("\n" + "=" * 70)
print("【专业分析】")
print("=" * 70)
print("""
1. 丁未年（破鬼）分析：
   - 丁壬化木，木克土（山家）
   - 破鬼为凶星，但此课有特殊格局
   
2. 丙午年（武财）分析：
   - 丙辛化水，水生土（山家）
   - 武财为吉星，生山家
   
3. 关键差异：
   - 丁未年：破鬼1个 + 元辰1个 + 武财2个
   - 丙午年：武财3个 + 元辰1个
   
4. 斗首理论分析：
   - 丁未年虽年柱为破鬼，但月日时三柱配合得当
   - 双武财制伏单破鬼，形成"武财关鬼格"
   - 丙午年虽年柱为武财，但武财过多也可能有"财多身弱"之嫌
   
5. 结论：
   - 两个方案都是吉课
   - 丁未年：100分（武财关鬼格）
   - 丙午年：需要计算确认
""")

print("\n" + "=" * 70)
