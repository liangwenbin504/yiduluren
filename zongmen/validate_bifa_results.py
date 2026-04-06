#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋匹配结果验证脚本
验证内容：
1. 检查三传数据是否正确提取
2. 验证规则匹配逻辑是否正确
3. 抽样检查具体课例
"""

import json
from pathlib import Path

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_bifa_results():
    base_path = Path(__file__).parent
    
    ke_li_file = base_path / 'data' / '720_ke_li_jiu_zong_men.json'
    bifa_file = base_path / 'bifa_matched_results_v5.json'
    
    print("=" * 60)
    print("毕法赋匹配结果验证报告")
    print("=" * 60)
    
    ke_li_data = load_json(ke_li_file)
    bifa_data = load_json(bifa_file)
    
    ke_li_list = ke_li_data.get('ke_li', {})
    
    print(f"\n【基本信息】")
    print(f"原始课例数: {len(ke_li_list)}")
    print(f"毕法匹配数: {len(bifa_data)}")
    
    missing_chuan = []
    correct_chuan = []
    
    sample_count = 0
    for ke_id, ke_info in ke_li_list.items():
        if ke_id not in bifa_data:
            print(f"警告: 课例 {ke_id} 未在毕法匹配结果中")
            continue
        
        bifa_info = bifa_data[ke_id]
        
        sanchuan = ke_info.get('sanchuan', {})
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        bifa_chu = bifa_info.get('chu_chuan', '')
        bifa_zhong = bifa_info.get('zhong_chuan', '')
        bifa_mo = bifa_info.get('mo_chuan', '')
        
        if not bifa_chu and chu:
            missing_chuan.append({
                'ke_id': ke_id,
                'correct': [chu, zhong, mo],
                'bifa': [bifa_chu, bifa_zhong, bifa_mo]
            })
        else:
            correct_chuan.append(ke_id)
        
        sample_count += 1
        if sample_count >= 100:
            break
    
    print(f"\n【三传数据检查】")
    print(f"三传数据正确: {len(correct_chuan)} 课例")
    print(f"三传数据缺失: {len(missing_chuan)} 课例")
    
    if missing_chuan:
        print(f"\n【缺失三传的课例示例】(前10个):")
        for item in missing_chuan[:10]:
            print(f"  {item['ke_id']}:")
            print(f"    正确三传: {item['correct']}")
            print(f"    毕法结果: {item['bifa']}")
    
    print(f"\n【规则匹配验证】")
    
    test_cases = [
        {
            'ke_id': '甲子_子_子',
            'ri_gan': '甲',
            'ri_zhi': '子',
            'expected_rules': ['六阳数足须公用']
        },
        {
            'ke_id': '乙丑_子_子',
            'ri_gan': '乙',
            'ri_zhi': '丑',
            'expected_rules': ['六阴相继尽昏迷']
        },
        {
            'ke_id': '庚申_未_子',
            'ri_gan': '庚',
            'ri_zhi': '申',
            'expected_rules': ['六阳数足须公用', '金日逢丁凶祸动']
        }
    ]
    
    for test in test_cases:
        ke_id = test['ke_id']
        if ke_id in bifa_data:
            bifa_info = bifa_data[ke_id]
            matched_rules = [r['rule_name'] for r in bifa_info.get('bifa_matched_rules', [])]
            
            print(f"\n课例: {ke_id}")
            print(f"  日干支: {bifa_info.get('ri_gan_zhi', '')}")
            print(f"  匹配规则数: {bifa_info.get('bifa_matched_count', 0)}")
            print(f"  匹配规则: {matched_rules[:5]}...")
            
            for expected in test['expected_rules']:
                if expected in matched_rules:
                    print(f"  ✓ 预期规则 '{expected}' 已匹配")
                else:
                    print(f"  ✗ 预期规则 '{expected}' 未匹配")
    
    print(f"\n【规则分布统计】")
    rule_counts = {}
    for ke_id, bifa_info in bifa_data.items():
        for rule in bifa_info.get('bifa_matched_rules', []):
            rule_name = rule.get('rule_name', '')
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
    
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"\n匹配频率最高的规则 (前10):")
    for rule_name, count in sorted_rules[:10]:
        pct = count / len(bifa_data) * 100
        print(f"  {rule_name}: {count} 次 ({pct:.1f}%)")
    
    print(f"\n匹配频率最低的规则 (后10):")
    for rule_name, count in sorted_rules[-10:]:
        pct = count / len(bifa_data) * 100
        print(f"  {rule_name}: {count} 次 ({pct:.1f}%)")
    
    print(f"\n【验证结论】")
    if len(missing_chuan) > 0:
        print(f"⚠️ 发现问题: {len(missing_chuan)} 个课例的三传数据未正确提取")
        print(f"建议: 重新运行匹配程序，确保正确读取三传数据")
    else:
        print(f"✓ 三传数据提取正确")
    
    print(f"\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)

if __name__ == '__main__':
    validate_bifa_results()
