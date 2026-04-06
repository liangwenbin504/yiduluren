#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋匹配修复脚本
问题：三传数据未正确提取，导致规则匹配错误
修复：从原始课例数据中正确提取三传信息
"""

import json
from pathlib import Path
from bifa_rules_engine_v5 import BiFaRulesMatcherV5

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fix_and_rematch():
    base_path = Path(__file__).parent
    
    ke_li_file = base_path / 'data' / '720_ke_li_jiu_zong_men.json'
    output_file = base_path / 'bifa_matched_results_v5_fixed.json'
    
    print("=" * 60)
    print("毕法赋匹配修复程序")
    print("=" * 60)
    
    ke_li_data = load_json(ke_li_file)
    ke_li_list = ke_li_data.get('ke_li', {})
    
    print(f"\n加载课例数: {len(ke_li_list)}")
    
    matcher = BiFaRulesMatcherV5()
    
    results = {}
    total = len(ke_li_list)
    processed = 0
    
    for ke_id, ke_info in ke_li_list.items():
        processed += 1
        if processed % 1000 == 0:
            print(f"处理进度: {processed}/{total} ({processed/total*100:.1f}%)")
        
        ri_gan_zhi = ke_info.get('ri_gan_zhi', '')
        yue = ke_info.get('yue', '')
        shi = ke_info.get('shi', '')
        yue_jiang = ke_info.get('yue_jiang', '')
        
        sanchuan = ke_info.get('sanchuan', {})
        chu_chuan = sanchuan.get('初传', '')
        zhong_chuan = sanchuan.get('中传', '')
        mo_chuan = sanchuan.get('末传', '')
        
        sike = ke_info.get('sike', [])
        gan_shang = ''
        zhi_shang = ''
        
        if len(sike) >= 2:
            first_ke = sike[0]
            second_ke = sike[1]
            if len(first_ke) >= 2:
                gan_shang = first_ke[1]
            if len(second_ke) >= 2:
                zhi_shang = second_ke[1]
        
        ke_ti_list = ke_info.get('ke_ti_list', [])
        ke_ti_ge_ju = ke_ti_list if ke_ti_list else []
        
        ke_li_for_match = {
            'ri_gan_zhi': ri_gan_zhi,
            'yue': yue,
            'shi': shi,
            'yue_jiang': yue_jiang,
            'chu_chuan': chu_chuan,
            'zhong_chuan': zhong_chuan,
            'mo_chuan': mo_chuan,
            'gan_shang': gan_shang,
            'zhi_shang': zhi_shang,
            'ke_ti_ge_ju': ke_ti_ge_ju,
            'ke_ti_list': ke_ti_list
        }
        
        match_result = matcher.match_all_rules(ke_li_for_match)
        
        duan_yu_parts = []
        for rule in match_result.get('matched_rules', [])[:5]:
            duan_yu_parts.append(f"{rule.get('rule_name', '')}：{rule.get('reasoning', '')}")
        duan_yu = "；".join(duan_yu_parts)
        
        results[ke_id] = {
            'ri_gan_zhi': ri_gan_zhi,
            'yue': yue,
            'shi': shi,
            'yue_jiang': yue_jiang,
            'chu_chuan': chu_chuan,
            'zhong_chuan': zhong_chuan,
            'mo_chuan': mo_chuan,
            'gan_shang': gan_shang,
            'zhi_shang': zhi_shang,
            'ke_ti_ge_ju': ke_ti_ge_ju,
            'bifa_matched_count': match_result.get('matched_count', 0),
            'bifa_matched_rules': match_result.get('matched_rules', []),
            'duan_yu': duan_yu
        }
    
    save_json(results, output_file)
    
    print(f"\n【修复完成】")
    print(f"输出文件: {output_file}")
    print(f"处理课例: {len(results)}")
    
    rule_counts = {}
    for ke_id, info in results.items():
        for rule in info.get('bifa_matched_rules', []):
            rule_name = rule.get('rule_name', '')
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
    
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n【修复后规则分布】(前15):")
    for rule_name, count in sorted_rules[:15]:
        pct = count / len(results) * 100
        print(f"  {rule_name}: {count} 次 ({pct:.1f}%)")
    
    print(f"\n【修复后规则分布】(后10):")
    for rule_name, count in sorted_rules[-10:]:
        pct = count / len(results) * 100
        print(f"  {rule_name}: {count} 次 ({pct:.1f}%)")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    fix_and_rematch()
