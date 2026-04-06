#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日课分析系统 - 综合测试脚本

测试所有已完成的模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'engine')))

from date_range_generator import DateRangeGenerator
from douhou_analyzer import DouhouKegeAnalyzer
from yanqin_analyzer import YanQinAnalyzer
from daliuren_kege_analyzer import DaLiuRenKegeAnalyzer
from comprehensive_scorer import ComprehensiveScorer, WeightConfig
from riku_analysis_system import RikeAnalysisSystem


def test_all_modules():
    """测试所有模块"""
    print("=" * 80)
    print(" " * 25 + "日课分析系统综合测试")
    print("=" * 80)
    
    test_count = 0
    pass_count = 0
    
    # 测试 1: 日期范围生成模块
    print("\n【测试 1】日期范围生成模块")
    print("-" * 80)
    try:
        generator = DateRangeGenerator()
        test_date = datetime(2026, 3, 24)
        daily_data = generator.get_single_day_data(test_date)
        
        assert len(daily_data) == 12, "应该生成 12 个时辰数据"
        assert '四柱信息' in daily_data[0], "数据应包含四柱信息"
        assert '时辰信息' in daily_data[0], "数据应包含时辰信息"
        
        print(f"OK 成功生成 {len(daily_data)} 个时辰数据")
        print(f"OK 四柱信息完整：年柱={daily_data[0]['四柱信息']['年柱']}")
        print(f"OK 时辰信息完整：{daily_data[6]['时辰信息']['时辰地支']}时")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 2: 斗首课格分析模块
    print("\n【测试 2】斗首课格分析模块")
    print("-" * 80)
    try:
        analyzer = DouhouKegeAnalyzer()
        sizhu = {
            '年柱': '丙午',
            '月柱': '辛丑',
            '日柱': '壬子',
            '时柱': '庚子'
        }
        result = analyzer.analyze_kege('壬', sizhu)
        
        assert '综合评分' in result, "应包含综合评分"
        assert 0 <= result['综合评分'] <= 100, "评分应在 0-100 之间"
        assert '课格格局' in result, "应包含课格格局"
        assert '山家五行' in result, "应包含山家五行"
        
        print(f"OK 坐山五行：{result['山家五行']}")
        print(f"OK 综合评分：{result['综合评分']}分")
        print(f"OK 格局数量：{len(result['课格格局'])}")
        if result['课格格局']:
            print(f"OK 主要格局：{result['课格格局'][0]['格局名称']}")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 3: 演禽真法分析模块
    print("\n【测试 3】演禽真法分析模块")
    print("-" * 80)
    try:
        analyzer = YanQinAnalyzer()
        sizhu = {
            '年柱': '丙午',
            '月柱': '辛丑',
            '日柱': '壬子',
            '时柱': '庚子'
        }
        result = analyzer.analyze_yanqin(sizhu)
        
        assert '四禽' in result, "应包含四禽"
        assert '综合评分' in result, "应包含综合评分"
        assert 0 <= result['综合评分'] <= 100, "评分应在 0-100 之间"
        assert '格局判定' in result, "应包含格局判定"
        
        print(f"OK 四禽：年={result['四禽']['年禽']}, 月={result['四禽']['月禽']}, "
              f"日={result['四禽']['日禽']}, 时={result['四禽']['时禽']}")
        print(f"OK 综合评分：{result['综合评分']}分")
        print(f"OK 格局数量：{len(result['格局判定'])}")
        if result['格局判定']:
            print(f"OK 主要格局：{result['格局判定'][0]['格局名称']}")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 4: 综合评分模块
    print("\n【测试 4】综合评分模块")
    print("-" * 80)
    try:
        scorer = ComprehensiveScorer()
        
        # 测试标准权重
        weights = scorer.get_weights()
        assert abs(weights['斗首'] - 0.4) < 0.01, "斗首权重应为 0.4"
        assert abs(weights['演禽'] - 0.3) < 0.01, "演禽权重应为 0.3"
        assert abs(weights['大六壬'] - 0.3) < 0.01, "大六壬权重应为 0.3"
        
        # 测试综合评分计算
        result = scorer.calculate_comprehensive_score(85, 75, 80)
        
        assert '综合评分' in result, "应包含综合评分"
        expected_score = 85 * 0.4 + 75 * 0.3 + 80 * 0.3
        assert abs(result['综合评分'] - expected_score) < 0.1, "综合评分计算应正确"
        
        print(f"OK 权重配置：斗首={weights['斗首']}, 演禽={weights['演禽']}, "
              f"大六壬={weights['大六壬']}")
        print(f"OK 输入评分：斗首=85, 演禽=75, 大六壬=80")
        print(f"OK 综合评分：{result['综合评分']}分")
        print(f"OK 综合吉凶：{result['综合吉凶']['level_name']}")
        
        # 测试自定义权重
        scorer.set_weights(0.5, 0.25, 0.25)
        result2 = scorer.calculate_comprehensive_score(85, 75, 80)
        print(f"OK 自定义权重后综合评分：{result2['综合评分']}分")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 5: 完整系统集成
    print("\n【测试 5】完整系统集成测试")
    print("-" * 80)
    try:
        system = RikeAnalysisSystem()
        test_date = datetime(2026, 3, 24)
        
        # 分析单个日课
        result = system.analyze_single_ke(test_date, 7, '壬')
        
        assert '基础信息' in result, "应包含基础信息"
        assert '斗首课格分析' in result, "应包含斗首分析"
        assert '演禽真法分析' in result, "应包含演禽分析"
        assert '综合评分' in result, "应包含综合评分"
        assert 'GLM 评价报告' in result, "应包含评价报告"
        
        print(f"OK 四柱：{result['基础信息']['四柱']}")
        print(f"OK 坐山：{result['基础信息']['坐山']}")
        print(f"OK 时辰：{result['基础信息']['时辰']['时辰地支']}时")
        print(f"OK 斗首评分：{result['斗首课格分析']['综合评分']}分")
        print(f"OK 演禽评分：{result['演禽真法分析']['综合评分']}分")
        print(f"OK 综合评分：{result['综合评分']['综合评分']}分")
        print(f"OK 综合吉凶：{result['综合评分']['综合吉凶']['level_name']}")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 6: 单日分析
    print("\n【测试 6】单日 12 时辰分析测试")
    print("-" * 80)
    try:
        system = RikeAnalysisSystem()
        test_date = datetime(2026, 3, 24)
        
        # 分析全天，筛选 60 分以上
        results = system.analyze_daily_ke(test_date, '壬', min_score=60)
        
        print(f"OK 找到 {len(results)} 个 60 分以上的日课")
        
        if results:
            print(f"OK 最佳时辰：{results[0]['基础信息']['时辰']['时辰地支']}时，"
                  f"{results[0]['综合评分']['综合评分']}分")
            print(f"OK 最差时辰：{results[-1]['基础信息']['时辰']['时辰地支']}时，"
                  f"{results[-1]['综合评分']['综合评分']}分")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 测试 7: 小范围日期分析
    print("\n【测试 7】小范围日期分析测试 (3 天)")
    print("-" * 80)
    try:
        system = RikeAnalysisSystem()
        start = datetime(2026, 3, 24)
        end = datetime(2026, 3, 26)
        
        # 分析 3 天，筛选 70 分以上
        results = system.analyze_date_range(start, end, '壬', min_score=70)
        
        print(f"OK 分析 3 天，找到 {len(results)} 个 70 分以上的日课")
        
        if results:
            print(f"OK 最佳日课：{results[0]['基础信息']['公历日期']['日期字符串']} "
                  f"{results[0]['基础信息']['时辰']['时辰地支']}时，"
                  f"{results[0]['综合评分']['综合评分']}分")
        
        test_count += 1
        pass_count += 1
        print("OK 测试通过")
    except Exception as e:
        print(f"X 测试失败：{e}")
        test_count += 1
    
    # 总结
    print("\n" + "=" * 80)
    print(f"测试总结：通过 {pass_count}/{test_count} 项测试")
    success_rate = (pass_count / test_count * 100) if test_count > 0 else 0
    print(f"测试覆盖率：{success_rate:.1f}%")
    
    if pass_count == test_count:
        print("\nOKOKOK 所有测试通过！系统运行正常 OKOKOK")
    else:
        print(f"\n⚠ {test_count - pass_count} 项测试失败，请检查")
    
    print("=" * 80)
    
    # 示例报告
    print("\n【示例报告】")
    print("-" * 80)
    system = RikeAnalysisSystem()
    result = system.analyze_single_ke(datetime(2026, 3, 24), 7, '壬')
    print(result['GLM 评价报告'])


if __name__ == '__main__':
    test_all_modules()
