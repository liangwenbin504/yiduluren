#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修正后的月柱计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate

calendar = PreciseCalendar()

print("=" * 80)
print("测试修正后的月柱计算")
print("=" * 80)

# 测试 2026 年各个月份
print("\n【2026 年（丙午年）各月月柱测试】")
print("五虎遁口诀：丙辛之岁从庚起（正月庚寅，二月辛卯...八月丁酉）\n")

test_dates = [
    (2026, 2, 4),    # 立春后，应该是庚寅月
    (2026, 3, 6),    # 惊蛰后，应该是辛卯月
    (2026, 4, 5),    # 清明后，应该是壬辰月
    (2026, 5, 5),    # 立夏后，应该是癸巳月
    (2026, 6, 6),    # 芒种后，应该是甲午月
    (2026, 7, 7),    # 小暑后，应该是乙未月
    (2026, 8, 8),    # 立秋后，应该是丙申月
    (2026, 9, 8),    # 白露后，应该是丁酉月 ← 重点测试
    (2026, 10, 8),   # 寒露后，应该是戊戌月
    (2026, 11, 7),   # 立冬后，应该是己亥月
    (2026, 12, 7),   # 大雪后，应该是庚子月
    (2027, 1, 5),    # 小寒后，应该是辛丑月
]

for year, month, day in test_dates:
    month_ganzhi = calendar.get_month_ganzhi(year, month, day)
    print(f"{year}年{month}月{day}日：{month_ganzhi}")

print("\n" + "=" * 80)
print("重点测试：2026 年 9 月 4 日、9 月 9 日")
print("=" * 80)

# 测试具体日期
test_cases = [
    (2026, 9, 4, 12),   # 用户指出的日期
    (2026, 9, 9, 10),   # 第一吉日
    (2026, 9, 9, 12),   # 正午
]

for year, month, day, hour in test_cases:
    sizhu = get_sizhu_accurate(year, month, day, hour, city_name='北京')
    print(f"\n{year}年{month}月{day}日 {hour}:00")
    print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")
    
    # 验证
    expected_month = '丁酉'
    actual_month = sizhu['月柱']
    if actual_month == expected_month:
        print(f"  ✓ 月柱正确（{expected_month}）")
    else:
        print(f"  ✗ 月柱错误：实际={actual_month}，期望={expected_month}")

print("\n" + "=" * 80)
