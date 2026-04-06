#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首课格吉凶评分查看器
显示所有课格的评分和使用建议
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))
from douhou_kege_system import DiYiDouShouKeGe
from douhou_shan_jia_system import DouShouShanJiaKeGe

def display_score_table():
    """显示评分表格"""
    print("=" * 80)
    print("斗首课格吉凶评分表（10 分制）")
    print("=" * 80)
    print()
    
    # 第一斗首课格评分
    print("【第一斗首课格】")
    print("-" * 80)
    print(f"{'课格名称':<10} {'评分':<8} {'吉凶':<10} {'是否可用':<10} {'建议':<30}")
    print("-" * 80)
    
    kege_analyzer = DiYiDouShouKeGe()
    for kege_name in kege_analyzer.get_all_ke_ge_names():
        score = kege_analyzer.get_ke_ge_score(kege_name)
        usable = kege_analyzer.is_ke_ge_usable(kege_name)
        desc = kege_analyzer.get_score_description(score)
        suggestion = "✓ 推荐使用" if usable else "✗ 不建议使用"
        print(f"{kege_name:<10} {score:<8.1f} {desc:<10} {str(usable):<10} {suggestion:<30}")
    
    print()
    print("=" * 80)
    print()
    
    # 二十四山课格评分
    print("【二十四山课格】")
    print("-" * 80)
    print(f"{'山家':<8} {'评分':<8} {'吉凶':<10} {'是否可用':<10} {'建议':<30}")
    print("-" * 80)
    
    shanjia_analyzer = DouShouShanJiaKeGe()
    for shanjia_name in shanjia_analyzer.get_all_shan_jia_names():
        score = shanjia_analyzer.get_shan_jia_score(shanjia_name)
        usable = shanjia_analyzer.is_shan_jia_usable(shanjia_name)
        desc = shanjia_analyzer.get_score_description(score)
        suggestion = "✓ 推荐使用" if usable else "✗ 不建议使用"
        print(f"{shanjia_name:<8} {score:<8.1f} {desc:<10} {str(usable):<10} {suggestion:<30}")
    
    print()
    print("=" * 80)
    print()
    
    # 统计信息
    print("【统计信息】")
    print("-" * 80)
    
    # 第一斗首课格统计
    kege_scores = [kege_analyzer.get_ke_ge_score(k) for k in kege_analyzer.get_all_ke_ge_names()]
    kege_usable_count = sum(1 for k in kege_analyzer.get_all_ke_ge_names() if kege_analyzer.is_ke_ge_usable(k))
    print(f"第一斗首课格：共{len(kege_scores)}个，可用{kege_usable_count}个，不可用{len(kege_scores)-kege_usable_count}个")
    print(f"  最高分：{max(kege_scores):.1f}分 ({kege_analyzer.get_score_description(max(kege_scores))})")
    print(f"  最低分：{min(kege_scores):.1f}分 ({kege_analyzer.get_score_description(min(kege_scores))})")
    print(f"  平均分：{sum(kege_scores)/len(kege_scores):.1f}分")
    
    print()
    
    # 二十四山课格统计
    shanjia_scores = [shanjia_analyzer.get_shan_jia_score(s) for s in shanjia_analyzer.get_all_shan_jia_names()]
    shanjia_usable_count = sum(1 for s in shanjia_analyzer.get_all_shan_jia_names() if shanjia_analyzer.is_shan_jia_usable(s))
    print(f"二十四山课格：共{len(shanjia_scores)}个，可用{shanjia_usable_count}个，不可用{len(shanjia_scores)-shanjia_usable_count}个")
    print(f"  最高分：{max(shanjia_scores):.1f}分 ({shanjia_analyzer.get_score_description(max(shanjia_scores))})")
    print(f"  最低分：{min(shanjia_scores):.1f}分 ({shanjia_analyzer.get_score_description(min(shanjia_scores))})")
    print(f"  平均分：{sum(shanjia_scores)/len(shanjia_scores):.1f}分")
    
    print()
    print("=" * 80)
    print()
    
    # 使用建议
    print("【使用建议】")
    print("-" * 80)
    print("评分标准：10 分制")
    print("  9.0-10.0: 上上大吉 - 最吉利的课格，百事皆宜")
    print("  8.0-8.9:  上吉 - 非常吉利，适合重要事项")
    print("  7.0-7.9:  中吉 - 吉利，适合一般事项")
    print("  6.0-6.9:  小吉 - 略有吉利，可使用")
    print("  5.0-5.9:  吉凶参半 - 需谨慎使用")
    print("  4.0-4.9:  小凶 - 不太吉利，不建议使用")
    print("  3.0-3.9:  中凶 - 凶险，避免使用")
    print("  2.0-2.9:  大凶 - 很凶险，严禁使用")
    print("  0.0-1.9:  上凶 - 极凶，绝对不可使用")
    print()
    print("⚠️ 重要提示：")
    print("  - 评分 5 分以下的课格在选择日期时不建议使用！")
    print("  - 评分 6 分以下的课格需特别谨慎，最好避免！")
    print("  - 选择日期时应优先考虑评分 7 分以上的课格！")
    print("=" * 80)

if __name__ == '__main__':
    display_score_table()
