#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课到山到向择日快速演示
展示完整的使用流程
"""

import sys
import os
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from long_de_ke_selector import LongDeKeSelector


def demo_basic_usage():
    """基础使用演示"""
    print("=" * 80)
    print("龙德课到山到向择日系统 - 基础演示")
    print("=" * 80)
    print()
    
    # 创建选择器
    selector = LongDeKeSelector()
    
    # 设置参数
    mountain = '壬'
    direction = '丙'
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2026, 12, 31)  # 测试 9 个月
    min_arrival = 3
    
    print(f"【择日参数】")
    print(f"  坐山：{mountain}山{direction}向")
    print(f"  日期范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"  最少到山到向：{min_arrival}个")
    print()
    
    # 执行择日
    print("【开始择日...】")
    results = selector.select_long_de_dates(
        mountain, direction, start_date, end_date, min_arrival
    )
    
    print(f"\n【择日结果】")
    print(f"  找到 {len(results)} 个符合条件的日期")
    print()
    
    if results:
        # 显示前 3 个最佳日期
        print("【最佳日期推荐】")
        for i, result in enumerate(results[:3], 1):
            print(f"\n  第{i}名：{result['date']} ({result['weekday']}) {result['shi']}时")
            print(f"    四柱：{result['year_gan_zhi']}年 {result['ri_gan_zhi']}日")
            print(f"    龙德课：{result['long_de_type']}")
            print(f"    三传：{result['sanchuan'].get('初传', '')} → {result['sanchuan'].get('中传', '')} → {result['sanchuan'].get('末传', '')}")
            print(f"    课体：{', '.join(result['ke_ti'][:3])}")
            print(f"    到山到向：{result['arrival_count']}个 ({', '.join(result['lu_ma_gui_arrival']['总结'][:3])}...)")
            print(f"    推荐指数：{selector._get_recommendation_level(result)}")
        
        # 显示首个日期的详细课格结构
        print("\n" + "=" * 80)
        print("【详细课格结构 - 第 1 名】")
        print("=" * 80)
        
        kege = selector.generate_kege_structure(results[0])
        
        print(f"\n日期：{kege['基本信息']['日期']} ({kege['基本信息']['星期']})")
        print(f"四柱：{kege['基本信息']['四柱']['年柱']}年 {kege['基本信息']['四柱']['月柱']}月 {kege['基本信息']['四柱']['日柱']}日 {kege['基本信息']['四柱']['时柱']}时")
        print(f"坐山朝向：{kege['基本信息']['坐山朝向']}")
        
        print(f"\n【六壬课式】")
        print(f"  月将：{kege['六壬课式']['月将']}")
        print(f"  占时：{kege['六壬课式']['占时']}")
        print(f"  三传：{kege['六壬课式']['三传'].get('初传', '')} → {kege['六壬课式']['三传'].get('中传', '')} → {kege['六壬课式']['三传'].get('末传', '')}")
        print(f"  课体：{', '.join(kege['六壬课式']['课体'][:5])}")
        
        print(f"\n【龙德课分析】")
        print(f"  类型：{kege['龙德课分析']['龙德课类型']}")
        print(f"\n  判断依据：")
        print(f"  {kege['龙德课分析']['判断依据']}")
        
        print(f"\n【到山到向分析】")
        arrival = kege['到山到向分析']
        print(f"  山家禄马贵：禄={arrival['山家信息'].get('禄', '')}, 马={arrival['山家信息'].get('马', '')}, 贵人={arrival['山家信息'].get('贵人', [])}")
        print(f"  到山到向详情：{', '.join(arrival['到山到向详情'])}")
        print(f"  总计：{len(arrival['到山到向详情'])}个")
        
        print(f"\n【综合评价】")
        print(f"  课格等级：{kege['综合评价']['课格等级']}")
        print(f"  推荐指数：{kege['综合评价']['推荐指数']}")
        
        # 保存结果
        print("\n" + "=" * 80)
        print("【保存结果】")
        selector.save_results(results, '龙德课演示结果.json')
        selector.generate_report(results, '龙德课演示报告.txt', mountain, direction)
        
    else:
        print("  未找到符合条件的日期，请调整参数后重试。")
    
    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


def demo_long_de_theory():
    """龙德课理论演示"""
    print("\n" + "=" * 80)
    print("龙德课理论知识演示")
    print("=" * 80)
    
    selector = LongDeKeSelector()
    
    # 测试案例
    test_cases = [
        {
            'desc': '案例 1：太岁龙德课',
            'ri_gan_zhi': '辛酉',
            'yue_jiang': '午',
            'tai_sui': '午',
            'sanchuan': {'初传': '午', '中传': '卯', '末传': '子'}
        },
        {
            'desc': '案例 2：月将龙德课',
            'ri_gan_zhi': '丙子',
            'yue_jiang': '亥',
            'tai_sui': '未',
            'sanchuan': {'初传': '亥', '中传': '寅', '末传': '巳'}
        },
        {
            'desc': '案例 3：非龙德课',
            'ri_gan_zhi': '甲子',
            'yue_jiang': '子',
            'tai_sui': '午',
            'sanchuan': {'初传': '子', '中传': '寅', '末传': '辰'}
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['desc']}")
        print(f"  日干支：{case['ri_gan_zhi']}")
        print(f"  月将：{case['yue_jiang']}, 太岁：{case['tai_sui']}")
        print(f"  三传：{case['sanchuan']}")
        
        is_long_de, long_de_type = selector.is_long_de_ke(
            case['ri_gan_zhi'], case['yue_jiang'], case['tai_sui'], case['sanchuan']
        )
        
        if is_long_de:
            print(f"  ✅ 龙德课成立：{long_de_type}")
        else:
            print(f"  ❌ 龙德课不成立：{long_de_type}")
    
    print("\n" + "=" * 80)


def demo_lu_ma_gui_theory():
    """禄马贵到山到向理论演示"""
    print("\n" + "=" * 80)
    print("禄马贵到山到向理论演示")
    print("=" * 80)
    
    selector = LongDeKeSelector()
    
    # 演示壬山丙向
    mountain = '壬'
    direction = '丙'
    year_gan_zhi = ('丙', '午')
    day_gan_zhi = '辛酉'
    shi_zhi = '子'
    
    print(f"\n演示：{mountain}山{direction}向")
    print(f"  年柱：{year_gan_zhi[0]}{year_gan_zhi[1]}")
    print(f"  日柱：{day_gan_zhi}")
    print(f"  时支：{shi_zhi}")
    
    result = selector.check_lu_ma_gui_arrival(mountain, direction, year_gan_zhi, day_gan_zhi, shi_zhi)
    
    print(f"\n【山家信息】")
    print(f"  禄：{result['山家信息'].get('禄', '')}")
    print(f"  马：{result['山家信息'].get('马', '')}")
    print(f"  贵人：{result['山家信息'].get('贵人', [])}")
    
    print(f"\n【年柱禄马贵】")
    for key, value in result['年柱禄马贵'].items():
        print(f"  {key}: {value}")
    
    print(f"\n【日柱禄马贵】")
    for key, value in result['日柱禄马贵'].items():
        print(f"  {key}: {value}")
    
    print(f"\n【到山到向详情】")
    if result['到山到向详情']:
        for item in result['到山到向详情']:
            print(f"  ✅ {item}")
    else:
        print(f"  禄马贵未到山到向")
    
    print(f"\n【总结】")
    print(f"  {', '.join(result['总结'])}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    # 运行演示
    demo_long_de_theory()
    demo_lu_ma_gui_theory()
    demo_basic_usage()
    
    print("\n" + "=" * 80)
    print("所有演示完成！")
    print("查看生成的文件：")
    print("  - 龙德课演示结果.json")
    print("  - 龙德课演示报告.txt")
    print("=" * 80)
