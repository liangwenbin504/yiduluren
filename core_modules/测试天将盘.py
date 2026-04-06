#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
天将盘计算测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.gui_ren_engine import GuiRenCalculator
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator

# 测试案例：甲子日午时
ri_gan = '甲'
ri_zhi = '子'
shi_ganzhi = '庚午'
shi_zhi = '午'

print("=" * 60)
print("天将盘计算测试")
print("=" * 60)
print(f"日干：{ri_gan}")
print(f"日支：{ri_zhi}")
print(f"时柱：{shi_ganzhi}")
print(f"时支：{shi_zhi}")
print()

# 计算天地盘
sike_engine = SiKeSanChuanCalculator()
yue_jiang = '亥'  # 正月亥将
tiandi_pan = sike_engine.get_tiandi_pan(yue_jiang, shi_zhi)

print("【天地盘】")
print("-" * 60)
for dizhi in ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']:
    tian = tiandi_pan.get(dizhi, '')
    print(f"地盘{dizhi:2s} → 天盘{tian:2s}")
print()

# 计算贵人盘
gui_ren_calc = GuiRenCalculator()

# 判断昼夜
zhou_hours = ['卯', '辰', '巳', '午', '未', '申']
is_night = shi_zhi not in zhou_hours
print(f"昼夜判断：{shi_zhi}时属于{'夜时' if is_night else '昼时'}")
print()

# 排贵人盘
try:
    # 包装天地盘为正确格式
    tiandi_pan_dict = {'天地对应': tiandi_pan}
    
    gui_ren_pan = gui_ren_calc.arrange_gui_ren_pan(ri_gan, tiandi_pan_dict, shi_ganzhi, is_night)
    
    print("【贵人盘信息】")
    print("-" * 60)
    print(f"贵人：{gui_ren_pan['贵人']}")
    print(f"昼夜：{gui_ren_pan['昼夜']}")
    print(f"贵人落地盘位置：{gui_ren_pan['贵人落地盘位置']}")
    print(f"顺逆：{gui_ren_pan['顺逆']}行")
    print()
    
    print("【十二天将】")
    print("-" * 60)
    for tj in gui_ren_pan['天将列表']:
        print(f"{tj['天将']:6} → 天盘{tj['地支']:2}")
    print()
    
    print("【天将映射】")
    print("-" * 60)
    tian_jiang_map = gui_ren_pan['天将映射']
    for tian, tianjiang in tian_jiang_map.items():
        print(f"天盘{tian:2s} → {tianjiang:4}")
    
except Exception as e:
    print(f"错误：{e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
