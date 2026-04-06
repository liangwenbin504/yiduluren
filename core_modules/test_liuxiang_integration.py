#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试斗首择日六相六替之法集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime
from douhou_analyzer import DouhouKegeAnalyzer

print('=' * 80)
print('斗首择日 - 六相六替之法集成测试')
print('=' * 80)

analyzer = DouhouKegeAnalyzer()

# 测试案例：2026 年 3 月 31 日未时 壬山（最佳日课）
print('\n【测试案例 1】2026 年 3 月 31 日未时 壬山')
print('-' * 80)

sizhu = {
    '年柱': '丙午',
    '月柱': '辛卯',
    '日柱': '甲辰',
    '时柱': '辛未'
}

result = analyzer.analyze_kege('壬', sizhu)

print(f"坐山：{result['坐山']}山（{result['山家五行']}）")
print(f"四柱：{result['四柱分析']['年柱']['干支']} {result['四柱分析']['月柱']['干支']} {result['四柱分析']['日柱']['干支']} {result['四柱分析']['时柱']['干支']}")

print(f"\n【四柱斗首分析】")
for pillar, data in result['四柱分析'].items():
    print(f"  {pillar}: {data['干支']} - {data['斗首星曜']} (化气：{data['化气五行']})")

print(f"\n【六相六替分析】")
liuxiang = result['六相六替分析']
print(f"  山家五行：{liuxiang['山家五行']}")
print(f"  六相统计：")
for star, count in liuxiang['六相统计'].items():
    print(f"    {star}: {count}重")

print(f"  三元分析：")
sanyuan = liuxiang['三元分析']
print(f"    天元：{', '.join(sanyuan['天元'])}")
print(f"    地元：{', '.join(sanyuan['地元'])}")
print(f"    人元：{sanyuan['人元']}")

print(f"\n【课格格局】")
for pattern in result['课格格局']:
    print(f"  - {pattern['格局名称']} ({pattern['吉凶']})")
    print(f"    {pattern['描述']}")

print(f"\n【综合评分】{result['综合评分']}分")

print(f"\n【吉凶断语】")
for duanyu in result['吉凶断语']:
    print(f"  - {duanyu}")

# 测试案例 2：2026 年 3 月 26 日巳时 壬山
print('\n' + '=' * 80)
print('\n【测试案例 2】2026 年 3 月 26 日巳时 壬山')
print('-' * 80)

sizhu2 = {
    '年柱': '丙午',
    '月柱': '辛卯',
    '日柱': '己亥',
    '时柱': '己巳'
}

result2 = analyzer.analyze_kege('壬', sizhu2)

print(f"坐山：{result2['坐山']}山（{result2['山家五行']}）")
print(f"四柱：{result2['四柱分析']['年柱']['干支']} {result2['四柱分析']['月柱']['干支']} {result2['四柱分析']['日柱']['干支']} {result2['四柱分析']['时柱']['干支']}")

print(f"\n【六相统计】")
for star, count in result2['六相六替分析']['六相统计'].items():
    print(f"  {star}: {count}重")

print(f"\n【课格格局】")
for pattern in result2['课格格局']:
    print(f"  - {pattern['格局名称']} ({pattern['吉凶']})")

print(f"\n【综合评分】{result2['综合评分']}分")

print(f"\n【吉凶断语】")
for duanyu in result2['吉凶断语']:
    print(f"  - {duanyu}")

print('\n' + '=' * 80)
print('测试完成')
print('=' * 80)
