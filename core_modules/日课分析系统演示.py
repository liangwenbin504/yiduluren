#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 快速演示脚本

展示系统的基本使用方法和功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'engine')))

from riku_analysis_system import RikeAnalysisSystem


def demo_basic_usage():
    """基础使用演示"""
    print("=" * 80)
    print(" " * 25 + "日课分析系统 - 基础演示")
    print("=" * 80)
    
    # 创建系统
    system = RikeAnalysisSystem()
    
    # 示例 1: 分析单个日课
    print("\n【示例 1】分析单个日课")
    print("-" * 80)
    
    test_date = datetime(2026, 3, 24)
    result = system.analyze_single_ke(test_date, 7, '壬')
    
    print(f"日期：{test_date.strftime('%Y 年%m 月%d 日')}")
    print(f"时辰：{result['基础信息']['时辰']['时辰地支']}时 ({result['基础信息']['时辰']['时间范围']})")
    print(f"坐山：{result['基础信息']['坐山']}山")
    print(f"四柱：{result['基础信息']['四柱']['年柱']} {result['基础信息']['四柱']['月柱']} "
          f"{result['基础信息']['四柱']['日柱']} {result['基础信息']['四柱']['时柱']}")
    print(f"\n综合评分：{result['综合评分']['综合评分']}分")
    print(f"综合吉凶：{result['综合评分']['综合吉凶']['level_name']}")
    print(f"吉凶描述：{result['综合评分']['综合吉凶']['description']}")
    
    # 示例 2: 分析单日所有时辰
    print("\n【示例 2】分析单日 12 时辰，筛选 70 分以上")
    print("-" * 80)
    
    daily_results = system.analyze_daily_ke(test_date, '壬', min_score=70)
    
    print(f"日期：{test_date.strftime('%Y 年%m 月%d 日')} 壬山")
    print(f"找到 {len(daily_results)} 个 70 分以上的时辰\n")
    
    if daily_results:
        print("时辰评分排行:")
        for i, res in enumerate(daily_results, 1):
            shichen = res['基础信息']['时辰']['时辰地支']
            score = res['综合评分']['综合评分']
            jixiong = res['综合评分']['综合吉凶']['level_name']
            print(f"  {i:2d}. {shichen}时 - {score:5.1f}分 ({jixiong})")
    
    # 示例 3: 查看完整报告
    print("\n【示例 3】完整分析评价报告")
    print("-" * 80)
    
    print(result['GLM 评价报告'])


def demo_date_range():
    """日期范围分析演示"""
    print("\n" + "=" * 80)
    print(" " * 25 + "日期范围分析演示")
    print("=" * 80)
    
    system = RikeAnalysisSystem()
    
    # 分析 2026 年 3 月下旬
    print("\n【演示】分析 2026 年 3 月 21-31 日，壬山，筛选 75 分以上日课")
    print("-" * 80)
    
    start = datetime(2026, 3, 21)
    end = datetime(2026, 3, 31)
    
    best_results = system.get_best_ke(start, end, '壬', top_n=10)
    
    print(f"\n2026 年 3 月下旬最佳 10 个日课 (壬山):")
    print("-" * 80)
    
    for i, res in enumerate(best_results, 1):
        date_str = res['基础信息']['公历日期']['日期字符串']
        shichen = res['基础信息']['时辰']['时辰地支']
        score = res['综合评分']['综合评分']
        jixiong = res['综合评分']['综合吉凶']['level_name']
        
        print(f"{i:2d}. {date_str} {shichen:2s}时  {score:5.1f}分 ({jixiong})")


def demo_custom_weights():
    """自定义权重演示"""
    print("\n" + "=" * 80)
    print(" " * 25 + "自定义权重配置演示")
    print("=" * 80)
    
    from src.engine.comprehensive_scorer import WeightConfig
    
    # 标准权重
    print("\n【标准权重】斗首 40%、演禽 30%、大六壬 30%")
    system1 = RikeAnalysisSystem()
    result1 = system1.analyze_single_ke(datetime(2026, 3, 24), 7, '壬')
    print(f"综合评分：{result1['综合评分']['综合评分']}分")
    
    # 自定义权重 1: 重视斗首
    print("\n【自定义权重 1】斗首 60%、演禽 20%、大六壬 20%")
    from src.engine.comprehensive_scorer import WeightConfig
    custom_weight1 = WeightConfig(douhou_weight=0.6, yanqin_weight=0.2, daliuren_weight=0.2)
    system2 = RikeAnalysisSystem(weight_config=custom_weight1)
    result2 = system2.analyze_single_ke(datetime(2026, 3, 24), 7, '壬')
    print(f"综合评分：{result2['综合评分']['综合评分']}分")
    
    # 自定义权重 2: 平衡配置
    print("\n【自定义权重 2】斗首 33%、演禽 33%、大六壬 34%")
    custom_weight2 = WeightConfig(douhou_weight=0.33, yanqin_weight=0.33, daliuren_weight=0.34)
    system3 = RikeAnalysisSystem(weight_config=custom_weight2)
    result3 = system3.analyze_single_ke(datetime(2026, 3, 24), 7, '壬')
    print(f"综合评分：{result3['综合评分']['综合评分']}分")


def show_score_reference():
    """评分标准参考"""
    print("\n" + "=" * 80)
    print(" " * 28 + "评分标准参考表")
    print("=" * 80)
    
    score_table = """
    分数范围    吉凶等级    说明                  建议
    ─────────────────────────────────────────────────────
    90-100    上上大吉    百事亨通，万事如意    百事可为
    80-89     上吉        诸事顺利，谋事可成    大利行事
    70-79     中吉        总体吉利，小有波折    可用，行事谨慎
    60-69     小吉        小利，宜守不宜攻      斟酌用之
    50-59     吉凶参半    吉凶混杂，需谨慎行事  可不用，用需化解
    40-49     小凶        小有不利，易生波折    不宜用
    30-39     中凶        多有不利，诸事难成    忌用
    20-29     大凶        大凶之象，灾祸难免    不可用
    0-19      上凶        极凶，大灾大难        大忌
    """
    print(score_table)


if __name__ == '__main__':
    # 运行所有演示
    demo_basic_usage()
    demo_date_range()
    demo_custom_weights()
    show_score_reference()
    
    print("\n" + "=" * 80)
    print("演示完毕")
    print("=" * 80)
    print("\n更多信息请查看:")
    print("  - 日课分析系统使用手册.md")
    print("  - 日课分析系统完成报告.md")
    print("  - test_riku_system.py (测试脚本)")
    print("\n" + "=" * 80)
