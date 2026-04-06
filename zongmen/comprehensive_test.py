#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋规则综合测试脚本
测试所有改进的规则，确保它们能够正确匹配各种情况
"""

from bifa_rules_engine_v5 import BiFaRulesMatcherV5

# 测试课例
test_cases = [
    # 测试规则13：无亲卦主事无依
    {
        "name": "无亲卦测试",
        "data": {
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
        "expected": {
            "rule_13": True
        }
    },
    # 测试规则38：人宅皆死各尫羸
    {
        "name": "人宅皆死测试",
        "data": {
            "ri_gan_zhi": "庚戌",
            "yue": "子",
            "shi": "子",
            "yue_jiang": "丑",
            "chu_chuan": "辰",
            "zhong_chuan": "巳",
            "mo_chuan": "午",
            "gan_shang": "丑",  # 庚的墓地
            "zhi_shang": "寅",  # 庚的绝地
            "ke_ti_ge_ju": ["重审课"]
        },
        "expected": {
            "rule_38": True
        }
    },
    # 测试规则66：干支值绝事无成
    {
        "name": "干支值绝测试",
        "data": {
            "ri_gan_zhi": "甲子",
            "yue": "子",
            "shi": "子",
            "yue_jiang": "丑",
            "chu_chuan": "辰",
            "zhong_chuan": "巳",
            "mo_chuan": "午",
            "gan_shang": "申",  # 甲的绝地
            "zhi_shang": "卯",
            "ke_ti_ge_ju": ["重审课"]
        },
        "expected": {
            "rule_66": True
        }
    },
    # 测试规则23：彼求我事支传干
    {
        "name": "彼求我事测试",
        "data": {
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
        },
        "expected": {
            "rule_23": True,
            "rule_24": False
        }
    },
    # 测试规则24：我求彼事干传支
    {
        "name": "我求彼事测试",
        "data": {
            "ri_gan_zhi": "甲子",
            "yue": "子",
            "shi": "子",
            "yue_jiang": "丑",
            "chu_chuan": "辰",
            "zhong_chuan": "巳",
            "mo_chuan": "午",
            "gan_shang": "卯",
            "zhi_shang": "寅",  # 甲的寄宫
            "ke_ti_ge_ju": ["重审课"]
        },
        "expected": {
            "rule_23": False,
            "rule_24": True
        }
    }
]

def test_bifa_rules():
    """测试毕法赋规则"""
    matcher = BiFaRulesMatcherV5()
    
    for test_case in test_cases:
        print(f"\n测试：{test_case['name']}")
        print("=" * 60)
        data = test_case['data']
        expected = test_case['expected']
        
        # 测试规则13：无亲卦主事无依
        if 'rule_13' in expected:
            result_13 = matcher.match_rule_013(data)
            status = "✓" if result_13['matched'] == expected['rule_13'] else "✗"
            print(f"{status} 规则13：{result_13['rule_name']} - {'匹配' if result_13['matched'] else '不匹配'} (期望: {'匹配' if expected['rule_13'] else '不匹配'})")
            if result_13['matched']:
                print(f"  推理：{result_13['reasoning']}")
        
        # 测试规则38：人宅皆死各尫羸
        if 'rule_38' in expected:
            result_38 = matcher.match_rule_038(data)
            status = "✓" if result_38['matched'] == expected['rule_38'] else "✗"
            print(f"{status} 规则38：{result_38['rule_name']} - {'匹配' if result_38['matched'] else '不匹配'} (期望: {'匹配' if expected['rule_38'] else '不匹配'})")
            if result_38['matched']:
                print(f"  推理：{result_38['reasoning']}")
        
        # 测试规则66：干支值绝事无成
        if 'rule_66' in expected:
            result_66 = matcher.match_rule_066(data)
            status = "✓" if result_66['matched'] == expected['rule_66'] else "✗"
            print(f"{status} 规则66：{result_66['rule_name']} - {'匹配' if result_66['matched'] else '不匹配'} (期望: {'匹配' if expected['rule_66'] else '不匹配'})")
            if result_66['matched']:
                print(f"  推理：{result_66['reasoning']}")
        
        # 测试规则23：彼求我事支传干
        if 'rule_23' in expected:
            result_23 = matcher.match_rule_023(data)
            status = "✓" if result_23['matched'] == expected['rule_23'] else "✗"
            print(f"{status} 规则23：{result_23['rule_name']} - {'匹配' if result_23['matched'] else '不匹配'} (期望: {'匹配' if expected['rule_23'] else '不匹配'})")
            if result_23['matched']:
                print(f"  推理：{result_23['reasoning']}")
        
        # 测试规则24：我求彼事干传支
        if 'rule_24' in expected:
            result_24 = matcher.match_rule_024(data)
            status = "✓" if result_24['matched'] == expected['rule_24'] else "✗"
            print(f"{status} 规则24：{result_24['rule_name']} - {'匹配' if result_24['matched'] else '不匹配'} (期望: {'匹配' if expected['rule_24'] else '不匹配'})")
            if result_24['matched']:
                print(f"  推理：{result_24['reasoning']}")
        
        print("=" * 60)

if __name__ == "__main__":
    print("开始综合测试毕法赋规则...")
    test_bifa_rules()
    print("\n测试完成！")
