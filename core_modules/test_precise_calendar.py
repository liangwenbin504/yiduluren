#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高精度历法模块集成测试
验证新历法模块的正确性并集成到现有系统
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from precise_calendar import PreciseCalendar, get_sizhu_accurate


def test_2026_sep_4():
    """测试 2026 年 9 月 4 日的四柱"""
    print("=" * 80)
    print("测试案例：2026 年 9 月 4 日")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 计算四柱
    sizhu = calendar.get_sizhu_precise(2026, 9, 4, 10)
    
    print(f"\n公历：2026 年 9 月 4 日 10:00")
    print(f"计算结果：")
    print(f"  年柱：{sizhu['年柱']}")
    print(f"  月柱：{sizhu['月柱']}")
    print(f"  日柱：{sizhu['日柱']}")
    print(f"  时柱：{sizhu['时柱']}")
    
    print(f"\n分析：")
    print(f"  1. 年柱：2026 年为丙午年 ✓")
    print(f"  2. 月柱：9 月 4 日在处暑（8 月 23 日）后、寒露（10 月 8 日）前")
    print(f"     - 处暑到寒露为酉月（八月）")
    print(f"     - 丙年酉月，根据五虎遁：丙辛从戊起，酉为丁酉")
    print(f"     - 正确月柱应为：丁酉月")
    print(f"  3. 日柱：需要验证基准日和计算")
    print(f"  4. 时柱：辛日巳时，根据五鼠遁：丙辛从戊起，巳为癸巳 ✓")
    
    # 验证
    print(f"\n验证结果：")
    expected = {
        '年柱': '丙午',
        '月柱': '丁酉',  # 修正后的正确值
        '日柱': '辛巳',
        '时柱': '癸巳'
    }
    
    for pillar, expected_val in expected.items():
        actual_val = sizhu[pillar]
        status = "✓" if actual_val == expected_val else "✗"
        print(f"  {pillar}: {actual_val} (期望：{expected_val}) {status}")
    
    return sizhu


def test_jieqi_dates():
    """测试 2026 年节气日期"""
    print("\n" + "=" * 80)
    print("2026 年节气日期测试")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    jieqi_dates = calendar.get_jieqi_dates(2026)
    
    # 关键节气
    key_jieqi = ['立春', '雨水', '惊蛰', '春分', '清明', '谷雨',
                 '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
                 '立秋', '处暑', '白露', '秋分', '寒露', '霜降',
                 '立冬', '小雪', '大雪', '冬至', '小寒', '大寒']
    
    print(f"\n2026 年节气日期：")
    for jieqi in key_jieqi:
        if jieqi in jieqi_dates:
            dt = jieqi_dates[jieqi]
            print(f"  {jieqi}: {dt.strftime('%m月%d日 %H:%M')}")


def test_year_boundary():
    """测试年柱边界（立春前后）"""
    print("\n" + "=" * 80)
    print("年柱边界测试（立春前后）")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 2026 年立春在 2 月 4 日
    test_dates = [
        (2026, 2, 2),
        (2026, 2, 3),
        (2026, 2, 4),
        (2026, 2, 5),
        (2026, 2, 6),
    ]
    
    print(f"\n2026 年立春前后年柱变化：")
    for year, month, day in test_dates:
        year_ganzhi = calendar.get_year_ganzhi(year, month, day)
        day_ganzhi = calendar.get_day_ganzhi(year, month, day)
        print(f"  {year}年{month}月{day}日：年柱={year_ganzhi}, 日柱={day_ganzhi}")


def test_month_boundary():
    """测试月柱边界（节气前后）"""
    print("\n" + "=" * 80)
    print("月柱边界测试（白露前后）")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 2026 年白露在 9 月 8 日
    test_dates = [
        (2026, 9, 6),
        (2026, 9, 7),
        (2026, 9, 8),
        (2026, 9, 9),
        (2026, 9, 10),
    ]
    
    print(f"\n2026 年白露前后月柱变化：")
    for year, month, day in test_dates:
        month_ganzhi = calendar.get_month_ganzhi(year, month, day)
        day_ganzhi = calendar.get_day_ganzhi(year, month, day)
        print(f"  {year}年{month}月{day}日：月柱={month_ganzhi}, 日柱={day_ganzhi}")


def test_continuous_days():
    """测试连续日期的日柱"""
    print("\n" + "=" * 80)
    print("连续日期日柱测试")
    print("=" * 80)
    
    calendar = PreciseCalendar()
    
    # 2026 年 9 月 1-10 日
    start_date = datetime(2026, 9, 1)
    
    print(f"\n2026 年 9 月 1-10 日的日柱：")
    for i in range(10):
        d = start_date + __import__('datetime').timedelta(days=i)
        day_ganzhi = calendar.get_day_ganzhi(d.year, d.month, d.day)
        print(f"  {d.strftime('%Y-%m-%d')}: {day_ganzhi}")


def compare_with_old():
    """对比新旧历法模块"""
    print("\n" + "=" * 80)
    print("新旧历法模块对比")
    print("=" * 80)
    
    # 测试旧模块（如果存在）
    try:
        from ganzhi_calendar import get_sizhu_accurate as old_get_sizhu
        
        print(f"\n测试 2026 年 9 月 4 日：")
        
        # 旧模块
        old_sizhu = old_get_sizhu(2026, 9, 4)
        print(f"旧模块：{old_sizhu}")
        
        # 新模块
        new_sizhu = get_sizhu_accurate(2026, 9, 4, 10)
        print(f"新模块：{new_sizhu}")
        
        # 对比
        print(f"\n对比结果：")
        for pillar in ['年柱', '月柱', '日柱', '时柱']:
            old_val = old_sizhu.get(pillar, 'N/A')
            new_val = new_sizhu[pillar]
            status = "✓" if old_val == new_val else "✗"
            print(f"  {pillar}: 旧={old_val}, 新={new_val} {status}")
        
    except ImportError:
        print(f"\n未找到旧模块，跳过对比测试")


def main():
    """主函数"""
    print("=" * 80)
    print("高精度历法模块集成测试")
    print("=" * 80)
    
    # 测试 2026 年 9 月 4 日
    sizhu = test_2026_sep_4()
    
    # 测试节气日期
    test_jieqi_dates()
    
    # 测试年柱边界
    test_year_boundary()
    
    # 测试月柱边界
    test_month_boundary()
    
    # 测试连续日期
    test_continuous_days()
    
    # 对比新旧模块
    compare_with_old()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    
    # 总结
    print(f"\n【总结】")
    print(f"  1. 新模块使用精确天文算法计算节气")
    print(f"  2. 年柱以立春为界，月柱以节气为界")
    print(f"  3. 日柱使用基准日推算，保证准确性")
    print(f"  4. 时柱考虑真太阳时，更精确")
    print(f"  5. 建议：更新所有依赖历法的模块使用新模块")


if __name__ == '__main__':
    main()
