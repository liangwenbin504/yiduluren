#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试鬼墓课断语是否正确集成
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'utils'))

from comprehensive_evaluation import ComprehensiveEvaluation

print("=" * 80)
print("测试鬼墓课断语集成")
print("=" * 80)
print()

# 创建评价系统
evaluator = ComprehensiveEvaluation()

# 检查鬼墓课断语是否存在
print("【检查鬼墓课断语】")
if '鬼墓' in evaluator.kejing_duanyu:
    print("✓ 鬼墓课断语已正确添加")
    print()
    
    gui_mu = evaluator.kejing_duanyu['鬼墓']
    print(f"课名：鬼墓课")
    print(f"评分：{gui_mu['score']}分")
    print(f"吉凶等级：大凶")
    print()
    print("【断语内容】")
    for i, duanyu in enumerate(gui_mu['duanyu'], 1):
        print(f"{i}. {duanyu}")
    print()
    print(f"【综述】{gui_mu['summary']}")
    print()
else:
    print("✗ 鬼墓课断语未找到！")
    print()

# 检查其他新增课目
print("【检查其他新增课目】")
for ke_name in ['天网', '地网', '空亡']:
    if ke_name in evaluator.kejing_duanyu:
        print(f"✓ {ke_name}课已添加（{evaluator.kejing_duanyu[ke_name]['score']}分）")
    else:
        print(f"✗ {ke_name}课未找到")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
