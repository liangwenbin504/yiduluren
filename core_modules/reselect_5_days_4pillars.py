#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六相六替完整系统重新择日（四柱全面分析版）
重点：六相六替应用到年柱、月柱、日柱、时柱每一柱
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from datetime import datetime
from liuxiang_liuti_complete_system import LiuXiangLiuTiSystem
from douhou_analyzer import DouhouKegeAnalyzer

print('=' * 80)
print('六相六替完整系统重新择日')
print('重点：六相六替应用到四柱（年、月、日、时）每一柱')
print('坐山：壬山')
print('=' * 80)

# 创建系统
liuxiang_system = LiuXiangLiuTiSystem()
douhou_analyzer = DouhouKegeAnalyzer()

# 使用之前的 5 个最佳日课，现在用六相六替全面分析四柱
test_cases = [
    {
        '公历': '2026 年 3 月 31 日',
        '时辰': '未时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '甲辰',
            '时柱': '辛未'
        }
    },
    {
        '公历': '2026 年 4 月 22 日',
        '时辰': '申时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '丙寅',
            '时柱': '丙申'
        }
    },
    {
        '公历': '2026 年 3 月 30 日',
        '时辰': '未时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '癸卯',
            '时柱': '己未'
        }
    },
    {
        '公历': '2026 年 3 月 26 日',
        '时辰': '巳时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '辛卯',
            '日柱': '己亥',
            '时柱': '己巳'
        }
    },
    {
        '公历': '2026 年 4 月 7 日',
        '时辰': '申时',
        'sizhu': {
            '年柱': '丙午',
            '月柱': '壬辰',
            '日柱': '辛亥',
            '时柱': '丙申'
        }
    }
]

print('\n重新分析 5 个最佳日课（六相六替全面应用到四柱）\n')
print('=' * 80)

results = []

for i, case in enumerate(test_cases, 1):
    print(f'\n{"="*80}')
    print(f'【第 {i} 吉课】')
    print(f'公历：{case["公历"]} {case["时辰"]}')
    print(f'四柱：{case["sizhu"]["年柱"]} {case["sizhu"]["月柱"]} {case["sizhu"]["日柱"]} {case["sizhu"]["时柱"]}')
    print('='*80)
    
    sizhu = case['sizhu']
    
    # 1. 逐柱分析六相六替（重点！）
    print('\n【四柱六相六替详细分析】')
    print('-' * 80)
    
    pillar_scores = {}
    pillar_states = {}
    liuxiang_count = 0
    liuti_count = 0
    
    for pillar_name, ganzhi in sizhu.items():
        tiangan = ganzhi[0]
        dizhi = ganzhi[1]
        
        # 查询该柱的六相六替状态
        state = liuxiang_system.query_table.get_state_by_zhi(tiangan, dizhi)
        is_liuxiang = liuxiang_system.query_table.is_liuxiang_zhi(tiangan, dizhi)
        state_info = liuxiang_system.states.get_state_info(state)
        
        pillar_scores[pillar_name] = state_info.score if state_info else 50
        pillar_states[pillar_name] = {
            '干支': ganzhi,
            '状态': state,
            '六相/六替': '六相' if is_liuxiang else '六替',
            '吉凶': '吉' if is_liuxiang else '凶',
            '分数': state_info.score if state_info else 50,
            '含义': state_info.meaning if state_info else '未知'
        }
        
        if is_liuxiang:
            liuxiang_count += 1
        else:
            liuti_count += 1
        
        # 输出该柱分析
        print(f'\n{pillar_name}：{ganzhi}')
        print(f'  状态：{state} ({ "六相【吉】" if is_liuxiang else "六替【凶】"})')
        print(f'  分数：{state_info.score if state_info else 50}分')
        print(f'  含义：{state_info.meaning if state_info else "未知"}')
    
    # 2. 四柱综合统计
    print(f'\n\n【四柱六相六替综合统计】')
    print('-' * 80)
    print(f'六相数：{liuxiang_count}个（吉）')
    print(f'六替数：{liuti_count}个（凶）')
    
    # 计算四柱平均分
    avg_score = sum(pillar_scores.values()) / len(pillar_scores)
    print(f'四柱平均分：{avg_score:.1f}分')
    
    # 判断吉凶格局
    if liuxiang_count == 4:
        jige = '上上大吉（四柱皆六相）'
    elif liuxiang_count == 3:
        jige = '大吉（三吉一凶）'
    elif liuxiang_count == 2:
        jige = '中吉（二吉二凶）'
    elif liuxiang_count == 1:
        jige = '小吉（一吉三凶）'
    else:
        jige = '凶（四柱皆六替）'
    
    print(f'吉凶格局：{jige}')
    
    # 3. 核心诀法验证
    print(f'\n【核心诀法验证】')
    print('-' * 80)
    
    juefa_checks = []
    
    # 验证 1：三吉喜居六相支
    if liuxiang_count >= 3:
        print('✅ 符合"三吉喜居六相支"')
        juefa_checks.append(True)
    else:
        print('❌ 不符合"三吉喜居六相支"')
        juefa_checks.append(False)
    
    # 验证 2：二凶喜居六替支
    if liuti_count >= 2:
        print('✅ 符合"二凶喜居六替支"')
        juefa_checks.append(True)
    else:
        print('⚠️ 二凶未居六替支')
        juefa_checks.append(False)
    
    # 验证 3：年柱是否六相
    if pillar_states['年柱']['六相/六替'] == '六相':
        print('✅ 年柱居六相（吉）')
        juefa_checks.append(True)
    else:
        print('❌ 年柱居六替（凶）')
        juefa_checks.append(False)
    
    # 验证 4：月柱是否六相
    if pillar_states['月柱']['六相/六替'] == '六相':
        print('✅ 月柱居六相（吉）')
        juefa_checks.append(True)
    else:
        print('❌ 月柱居六替（凶）')
        juefa_checks.append(False)
    
    # 验证 5：日柱是否六相
    if pillar_states['日柱']['六相/六替'] == '六相':
        print('✅ 日柱居六相（吉）')
        juefa_checks.append(True)
    else:
        print('❌ 日柱居六替（凶）')
        juefa_checks.append(False)
    
    # 验证 6：时柱是否六相
    if pillar_states['时柱']['六相/六替'] == '六相':
        print('✅ 时柱居六相（吉）')
        juefa_checks.append(True)
    else:
        print('❌ 时柱居六替（凶）')
        juefa_checks.append(False)
    
    # 4. 斗首分析
    print(f'\n【斗首课格分析】')
    print('-' * 80)
    douhou_result = douhou_analyzer.analyze_kege('壬', sizhu)
    print(f'综合评分：{douhou_result["综合评分"]}分')
    
    if douhou_result.get('课格格局'):
        print(f'课格格局：')
        for pattern in douhou_result['课格格局'][:3]:
            print(f'  - {pattern.get("格局名称", "未知")} ({pattern.get("吉凶", "未知")})')
    
    # 5. 综合评分（四柱六相六替占 60%，斗首占 40%）
    liuxiang_score = avg_score
    douhou_score = douhou_result['综合评分']
    
    # 六相六替格局加分
    if liuxiang_count == 4:
        bonus = 20
    elif liuxiang_count == 3:
        bonus = 15
    elif liuxiang_count == 2:
        bonus = 10
    elif liuxiang_count == 1:
        bonus = 5
    else:
        bonus = 0
    
    total_score = (liuxiang_score * 0.6 + douhou_score * 0.4) + bonus
    total_score = min(100, total_score)  # 不超过 100 分
    
    print(f'\n【综合评分】{total_score:.1f}分')
    print(f'  六相六替分：{liuxiang_score:.1f} × 60% = {liuxiang_score * 0.6:.1f}')
    print(f'  斗首分：{douhou_score} × 40% = {douhou_score * 0.4:.1f}')
    print(f'  格局加分：+{bonus}分')
    
    # 6. 吉凶判断
    print(f'\n【吉凶判断】')
    print('-' * 80)
    
    if total_score >= 90:
        level = '上上大吉'
        recommendation = '强烈推荐'
    elif total_score >= 80:
        level = '上吉'
        recommendation = '推荐'
    elif total_score >= 70:
        level = '中吉'
        recommendation = '可用'
    elif total_score >= 60:
        level = '小吉'
        recommendation = '谨慎使用'
    else:
        level = '凶'
        recommendation = '不推荐'
    
    print(f'等级：{level}')
    print(f'推荐度：{recommendation}')
    
    # 7. 补救建议
    if liuti_count > liuxiang_count or total_score < 70:
        print(f'\n【补救建议】')
        print('-' * 80)
        best_remedy = liuxiang_system.remedy.get_best_remedy()
        print(f'推荐方法：{best_remedy.method}')
        print(f'{best_remedy.description}')
        print(f'\n示例：{best_remedy.example}')
    
    # 保存结果
    results.append({
        '公历': case['公历'],
        '时辰': case['时辰'],
        '四柱': sizhu,
        '六相数': liuxiang_count,
        '六替数': liuti_count,
        '四柱平均分': avg_score,
        '斗首分数': douhou_result['综合评分'],
        '格局加分': bonus,
        '综合评分': total_score,
        '吉凶等级': level,
        '推荐度': recommendation,
        'pillar_states': pillar_states,
        'juefa_checks': sum(juefa_checks)
    })

# 8. 综合对比
print('\n' + '='*80)
print('5 个吉日综合对比（四柱六相六替全面分析）')
print('='*80)

print(f'\n{"排名":<4} {"公历":<12} {"时辰":<6} {"六相":<4} {"六替":<4} {"四柱均":<6} {"斗首":<4} {"加分":<4} {"综合":<6} {"等级":<8} {"推荐":<8}')
print('-'*100)

results.sort(key=lambda x: x['综合评分'], reverse=True)

for i, r in enumerate(results, 1):
    print(f'{i:<4} {r["公历"]:<12} {r["时辰"]:<6} {r["六相数"]:<4} {r["六替数"]:<4} '
          f'{r["四柱平均分"]:<6.1f} {r["斗首分数"]:<4} {r["格局加分"]:<4} '
          f'{r["综合评分"]:<6.1f} {r["吉凶等级"]:<8} {r["推荐度"]:<8}')

print('\n' + '='*80)
print('最终推荐（前 3 名）')
print('='*80)

for i, r in enumerate(results[:3], 1):
    print(f'\n【第{i}名】{r["公历"]} {r["时辰"]}')
    print(f'  四柱：{r["四柱"]["年柱"]} {r["四柱"]["月柱"]} {r["四柱"]["日柱"]} {r["四柱"]["时柱"]}')
    print(f'  六相六替：{r["六相数"]}吉 {r["六替数"]}凶')
    print(f'  综合评分：{r["综合评分"]:.1f}分（{r["吉凶等级"]}）')
    print(f'  推荐度：{r["推荐度"]}')
    
    # 显示四柱状态
    print(f'  四柱状态：')
    for pillar_name, state_info in r['pillar_states'].items():
        print(f'    {pillar_name}: {state_info["干支"]} - {state_info["状态"]} ({state_info["六相/六替"]})')
    
    # 显示诀法验证
    print(f'  诀法验证：{r["juefa_checks"]}/6 符合')

print('\n' + '='*80)
print('分析完成')
print('='*80)
