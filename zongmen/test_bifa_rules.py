#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋规则测试脚本
验证改进后的规则是否能够正确匹配课例
"""

from bifa_rules_engine_v5 import BiFaRulesMatcherV5

# 测试课例
test_cases = [
    {
        "ri_gan_zhi": "甲子",
        "yue": "子",
        "shi": "子",
        "yue_jiang": "丑",
        "chu_chuan": "辰",
        "zhong_chuan": "巳",
        "mo_chuan": "午",
        "gan_shang": "卯",
        "zhi_shang": "辰",
        "ke_ti_ge_ju": ["重审课"]
    },
    {
        "ri_gan_zhi": "甲子",
        "yue": "子",
        "shi": "丑",
        "yue_jiang": "丑",
        "chu_chuan": "寅",
        "zhong_chuan": "巳",
        "mo_chuan": "申",
        "gan_shang": "寅",
        "zhi_shang": "寅",
        "ke_ti_ge_ju": ["伏吟课"]
    }
]

def test_bifa_rules():
    """测试毕法赋规则"""
    matcher = BiFaRulesMatcherV5()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test_case['ri_gan_zhi']}_{test_case['yue']}_{test_case['shi']}")
        print("=" * 60)
        
        # 测试规则13：无亲卦主事无依
        result_13 = matcher.match_rule_013(test_case)
        print(f"规则13：{result_13['rule_name']} - {'匹配' if result_13['matched'] else '不匹配'}")
        if result_13['matched']:
            print(f"  推理：{result_13['reasoning']}")
        
        # 测试规则38：人宅皆死各尫羸
        result_38 = matcher.match_rule_038(test_case)
        print(f"规则38：{result_38['rule_name']} - {'匹配' if result_38['matched'] else '不匹配'}")
        if result_38['matched']:
            print(f"  推理：{result_38['reasoning']}")
        
        # 测试规则66：干支值绝事无成
        result_66 = matcher.match_rule_066(test_case)
        print(f"规则66：{result_66['rule_name']} - {'匹配' if result_66['matched'] else '不匹配'}")
        if result_66['matched']:
            print(f"  推理：{result_66['reasoning']}")
        
        # 测试规则23：彼求我事支传干
        result_23 = matcher.match_rule_023(test_case)
        print(f"规则23：{result_23['rule_name']} - {'匹配' if result_23['matched'] else '不匹配'}")
        if result_23['matched']:
            print(f"  推理：{result_23['reasoning']}")
        
        # 测试规则24：我求彼事干传支
        result_24 = matcher.match_rule_024(test_case)
        print(f"规则24：{result_24['rule_name']} - {'匹配' if result_24['matched'] else '不匹配'}")
        if result_24['matched']:
            print(f"  推理：{result_24['reasoning']}")
        
        print("=" * 60)

if __name__ == "__main__":
    print("开始测试毕法赋规则...")
    test_bifa_rules()
    print("\n测试完成！")
