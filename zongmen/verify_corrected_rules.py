#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证修正后的规则17、23、24"""

import json
from pathlib import Path

def verify_corrected_rules():
    bifa_file = Path(__file__).parent / 'bifa_matched_results_v5_fixed.json'
    bifa_data = json.load(open(bifa_file, 'r', encoding='utf-8'))
    
    rule_counts = {17: 0, 23: 0, 24: 0}
    examples = {17: [], 23: [], 24: []}
    
    for ke_id, info in bifa_data.items():
        for rule in info.get('bifa_matched_rules', []):
            rule_id = rule.get('rule_id', 0)
            if rule_id in [17, 23, 24]:
                rule_counts[rule_id] += 1
                if len(examples[rule_id]) < 3:
                    examples[rule_id].append({
                        'ke_id': ke_id,
                        'ri_gan_zhi': info.get('ri_gan_zhi', ''),
                        'reasoning': rule.get('reasoning', '')
                    })
    
    print("=" * 60)
    print("修正后的规则匹配验证")
    print("=" * 60)
    
    print(f"\n规则17 '进茹空亡宜退步': {rule_counts[17]} 次 ({rule_counts[17]/8640*100:.1f}%)")
    if examples[17]:
        print("  示例:")
        for ex in examples[17]:
            print(f"    {ex['ke_id']}: {ex['reasoning']}")
    
    print(f"\n规则23 '彼求我事支传干': {rule_counts[23]} 次 ({rule_counts[23]/8640*100:.1f}%)")
    if examples[23]:
        print("  示例:")
        for ex in examples[23]:
            print(f"    {ex['ke_id']}: {ex['reasoning']}")
    
    print(f"\n规则24 '我求彼事干传支': {rule_counts[24]} 次 ({rule_counts[24]/8640*100:.1f}%)")
    if examples[24]:
        print("  示例:")
        for ex in examples[24]:
            print(f"    {ex['ke_id']}: {ex['reasoning']}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    verify_corrected_rules()
