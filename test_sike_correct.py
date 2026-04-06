#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证四课起法 - 己亥日卯将戌时
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))

from dizhi_layout_generator import arrange_tiandi_pan

print("=" * 70)
print("验证四课起法 - 己亥日卯将戌时")
print("=" * 70)

# 月将和时辰
yue_jiang = '卯'
shi_chen = '戌'

print(f"\n月将: {yue_jiang}")
print(f"时辰: {shi_chen}")

# 天地盘
tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)

print(f"\n天地盘:")
for di, tian in tiandi_pan.items():
    print(f"  地盘{di} → 天盘{tian}")

# 日干支
day_gan = '己'
day_zhi = '亥'

print(f"\n日干支: {day_gan}{day_zhi}")

# 日干寄宫
RIGAN_JIGONG = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
    '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
}

# 等等，我需要检查己的寄宫
# 根据《六壬大全》：
# 甲寄寅、乙寄辰、丙戊寄巳、丁己寄未、庚寄申、辛寄戌、壬寄亥、癸寄丑

RIGAN_JIGONG_CORRECT = {
    '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
    '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'
}

ri_gan_ji_gong = RIGAN_JIGONG_CORRECT[day_gan]
print(f"日干寄宫: {ri_gan_ji_gong}")

# 四课起法
print(f"\n四课起法（根据《六壬大全》）:")

# 第一课：日干上神
# 己寄未宫，未的天盘
ke1_bottom = day_gan  # 显示日干
ke1_top = tiandi_pan[ri_gan_ji_gong]  # 未的天盘
print(f"  第一课: 上神={ke1_top}, 下神={ke1_bottom}")
print(f"    （己寄{ri_gan_ji_gong}宫，{ri_gan_ji_gong}的天盘是{ke1_top}）")

# 第二课：日干上神之上神
ke2_bottom = ke1_top
ke2_top = tiandi_pan[ke2_bottom]
print(f"  第二课: 上神={ke2_top}, 下神={ke2_bottom}")

# 第三课：日支上神
ke3_bottom = day_zhi
ke3_top = tiandi_pan[day_zhi]
print(f"  第三课: 上神={ke3_top}, 下神={ke3_bottom}")
print(f"    （亥的天盘是{ke3_top}）")

# 第四课：日支上神之上神
ke4_bottom = ke3_top
ke4_top = tiandi_pan[ke4_bottom]
print(f"  第四课: 上神={ke4_top}, 下神={ke4_bottom}")

print("\n" + "=" * 70)
