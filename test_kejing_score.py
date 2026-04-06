#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试六壬评分逻辑"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from kejing_scoring import KeJingScoring

scorer = KeJingScoring()

print("=" * 70)
print("六壬课格评分系统分析")
print("=" * 70)

# 测试不同课格的评分
test_cases = [
    ('龙德', ['贵人', '禄神'], ['天德', '月德'], []),  # 上上吉课
    ('天德', ['贵人'], ['天德'], []),  # 上吉课
    ('伏吟', [], [], []),  # 吉凶参半
    ('伏吟', ['贵人'], [], []),  # 有贵人
    ('反吟', [], [], []),  # 吉凶参半
    ('丧门', [], [], []),  # 大凶课
]

print("\n【评分测试】")
for kejing, sanji, jishen, xiongsha in test_cases:
    score = scorer.calculate_score(kejing, sanji, jishen, xiongsha)
    level = scorer.get_score_level(score)
    usable = scorer.is_usable(score)
    print(f"  {kejing}: {score}分 ({level}) - 三吉={sanji}, 吉神={jishen}, 凶煞={xiongsha}")

print("\n" + "=" * 70)
print("【问题分析】")
print("=" * 70)

# 分析评分公式
print("\n评分公式分析（以伏吟课为例）：")
base_score = 5.5  # 伏吟课基础分
print(f"  基础分: {base_score}")
print(f"  基础分×0.30: {base_score * 0.30}")
print(f"  min(10, 5.5+0)×0.25: {min(10, base_score + 0) * 0.25}")
print(f"  min(10, 5.5+0)×0.20: {min(10, base_score + 0) * 0.20}")
print(f"  凶煞减分×0.15: {0 * 0.15}")
print(f"  旺衰×0.10: {5.0 * 0.10}")
total = base_score * 0.30 + min(10, base_score + 0) * 0.25 + min(10, base_score + 0) * 0.20 - 0 * 0.15 + 5.0 * 0.10
print(f"  总分: {total:.2f}")
print(f"  转换为100分制: {total * 10:.0f}")

print("\n" + "=" * 70)
print("【评分公式问题】")
print("=" * 70)
print("""
当前评分公式：
  total = base_score × 0.30 + min(10, base_score + sanji_bonus) × 0.25 
        + min(10, base_score + jishen_bonus) × 0.20 - xiongsha_penalty × 0.15 
        + 5.0 × 0.10

问题：
1. 公式过于复杂，导致基础分被稀释
2. 没有三吉、吉神时，分数会偏低
3. API中没有传入三吉、吉神、凶煞参数

建议修改为更简单的公式：
  total = base_score + sanji_bonus + jishen_bonus - xiongsha_penalty
""")

print("\n" + "=" * 70)
