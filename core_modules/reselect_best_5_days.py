#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用六相六替完整系统重新择日（精确版）
基于已有的日课分析系统
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime
from liuxiang_liuti_complete_system import LiuXiangLiuTiSystem
from douhou_analyzer import DouhouKegeAnalyzer

print('=' * 80)
print('使用六相六替完整系统重新择日')
print('坐山：壬山')
print('分析已有的最佳日课')
print('=' * 80)

# 创建系统
liuxiang_system = LiuXiangLiuTiSystem()
douhou_analyzer = DouhouKegeAnalyzer()

# 使用之前找到的最佳日课（2026 年 3 月 24 日 -4 月 24 日范围）
# 现在用六相六替系统重新分析

test_cases = [
    {
        '公历': '2026 年 3 月 31 日',
        '时辰': '未时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '甲辰',
            '时柱': '辛未'
        }
    },
    {
        '公历': '2026 年 3 月 26 日',
        '时辰': '巳时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '己亥',
            '时柱': '己巳'
        }
    },
    {
        '公历': '2026 年 3 月 30 日',
        '时辰': '未时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '癸卯',
            '时柱': '己未'
        }
    },
    {
        '公历': '2026 年 4 月 7 日',
        '时辰': '申时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '辛亥',
            '时柱': '丙申'
        }
    },
    {
        '公历': '2026 年 4 月 22 日',
        '时辰': '申时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '丙寅',
            '时柱': '丙申'
        }
    }
]

print('\n重新分析 5 个最佳日课（使用六相六替完整系统）\n')
print('=' * 80)

results = []

for i, case in enumerate(test_cases, 1):
    print(f'\n【第 {i} 吉课】')
    print(f'公历：{case["公历"]} {case["时辰"]}')
    print('-' * 80)
    
    sizhu = case['sizhu']
    riganzhi = sizhu['日柱']
    tiangan = riganzhi[0]
    dizhi = riganzhi[1]
    
    # 1. 六相六替分析
    print('\n【六相六替分析】')
    liuxiang_result = liuxiang_system.analyze_day(tiangan, dizhi)
    print(f'  日柱：{riganzhi}')
    print(f'  状态：{liuxiang_result["状态"]} ({liuxiang_result["六相/六替"]}, {liuxiang_result["吉凶"]})')
    print(f'  分数：{liuxiang_result["分数"]}分')
    print(f'  含义：{liuxiang_result["含义"]}')
    
    # 2. 四柱六相六替分析
    print('\n【四柱六相六替统计】')
    sizhu_analysis = liuxiang_system.analyze_sizhu(sizhu)
    print(f'  六相数：{sizhu_analysis["六相统计"]}')
    print(f'  六替数：{sizhu_analysis["六替统计"]}')
    print(f'  总评分：{sizhu_analysis["总评分"]}分')
    print(f'  吉凶判断：{sizhu_analysis["吉凶判断"]}')
    
    # 3. 斗首分析
    print('\n【斗首课格分析】')
    douhou_result = douhou_analyzer.analyze_kege('壬', sizhu)
    print(f'  综合评分：{douhou_result["综合评分"]}分')
    
    if douhou_result.get('课格格局'):
        print(f'  课格格局：')
        for pattern in douhou_result['课格格局'][:3]:
            print(f'    - {pattern.get("格局名称", "未知")} ({pattern.get("吉凶", "未知")})')
    
    if douhou_result.get('吉凶断语'):
        print(f'  吉凶断语：')
        for duanyu in douhou_result['吉凶断语'][:2]:
            print(f'    - {duanyu}')
    
    # 4. 综合评分
    total_score = (
        liuxiang_result['分数'] * 0.3 +
        sizhu_analysis['总评分'] * 0.3 +
        douhou_result['综合评分'] * 0.4
    )
    
    print(f'\n【综合评分】{total_score:.1f}分')
    
    # 5. 核心诀法
    print(f'\n【核心诀法提醒】')
    if sizhu_analysis['六相统计'] >= 3:
        print(f'  ✓ 符合"三元三武吉，富贵永安康"')
    if sizhu_analysis['六相统计'] >= 2:
        print(f'  ✓ 符合"三吉喜居六相支"')
    if liuxiang_result['六相/六替'] == '六相':
        print(f'  ✓ 日柱居六相，吉')
    
    # 6. 补救建议
    if sizhu_analysis['六替统计'] > sizhu_analysis['六相统计']:
        print(f'\n【补救建议】')
        best_remedy = liuxiang_system.remedy.get_best_remedy()
        print(f'  推荐：{best_remedy.method}')
        print(f'  {best_remedy.description}')
    
    results.append({
        '公历': case['公历'],
        '时辰': case['时辰'],
        '日柱': riganzhi,
        '六相六替分数': liuxiang_result['分数'],
        '四柱总评分': sizhu_analysis['总评分'],
        '斗首分数': douhou_result['综合评分'],
        '综合评分': total_score
    })

# 总结
print('\n' + '=' * 80)
print('5 个吉日综合对比')
print('=' * 80)

print(f'\n{"排名":<4} {"公历":<12} {"时辰":<6} {"日柱":<6} {"六相":<6} {"四柱":<6} {"斗首":<6} {"综合":<6}')
print('-' * 80)

results.sort(key=lambda x: x['综合评分'], reverse=True)

for i, r in enumerate(results, 1):
    print(f'{i:<4} {r["公历"]:<12} {r["时辰"]:<6} {r["日柱"]:<6} '
          f'{r["六相六替分数"]:<6} {r["四柱总评分"]:<6} {r["斗首分数"]:<6} {r["综合评分"]:<6.1f}')

print('\n' + '=' * 80)
print('最终推荐（前 3 个）')
print('=' * 80)

for i, r in enumerate(results[:3], 1):
    print(f'\n第{i}名：{r["公历"]} {r["时辰"]}（{r["日柱"]}日）')
    print(f'  综合评分：{r["综合评分"]:.1f}分')
    print(f'  六相六替：{r["六相六替分数"]}分')
    print(f'  四柱分析：{r["四柱总评分"]}分')
    print(f'  斗首分析：{r["斗首分数"]}分')

print('\n' + '=' * 80)
print('分析完成')
print('=' * 80)
