#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成图片功能
单独生成四柱、天地盘、四课、三传的图片
"""

import os
from generate_images import generate_sizhu_image, generate_tiandi_image, generate_sike_image, generate_sanchuan_image

# 测试数据
test_data = {
    'four_pillars': {'年': '丙午', '月': '辛卯', '日': '己亥', '时': '甲戌'},
    'daliuren_data': {
        'tianPan': {'子': '丑', '丑': '寅', '寅': '卯', '卯': '辰', '辰': '巳', '巳': '午', '午': '未', '未': '申', '申': '酉', '酉': '戌', '戌': '亥', '亥': '子'},
        'sike': [
            {'top': '申', 'bottom': '己'},
            {'top': '酉', 'bottom': '申'},
            {'top': '子', 'bottom': '亥'},
            {'top': '丑', 'bottom': '子'}
        ],
        'sanchuan': {
            '初传': {'tiangan': '辛', 'dizhi': '丑', 'liuqin': '兄弟'},
            '中传': {'tiangan': '壬', 'dizhi': '寅', 'liuqin': '官鬼'},
            '末传': {'tiangan': '癸', 'dizhi': '卯', 'liuqin': '官鬼'}
        }
    }
}

# 生成四柱图片
print("生成四柱图片...")
sizhu_data = test_data['four_pillars']
sizhu_image = generate_sizhu_image(sizhu_data)
if sizhu_image:
    print(f"✅ 四柱图片生成成功：{sizhu_image}")
else:
    print("❌ 四柱图片生成失败")

# 生成天地盘图片
print("\n生成天地盘图片...")
tian_pan = test_data['daliuren_data']['tianPan']
tiandi_image = generate_tiandi_image(tian_pan)
if tiandi_image:
    print(f"✅ 天地盘图片生成成功：{tiandi_image}")
else:
    print("❌ 天地盘图片生成失败")

# 生成四课图片
print("\n生成四课图片...")
sike = test_data['daliuren_data']['sike']
sike_image = generate_sike_image(sike)
if sike_image:
    print(f"✅ 四课图片生成成功：{sike_image}")
else:
    print("❌ 四课图片生成失败")

# 生成三传图片
print("\n生成三传图片...")
sanchuan = test_data['daliuren_data']['sanchuan']
sanchuan_image = generate_sanchuan_image(sanchuan)
if sanchuan_image:
    print(f"✅ 三传图片生成成功：{sanchuan_image}")
else:
    print("❌ 三传图片生成失败")

print("\n所有图片生成完成！")
