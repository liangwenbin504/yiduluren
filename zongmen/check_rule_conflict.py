#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查规则69和70的匹配矛盾
"""

import json
from pathlib import Path

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_rule_conflict():
    base_path = Path(__file__).parent
    bifa_file = base_path / 'bifa_matched_results_v5_fixed.json'
    
    print("=" * 60)
    print("检查规则69和70的匹配矛盾")
    print("=" * 60)
    
    bifa_data = load_json(bifa_file)
    
    both_matched = []
    rule69_only = []
    rule70_only = []
    neither = []
    
    for ke_id, info in bifa_data.items():
        matched_rules = [r['rule_id'] for r in info.get('bifa_matched_rules', [])]
        
        has_69 = 69 in matched_rules
        has_70 = 70 in matched_rules
        
        if has_69 and has_70:
            both_matched.append(ke_id)
        elif has_69:
            rule69_only.append(ke_id)
        elif has_70:
            rule70_only.append(ke_id)
        else:
            neither.append(ke_id)
    
    print(f"\n【统计结果】")
    print(f"同时匹配规则69和70: {len(both_matched)} 个课例")
    print(f"仅匹配规则69: {len(rule69_only)} 个课例")
    print(f"仅匹配规则70: {len(rule70_only)} 个课例")
    print(f"都不匹配: {len(neither)} 个课例")
    
    if both_matched:
        print(f"\n⚠️ 存在矛盾: {len(both_matched)} 个课例同时匹配规则69和70")
        print(f"这说明规则判断逻辑有问题，三传不可能同时'生日干'和'克日干'")
        print(f"\n【矛盾课例示例】(前5个):")
        for ke_id in both_matched[:5]:
            info = bifa_data[ke_id]
            print(f"  {ke_id}:")
            print(f"    三传: {info.get('chu_chuan', '')} {info.get('zhong_chuan', '')} {info.get('mo_chuan', '')}")
            print(f"    日干: {info.get('ri_gan_zhi', '')[:1]}")
    else:
        print(f"\n✓ 无矛盾: 没有课例同时匹配规则69和70")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    check_rule_conflict()
