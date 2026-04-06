#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试真太阳时计算（简化版）
"""

import sys
import os
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
    '子时': 0, '丑时': 2, '寅时': 4, '卯时': 6,
    '辰时': 8, '巳时': 10, '午时': 12, '未时': 14,
    '申时': 16, '酉时': 18, '戌时': 20, '亥时': 22
}

print(f"{'时辰':<8} {'北京时间':<10} {'真太阳时':<10} {'时柱':<8}")
print("-" * 80)

for shichen, hour in shichen_map.items():
    # 计算真太阳时（返回浮点数小时）
    true_solar_hour = calendar._calculate_true_solar_time(hour, 0, 116.4074, 
                                                           __import__('datetime').date(test_date[0], test_date[1], test_date[2]))
    
    # 获取四柱
    sizhu = get_sizhu_accurate(test_date[0], test_date[1], test_date[2], hour, city_name='北京')
    shi_zhu = sizhu['时柱']
    
    # 计算时差（分钟）
    diff_minutes = int((true_solar_hour - hour) * 60)
    
    # 显示结果
    true_hour_int = int(true_solar_hour)
    true_min_int = int((true_solar_hour - true_hour_int) * 60)
    print(f"{shichen:<8} {hour:02d}:00      {true_hour_int:02d}:{true_min_int:02d}     {shi_zhu:<8} (时差：{diff_minutes:+d}分钟)")

print("\n" + "=" * 80)
print("重点时辰验证（巳时和亥时）")
print("=" * 80)

# 重点测试巳时和亥时
for hour in [9, 10, 11, 21, 22, 23]:
    sizhu = get_sizhu_accurate(2026, 9, 9, hour, city_name='北京')
    true_solar_hour = calendar._calculate_true_solar_time(hour, 0, 116.4074, 
                                                           __import__('datetime').date(2026, 9, 9))
    print(f"\n北京时间 {hour:02d}:00")
    print(f"  真太阳时：{true_solar_hour:.2f}小时 ({int(true_solar_hour):02d}:{int((true_solar_hour % 1) * 60):02d})")
    print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")

print("\n" + "=" * 80)
print("结论：")
print("北京地区真太阳时比北京时间晚约 14-16 分钟")
print("但时柱地支仍然按照真太阳时所在时辰确定")
print("=" * 80)
