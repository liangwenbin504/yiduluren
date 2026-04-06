#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试龙德课判断逻辑
"""

import sys
import os
import importlib.util
from datetime import datetime

# 添加引擎路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

# 加载 720_ke_database 模块
spec = importlib.util.spec_from_file_location("ke_database", 
    os.path.join(os.path.dirname(__file__), 'src', 'engine', '720_ke_database.py'))
ke_database = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ke_database)
LiuShiJiaZi = ke_database.LiuShiJiaZi

from complete_qi_ke_engine import CompleteQiKeEngine
from ke_ti_judge_pro import KeTiJudgeProfessional

# 测试一个具体的课例
engine = CompleteQiKeEngine()
ke_ti_judge = KeTiJudgeProfessional()

# 2026 年 3 月 15 日
test_date = datetime(2026, 3, 15)
base_date = datetime(1984, 1, 1)
days_offset = (test_date - base_date).days
gan_zhi_index = days_offset % 60
ri_gan_zhi = LiuShiJiaZi.get_all_gan_zhi()[gan_zhi_index]

# 2026 年是丙午年，太岁为午
year_gan, tai_sui = LiuShiJiaZi.get_gan_zhi(2026)

# 农历二月，月将为戌（正月将亥，二月将戌）
lunar_month = 2
yue_jiang = LiuShiJiaZi.DI_ZHI[(12 - lunar_month) % 12]  # 正月亥，二月戌

print(f"测试日期：{test_date.strftime('%Y-%m-%d')}")
print(f"日干支：{ri_gan_zhi}")
print(f"太岁：{tai_sui} (2026 丙午年)")
print(f"月将：{yue_jiang} (农历{lunar_month}月)")
ri_gan = ri_gan_zhi[0]
gui_ren_list = ke_ti_judge.SHI_GAN_GUI_REN.get(ri_gan, [])
print(f"日干'{ri_gan}'贵人：{gui_ren_list}")
print("=" * 80)

# 测试第一个时辰
shi = LiuShiJiaZi.DI_ZHI[0]  # 子时
result = engine.qi_ke(
    ri_gan_zhi=ri_gan_zhi,
    yue_jiang=yue_jiang,
    shi_chen=shi,
    lunar_month=lunar_month,
    nian_zhi=tai_sui
)

print(f"\n{shi}时起课结果:")
print(f"返回类型：{type(result)}")
print(f"所有键：{result.keys()}")
print(f"\n四课：{result.get('四课', [])}")
print(f"\n三传：{result.get('三传', {})}")
print(f"\n课体：{result.get('课体', [])}")
