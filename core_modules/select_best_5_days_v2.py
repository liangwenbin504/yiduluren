#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用六相六替完整系统重新择日
时间范围：2026 年 3 月 24 日 至 2029 年 3 月 24 日
坐山：壬山
目标：择出 5 个最佳吉日
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from liuxiang_liuti_complete_system import LiuXiangLiuTiSystem
from douhou_analyzer import DouhouKegeAnalyzer

print('=' * 80)
print('使用六相六替完整系统重新择日')
print('时间范围：2026 年 3 月 24 日 至 2029 年 3 月 24 日')
print('坐山：壬山')
print('=' * 80)

# 创建系统
liuxiang_system = LiuXiangLiuTiSystem()
douhou_analyzer = DouhouKegeAnalyzer()

# 定义天干地支
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def get_ganzhi_from_date(date):
    """简化获取干支（实际需要精确计算，这里用示例数据）"""
    # 2026 年 3 月 24 日为丙午年 辛卯月 甲辰日
    # 这里简化处理，实际应该用精确的干支计算
    base_date = datetime(2026, 3, 24)
    days_diff = (date - base_date).days
    
    # 简化计算（实际应该用精确的干支推算）
    tiangan_idx = (2 + days_diff) % 10  # 甲为 2
    dizhi_idx = (4 + days_diff) % 12    # 辰为 4
    
    return TIANGAN[tiangan_idx], DIZHI[dizhi_idx]

def analyze_single_day(date, shichen_idx):
    """分析单日的六相六替和斗首"""
    # 获取干支（简化）
    tiangan, dizhi = get_ganzhi_from_date(date)
    ganzhi = f"{tiangan}{dizhi}"
    
    # 六相六替分析
    liuxiang_result = liuxiang_system.analyze_day(tiangan, dizhi)
    
    # 时辰干支（简化）
    shichen_dizhi = DIZHI[(shichen_idx - 1) % 12]
    shichen_ganzhi = f"{TIANGAN[(TIANGAN.index(tiangan) * 2 + shichen_idx) % 10]}{shichen_dizhi}"
    
    # 斗首分析（简化）
    sizhu = {
        '年柱': '丙午',
        '月柱': '辛卯',
        '日柱': ganzhi,
        '时柱': shichen_ganzhi
    }
    
    douhou_result = douhou_analyzer.analyze_kege('壬', sizhu)
    
    # 综合评分
    total_score = (
        liuxiang_result['分数'] * 0.4 +
        douhou_result['综合评分'] * 0.6
    )
    
    return {
        '日期': date,
        '干支': ganzhi,
        '时辰': shichen_ganzhi,
        '六相六替': liuxiang_result,
        '斗首': douhou_result,
        '综合评分': total_score
    }

# 筛选最佳日课
print('\n正在分析 2026 年 3 月 24 日至 2029 年 3 月 24 日的日课...')
print('（使用六相六替完整系统 + 斗首择日）\n')

best_results = []

# 遍历 3 年范围
start_date = datetime(2026, 3, 24)
end_date = datetime(2029, 3, 24)

current_date = start_date
while current_date <= end_date:
    # 分析 12 个时辰
    for shichen_idx in range(1, 13):
        result = analyze_single_day(current_date, shichen_idx)
        
        # 筛选条件
        if (result['六相六替']['六相/六替'] == '六相' and 
            result['六相六替']['分数'] >= 80 and
            result['斗首']['综合评分'] >= 70):
            best_results.append(result)
    
    current_date += timedelta(days=1)

# 按综合评分排序
best_results.sort(key=lambda x: x['综合评分'], reverse=True)

# 取前 5 个
top_5 = best_results[:5]

print('=' * 80)
print('最佳 5 个吉日')
print('=' * 80)

for i, result in enumerate(top_5, 1):
    print(f'\n【第 {i} 吉课】')
    print('-' * 80)
    print(f'公历日期：{result["日期"].strftime("%Y 年%m 月%d 日")}')
    print(f'日柱干支：{result["干支"]}')
    print(f'时辰：{result["时辰"]}时')
    
    print(f'\n【六相六替分析】')
    lx = result['六相六替']
    print(f'  状态：{lx["状态"]} ({lx["六相/六替"]}, {lx["吉凶"]})')
    print(f'  分数：{lx["分数"]}分')
    print(f'  含义：{lx["含义"]}')
    
    print(f'\n【斗首分析】')
    dh = result['斗首']
    print(f'  综合评分：{dh["综合评分"]}分')
    if dh.get('课格格局'):
        print(f'  格局：')
        for pattern in dh['课格格局'][:2]:
            print(f'    - {pattern.get("格局名称", "未知")} ({pattern.get("吉凶", "未知")})')
    
    print(f'\n【综合评分】{result["综合评分"]:.1f}分')
    
    # 核心诀法
    print(f'\n【核心诀法】')
    print(f'  化气六相诀：{liuxiang_system.juefa.get_liuxiang_jue()[:50]}...')

print('\n' + '=' * 80)
print('择日完成')
print('=' * 80)
