#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成壬山丙向阴宅安葬完整择日报告
"""

import sys
import os
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from ren_shan_feng_shui_selector import RenShanFengShuiSelector


def main():
    print("=" * 80)
    print("壬山丙向阴宅安葬择日报告")
    print("=" * 80)
    print()
    
    selector = RenShanFengShuiSelector()
    
    # 择日范围：2026 年 3 月 15 日至 2027 年 12 月 31 日
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2027, 12, 31)
    
    print(f"择日范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"山向：壬山丙向")
    print(f"用途：阴宅安葬")
    print()
    
    # 先尝试较低评分要求，确保能找到日期
    print("第一轮：搜索评分 >= 6.0 的日期...")
    results = selector.select_an_zang_dates(start_date, end_date, min_score=6.0)
    
    if not results:
        print("未找到符合条件的日期，降低标准...")
        results = selector.select_an_zang_dates(start_date, end_date, min_score=5.0)
    
    print(f"\n共找到 {len(results)} 个符合条件的日期\n")
    
    # 生成详细报告
    output_file = os.path.join(os.path.dirname(__file__), 'ren_shan_an_zang_report.txt')
    selector.generate_report(results, output_file)
    
    # 在控制台显示前 5 个最佳日期
    print("=" * 80)
    print("精选前 5 个安葬吉日")
    print("=" * 80)
    
    for i, item in enumerate(results[:5], 1):
        print(f"\n【第{i}名】{item['date']} ({item['weekday']})")
        print(f"四柱：{item['sizhu']['年柱']}年 {item['sizhu']['月柱']}月 {item['sizhu']['日柱']}日 {item['sizhu']['时柱']}时")
        print(f"斗首：{item['douhou']['课格']} ({item['douhou']['评分']}分) - {item['douhou']['断语']}")
        print(f"吉神：{', '.join(item['ji_xiong']['吉神']) if item['ji_xiong']['吉神'] else '无'}")
        print(f"凶煞：{', '.join(item['ji_xiong']['凶煞']) if item['ji_xiong']['凶煞'] else '无'}")
        print(f"龙德课：{item['long_de_type']}")
        print(f"禄马贵：{', '.join(item['lu_ma_gui']['到山到向详情'])} (共{item['lu_ma_gui']['总数']}个)")
        print(f"综合评分：{item['total_score']:.1f}分")
        print(f"推荐指数：{item['recommendation']}")
        print("-" * 80)
    
    print(f"\n完整报告已保存至：{output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
