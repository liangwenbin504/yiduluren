#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试完整的 64 课经断语库
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))

from kejing_duanyu_complete import KEJING_DUANYU_COMPLETE

print("=" * 80)
print("测试 64 课经完整断语库")
print("=" * 80)
print()

print(f"课经总数：{len(KEJING_DUANYU_COMPLETE)}个")
print()

# 检查鬼墓课
print("【检查鬼墓课】")
if '鬼墓课' in KEJING_DUANYU_COMPLETE:
    gui_mu = KEJING_DUANYU_COMPLETE['鬼墓课']
    print("✓ 鬼墓课已找到")
    print(f"  评分：{gui_mu['score']}分")
    print(f"  等级：{gui_mu['level']}")
    print(f"  综述：{gui_mu['summary']}")
    print(f"  断语数量：{len(gui_mu['duanyu'])}条")
    print(f"  特殊格局：{len(gui_mu.get('special_cases', []))}个")
else:
    print("✗ 鬼墓课未找到")

print()

# 检查所有课经
print("【课经列表】")
for i, (name, info) in enumerate(KEJING_DUANYU_COMPLETE.items(), 1):
    print(f"{i:2d}. {name:10s} - {info['score']:2d}分 - {info['level']}")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
