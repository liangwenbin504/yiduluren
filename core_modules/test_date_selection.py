#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试日期选择核心逻辑
"""

import sys
import os
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.precise_calendar import PreciseCalendar, get_sizhu_accurate
from engine.ke_ti_judge import KeTiJudgeCalculator
from engine.long_de_ke_selector import LongDeKeSelector
from engine.liuren_scoring import LiuRenKeTiScorer

def test_single_date():
    """测试单个日期的计算"""
    print("=" * 60)
    print("测试单个日期计算")
    print("=" * 60)
    
    # 初始化
    calendar = PreciseCalendar()
    ke_ti_judge = KeTiJudgeCalculator()
    long_de_selector = LongDeKeSelector()
    liuren_scorer = LiuRenKeTiScorer()
    
    # 测试日期
    test_date = datetime(2026, 3, 15)
    shi_zhi = '子'
    shi_hour = 0
    
    print(f"\n测试日期：{test_date.strftime('%Y-%m-%d')} {shi_zhi}时")
    
    try:
        # 计算四柱
        sizhu = get_sizhu_accurate(
            test_date.year, test_date.month, test_date.day,
            shi_hour, 0, 116.4074, 39.9042
        )
        
        print(f"四柱：{sizhu}")
        
        ri_ganzhi = sizhu['日柱']
        ri_gan = ri_ganzhi[0]
        ri_zhi = ri_ganzhi[1]
        
        print(f"日柱：{ri_ganzhi}")
        
        # 计算课体
        matched_kege = ke_ti_judge.match_ke_ti(ri_gan, ri_zhi, shi_zhi)
        
        print(f"匹配课体：{matched_kege}")
        print(f"课体数量：{len(matched_kege)}")
        
        if matched_kege:
            # 计算评分
            kege_scores = {}
            for kege in matched_kege:
                score = liuren_scorer.get_ke_ti_score(kege)
                kege_scores[kege] = score
                print(f"  {kege}: {score}分")
            
            # 计算六壬综合评分
            liuren_score_list = list(kege_scores.values())
            max_liuren_score = max(liuren_score_list)
            avg_liuren_score = sum(liuren_score_list) / len(liuren_score_list)
            liuren_final_score = max_liuren_score * 0.6 + avg_liuren_score * 0.4
            
            print(f"\n六壬综合评分：{liuren_final_score:.1f}")
            print(f"  最高分：{max_liuren_score}")
            print(f"  平均分：{avg_liuren_score:.1f}")
            
            # 检查龙德课
            if '龙德课' in matched_kege:
                is_longde, longde_type = long_de_selector.is_long_de_ke(
                    ri_ganzhi,
                    sizhu.get('月柱', ['', ''])[1] if sizhu.get('月柱') else '',
                    sizhu.get('年柱', ['', ''])[1] if sizhu.get('年柱') else '',
                    []
                )
                print(f"\n龙德课检查：{is_longde}, 类型：{longde_type}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

def test_date_range():
    """测试日期范围计算"""
    print("\n\n" + "=" * 60)
    print("测试日期范围计算（3 天）")
    print("=" * 60)
    
    calendar = PreciseCalendar()
    ke_ti_judge = KeTiJudgeCalculator()
    liuren_scorer = LiuRenKeTiScorer()
    
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2026, 3, 17)
    
    total_results = 0
    dates_with_results = 0
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\n日期：{current_date.strftime('%Y-%m-%d')}")
        
        for shi_zhi in calendar.DIZHI:
            shi_index = calendar.DIZHI.index(shi_zhi)
            shi_hour = shi_index * 2
            
            try:
                sizhu = get_sizhu_accurate(
                    current_date.year, current_date.month, current_date.day,
                    shi_hour, 0, 116.4074, 39.9042
                )
                
                ri_ganzhi = sizhu['日柱']
                ri_gan = ri_ganzhi[0]
                ri_zhi = ri_ganzhi[1]
                
                matched_kege = ke_ti_judge.match_ke_ti(ri_gan, ri_zhi, shi_zhi)
                
                if matched_kege:
                    # 计算评分
                    kege_scores = {kege: liuren_scorer.get_ke_ti_score(kege) for kege in matched_kege}
                    liuren_score_list = list(kege_scores.values())
                    max_liuren_score = max(liuren_score_list)
                    avg_liuren_score = sum(liuren_score_list) / len(liuren_score_list)
                    liuren_final_score = max_liuren_score * 0.6 + avg_liuren_score * 0.4
                    
                    # 简单过滤：评分>=7.0
                    if liuren_final_score >= 7.0:
                        total_results += 1
                        if dates_with_results == 0:
                            print(f"  ✓ {shi_zhi}时 - 课体：{matched_kege[:3]}, 评分：{liuren_final_score:.1f}")
                        dates_with_results += 1
                        
            except Exception as e:
                print(f"  错误：{e}")
                continue
        
        current_date += timedelta(days=1)
    
    print(f"\n统计：")
    print(f"  检查天数：3 天")
    print(f"  有结果的日期数：{dates_with_results}")
    print(f"  总结果数：{total_results}")
    print("=" * 60)

if __name__ == '__main__':
    test_single_date()
    test_date_range()
    
    print("\n\n核心结论：")
    print("1. 如果单日期测试成功，说明核心计算逻辑正常")
    print("2. 如果范围测试有结果，说明筛选逻辑正常")
    print("3. 如果 GUI 无结果，问题可能在界面更新或线程通信")
