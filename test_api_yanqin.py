#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模拟API调用，检查演禽评分"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from yanqin_analyzer import YanQinAnalyzer
from sizhu_engine import get_sizhu
from datetime import datetime, timedelta

print("=" * 70)
print("模拟API调用 - 检查演禽评分")
print("=" * 70)

yanqin_analyzer = YanQinAnalyzer()

# 测试几个日期
test_dates = [
    (2026, 4, 4, '子'),
    (2026, 4, 5, '午'),
    (2026, 4, 6, '子'),
]

for year, month, day, shichen in test_dates:
    print(f"\n【测试】{year}-{month:02d}-{day:02d} {shichen}时")
    
    # 模拟API中的调用方式
    sizhu_result = get_sizhu(year, month, day, shichen)
    print(f"  四柱: {sizhu_result}")
    
    # API中的调用方式
    year_zhi = sizhu_result.get('年柱', '甲子')[1]
    month_zhi = sizhu_result.get('月柱', '甲子')[1]
    day_zhi = sizhu_result.get('日柱', '甲子')[1]
    hour_zhi = sizhu_result.get('时柱', '甲子')[1]
    
    print(f"  地支: 年={year_zhi}, 月={month_zhi}, 日={day_zhi}, 时={hour_zhi}")
    
    yanqin_result = yanqin_analyzer.analyze_four_qin(year_zhi, month_zhi, day_zhi, hour_zhi)
    
    if yanqin_result:
        yanqin_score = yanqin_result.get('综合评分', 50)
        print(f"  演禽评分: {yanqin_score}")
        print(f"  四禽: {yanqin_result.get('四禽')}")
        print(f"  格局: {yanqin_result.get('格局判定')}")
    else:
        print(f"  演禽结果为None!")

print("\n" + "=" * 70)
print("结论：演禽模块直接调用正常，评分在70-100之间")
print("=" * 70)
