#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬课体分析模块专项测试
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'engine')))

from daliuren_kege_analyzer import DaLiuRenKegeAnalyzer


def test_basic_analysis():
    """测试基础分析功能"""
    print("=" * 80)
    print(" " * 25 + "大六壬课体分析模块专项测试")
    print("=" * 80)
    
    analyzer = DaLiuRenKegeAnalyzer()
    
    # 测试 1：元首课
    print("\n【测试 1】元首课测试")
    print("-" * 80)
    result = analyzer.analyze_kege(
        date=datetime(2026, 3, 24),
        shichen_index=7,
        ri_gan='丁',
        ri_zhi='酉'
    )
    
    print(f"课体类型：{result['课体结构分析']['课体类型']}")
    print(f"起法：{result['课体结构分析']['起法']}")
    print(f"三传：{result['三传']['初传']}, {result['三传']['中传']}, {result['三传']['末传']}")
    print(f"综合评分：{result['综合评分']}分")
    print(f"吉凶：{analyzer.get_score_description(result['综合评分'])}")
    
    assert result['课体结构分析']['课体类型'] == '元首课', "应为元首课"
    assert 0 <= result['综合评分'] <= 100, "评分应在 0-100 之间"
    print("✓ 测试通过")
    
    # 测试 2：不同日干
    print("\n【测试 2】不同日干测试")
    print("-" * 80)
    
    test_cases = [
        ('甲', '子'),
        ('乙', '丑'),
        ('丙', '寅'),
        ('丁', '卯'),
        ('戊', '辰')
    ]
    
    for ri_gan, ri_zhi in test_cases:
        result = analyzer.analyze_kege(
            date=datetime(2026, 3, 24),
            shichen_index=1,
            ri_gan=ri_gan,
            ri_zhi=ri_zhi
        )
        
        print(f"{ri_gan}{ri_zhi}日：课体={result['课体结构分析']['课体类型']}, "
              f"评分={result['综合评分']}分")
        
        assert '课体类型' in result['课体结构分析']
        assert 0 <= result['综合评分'] <= 100
    
    print("✓ 测试通过")
    
    # 测试 3：不同时辰
    print("\n【测试 3】不同时辰测试")
    print("-" * 80)
    
    for shichen_idx in range(1, 13):
        result = analyzer.analyze_kege(
            date=datetime(2026, 3, 24),
            shichen_index=shichen_idx,
            ri_gan='丁',
            ri_zhi='酉'
        )
        
        shichen = analyzer.get_shichen_dizhi(shichen_idx)
        print(f"{shichen}时：课体={result['课体结构分析']['课体类型']}, "
              f"评分={result['综合评分']}分")
    
    print("✓ 测试通过")
    
    # 测试 4：六亲关系分析
    print("\n【测试 4】六亲关系分析测试")
    print("-" * 80)
    
    result = analyzer.analyze_kege(
        date=datetime(2026, 3, 24),
        shichen_index=7,
        ri_gan='丁',
        ri_zhi='酉'
    )
    
    liuqin = result['六亲关系']
    print(f"日干五行：{liuqin['日干五行']}")
    print(f"三传六亲:")
    for qin_info in liuqin['三传六亲']:
        print(f"  {qin_info['传名']}: {qin_info['地支']} ({qin_info['五行']}) - {qin_info['六亲']}")
    
    assert '日干五行' in liuqin
    assert len(liuqin['三传六亲']) == 3
    print("✓ 测试通过")
    
    # 测试 5：课体结构分析
    print("\n【测试 5】课体结构分析测试")
    print("-" * 80)
    
    kege = result['课体结构分析']
    print(f"课体类型：{kege['课体类型']}")
    print(f"起法：{kege['起法']}")
    print(f"三传关系：{kege['三传关系']}")
    print(f"四课结构:")
    for ke in kege['四课结构']:
        print(f"  {ke['课名']}: {ke['上神']} {ke['下神']} ({ke['克应']})")
    
    assert '课体类型' in kege
    assert '四课结构' in kege
    assert len(kege['四课结构']) == 4
    print("✓ 测试通过")
    
    # 测试 6：吉凶断语生成
    print("\n【测试 6】吉凶断语生成测试")
    print("-" * 80)
    
    duanyu = result['吉凶断语']
    print("生成的断语:")
    for duan in duanyu:
        print(f"  - {duan}")
    
    assert len(duanyu) > 0
    print("✓ 测试通过")
    
    # 测试 7：日志记录
    print("\n【测试 7】日志记录测试")
    print("-" * 80)
    
    logs = result['日志']
    print(f"日志条数：{len(logs)}")
    print("部分日志:")
    for log in logs[:5]:
        print(f"  - {log}")
    
    assert len(logs) > 0
    print("✓ 测试通过")
    
    print("\n" + "=" * 80)
    print("测试总结：所有测试通过！")
    print("=" * 80)


def test_score_range():
    """测试评分范围"""
    print("\n【附加测试】评分范围测试")
    print("-" * 80)
    
    analyzer = DaLiuRenKegeAnalyzer()
    
    scores = []
    
    # 测试多个案例
    for day in range(1, 11):
        for shichen in range(1, 13):
            result = analyzer.analyze_kege(
                date=datetime(2026, 3, day),
                shichen_index=shichen,
                ri_gan='甲',
                ri_zhi='子'
            )
            scores.append(result['综合评分'])
    
    print(f"测试案例数：{len(scores)}")
    print(f"最高分：{max(scores)}")
    print(f"最低分：{min(scores)}")
    print(f"平均分：{sum(scores) / len(scores):.1f}")
    
    # 验证所有分数在 0-100 之间
    assert all(0 <= s <= 100 for s in scores), "所有评分应在 0-100 之间"
    print("✓ 评分范围测试通过")


if __name__ == '__main__':
    test_basic_analysis()
    test_score_range()
    
    print("\n" + "=" * 80)
    print("✓✓✓ 大六壬课体分析模块所有测试通过！✓✓✓")
    print("=" * 80)
