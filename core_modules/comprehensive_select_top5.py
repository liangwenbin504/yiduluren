#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面筛选 2026-2029 年所有日课
从每一年的每一月、每一日、每一时辰中筛选
按综合评分排序，选出前 5 个吉课
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime, timedelta
from douhou_analyzer import DouhouKegeAnalyzer
from liuxiang_liuti_correct import LiuXiangLiuTiCorrect
from sizhu_engine import get_sizhu, get_day_ganzhi


def analyze_full_kege(sizhu: dict, shan: str = '壬'):
    """
    综合分析斗首课格和六相六替
    """
    douhou_analyzer = DouhouKegeAnalyzer()
    liuxiang_system = LiuXiangLiuTiCorrect()
    
    # 1. 斗首课格分析
    douhou_result = douhou_analyzer.analyze_kege(shan, sizhu)
    douhou_score = douhou_result['综合评分']
    
    # 2. 六相六替分析
    liuxiang_result = liuxiang_system.analyze_sizhu(sizhu, '土')
    liuxiang_score = liuxiang_result.get('平均分', 0)
    
    # 3. 检查元辰是否得位
    yuanchen_positions = []
    for pillar_name, ganzhi in sizhu.items():
        tiangan = ganzhi[0]
        huaqi = liuxiang_system.get_huaqi(tiangan)
        if huaqi == '土':  # 元辰
            yuanchen_positions.append(pillar_name)
    
    yuanchen_dewei = len(yuanchen_positions) >= 1
    
    # 4. 元辰不得位则减分
    if not yuanchen_dewei:
        adjusted_douhou_score = max(0, douhou_score - 30)
    else:
        adjusted_douhou_score = douhou_score
    
    # 5. 综合评分：斗首 70% + 六相六替 30%
    total_score = adjusted_douhou_score * 0.7 + liuxiang_score * 0.3
    
    return {
        'sizhu': sizhu,
        '斗首评分': douhou_score,
        '调整后斗首评分': adjusted_douhou_score,
        '六相六替评分': liuxiang_score,
        '总分': total_score,
        '元辰位置': yuanchen_positions,
        '元辰得位': yuanchen_dewei,
        '斗首格局': douhou_result.get('课格格局', []),
        '六相统计': liuxiang_result.get('六相统计', 0),
        '六替统计': liuxiang_result.get('六替统计', 0),
        '吉课数': liuxiang_result.get('吉课数', 0),
        '凶课数': liuxiang_result.get('凶课数', 0),
        '综合评价': liuxiang_result.get('综合评价', '')
    }


def main():
    print('='*100)
    print('全面筛选 2026-2029 年所有日课')
    print('时间范围：2026 年 3 月 24 日至 2029 年 3 月 24 日')
    print('坐山：壬山')
    print('方法：遍历每一年、每一月、每一日、每一时辰')
    print('目标：按综合评分排序，选出前 5 个吉课')
    print('='*100)
    
    # 时间范围
    start_date = datetime(2026, 3, 24)
    end_date = datetime(2029, 3, 24)
    
    # 时辰地支
    shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    all_results = []
    total_days = (end_date - start_date).days + 1
    total_ke = total_days * 12
    
    print(f'\n总天数：{total_days}天')
    print(f'总课数：{total_ke}课（每天 12 时辰）')
    print(f'\n开始分析...\n')
    
    # 遍历每一天
    current_date = start_date
    day_count = 0
    
    while current_date <= end_date:
        day_count += 1
        
        # 获取日柱干支
        day_ganzhi = get_day_ganzhi(current_date.year, current_date.month, current_date.day)
        
        # 遍历 12 个时辰
        for shichen_idx, shichen in enumerate(shichen_list):
            # 获取四柱（精确计算）
            sizhu = get_sizhu(current_date.year, current_date.month, current_date.day, shichen)
            
            # 分析课格
            result = analyze_full_kege(sizhu, '壬')
            result['公历日期'] = current_date
            result['时辰'] = shichen
            result['日柱'] = f"{day_ganzhi[0]}{day_ganzhi[1]}"
            
            all_results.append(result)
        
        # 进度显示
        if day_count % 100 == 0:
            progress = day_count / total_days * 100
            print(f"已分析 {day_count}/{total_days} 天 ({progress:.1f}%)")
        
        current_date += timedelta(days=1)
    
    print(f'\n分析完成！共分析 {len(all_results)} 个课格')
    
    # 按总分排序
    print('\n正在排序...')
    all_results.sort(key=lambda x: x['总分'], reverse=True)
    
    # 显示前 5 名
    print('\n' + '='*100)
    print('🏆 最佳 5 个吉课（按综合评分排序）')
    print('='*100)
    
    for i in range(min(5, len(all_results))):
        result = all_results[i]
        print(f'\n【第{i+1}名】{result["公历日期"].strftime("%Y 年%m 月%d 日")} {result["时辰"]}时')
        print('-'*100)
        print(f'四柱：{result["sizhu"]["年柱"]} {result["sizhu"]["月柱"]} {result["sizhu"]["日柱"]} {result["sizhu"]["时柱"]}')
        print(f'\n【斗首课格】')
        print(f'  元辰位置：{result["元辰位置"]}')
        print(f'  元辰得位：{"✅ 是" if result["元辰得位"] else "❌ 否"}')
        print(f'  斗首评分：{result["斗首评分"]}分 → 调整后：{result["调整后斗首评分"]}分')
        
        if result['斗首格局']:
            print(f'  格局：')
            for pattern in result['斗首格局'][:3]:
                print(f'    - {pattern["格局名称"]} ({pattern["吉凶"]}): {pattern["描述"]}')
        
        print(f'\n【六相六替】')
        print(f'  六相数：{result["六相统计"]}个')
        print(f'  六替数：{result["六替统计"]}个')
        print(f'  吉课数：{result["吉课数"]}个')
        print(f'  凶课数：{result["凶课数"]}个')
        print(f'  评分：{result["六相六替评分"]:.1f}分')
        print(f'  综合评价：{result["综合评价"]}')
        
        print(f'\n【综合评分】')
        print(f'  总分：{result["总分"]:.1f}分')
        print(f'  计算：斗首 ({result["调整后斗首评分"]}×70%) + 六相六替 ({result["六相六替评分"]:.1f}×30%)')
    
    print('\n' + '='*100)
    print('筛选完成')
    print('='*100)
    
    # 保存结果到文件
    output_file = os.path.join(os.path.dirname(__file__), 'top5_results.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('壬山最佳 5 课（2026.3.24-2029.3.24）\n')
        f.write('='*100 + '\n\n')
        for i in range(min(5, len(all_results))):
            result = all_results[i]
            f.write(f'【第{i+1}名】{result["公历日期"].strftime("%Y 年%m 月%d 日")} {result["时辰"]}时\n')
            f.write(f'四柱：{result["sizhu"]["年柱"]} {result["sizhu"]["月柱"]} {result["sizhu"]["日柱"]} {result["sizhu"]["时柱"]}\n')
            f.write(f'总分：{result["总分"]:.1f}分\n')
            f.write(f'元辰得位：{"是" if result["元辰得位"] else "否"}\n')
            f.write(f'斗首格局：{", ".join([p["格局名称"] for p in result["斗首格局"]])}\n')
            f.write('\n')
    
    print(f'\n结果已保存到：{output_file}')


if __name__ == '__main__':
    main()
