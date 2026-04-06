#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试并找出正确的基准日
"""

# 六十甲子表
JIANGZI = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

def find_correct_base():
    """
    找出正确的基准日
    已知：2026 年 3 月 20 日是癸巳日
    需要验证：3 月 18 日、19 日的日柱
    """
    from datetime import date, timedelta
    
    # 从 2026-03-20 癸巳日倒推
    base_date = date(2026, 3, 20)
    base_ganzhi_index = 29  # 癸巳
    
    print("从 2026-03-20 癸巳日倒推：")
    print("=" * 60)
    
    for i in range(10):
        test_date = base_date - timedelta(days=i)
        ganzhi_index = (base_ganzhi_index - i) % 60
        ganzhi = JIANGZI[ganzhi_index]
        print(f"{test_date} ({test_date.strftime('%m-%d')}) : {ganzhi}")
    
    print("\n从 2026-03-20 癸巳日顺推：")
    print("=" * 60)
    
    for i in range(10):
        test_date = base_date + timedelta(days=i)
        ganzhi_index = (base_ganzhi_index + i) % 60
        ganzhi = JIANGZI[ganzhi_index]
        print(f"{test_date} ({test_date.strftime('%m-%d')}) : {ganzhi}")

if __name__ == '__main__':
    find_correct_base()
