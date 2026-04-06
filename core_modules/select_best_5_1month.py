#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
壬山择日：2026 年 3 月 24 日 至 2026 年 4 月 24 日（一个月范围）
筛选最佳 5 个日课
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime
from riku_analysis_system import RikeAnalysisSystem

print('=' * 80)
print('壬山择日：2026 年 3 月 24 日 至 2026 年 4 月 24 日')
print('=' * 80)

system = RikeAnalysisSystem()

# 获取最佳 5 个日课（一个月范围）
best_results = system.get_best_ke(
    start_date=datetime(2026, 3, 24),
    end_date=datetime(2026, 4, 24),
    shan='壬',
    top_n=5
)

print(f'\n找到 {len(best_results)} 个最佳日课\n')

for i, res in enumerate(best_results, 1):
    print('=' * 80)
    print(f'【第 {i} 吉课】')
    print('=' * 80)
    
    # 基础信息
    base = res['基础信息']
    print(f'公历日期：{base["公历日期"]["日期字符串"]}')
    print(f'四柱：{base["四柱"]["年柱"]} {base["四柱"]["月柱"]} {base["四柱"]["日柱"]} {base["四柱"]["时柱"]}')
    print(f'坐山：{base["坐山"]}')
    print(f'时辰：{base["时辰"]["时辰地支"]}时 ({base["时辰"]["时间范围"]})')
    
    # 综合评分
    comp = res['综合评分']
    print(f'\n【综合评分】{comp["综合评分"]}分 - {comp["综合吉凶"]["level_name"]}')
    
    # 评分详情
    print(f'\n【评分构成】')
    for item in comp['评分详情']:
        print(f'  {item["名称"]}: {item["分数"]}分 (权重{item["权重"]*100}%, 占比{item["占比"]})')
    
    # 斗首分析
    douhou = res['斗首课格分析']
    print(f'\n【斗首课格分析】{douhou["综合评分"]}分')
    print(f'  山家五行：{douhou["山家五行"]}')
    if douhou.get('课格格局'):
        for pattern in douhou['课格格局']:
            print(f'  格局：{pattern["格局名称"]} ({pattern["吉凶"]})')
    if douhou.get('吉凶断语'):
        print('  断语:')
        for duanyu in douhou['吉凶断语'][:3]:
            print(f'    - {duanyu}')
    
    # 演禽分析
    yanqin = res['演禽真法分析']
    print(f'\n【演禽真法分析】{yanqin["综合评分"]}分')
    print(f'  四禽:')
    for key, value in yanqin['四禽'].items():
        qin_xing = yanqin['四禽禽星'].get(f'{key}星', '')
        jixiong = yanqin['二十八宿属性'].get(f'{key.replace("禽", "宿")}吉凶', '')
        print(f'    {key}: {value} ({qin_xing}) - {jixiong}')
    if yanqin.get('吉凶断语'):
        print('  断语:')
        for duanyu in yanqin['吉凶断语'][:3]:
            print(f'    - {duanyu}')
    
    # 大六壬分析
    daliuren = res['大六壬课体分析']
    print(f'\n【大六壬课体分析】{daliuren["综合评分"]}分')
    print(f'  课体：{daliuren.get("课体", "待查")}')
    if daliuren.get('课体格局'):
        for pattern in daliuren['课体格局']:
            print(f'  格局：{pattern}')
    
    # 使用建议
    print(f'\n【使用建议】')
    print(f'  {comp["综合吉凶"].get("suggestion", "")}')
    print()
