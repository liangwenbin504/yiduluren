#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析特定日课的斗首评分"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer
from sizhu_engine import get_sizhu

print("=" * 70)
print("分析丁未 己酉 辛卯 丙申的斗首评分")
print("=" * 70)

# 坐山
shan = '壬'

# 四柱
sizhu = {
    '年柱': '丁未',
    '月柱': '己酉',
    '日柱': '辛卯',
    '时柱': '丙申'
}

print(f"\n坐山: {shan}山")
print(f"四柱: {sizhu['年柱']} {sizhu['月柱']} {sizhu['日柱']} {sizhu['时柱']}")

# 分析
analyzer = DouhouKegeAnalyzer()
result = analyzer.analyze_kege(shan, sizhu)

print(f"\n【分析结果】")
print(f"山家五行: {result.get('山家五行')}")
print(f"综合评分: {result.get('综合评分')}")
print(f"吉凶等级: {result.get('吉凶等级')}")
print(f"吉凶断语: {result.get('吉凶断语')}")

print(f"\n【四柱分析】")
for pillar, info in result.get('四柱分析', {}).items():
    print(f"  {pillar}: {info.get('干支')} 化气={info.get('化气五行')} 星曜={info.get('斗首星曜')}")

print(f"\n【六相六替分析】")
liuxiang = result.get('六相六替分析', {})
print(f"  六相统计: {liuxiang.get('六相统计', {})}")
print(f"  四柱六相:")
for pillar, info in liuxiang.get('四柱六相', {}).items():
    print(f"    {pillar}: 六相={info.get('六相')}, 番化={info.get('番化')}")

print(f"\n【课格格局】")
for pattern in result.get('课格格局', []):
    print(f"  {pattern.get('格局名称')}: {pattern.get('描述')} ({pattern.get('吉凶')})")

print(f"\n【日志】")
for log in result.get('日志', []):
    print(f"  {log}")

print("\n" + "=" * 70)
