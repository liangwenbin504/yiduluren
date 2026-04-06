#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优先斗首课格，再配合六相六替
重新筛选最佳 5 个吉日
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer
from liuxiang_liuti_correct import LiuXiangLiuTiCorrect


def analyze_priority_douhou(sizhu: dict, shan: str = '壬'):
    """
    优先分析斗首课格，再配合六相六替
    """
    douhou_analyzer = DouhouKegeAnalyzer()
    liuxiang_system = LiuXiangLiuTiCorrect()
    
    # 1. 先分析斗首课格
    douhou_result = douhou_analyzer.analyze_kege(shan, sizhu)
    douhou_score = douhou_result['综合评分']
    douhou_patterns = douhou_result['课格格局']
    
    # 2. 分析六相六替
    liuxiang_result = liuxiang_system.analyze_sizhu(sizhu, '土')
    liuxiang_score = liuxiang_result.get('平均分', 0)
    
    # 3. 检查元辰是否得位（关键！）
    yuanchen_positions = []
    for pillar_name, ganzhi in sizhu.items():
        tiangan = ganzhi[0]
        huaqi = liuxiang_system.get_huaqi(tiangan)
        if huaqi == '土':  # 元辰
            yuanchen_positions.append(pillar_name)
    
    yuanchen_dewei = len(yuanchen_positions) >= 1  # 至少一柱见元辰
    
    # 4. 综合评分（斗首为主，六相六替为辅）
    # 如果元辰不得位，斗首分数再高也要降级
    if not yuanchen_dewei:
        # 元辰不得位，降 30 分
        adjusted_douhou_score = max(0, douhou_score - 30)
    else:
        adjusted_douhou_score = douhou_score
    
    # 综合评分：斗首 70% + 六相六替 30%
    total_score = adjusted_douhou_score * 0.7 + liuxiang_score * 0.3
    
    return {
        '四柱': sizhu,
        '斗首评分': douhou_score,
        '调整后斗首评分': adjusted_douhou_score,
        '六相六替评分': liuxiang_score,
        '总分': total_score,
        '元辰位置': yuanchen_positions,
        '元辰得位': yuanchen_dewei,
        '斗首格局': douhou_patterns,
        '六相六替统计': {
            '六相数': liuxiang_result.get('六相统计', 0),
            '六替数': liuxiang_result.get('六替统计', 0),
            '吉课数': liuxiang_result.get('吉课数', 0),
            '凶课数': liuxiang_result.get('凶课数', 0)
        },
        '综合评价': liuxiang_result.get('综合评价', '')
    }


def main():
    print('='*100)
    print('优先斗首课格，再配合六相六替')
    print('重新筛选壬山最佳 5 个吉日（2026.3.24-2029.3.24）')
    print('='*100)
    
    # 候选日课（从原有数据库中筛选元辰得位的）
    candidate_days = [
        {
            '公历': '2026 年 5 月 24 日 午时',
            'sizhu': {'年柱': '丙午', '月柱': '癸巳', '日柱': '庚子', '时柱': '壬午'}
        },
        {
            '公历': '2026 年 4 月 22 日 申时',
            'sizhu': {'年柱': '丙午', '月柱': '壬辰', '日柱': '丙寅', '时柱': '丙申'}
        },
        {
            '公历': '2026 年 7 月 8 日 巳时',
            'sizhu': {'年柱': '丙午', '月柱': '甲午', '日柱': '壬申', '时柱': '乙巳'}
        },
        {
            '公历': '2026 年 9 月 16 日 辰时',
            'sizhu': {'年柱': '丙午', '月柱': '丙申', '日柱': '戊戌', '时柱': '丙辰'}
        },
        {
            '公历': '2026 年 3 月 31 日 未时',
            'sizhu': {'年柱': '丙午', '月柱': '辛卯', '日柱': '甲辰', '时柱': '辛未'}
        },
        # 新增：元辰得位的日课
        {
            '公历': '2026 年 6 月 18 日 午时',
            'sizhu': {'年柱': '丙午', '月柱': '甲午', '日柱': '己巳', '时柱': '庚午'}
        },
        {
            '公历': '2026 年 8 月 10 日 巳时',
            'sizhu': {'年柱': '丙午', '月柱': '丙申', '日柱': '己亥', '时柱': '己巳'}
        },
        {
            '公历': '2026 年 10 月 5 日 辰时',
            'sizhu': {'年柱': '丙午', '月柱': '丁酉', '日柱': '甲戌', '时柱': '戊辰'}
        },
        {
            '公历': '2027 年 1 月 15 日 丑时',
            'sizhu': {'年柱': '丁未', '月柱': '癸丑', '日柱': '己卯', '时柱': '乙丑'}
        },
        {
            '公历': '2027 年 4 月 8 日 午时',
            'sizhu': {'年柱': '丁未', '月柱': '甲辰', '日柱': '丙午', '时柱': '甲午'}
        }
    ]
    
    results = []
    
    for day in candidate_days:
        result = analyze_priority_douhou(day['sizhu'], '壬')
        result['公历'] = day['公历']
        results.append(result)
        
        print(f"\n{'='*100}")
        print(f"{day['公历']}")
        print(f"四柱：{day['sizhu']['年柱']} {day['sizhu']['月柱']} {day['sizhu']['日柱']} {day['sizhu']['时柱']}")
        print('='*100)
        
        print(f'\n【斗首课格分析】')
        print(f'  元辰位置：{result["元辰位置"]}')
        print(f'  元辰得位：{result["元辰得位"]}')
        print(f'  斗首评分：{result["斗首评分"]}分 → 调整后：{result["调整后斗首评分"]}分')
        
        if result['斗首格局']:
            print(f'  格局：')
            for pattern in result['斗首格局']:
                print(f'    - {pattern["格局名称"]} ({pattern["吉凶"]}): {pattern["描述"]}')
        
        print(f'\n【六相六替分析】')
        stats = result['六相六替统计']
        print(f'  六相数：{stats["六相数"]}个')
        print(f'  六替数：{stats["六替数"]}个')
        print(f'  吉课数：{stats["吉课数"]}个')
        print(f'  凶课数：{stats["凶课数"]}个')
        print(f'  评分：{result["六相六替评分"]:.1f}分')
        print(f'  综合评价：{result["综合评价"]}')
        
        print(f'\n【综合评分】')
        print(f'  总分：{result["总分"]:.1f}分')
        print(f'  计算：斗首 ({result["调整后斗首评分"]}×70%) + 六相六替 ({result["六相六替评分"]:.1f}×30%)')
    
    # 重新排序
    print('\n' + '='*100)
    print('重新排序（按总分，优先元辰得位）')
    print('='*100)
    
    results_sorted = sorted(results, key=lambda x: x['总分'], reverse=True)
    
    for i, result in enumerate(results_sorted[:5], 1):
        print(f'\n第{i}名：{result["公历"]}')
        print(f'  四柱：{result["四柱"]["年柱"]} {result["四柱"]["月柱"]} {result["四柱"]["日柱"]} {result["四柱"]["时柱"]}')
        print(f'  元辰位置：{result["元辰位置"]}')
        print(f'  总分：{result["总分"]:.1f}分')
        print(f'  斗首：{result["调整后斗首评分"]}分 | 六相六替：{result["六相六替评分"]:.1f}分')
        if result['斗首格局']:
            print(f'  格局：{", ".join([p["格局名称"] for p in result["斗首格局"]])}')
    
    print('\n' + '='*100)
    print('分析完成')
    print('='*100)


if __name__ == '__main__':
    main()
