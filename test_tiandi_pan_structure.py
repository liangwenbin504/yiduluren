#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试天地盘数据结构
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))

from dizhi_layout_generator import arrange_tiandi_pan

# 测试天地盘
yue_jiang = '亥'
shi_chen = '寅'

tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)

print("=" * 60)
print(f"天地盘数据结构 (月将={yue_jiang}, 时辰={shi_chen}):")
print("=" * 60)

print(f"\ntiandi_pan 类型: {type(tiandi_pan)}")
print(f"\ntiandi_pan 内容:")
print(tiandi_pan)

print(f"\n验证三传计算:")
chu_chuan = '寅'
print(f"初传: {chu_chuan}")

zhong_chuan = tiandi_pan.get(chu_chuan, 'N/A')
print(f"中传 (tiandi_pan['{chu_chuan}']): {zhong_chuan}")

mo_chuan = tiandi_pan.get(zhong_chuan, 'N/A')
print(f"末传 (tiandi_pan['{zhong_chuan}']): {mo_chuan}")

print(f"\n三传: {chu_chuan} → {zhong_chuan} → {mo_chuan}")
