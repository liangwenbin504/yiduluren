#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查API服务器中的tiandi_pan数据结构
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
print(f"检查API服务器中的tiandi_pan数据结构")
print(f"日期时间: {year}年{month}月{day}日{hour}时")
print("=" * 70)

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

print(f"\ntiandi_pan 类型: {type(tiandi_pan)}")
print(f"tiandi_pan 内容:")
print(tiandi_pan)

print(f"\n验证三传计算:")
chu_chuan = '午'
print(f"初传: {chu_chuan}")

zhong_chuan = tiandi_pan.get(chu_chuan, 'N/A')
print(f"中传 (tiandi_pan['{chu_chuan}']): {zhong_chuan}")

mo_chuan = tiandi_pan.get(zhong_chuan, 'N/A')
print(f"末传 (tiandi_pan['{zhong_chuan}']): {mo_chuan}")

print(f"\n三传: {chu_chuan} → {zhong_chuan} → {mo_chuan}")

print("\n" + "=" * 70)
