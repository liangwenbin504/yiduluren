#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试斗首六亲术语修正
验证修改后的逻辑是否正确
"""

import sys
import os

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

from douhou_analyzer import DouhouKegeAnalyzer

def test_terminology():
    """测试术语修正"""
    print("=" * 80)
    print("斗首六亲术语修正验证")
    print("=" * 80)
    
    analyzer = DouhouKegeAnalyzer()
    
    # 测试案例：壬山土元辰
    print("\n【测试案例】壬山土元辰")
    print("-" * 80)
    
    # 壬山属土
    shan_wuxing = analyzer.get_shan_jia_wuxing('壬')
    print(f"壬山五行：{shan_wuxing}")
    
    # 测试四柱天干
    test_cases = [
        ('年柱', '戊', '火'),  # 戊化火
        ('月柱', '丁', '木'),  # 丁化木
        ('日柱', '戊', '火'),  # 戊化火
        ('时柱', '癸', '火'),  # 癸化火
    ]
    
    print("\n四柱分析：")
    for pillar, tiangan, expected_huaqi in test_cases:
        huaqi = analyzer.get_tiangan_huaqi(tiangan)
        liuqin = analyzer.get_liuqin(shan_wuxing, huaqi)
        print(f"  {pillar}：{tiangan}干 → 化气{huaqi} → {liuqin}")
    
    # 验证术语
    print("\n【术语验证】")
    print("-" * 80)
    
    # 火生土 → 生我者为贪官
    print(f"火生土（生我者）：{analyzer.get_liuqin('土', '火')} ← 应该是：贪官")
    
    # 木克土 → 克我者为破鬼
    print(f"木克土（克我者）：{analyzer.get_liuqin('土', '木')} ← 应该是：破鬼")
    
    # 土克水 → 我克者为武财
    print(f"土克水（我克者）：{analyzer.get_liuqin('土', '水')} ← 应该是：武财")
    
    # 土生金 → 我生者为廉贞
    print(f"土生金（我生者）：{analyzer.get_liuqin('土', '金')} ← 应该是：廉贞")
    
    # 土土比和 → 同我者为元辰
    print(f"土土比和（同我者）：{analyzer.get_liuqin('土', '土')} ← 应该是：元辰")
    
    print("\n" + "=" * 80)
    
    # 完整课格分析
    print("\n【完整课格分析】")
    print("-" * 80)
    
    sizhu = {
        '年柱': '戊申',
        '月柱': '丁巳',
        '日柱': '戊午',
        '时柱': '癸亥'
    }
    
    result = analyzer.analyze_kege('壬', sizhu)
    
    print(f"\n坐山：{result.get('坐山', 'N/A')}")
    print(f"山家五行：{result.get('山家五行', 'N/A')}")
    
    if '四柱分析' in result:
        print(f"\n四柱分析：")
        for pillar, analysis in result['四柱分析'].items():
            print(f"  {pillar}：{analysis}")
    
    if '课格格局' in result:
        print(f"\n课格格局：")
        for pattern in result['课格格局']:
            print(f"  - {pattern}")
    
    if '吉凶断语' in result:
        print(f"\n吉凶断语：")
        for duanyu in result['吉凶断语']:
            print(f"  - {duanyu}")
    
    print(f"\n综合评分：{result.get('综合评分', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)

if __name__ == '__main__':
    test_terminology()
