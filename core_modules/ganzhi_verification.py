#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六相六替四柱干支详细对照表
用于与资料印证核对
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime
from liuxiang_liuti_complete_system import LiuXiangLiuTiSystem
from douhou_analyzer import DouhouKegeAnalyzer

print('=' * 100)
print('六相六替四柱干支详细对照表')
print('用于与资料印证核对')
print('=' * 100)

# 创建系统
liuxiang_system = LiuXiangLiuTiSystem()
douhou_analyzer = DouhouKegeAnalyzer()

# 5 个日课的四柱干支
test_cases = [
    {
        '排名': 1,
        '公历': '2026 年 4 月 22 日',
        '时辰': '申时 (15:00-17:00)',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '丙寅',
            '时柱': '丙申'
        }
    },
    {
        '排名': 2,
        '公历': '2026 年 3 月 31 日',
        '时辰': '未时 (13:00-15:00)',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '甲辰',
            '时柱': '辛未'
        }
    },
    {
        '排名': 3,
        '公历': '2026 年 3 月 26 日',
        '时辰': '巳时 (09:00-11:00)',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '己亥',
            '时柱': '己巳'
        }
    },
    {
        '排名': 4,
        '公历': '2026 年 4 月 7 日',
        '时辰': '申时 (15:00-17:00)',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '辛亥',
            '时柱': '丙申'
        }
    },
    {
        '排名': 5,
        '公历': '2026 年 3 月 30 日',
        '时辰': '未时 (13:00-15:00)',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '癸卯',
            '时柱': '己未'
        }
    }
]

# 打印总表
print('\n' + '='*100)
print('【总表】5 个日课四柱干支对照')
print('='*100)

header = f'{"排名":<4} {"公历":<15} {"时辰":<20} {"年柱":<8} {"月柱":<8} {"日柱":<8} {"时柱":<8}'
print(header)
print('-'*100)

for case in test_cases:
    sizhu = case['sizhu']
    row = f'{case["排名"]:<4} {case["公历"]:<15} {case["时辰"]:<20} {sizhu["年柱"]:<8} {sizhu["月柱"]:<8} {sizhu["日柱"]:<8} {sizhu["时柱"]:<8}'
    print(row)

print('='*100)

# 逐个详细分析
print('\n' + '='*100)
print('【分课详解】')
print('='*100)

for case in test_cases:
    print(f'\n{"="*100}')
    print(f'第{case["排名"]}名：{case["公历"]} {case["时辰"]}')
    print(f'{"="*100}')
    
    sizhu = case['sizhu']
    
    # 打印四柱干支
    print('\n【四柱干支】')
    print(f'  年柱：{sizhu["年柱"]}')
    print(f'  月柱：{sizhu["月柱"]}')
    print(f'  日柱：{sizhu["日柱"]}')
    print(f'  时柱：{sizhu["时柱"]}')
    
    # 逐柱六相六替分析
    print('\n【逐柱六相六替分析】')
    print('-'*100)
    
    pillar_details = []
    liuxiang_count = 0
    liuti_count = 0
    total_score = 0
    
    for pillar_name, ganzhi in sizhu.items():
        tiangan = ganzhi[0]
        dizhi = ganzhi[1]
        
        # 查询状态
        state = liuxiang_system.query_table.get_state_by_zhi(tiangan, dizhi)
        is_liuxiang = liuxiang_system.query_table.is_liuxiang_zhi(tiangan, dizhi)
        state_info = liuxiang_system.states.get_state_info(state)
        
        if is_liuxiang:
            liuxiang_count += 1
        else:
            liuti_count += 1
        
        score = state_info.score if state_info else 50
        total_score += score
        
        # 打印该柱详情
        print(f'\n{pillar_name}：{ganzhi}')
        print(f'  天干：{tiangan}')
        print(f'  地支：{dizhi}')
        print(f'  状态：{state}')
        print(f'  类型：{"六相【吉】" if is_liuxiang else "六替【凶】"}')
        print(f'  分数：{score}分')
        print(f'  含义：{state_info.meaning if state_info else "未知"}')
        
        pillar_details.append({
            'name': pillar_name,
            'ganzhi': ganzhi,
            'tiangan': tiangan,
            'dizhi': dizhi,
            'state': state,
            'is_liuxiang': is_liuxiang,
            'score': score
        })
    
    # 综合统计
    print(f'\n\n【综合统计】')
    print('-'*100)
    avg_score = total_score / 4
    print(f'六相数：{liuxiang_count}个（吉）')
    print(f'六替数：{liuti_count}个（凶）')
    print(f'四柱总分：{total_score}分')
    print(f'四柱平均分：{avg_score:.1f}分')
    
    # 吉凶格局
    if liuxiang_count == 4:
        jige = '上上大吉（四柱皆六相）'
    elif liuxiang_count == 3:
        jige = '大吉（三吉一凶）'
    elif liuxiang_count == 2:
        jige = '中吉（二吉二凶）'
    elif liuxiang_count == 1:
        jige = '小吉（一吉三凶）'
    else:
        jige = '凶（四柱皆六替）'
    
    print(f'吉凶格局：{jige}')
    
    # 斗首分析
    print(f'\n【斗首课格分析】')
    print('-'*100)
    douhou_result = douhou_analyzer.analyze_kege('壬', sizhu)
    print(f'综合评分：{douhou_result["综合评分"]}分')
    
    if douhou_result.get('课格格局'):
        print(f'课格格局：')
        for pattern in douhou_result['课格格局'][:3]:
            print(f'  - {pattern.get("格局名称", "未知")} ({pattern.get("吉凶", "未知")})')
    
    if douhou_result.get('吉凶断语'):
        print(f'吉凶断语：')
        for duanyu in douhou_result['吉凶断语'][:2]:
            print(f'  - {duanyu}')
    
    # 综合评分
    if liuxiang_count == 4:
        bonus = 20
    elif liuxiang_count == 3:
        bonus = 15
    elif liuxiang_count == 2:
        bonus = 10
    elif liuxiang_count == 1:
        bonus = 5
    else:
        bonus = 0
    
    total_score_final = (avg_score * 0.6 + douhou_result['综合评分'] * 0.4) + bonus
    
    print(f'\n【综合评分】')
    print('-'*100)
    print(f'六相六替分：{avg_score:.1f} × 60% = {avg_score * 0.6:.1f}')
    print(f'斗首分：{douhou_result["综合评分"]} × 40% = {douhou_result["综合评分"] * 0.4:.1f}')
    print(f'格局加分：+{bonus}分')
    print(f'总计：{total_score_final:.1f}分')
    
    # 吉凶等级
    if total_score_final >= 90:
        level = '上上大吉'
    elif total_score_final >= 80:
        level = '上吉'
    elif total_score_final >= 70:
        level = '中吉'
    elif total_score_final >= 60:
        level = '小吉'
    else:
        level = '凶'
    
    print(f'吉凶等级：{level}')

print('\n' + '='*100)
print('【四柱干支速查表】')
print('='*100)

print('\n方便您快速对比资料：\n')

for case in test_cases:
    sizhu = case['sizhu']
    print(f'第{case["排名"]}名：{case["公历"]} {case["时辰"]}')
    print(f'  四柱：{sizhu["年柱"]} {sizhu["月柱"]} {sizhu["日柱"]} {sizhu["时柱"]}')
    print(f'  简写：{sizhu["年柱"][0]}{sizhu["年柱"][1]} {sizhu["月柱"][0]}{sizhu["月柱"][1]} {sizhu["日柱"][0]}{sizhu["日柱"][1]} {sizhu["时柱"][0]}{sizhu["时柱"][1]}')
    print()

print('='*100)
print('数据核对完成')
print('='*100)
