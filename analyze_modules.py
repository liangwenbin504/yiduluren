#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析各模块评分情况"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer
from yanqin_analyzer import YanQinAnalyzer
from sizhu_engine import get_sizhu
from datetime import datetime, timedelta

doushou = DouhouKegeAnalyzer()
yanqin = YanQinAnalyzer()

print("=" * 70)
print("分析各模块评分情况")
print("=" * 70)

# 测试未来30天
today = datetime.now()
stats = {
    'doushou_pass': 0,  # 斗首>=50
    'yanqin_pass': 0,   # 演禽>=70
    'both_pass': 0,     # 两者都通过
    'total': 0
}

for day_offset in range(30):
    date = today + timedelta(days=day_offset)
    year, month, day = date.year, date.month, date.day
    
    for shichen in ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']:
        try:
            sizhu = get_sizhu(year, month, day, shichen)
            if not sizhu:
                continue
            
            # 斗首评分
            doushou_result = doushou.analyze_kege('壬', sizhu)
            doushou_score = doushou_result.get('综合评分', 0)
            
            # 演禽评分
            year_zhi = sizhu['年柱'][1]
            month_zhi = sizhu['月柱'][1]
            day_zhi = sizhu['日柱'][1]
            hour_zhi = sizhu['时柱'][1]
            yanqin_result = yanqin.analyze_four_qin(year_zhi, month_zhi, day_zhi, hour_zhi)
            yanqin_score = yanqin_result.get('综合评分', 0)
            
            stats['total'] += 1
            if doushou_score >= 50:
                stats['doushou_pass'] += 1
            if yanqin_score >= 70:
                stats['yanqin_pass'] += 1
            if doushou_score >= 50 and yanqin_score >= 70:
                stats['both_pass'] += 1
                print(f"✓ {date.strftime('%Y-%m-%d')} {shichen}时: 斗首={doushou_score}, 演禽={yanqin_score}")
                
        except Exception as e:
            pass

print("\n" + "=" * 70)
print("统计结果（30天×12时辰=360课）:")
print(f"  总课数: {stats['total']}")
print(f"  斗首>=50: {stats['doushou_pass']} ({stats['doushou_pass']*100/stats['total']:.1f}%)")
print(f"  演禽>=70: {stats['yanqin_pass']} ({stats['yanqin_pass']*100/stats['total']:.1f}%)")
print(f"  两者都通过: {stats['both_pass']} ({stats['both_pass']*100/stats['total']:.1f}%)")
print("=" * 70)
