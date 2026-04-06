#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整验证当前排盘数据
"""

import sys
import os
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from dizhi_layout_generator import arrange_tiandi_pan
from sike_sanchuan_engine import SiKeSanChuanCalculator
from sizhu_engine import get_sizhu

# 获取当前日期时间
now = datetime.now()
year = now.year
month = now.month
day = now.day
hour = now.hour

print("=" * 70)
print(f"完整验证当前排盘数据")
print(f"日期时间: {year}年{month}月{day}日{hour}时")
print("=" * 70)

# 获取四柱
sizhu = get_sizhu(year, month, day, hour, 0)  # 添加分钟参数
print(f"\n四柱信息:")
print(f"  年柱: {sizhu['yearPillar']}")
print(f"  月柱: {sizhu['monthPillar']}")
print(f"  日柱: {sizhu['dayPillar']}")
print(f"  时柱: {sizhu['hourPillar']}")

day_gan = sizhu['dayGan']
day_zhi = sizhu['dayZhi']

print(f"\n日干支: {day_gan}{day_zhi}")

# 月将映射
yuejiang_map = {
    1: '丑', 2: '子', 3: '亥', 4: '戌', 5: '酉', 6: '申',
    7: '未', 8: '午', 9: '巳', 10: '辰', 11: '卯', 12: '寅'
}
yue_jiang = yuejiang_map[month]

# 时辰地支
dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
shichen_index = (hour + 1) // 2 % 12
shi_chen = dizhi[shichen_index]

print(f"月将: {yue_jiang}")
print(f"时辰: {shi_chen}")

# 天地盘
tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)
print(f"\n天地盘:")
for di, tian in tiandi_pan.items():
    print(f"  地盘{di} → 天盘{tian}")

# 四课
calculator = SiKeSanChuanCalculator()
sike = calculator.qi_sike(day_gan, day_zhi, tiandi_pan)

print(f"\n四课:")
for i, ke in enumerate(sike, 1):
    print(f"  第{i}课: 上神={ke['上神']}, 下神={ke['下神']}")

# 三传
sanchuan_result = calculator.fa_sanchuan(sike, day_gan, day_zhi, tiandi_pan)

print(f"\n三传:")
print(f"  初传: {sanchuan_result['初传']}")
print(f"  中传: {sanchuan_result['中传']}")
print(f"  末传: {sanchuan_result['末传']}")
print(f"  课体: {sanchuan_result['课体']}")
print(f"  起法: {sanchuan_result['起法']}")

# 验证三传计算
print(f"\n三传验证:")
chu = sanchuan_result['初传']
zhong = tiandi_pan.get(chu, '?')
mo = tiandi_pan.get(zhong, '?')

print(f"  初传: {chu}")
print(f"  中传（初传作为地盘，其天盘）: {zhong}")
print(f"  末传（中传作为地盘，其天盘）: {mo}")

if sanchuan_result['中传'] == zhong and sanchuan_result['末传'] == mo:
    print("\n✅ 三传计算正确！")
else:
    print(f"\n❌ 三传计算错误！")
    print(f"  期望中传: {zhong}, 实际: {sanchuan_result['中传']}")
    print(f"  期望末传: {mo}, 实际: {sanchuan_result['末传']}")

print("\n" + "=" * 70)
