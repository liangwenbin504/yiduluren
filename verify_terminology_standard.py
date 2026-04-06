#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首术语标准化验证脚本
验证所有斗首术语是否完全符合标准规范
"""

import sys
import os

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer

def test_terminology_standard():
    """测试术语标准化"""
    print("=" * 80)
    print("斗首术语标准化验证")
    print("=" * 80)
    
    # 标准术语定义
    STANDARD_TERMINOLOGY = {
        '贪官': {'关系': '生我者', '属性': '凶', '说明': '贪化鬼'},
        '破鬼': {'关系': '克我者', '属性': '凶', '说明': '鬼贼'},
        '武财': {'关系': '我克者', '属性': '吉', '说明': '妻财'},
        '廉贞': {'关系': '我生者', '属性': '平', '说明': '子孙'},
        '元辰': {'关系': '同我者', '属性': '吉', '说明': '比和'}
    }
    
    print("\n【标准术语定义】")
    print("-" * 80)
    for term, definition in STANDARD_TERMINOLOGY.items():
        print(f"{term}：{definition['关系']}，{definition['属性']}，{definition['说明']}")
    
    # 测试案例
    analyzer = DouhouKegeAnalyzer()
    
    print("\n【测试案例：壬山土元辰】")
    print("-" * 80)
    
    # 壬山属土
    shan_wuxing = analyzer.get_shan_jia_wuxing('壬')
    print(f"壬山五行：{shan_wuxing}")
    
    # 测试所有六亲关系
    test_cases = [
        ('火', '土', '贪官'),  # 火生土 → 生我者为贪官
        ('木', '土', '破鬼'),  # 木克土 → 克我者为破鬼
        ('水', '土', '武财'),  # 土克水 → 我克者为武财
        ('金', '土', '廉贞'),  # 土生金 → 我生者为廉贞
        ('土', '土', '元辰'),  # 土土比和 → 同我者为元辰
    ]
    
    print("\n【六亲关系验证】")
    print("-" * 80)
    
    all_correct = True
    for huaqi, shan, expected in test_cases:
        result = analyzer.get_liuqin(shan, huaqi)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_correct = False
        
        # 获取标准定义
        standard = STANDARD_TERMINOLOGY.get(result, {})
        
        print(f"{status} {huaqi} → {shan}：{result}")
        print(f"   关系：{standard.get('关系', 'N/A')}")
        print(f"   属性：{standard.get('属性', 'N/A')}")
        print(f"   说明：{standard.get('说明', 'N/A')}")
        print()
    
    # 完整课格分析
    print("\n【完整课格分析验证】")
    print("-" * 80)
    
    sizhu = {
        '年柱': '戊申',
        '月柱': '丁巳',
        '日柱': '戊午',
        '时柱': '癸亥'
    }
    
    result = analyzer.analyze_kege('壬', sizhu)
    
    print(f"坐山：{result.get('坐山', 'N/A')}")
    print(f"山家五行：{result.get('山家五行', 'N/A')}")
    
    if '四柱分析' in result:
        print(f"\n四柱分析：")
        for pillar, analysis in result['四柱分析'].items():
            liuqin = analysis.get('六亲', 'N/A')
            standard = STANDARD_TERMINOLOGY.get(liuqin, {})
            print(f"  {pillar}：{analysis.get('干支', 'N/A')} → {liuqin}")
            print(f"       关系：{standard.get('关系', 'N/A')}")
            print(f"       属性：{standard.get('属性', 'N/A')}")
    
    if '吉凶断语' in result:
        print(f"\n吉凶断语：")
        for duanyu in result['吉凶断语']:
            print(f"  - {duanyu}")
    
    print(f"\n综合评分：{result.get('综合评分', 'N/A')}")
    
    # 最终结果
    print("\n" + "=" * 80)
    if all_correct:
        print("✅ 所有斗首术语已完全标准化！")
    else:
        print("❌ 存在术语不一致的情况，请检查！")
    print("=" * 80)
    
    return all_correct

if __name__ == '__main__':
    success = test_terminology_standard()
    sys.exit(0 if success else 1)
