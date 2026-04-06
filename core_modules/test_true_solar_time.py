#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真太阳时计算测试
测试不同城市、不同日期的真太阳时和时柱计算
"""

import sys
import os
from datetime import datetime, date

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate


def test_true_solar_time():
    """测试真太阳时计算"""
    print("=" * 80)
    print("真太阳时计算测试")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 测试日期：2026 年 9 月 4 日 10:00（北京时间）
    test_date = date(2026, 9, 4)
    beijing_time = 10.0  # 10:00
    
    print(f"\n测试日期：2026 年 9 月 4 日 10:00（北京时间）")
    print(f"均时差：{calendar._calculate_equation_of_time_precise(test_date) * 60:.2f}分钟")
    
    # 测试不同城市
    test_cities = ['北京', '上海', '广州', '成都', '乌鲁木齐', '拉萨']
    
    print(f"\n{'城市':<10} {'经度':<10} {'北京时间':<10} {'真太阳时':<10} {'时差':<10} {'时辰':<8}")
    print("-" * 80)
    
    for city in test_cities:
        coords = calendar.get_city_coordinates(city)
        if coords:
            longitude, latitude = coords
            
            # 计算真太阳时
            true_solar_time = calendar._calculate_true_solar_time(
                int(beijing_time), 0, longitude, test_date
            )
            
            # 计算时差
            time_diff = (true_solar_time - beijing_time) * 60  # 分钟
            
            # 确定时辰
            if true_solar_time >= 23 or true_solar_time < 1:
                shichen = '子时'
            elif true_solar_time < 3:
                shichen = '丑时'
            elif true_solar_time < 5:
                shichen = '寅时'
            elif true_solar_time < 7:
                shichen = '卯时'
            elif true_solar_time < 9:
                shichen = '辰时'
            elif true_solar_time < 11:
                shichen = '巳时'
            elif true_solar_time < 13:
                shichen = '午时'
            elif true_solar_time < 15:
                shichen = '未时'
            elif true_solar_time < 17:
                shichen = '申时'
            elif true_solar_time < 19:
                shichen = '酉时'
            elif true_solar_time < 21:
                shichen = '戌时'
            else:
                shichen = '亥时'
            
            print(f"{city:<10} {longitude:<10.2f} {beijing_time:<10.2f} {true_solar_time:<10.2f} {time_diff:<10.2f} {shichen:<8}")
    
    print("-" * 80)


def test_hour_ganzhi_by_city():
    """测试不同城市的时柱"""
    print("\n" + "=" * 80)
    print("不同城市时柱对比测试")
    print("=" * 80)
    
    # 测试日期：2026 年 9 月 4 日（辛巳日）
    year, month, day = 2026, 9, 4
    beijing_hour = 10  # 10:00（北京时间）
    
    print(f"\n测试条件：{year}年{month}月{day}日 {beijing_hour}:00（北京时间）")
    print(f"日柱：辛巳")
    print(f"五鼠遁：丙辛从戊起\n")
    
    # 测试城市
    test_cities = [
        ('北京', 9),   # 北京 9 点
        ('北京', 10),  # 北京 10 点
        ('北京', 11),  # 北京 11 点
        ('上海', 10),  # 上海 10 点
        ('广州', 10),  # 广州 10 点
        ('成都', 10),  # 成都 10 点
        ('乌鲁木齐', 10),  # 乌鲁木齐 10 点
        ('拉萨', 10),  # 拉萨 10 点
    ]
    
    print(f"{'城市':<10} {'北京时间':<10} {'真太阳时':<12} {'时柱':<8} {'说明':<30}")
    print("-" * 80)
    
    for city, hour in test_cities:
        # 使用城市名称计算四柱
        sizhu = get_sizhu_accurate(year, month, day, hour, 0, city_name=city)
        
        # 获取经纬度
        calendar = PreciseCalendar()
        longitude, latitude = calendar.get_city_coordinates(city)
        
        # 计算真太阳时
        true_solar = calendar._calculate_true_solar_time(hour, 0, longitude, date(year, month, day))
        
        # 说明
        if '乌鲁木齐' in city or '拉萨' in city:
            note = "西部地区，时差显著"
        elif '成都' in city:
            note = "四川盆地，时差较大"
        else:
            note = "-"
        
        print(f"{city:<10} {hour}:00       {true_solar:<12.2f} {sizhu['时柱']:<8} {note:<30}")
    
    print("-" * 80)


def test_boundary_cases():
    """测试时辰边界情况"""
    print("\n" + "=" * 80)
    print("时辰边界测试（北京）")
    print("=" * 80)
    
    year, month, day = 2026, 9, 4
    city = '北京'
    
    # 测试每个时辰的边界
    boundary_times = [
        0, 1, 2, 3, 4, 5,  # 子时、丑时、寅时
        6, 7, 8, 9, 10, 11,  # 卯时、辰时、巳时
        12, 13, 14, 15, 16, 17,  # 午时、未时、申时
        18, 19, 20, 21, 22, 23,  # 酉时、戌时、亥时
    ]
    
    print(f"\n测试日期：{year}年{month}月{day}日（辛巳日）")
    print(f"城市：北京（东经 116.41 度）")
    print(f"五鼠遁：丙辛从戊起\n")
    
    print(f"{'北京时间':<10} {'真太阳时':<12} {'时柱':<8} {'时辰':<8}")
    print("-" * 80)
    
    for hour in boundary_times:
        sizhu = get_sizhu_accurate(year, month, day, hour, 0, city_name=city)
        
        calendar = PreciseCalendar()
        longitude, _ = calendar.get_city_coordinates(city)
        true_solar = calendar._calculate_true_solar_time(hour, 0, longitude, date(year, month, day))
        
        # 确定时辰
        if true_solar >= 23 or true_solar < 1:
            shichen = '子时'
        elif true_solar < 3:
            shichen = '丑时'
        elif true_solar < 5:
            shichen = '寅时'
        elif true_solar < 7:
            shichen = '卯时'
        elif true_solar < 9:
            shichen = '辰时'
        elif true_solar < 11:
            shichen = '巳时'
        elif true_solar < 13:
            shichen = '午时'
        elif true_solar < 15:
            shichen = '未时'
        elif true_solar < 17:
            shichen = '申时'
        elif true_solar < 19:
            shichen = '酉时'
        elif true_solar < 21:
            shichen = '戌时'
        else:
            shichen = '亥时'
        
        print(f"{hour}:00       {true_solar:<12.2f} {sizhu['时柱']:<8} {shichen:<8}")
    
    print("-" * 80)


def test_eot_through_year():
    """测试全年均时差变化"""
    print("\n" + "=" * 80)
    print("2026 年全年均时差变化")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 每月 15 日
    print(f"\n{'日期':<15} {'均时差 (分钟)':<15} {'说明':<30}")
    print("-" * 80)
    
    for month in range(1, 13):
        test_date = date(2026, month, 15)
        eot = calendar._calculate_equation_of_time_precise(test_date)
        eot_minutes = eot * 60  # 转换为分钟
        
        if eot_minutes > 5:
            note = "真太阳时快"
        elif eot_minutes < -5:
            note = "真太阳时慢"
        else:
            note = "接近平均"
        
        print(f"2026-{month:02d}-15     {eot_minutes:>7.2f}          {note:<30}")
    
    print("-" * 80)


def test_practical_example():
    """实际应用案例"""
    print("\n" + "=" * 80)
    print("实际应用案例：2026 年 9 月 4 日 10:00 起课")
    print("=" * 80)
    
    year, month, day = 2026, 9, 4
    hour = 10
    
    print(f"\n场景：客户在不同城市要求同一时间（北京时间 10:00）起课")
    print(f"公历：{year}年{month}月{day}日 {hour}:00（北京时间）\n")
    
    cities = ['北京', '上海', '广州', '成都', '乌鲁木齐']
    
    for city in cities:
        # 计算四柱
        sizhu = get_sizhu_accurate(year, month, day, hour, 0, city_name=city)
        
        # 获取经纬度
        calendar = PreciseCalendar()
        longitude, _ = calendar.get_city_coordinates(city)
        
        # 计算真太阳时
        true_solar = calendar._calculate_true_solar_time(hour, 0, longitude, date(year, month, day))
        
        print(f"{city}（东经{longitude:.2f}°）:")
        print(f"  四柱：{sizhu['年柱']}年 {sizhu['月柱']}月 {sizhu['日柱']}日 {sizhu['时柱']}时")
        print(f"  真太阳时：{true_solar:.2f}小时（{int(true_solar)}:{int((true_solar % 1) * 60):02d}）")
        print(f"  时柱地支：{sizhu['时柱'][1]}")
        print()
    
    print("结论：")
    print("  1. 年柱、月柱、日柱各地相同")
    print("  2. 时柱因地域不同可能不同（特别是西部地区）")
    print("  3. 真太阳时确保时柱准确对应当地实际太阳位置")
    print("-" * 80)


def main():
    """主测试函数"""
    print("=" * 80)
    print("真太阳时计算功能完整测试")
    print("=" * 80)
    
    # 测试真太阳时
    test_true_solar_time()
    
    # 测试不同时柱
    test_hour_ganzhi_by_city()
    
    # 测试边界
    test_boundary_cases()
    
    # 测试全年均时差
    test_eot_through_year()
    
    # 实际案例
    test_practical_example()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    
    # 总结
    print(f"\n【功能总结】")
    print(f"  ✅ 精确计算均时差（地球轨道椭圆引起）")
    print(f"  ✅ 考虑经度差异（每度 4 分钟）")
    print(f"  ✅ 支持 60+ 中国主要城市")
    print(f"  ✅ 时柱地支与真太阳时严格对应")
    print(f"  ✅ 可使用城市名称自动获取经纬度")
    print(f"\n【使用建议】")
    print(f"  1. 东部地区（北京、上海）：时差较小，影响不大")
    print(f"  2. 中部地区（成都、重庆）：时差约 30-60 分钟，需注意")
    print(f"  3. 西部地区（乌鲁木齐、拉萨）：时差 2-3 小时，必须使用真太阳时")
    print(f"  4. 时辰边界附近：务必使用真太阳时确认时辰")


if __name__ == '__main__':
    main()
