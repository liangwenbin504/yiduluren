#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首五行定义验证测试
验证修正后的山家五行是否符合《斗首择日秘本》的规定
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core_modules.data.斗首择日规则 import SHANJIA_WUXING, TIANGAN_HUAQI

def verify_shanjia_wuxing():
    """验证山家五行"""
    print("=" * 70)
    print("斗首五行定义验证测试")
    print("=" * 70)
    print()
    
    # 秘本中的斗首五行歌诀
    print("【秘本歌诀】")
    print("壬子巽巳辛戌土，艮寅丁未木元辰。")
    print("癸丑丙午乾亥火。")
    print("坤申甲卯属水神，若问金星何处是，乙庚辰酉四山真。")
    print()
    
    # 预期定义
    expected = {
        # 土：壬子巽巳辛戌（6 山）
        '壬': '土', '子': '土', '巽': '土', '巳': '土', '辛': '土', '戌': '土',
        # 火：癸丑丙午乾亥（6 山）
        '癸': '火', '丑': '火', '丙': '火', '午': '火', '乾': '火', '亥': '火',
        # 木：艮寅丁未（4 山）
        '艮': '木', '寅': '木', '丁': '木', '未': '木',
        # 水：坤申甲卯（4 山）
        '坤': '水', '申': '水', '甲': '水', '卯': '水',
        # 金：乙辰庚酉（4 山）
        '乙': '金', '辰': '金', '庚': '金', '酉': '金'
    }
    
    print("【验证结果】")
    print("-" * 70)
    
    all_correct = True
    
    # 分组验证
    groups = {
        '土': ['壬', '子', '巽', '巳', '辛', '戌'],
        '火': ['癸', '丑', '丙', '午', '乾', '亥'],
        '木': ['艮', '寅', '丁', '未'],
        '水': ['坤', '申', '甲', '卯'],
        '金': ['乙', '辰', '庚', '酉']
    }
    
    for wuxing, mountains in groups.items():
        print(f"\n【{wuxing}山】（共{len(mountains)}山）")
        for mountain in mountains:
            actual = SHANJIA_WUXING.get(mountain)
            expect = expected[mountain]
            status = "✓" if actual == expect else "✗"
            if actual != expect:
                all_correct = False
            print(f"  {mountain}山：{actual} {status}")
    
    print()
    print("-" * 70)
    
    # 统计
    total = len(SHANJIA_WUXING)
    correct = sum(1 for m, w in SHANJIA_WUXING.items() if expected.get(m) == w)
    
    print(f"【统计】")
    print(f"  总山数：{total}")
    print(f"  正确：{correct}")
    print(f"  错误：{total - correct}")
    print(f"  准确率：{correct/total*100:.1f}%")
    print()
    
    if all_correct:
        print("✅ 验证通过：所有山家五行定义与秘本完全一致！")
    else:
        print("❌ 验证失败：存在定义不符的情况")
    
    print()
    return all_correct

def verify_tiangan_huaqi():
    """验证天干化气"""
    print("=" * 70)
    print("天干化气五行验证")
    print("=" * 70)
    print()
    
    # 秘本中的天干化气
    print("【秘本歌诀】")
    print("甲己化土，乙庚化金，丙辛化水，丁壬化木，戊癸化火。")
    print()
    
    expected = {
        '甲': '土', '己': '土',
        '乙': '金', '庚': '金',
        '丙': '水', '辛': '水',
        '丁': '木', '壬': '木',
        '戊': '火', '癸': '火'
    }
    
    print("【验证结果】")
    print("-" * 70)
    
    all_correct = True
    for tiangan, expected_wx in expected.items():
        actual = TIANGAN_HUAQI.get(tiangan)
        status = "✓" if actual == expected_wx else "✗"
        if actual != expected_wx:
            all_correct = False
        print(f"  {tiangan}化：{actual} (应为{expected_wx}) {status}")
    
    print()
    print("-" * 70)
    
    if all_correct:
        print("✅ 验证通过：所有天干化气定义与秘本完全一致！")
    else:
        print("❌ 验证失败：存在定义不符的情况")
    
    print()
    return all_correct

def test_douhou_stars():
    """测试斗首五星配置"""
    print("=" * 70)
    print("斗首五星配置测试")
    print("=" * 70)
    print()
    
    from engine.douhou_engine import DouShouCalculator
    
    calculator = DouShouCalculator()
    
    # 测试案例：壬山（属土）
    print("【测试案例 1】壬山（属土）")
    print("-" * 70)
    result = calculator.calculate_douhou_stars('壬', '甲')
    print(f"山家五行：{result['山家五行']}")
    print(f"化气五行：{result['化气五行']}")
    print(f"五星配置：{result['五星配置']}")
    print()
    
    # 验证：壬山属土，甲己化土
    # 元辰：土（与山家同）
    # 武财：土克水（我克者为财）
    # 贪官：木克土（克我者为官鬼）
    # 廉贞：土生金（我生者为子孙）
    # 破鬼：火生土（生我者为父母）
    
    print("【验证】")
    stars = result['五星配置']
    print(f"  元辰：{stars['元辰']} (应为土)")
    print(f"  武财：{stars['武财']} (应为水)")
    print(f"  贪官：{stars['贪官']} (应为木)")
    print(f"  廉贞：{stars['廉贞']} (应为金)")
    print(f"  破鬼：{stars['破鬼']} (应为火)")
    print()
    
    # 测试案例：艮山（属木）
    print("【测试案例 2】艮山（属木）")
    print("-" * 70)
    result2 = calculator.calculate_douhou_stars('艮', '丁')
    print(f"山家五行：{result2['山家五行']}")
    print(f"化气五行：{result2['化气五行']}")
    print(f"五星配置：{result2['五星配置']}")
    print()
    
    print("=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    result1 = verify_shanjia_wuxing()
    print()
    result2 = verify_tiangan_huaqi()
    print()
    test_douhou_stars()
    
    print()
    print("=" * 70)
    if result1 and result2:
        print("✅ 所有验证通过！斗首五行定义已完全符合《斗首择日秘本》")
    else:
        print("❌ 存在验证失败项，请检查")
    print("=" * 70)
