#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
吉凶评价系统架构验证测试

验证架构设计的完整性和一致性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core_modules.engine.jixiong_evaluation_core import (
    JixiongEvaluationCore,
    JixiongLevel,
    JixiongDefinitionLayer,
    WeightConfigLayer,
    DuanyuMappingLayer,
    ScoringAlgorithmLayer
)
from core_modules.engine.jixiong_evaluation_adapter import (
    JixiongEvaluationAdapter,
    JixiongEvaluationService,
    WeightConfigManager,
    ScoreThresholdManager
)


def test_architecture_integrity():
    """测试架构完整性"""
    print("=" * 60)
    print("【测试1】架构完整性验证")
    print("=" * 60)
    
    # 验证各层是否正确初始化
    core = JixiongEvaluationCore()
    
    assert hasattr(core, 'definition_layer'), "缺少定义层"
    assert hasattr(core, 'weight_layer'), "缺少权重层"
    assert hasattr(core, 'duanyu_layer'), "缺少断语层"
    assert hasattr(core, 'scoring_layer'), "缺少评分层"
    
    print("✅ 核心架构各层完整")
    
    # 验证适配器
    adapter = JixiongEvaluationAdapter()
    assert hasattr(adapter, 'core'), "适配器缺少核心引用"
    assert hasattr(adapter, 'adapt_from_comprehensive_scorer'), "缺少综合评分适配方法"
    assert hasattr(adapter, 'adapt_from_api_request'), "缺少API请求适配方法"
    assert hasattr(adapter, 'to_api_response'), "缺少API响应转换方法"
    
    print("✅ 适配器架构完整")
    
    # 验证服务层
    service = JixiongEvaluationService()
    assert hasattr(service, 'adapter'), "服务层缺少适配器"
    assert hasattr(service, 'evaluate_date_course'), "缺少日课评价方法"
    
    print("✅ 服务层架构完整")


def test_data_consistency():
    """测试数据一致性"""
    print("\n" + "=" * 60)
    print("【测试2】数据一致性验证")
    print("=" * 60)
    
    # 验证吉凶等级定义一致性
    for level in JixiongLevel:
        attr = JixiongDefinitionLayer.JIXIONG_ATTRIBUTES[level]
        assert attr.level == level, f"等级不一致：{level}"
        assert len(attr.score_range) == 2, f"分数范围错误：{level}"
        assert attr.score_range[0] < attr.score_range[1], f"分数范围无效：{level}"
    
    print("✅ 吉凶等级定义一致")
    
    # 验证权重配置一致性
    weights = WeightConfigLayer.DEFAULT_WEIGHTS
    total_weight = sum(w.weight for w in weights.values())
    assert abs(total_weight - 1.0) < 0.001, f"权重总和不为1：{total_weight}"
    
    print("✅ 权重配置一致")
    
    # 验证预设配置一致性
    for preset_name, preset_weights in WeightConfigManager.PRESETS.items():
        assert WeightConfigManager.validate_custom_weights(preset_weights), f"预设配置无效：{preset_name}"
    
    print("✅ 预设配置一致")


def test_scoring_logic():
    """测试评分逻辑"""
    print("\n" + "=" * 60)
    print("【测试3】评分逻辑验证")
    print("=" * 60)
    
    core = JixiongEvaluationCore()
    
    # 测试大吉课体
    result = core.evaluate(keti_name='龙德课')
    assert result.score >= 90, f"龙德课评分应>=90，实际：{result.score}"
    assert result.level == JixiongLevel.DA_JI, f"龙德课应为大吉，实际：{result.level}"
    print(f"✅ 龙德课评分正确：{result.score}分，{result.level.value}")
    
    # 测试上吉课体
    result = core.evaluate(keti_name='荣华课')
    assert result.score >= 80, f"荣华课评分应>=80，实际：{result.score}"
    assert result.level == JixiongLevel.SHANG_JI, f"荣华课应为上吉，实际：{result.level}"
    print(f"✅ 荣华课评分正确：{result.score}分，{result.level.value}")
    
    # 测试凶课
    result = core.evaluate(keti_name='勾陈课')
    assert result.score < 40, f"勾陈课评分应<40，实际：{result.score}"
    assert result.level == JixiongLevel.DA_XIONG, f"勾陈课应为大凶，实际：{result.level}"
    print(f"✅ 勾陈课评分正确：{result.score}分，{result.level.value}")


def test_weight_adjustment():
    """测试权重调整"""
    print("\n" + "=" * 60)
    print("【测试4】权重调整验证")
    print("=" * 60)
    
    service = JixiongEvaluationService(preset='default')
    
    course_data = {
        'keti': '龙德课',
        'luma_info': {
            '禄神到山': {'日禄到山': True},
            '贵人到山': {'日贵到山': True}
        },
        'doushou_score': 85,
        'yanqin_score': 75
    }
    
    # 默认权重评分
    result1 = service.evaluate_date_course(course_data)
    print(f"默认权重评分：{result1['score']}")
    
    # 切换到强调课体权重
    service.set_weight_config(preset='emphasis_keti')
    result2 = service.evaluate_date_course(course_data)
    print(f"强调课体权重评分：{result2['score']}")
    
    # 由于龙德课是大吉课体，强调课体权重后评分应更高
    assert result2['score'] > result1['score'], "强调课体权重后评分应更高"
    
    print("✅ 权重调整逻辑正确")


def test_threshold_system():
    """测试阈值系统"""
    print("\n" + "=" * 60)
    print("【测试5】阈值系统验证")
    print("=" * 60)
    
    # 测试各阈值状态
    test_cases = [
        (95, 'excellent'),
        (80, 'good'),
        (65, 'pass'),
        (55, 'warning'),
        (45, 'danger'),
        (25, 'critical')
    ]
    
    for score, expected_status in test_cases:
        status = ScoreThresholdManager.get_threshold_status(score)
        assert status == expected_status, f"分数{score}状态应为{expected_status}，实际为{status}"
        description = ScoreThresholdManager.get_threshold_description(status)
        print(f"  {score}分 → {status}：{description}")
    
    print("✅ 阈值系统正确")


def test_api_compatibility():
    """测试API兼容性"""
    print("\n" + "=" * 60)
    print("【测试6】API兼容性验证")
    print("=" * 60)
    
    adapter = JixiongEvaluationAdapter()
    
    # 测试API请求适配
    api_request = {
        'keti': '龙德课',
        'luma_info': {
            '禄神到山': {'日禄到山': True}
        },
        'doushou_score': 80
    }
    
    result = adapter.adapt_from_api_request(api_request)
    assert result.score > 0, "API请求适配失败"
    print(f"✅ API请求适配成功：{result.score}分")
    
    # 测试API响应格式
    response = adapter.to_api_response(result)
    required_fields = ['success', 'score', 'level', 'description', 'duanyu', 'factors', 'recommendations']
    for field in required_fields:
        assert field in response, f"API响应缺少字段：{field}"
    
    print("✅ API响应格式正确")
    
    # 测试旧版兼容格式
    legacy = adapter.to_legacy_format(result)
    required_legacy_fields = ['综合评分', '综合吉凶', '断语', '建议']
    for field in required_legacy_fields:
        assert field in legacy, f"旧版格式缺少字段：{field}"
    
    print("✅ 旧版兼容格式正确")


def test_literature_source():
    """测试文献依据"""
    print("\n" + "=" * 60)
    print("【测试7】文献依据验证")
    print("=" * 60)
    
    core = JixiongEvaluationCore()
    result = core.evaluate(keti_name='龙德课')
    
    assert result.literature_source, "缺少文献依据"
    assert "仪度六壬选日要诀" in result.literature_source, "文献依据不正确"
    
    print(f"✅ 文献依据：{result.literature_source}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("吉凶评价系统架构验证测试")
    print("=" * 60)
    
    try:
        test_architecture_integrity()
        test_data_consistency()
        test_scoring_logic()
        test_weight_adjustment()
        test_threshold_system()
        test_api_compatibility()
        test_literature_source()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！架构设计验证成功！")
        print("=" * 60)
        
        return True
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
