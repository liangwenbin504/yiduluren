#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证 64 课经匹配完整性
"""

import json
import os

def verify_matching():
    """验证匹配结果"""
    # 加载数据
    with open('data/64_ke_jing_accurate.json', 'r', encoding='utf-8') as f:
        ke_jing_data = json.load(f)
    
    with open('data/720_ke_li.json', 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
    
    # 统计每个课经的匹配数
    ke_jing_count = {}
    for ke_id, ke_data in ke_jing_data.get('courses', {}).items():
        ke_name = ke_data.get('ke_name', '')
        ke_jing_count[ke_name] = 0
    
    for ke_data in ke_li_data.values():
        for ke_name in ke_data.get('matched_ke_jing', []):
            if ke_name in ke_jing_count:
                ke_jing_count[ke_name] += 1
    
    # 显示结果
    print("=" * 60)
    print("64 课经匹配验证报告")
    print("=" * 60)
    print(f"课经总数：{len(ke_jing_data.get('courses', {}))}")
    print(f"课例总数：{len(ke_li_data)}")
    print()
    
    # 按匹配数排序
    sorted_counts = sorted(ke_jing_count.items(), key=lambda x: x[1], reverse=True)
    
    print("课经匹配统计 (按匹配数排序):")
    print("-" * 60)
    for i, (ke_name, count) in enumerate(sorted_counts, 1):
        print(f"{i:3d}. {ke_name:15s}: {count:5d} 课")
    
    print()
    print("-" * 60)
    
    # 统计未匹配的课经
    unmatched = [ke_name for ke_name, count in ke_jing_count.items() if count == 0]
    if unmatched:
        print(f"\n未匹配到课例的课经 ({len(unmatched)}个):")
        for ke_name in unmatched:
            print(f"  - {ke_name}")
    else:
        print("\n✓ 所有课经都已匹配到课例!")
    
    # 统计匹配率
    matched_count = sum(1 for count in ke_jing_count.values() if count > 0)
    total_count = len(ke_jing_count)
    match_rate = (matched_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n匹配率：{matched_count}/{total_count} = {match_rate:.1f}%")
    
    return unmatched

if __name__ == '__main__':
    unmatched = verify_matching()
    
    if unmatched:
        print("\n\n需要进一步完善以下课经的匹配规则:")
        for ke_name in unmatched:
            print(f"  - {ke_name}")
    else:
        print("\n\n✓ 匹配验证通过！所有课经都已正确匹配。")
