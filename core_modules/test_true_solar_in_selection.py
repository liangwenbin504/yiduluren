#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真太阳时计算
"""

import sys
import os
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate

calendar = PreciseCalendar()

print("=" * 80)
print("真太阳时计算测试（北京地区）")
print("=" * 80)

# 测试 2026 年 9 月 9 日的各个时辰
test_date = (2026, 9, 9)
print(f"\n测试日期：{test_date[0]}年{test_date[1]}月{test_date[2]}日")
print("北京经纬度：116.4074°E, 39.9042°N\n")

# 十二时辰的中点时间
shichen_map = {
    '子时': (23, '前一日'), '丑时': (1, ''), '寅时': (3, ''), '卯时': (5, ''),
    '辰时': (7, ''), '巳时': (9, ''), '午时': (11, ''), '未时': (13, ''),
    '申时': (15, ''), '酉时': (17, ''), '戌时': (19, ''), '亥时': (21, '')
}

print(f"{'时辰':<8} {'北京时间':<10} {'真太阳时':<10} {'时柱':<8} {'说明'}")
print("-" * 80)

for shichen, (hour, note) in shichen_map.items():
    # 计算真太阳时
    true_solar = calendar._calculate_true_solar_time(hour, 0, 116.4074, 
                                                      date(test_date[0], test_date[1], test_date[2]))
    
    # 获取四柱
    sizhu = get_sizhu_accurate(test_date[0], test_date[1], test_date[2], hour, city_name='北京')
    shi_zhu = sizhu['时柱']
    
    # 判断真太阳时的时辰
    true_hour = true_solar.hour
    if true_hour >= 23 or true_hour < 1:
        true_shichen = '子时'
    elif true_hour >= 1 and true_hour < 3:
        true_shichen = '丑时'
    elif true_hour >= 3 and true_hour < 5:
        true_shichen = '寅时'
    elif true_hour >= 5 and true_hour < 7:
        true_shichen = '卯时'
    elif true_hour >= 7 and true_hour < 9:
        true_shichen = '辰时'
    elif true_hour >= 9 and true_hour < 11:
        true_shichen = '巳时'
    elif true_hour >= 11 and true_hour < 13:
        true_shichen = '午时'
    elif true_hour >= 13 and true_hour < 15:
        true_shichen = '未时'
    elif true_hour >= 15 and true_hour < 17:
        true_shichen = '申时'
    elif true_hour >= 17 and true_hour < 19:
        true_shichen = '酉时'
    elif true_hour >= 19 and true_hour < 21:
        true_shichen = '戌时'
    else:
        true_shichen = '亥时'
    
    # 显示结果
    time_diff = true_solar - true_solar.replace(hour=hour, minute=0, second=0, microsecond=0)
    diff_minutes = int(time_diff.total_seconds() / 60)
    
    print(f"{shichen:<8} {hour:02d}:00      {true_solar.hour:02d}:{true_solar.minute:02d}     {shi_zhu:<8} {true_shichen} (时差：{diff_minutes:+d}分钟)")

print("\n" + "=" * 80)
print("重点时辰验证（巳时和亥时）")
print("=" * 80)

# 重点测试巳时和亥时
for hour in [9, 10, 11, 21, 22, 23]:
    sizhu = get_sizhu_accurate(2026, 9, 9, hour, city_name='北京')
    true_solar = calendar._calculate_true_solar_time(hour, 0, 116.4074, 
                                                      date(2026, 9, 9))
    print(f"\n北京时间 {hour:02d}:00")
    print(f"  真太阳时：{true_solar.hour:02d}:{true_solar.minute:02d}")
    print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")

print("\n" + "=" * 80)
