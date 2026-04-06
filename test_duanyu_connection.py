#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试综合评价系统与断语库的关联
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'utils'))

from comprehensive_evaluation import ComprehensiveEvaluation

def test_evaluation():
    """测试综合评价"""
    eval_sys = ComprehensiveEvaluation()
    
    print("=" * 80)
    print("综合吉凶评价测试 - 验证断语库关联")
    print("=" * 80)
    
    # 测试几个常见课格
    test_kejings = ['元首课', '龙德课', '重审课', '知一课']
    
    for kejing in test_kejings:
        print(f"\n{'=' * 80}")
        print(f"测试课格：{kejing}")
        print('=' * 80)
        
        # 测试 2026-03-20 23:00 壬山
        result = eval_sys.evaluate_date(2026, 3, 20, 23, '壬山', kejing)
        
        print(f"\n日期：{result['日期']}")
        print(f"四柱：{result['四柱']['年柱']} {result['四柱']['月柱']} {result['四柱']['日柱']} {result['四柱']['时柱']}")
        print(f"\n综合评分：{result['综合评分']}分 - {result['吉凶等级']}")
        print(f"\n【综合评语】\n{result['综合评语']}")
        print(f"\n【宜忌】")
        print(f"宜：{', '.join(result['宜忌']['宜'])}")
        print(f"忌：{', '.join(result['宜忌']['忌'])}")
        
        # 验证六壬信息是否包含详细断语
        liuren_info = result.get('六壬', {})
        print(f"\n【验证断语库关联】")
        print(f"  • 有详细断语：{'是' if liuren_info.get('详细断语') else '否'}")
        print(f"  • 有宜事：{'是' if liuren_info.get('宜事') else '否'}")
        print(f"  • 有忌事：{'是' if liuren_info.get('忌事') else '否'}")
        print(f"  • 有属相吉：{'是' if liuren_info.get('属相吉') else '否'}")
        print(f"  • 有行业：{'是' if liuren_info.get('行业') else '否'}")

if __name__ == '__main__':
    test_evaluation()
