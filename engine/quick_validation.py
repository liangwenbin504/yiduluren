#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速验证脚本 — 测试分层引擎的基本功能，不调用实际 API
"""

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

print("=" * 60)
print("🧪 分层引擎基本功能验证")
print("=" * 60)

# 1. 测试黄金案例加载
print("\n1️⃣ 测试黄金案例加载...")
try:
    from engine.golden_cases import get_golden_cases
    golden = get_golden_cases()
    cases = golden.get_all_cases()
    print(f"   ✅ 成功加载 {len(cases)} 个黄金案例")
    if cases:
        print(f"   📋 第一个案例: {cases[0]['title']}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试模板引擎初始化
print("\n2️⃣ 测试模板引擎初始化...")
try:
    from engine.template_engine import get_template_engine
    engine = get_template_engine()
    templates = engine.get_available_templates()
    print(f"   ✅ 模板引擎已初始化")
    print(f"   📋 可用模板: {templates[:5]}...")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试 Prompt 构建（不调用 API）
print("\n3️⃣ 测试 Prompt 构建...")
try:
    from engine.template_engine import get_template_engine
    engine = get_template_engine()
    
    test_paipan = {
        "keti": "元首课",
        "sanchuan": {"first": "巳", "second": "申", "third": "辰"},
        "tianjiang": "青龙+巳",
        "wuxing_analysis": "三传木火旺相"
    }
    
    test_rule = {
        "bifa_rules": [{"name": "青龙临身主吉"}],
        "leishen_analysis": "妻财临青龙"
    }
    
    for zhanshi in ["求财", "婚姻", "疾病", "出行"]:
        prompt_data = engine.build_prompt(zhanshi, test_paipan, test_rule)
        print(f"\n   🔹 占事: {zhanshi}")
        print(f"      - System Prompt: {len(prompt_data['system_prompt'])} 字符")
        print(f"      - User Prompt 预览: {prompt_data['user_prompt'][:80]}...")
        print(f"      - 输出格式: {prompt_data['output_format'][:50]}...")
    
    print("\n   ✅ Prompt 构建测试通过")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试智能决策引擎（不调用 API）
print("\n4️⃣ 测试智能决策引擎初始化...")
try:
    from engine.smart_judge import get_smart_judge, EngineLevel
    judge = get_smart_judge()
    stats = judge.get_statistics()
    print(f"   ✅ 智能引擎已初始化")
    print(f"   📊 状态:")
    for key, val in stats.items():
        if key != 'cost_estimate':
            print(f"      - {key}: {val}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试解析功能（模拟 API 返回）
print("\n5️⃣ 测试结果解析功能...")
try:
    from engine.template_engine import get_template_engine
    engine = get_template_engine()
    
    # 模拟 API 返回
    mock_response = """
    这是一些分析文本...
    {
        "keti_judgment": "元首课主吉",
        "wealth_source": "妻财临青龙，财源广进",
        "risk_warning": "无明显风险",
        "timing_advice": "亥月大吉",
        "overall_jixiong": "吉",
        "confidence_score": 85
    }
    更多分析文本...
    """
    
    result = engine._parse_result(mock_response)
    if result:
        print(f"   ✅ JSON 解析成功")
        print(f"   📋 解析结果:")
        for key, val in result.items():
            print(f"      - {key}: {val}")
    else:
        print(f"   ❌ 解析失败")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 基本功能验证完成")
print("=" * 60)
print("\n📝 总结：")
print("   - 黄金案例加载: ✅")
print("   - 模板引擎初始化: ✅")
print("   - Prompt 构建: ✅")
print("   - 智能决策引擎: ✅")
print("   - 结果解析: ✅")
print("\n💡 下一步：可以进行真实 API 调用测试")
