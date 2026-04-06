#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试：分析 2026 年 3 月 24 日壬山午时
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime
from riku_analysis_system import RikeAnalysisSystem

print('=' * 80)
print('测试单个日课：2026 年 3 月 24 日 午时 壬山')
print('=' * 80)

system = RikeAnalysisSystem()

# 分析单个日课
test_date = datetime(2026, 3, 24)
result = system.analyze_single_ke(test_date, 7, '壬')  # 午时是第 7 个时辰

print(f'\n公历日期：{result["基础信息"]["公历日期"]["日期字符串"]}')
print(f'四柱：{result["基础信息"]["四柱"]["年柱"]} {result["基础信息"]["四柱"]["月柱"]} {result["基础信息"]["四柱"]["日柱"]} {result["基础信息"]["四柱"]["时柱"]}')
print(f'时辰：{result["基础信息"]["时辰"]["时辰地支"]}时')
print(f'坐山：{result["基础信息"]["坐山"]}')

print(f'\n【综合评分】{result["综合评分"]["综合评分"]}分 - {result["综合评分"]["综合吉凶"]["level_name"]}')

print(f'\n【评分构成】')
for item in result['综合评分']['评分详情']:
    print(f'  {item["名称"]}: {item["分数"]}分 (权重{item["权重"]*100}%, 占比{item["占比"]})')

print(f'\n【斗首课格分析】{result["斗首课格分析"]["综合评分"]}分')
print(f'  山家五行：{result["斗首课格分析"]["山家五行"]}')

print(f'\n【演禽真法分析】{result["演禽真法分析"]["综合评分"]}分')

print(f'\n【大六壬课体分析】{result["大六壬课体分析"]["综合评分"]}分')

print('\n' + '=' * 80)
print('测试完成')
print('=' * 80)
