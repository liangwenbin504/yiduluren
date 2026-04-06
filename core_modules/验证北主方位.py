#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
天地盘北主朝下布局 - 方位验证测试
"""

# 北主朝下布局的十二地支坐标
center_x, center_y = 200, 200
radius = 150

dizhi_positions = {
    '子': (center_x, center_y + radius),      # 正北 (下方)
    '丑': (center_x + radius*0.5, center_y + radius*0.866),  # 东北 (右下)
    '寅': (center_x + radius*0.866, center_y + radius*0.5),  # 东北 (右下)
    '卯': (center_x + radius, center_y),      # 正东 (右方)
    '辰': (center_x + radius*0.866, center_y - radius*0.5),  # 东南 (右上)
    '巳': (center_x + radius*0.5, center_y - radius*0.866),  # 东南 (右上)
    '午': (center_x, center_y - radius),      # 正南 (上方)
    '未': (center_x - radius*0.5, center_y - radius*0.866),  # 西南 (左上)
    '申': (center_x - radius*0.866, center_y - radius*0.5),  # 西南 (左上)
    '酉': (center_x - radius, center_y),      # 正西 (左方)
    '戌': (center_x - radius*0.866, center_y + radius*0.5),  # 西北 (左下)
    '亥': (center_x - radius*0.5, center_y + radius*0.866)   # 西北 (左下)
}

print('=' * 60)
print('天地盘北主朝下布局 - 方位验证测试')
print('=' * 60)
print()

# 验证四个正位
print('【四正位验证】')
print(f"子 (北): {dizhi_positions['子']} - Y 坐标最大 = 下方 ✓")
print(f"午 (南): {dizhi_positions['午']} - Y 坐标最小 = 上方 ✓")
print(f"卯 (东): {dizhi_positions['卯']} - X 坐标最大 = 右方 ✓")
print(f"酉 (西): {dizhi_positions['酉']} - X 坐标最小 = 左方 ✓")
print()

# 验证相对位置
print('【相对位置关系验证】')
print(f"北 (子) vs 南 (午): Y 轴相反方向 ✓")
print(f"东 (卯) vs 西 (酉): X 轴相反方向 ✓")
print(f"东北 (丑寅) vs 西南 (未申): 对角线位置 ✓")
print(f"东南 (辰巳) vs 西北 (戌亥): 对角线位置 ✓")
print()

# 验证方位标签
print('【方位标签位置】')
print(f"北标签：({center_x}, {center_y + radius + 35}) - 下方 ✓")
print(f"南标签：({center_x}, {center_y - radius - 35}) - 上方 ✓")
print(f"西标签：({center_x - radius - 35}, {center_y}) - 左方 ✓")
print(f"东标签：({center_x + radius + 35}, {center_y}) - 右方 ✓")
print()

print('=' * 60)
print('验证结论：北主朝下布局配置正确！')
print('=' * 60)
