#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整起课引擎测试脚本
测试所有模块功能并验证 64 课经匹配
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

from complete_qi_ke_engine import CompleteQiKeEngine
from accurate_ke_jing_matcher import AccurateKeJingMatcher


def test_basic_qi_ke():
    """测试基本起课功能"""
    print("=" * 80)
    print("测试 1: 基本起课功能")
    print("=" * 80)
    
    engine = CompleteQiKeEngine()
    
    # 测试案例
    test_cases = [
        ('甲子', '亥', '午', '普通课'),
        ('戊辰', '子', '子', '伏吟课'),
        ('丙寅', '戌', '辰', '反吟课'),
        ('庚午', '未', '丑', '反吟课'),
        ('壬申', '午', '子', '反吟课'),
    ]
    
    for ri_gan_zhi, yue_jiang, shi_chen, expected in test_cases:
        print(f"\n测试：{ri_gan_zhi}日{yue_jiang}将{shi_chen}时 (期望：{expected})")
        result = engine.qi_ke(ri_gan_zhi, yue_jiang, shi_chen)
        
        # 检查课体
        ke_ti_list = result['课体']
        print(f"  课体：{ke_ti_list}")
        
        # 检查三传
        sanchuan = result['三传']
        print(f"  三传：{sanchuan['初传']}, {sanchuan['中传']}, {sanchuan['末传']}")
        print(f"  起法：{sanchuan['起法']}")
        
        # 验证期望课体
        if expected in ke_ti_list:
            print(f"  ✓ 通过 (包含{expected})")
        else:
            print(f"  ✗ 未通过 (期望{expected}，实际{ke_ti_list})")
    
    print("\n")


def test_ke_jing_matching():
    """测试 64 课经匹配"""
    print("=" * 80)
    print("测试 2: 64 课经匹配")
    print("=" * 80)
    
    engine = CompleteQiKeEngine()
    matcher = AccurateKeJingMatcher()
    
    # 测试案例
    test_cases = [
        ('甲子', '亥', '午'),
        ('戊辰', '子', '子'),
        ('丙寅', '戌', '辰'),
        ('庚午', '未', '丑'),
        ('壬申', '午', '子'),
        ('乙丑', '子', '午'),
        ('丁卯', '戌', '辰'),
    ]
    
    total_matched = 0
    total_tested = len(test_cases)
    
    for ri_gan_zhi, yue_jiang, shi_chen in test_cases:
        print(f"\n{ri_gan_zhi}日{yue_jiang}将{shi_chen}时:")
        
        # 起课
        result = engine.qi_ke(ri_gan_zhi, yue_jiang, shi_chen)
        
        # 匹配课经
        matched = matcher.match_by_complete_qi_ke(result)
        
        if matched:
            total_matched += 1
            print(f"  ✓ 匹配成功：{len(matched)}个课经")
            for ke in matched[:3]:  # 只显示前 3 个
                ke_name = ke.get('ke_name', '未知')
                print(f"    - {ke_name}")
            if len(matched) > 3:
                print(f"    ... 还有{len(matched) - 3}个")
        else:
            print(f"  ✗ 未匹配")
        
        # 显示课体
        ke_ti = result['课体']
        if ke_ti:
            print(f"  课体：{', '.join(ke_ti)}")
    
    print(f"\n\n匹配统计：{total_matched}/{total_tested} = {total_matched/total_tested*100:.1f}%")
    print("\n")


def test_nine_school_methods():
    """测试九宗门起法"""
    print("=" * 80)
    print("测试 3: 九宗门起法验证")
    print("=" * 80)
    
    engine = CompleteQiKeEngine()
    
    # 各种起法的测试案例
    test_cases = [
        ('甲子', '亥', '午', '贼克法'),
        ('戊辰', '子', '子', '伏吟法'),
        ('丙寅', '戌', '辰', '反吟法'),
        ('庚午', '未', '丑', '反吟法'),
    ]
    
    for ri_gan_zhi, yue_jiang, shi_chen, expected_method in test_cases:
        print(f"\n测试：{ri_gan_zhi}日{yue_jiang}将{shi_chen}时")
        result = engine.qi_ke(ri_gan_zhi, yue_jiang, shi_chen)
        
        sanchuan = result['三传']
        actual_method = sanchuan.get('起法', '')
        
        print(f"  起法：{actual_method}")
        
        if expected_method in actual_method:
            print(f"  ✓ 通过")
        else:
            print(f"  ✗ 未通过 (期望：{expected_method})")
    
    print("\n")


def test_shen_sha():
    """测试神煞计算"""
    print("=" * 80)
    print("测试 4: 神煞计算")
    print("=" * 80)
    
    engine = CompleteQiKeEngine()
    
    # 测试甲子日
    result = engine.qi_ke('甲子', '亥', '午', lunar_month=1, nian_zhi='子')
    
    shen_sha = result['神煞']
    print("\n甲子日神煞:")
    for name, value in shen_sha.items():
        print(f"  {name:8s}: {value}")
    
    # 验证关键神煞
    expected_shen_sha = {
        '日禄': '寅',
        '驿马': '寅',
        '桃花': '酉',
    }
    
    print("\n神煞验证:")
    for name, expected in expected_shen_sha.items():
        actual = shen_sha.get(name, '')
        if actual == expected:
            print(f"  ✓ {name}: {actual}")
        else:
            print(f"  ✗ {name}: 期望{expected}, 实际{actual}")
    
    print("\n")


def test_ke_ti_judge():
    """测试课体判断"""
    print("=" * 80)
    print("测试 5: 课体判断")
    print("=" * 80)
    
    engine = CompleteQiKeEngine()
    
    # 特殊课体测试
    test_cases = [
        ('戊辰', '子', '子', ['伏吟课']),
        ('丙寅', '戌', '辰', ['反吟课']),
    ]
    
    for ri_gan_zhi, yue_jiang, shi_chen, expected_ke_ti in test_cases:
        print(f"\n测试：{ri_gan_zhi}日{yue_jiang}将{shi_chen}时")
        result = engine.qi_ke(ri_gan_zhi, yue_jiang, shi_chen)
        
        actual_ke_ti = result['课体']
        print(f"  课体：{actual_ke_ti}")
        
        # 验证期望课体
        all_found = True
        for expected in expected_ke_ti:
            if expected not in actual_ke_ti:
                all_found = False
                print(f"  ✗ 缺少：{expected}")
        
        if all_found:
            print(f"  ✓ 通过")
    
    print("\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("大六壬完整起课引擎系统测试")
    print("=" * 80 + "\n")
    
    # 运行所有测试
    test_basic_qi_ke()
    test_ke_jing_matching()
    test_nine_school_methods()
    test_shen_sha()
    test_ke_ti_judge()
    
    print("=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
