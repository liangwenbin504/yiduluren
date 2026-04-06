#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析 64 课经数据和匹配情况
"""

import json
import os

# 加载 64 课经数据
with open('data/64_ke_jing_accurate.json', 'r', encoding='utf-8') as f:
    ke_jing_data = json.load(f)

print("=" * 80)
print("64 课经数据分析")
print("=" * 80)
print(f"\n课经总数：{len(ke_jing_data['courses'])}")
print("\n所有 64 个课体名称:")
for k, v in sorted(ke_jing_data['courses'].items(), key=lambda x: int(x[0])):
    print(f"{k:3s}: {v['ke_name']:10s} (类型：{v['ke_type']})")

# 加载课例数据
with open('data/720_ke_li.json', 'r', encoding='utf-8') as f:
    ke_li_data = json.load(f)

print(f"\n课例总数：{len(ke_li_data)}")

# 统计已匹配的课体
matched_ke_ti = set()
for ke_data in ke_li_data.values():
    matched = ke_data.get('matched_ke_jing', [])
    for ke_name in matched:
        matched_ke_ti.add(ke_name)

print(f"\n已匹配的课体数量：{len(matched_ke_ti)}")
print("已匹配的课体:")
for name in sorted(matched_ke_ti):
    print(f"  - {name}")

# 找出未匹配的课体
all_ke_ti_names = {v['ke_name'] for v in ke_jing_data['courses'].values()}
unmatched = all_ke_ti_names - matched_ke_ti

print(f"\n未匹配的课体数量：{len(unmatched)}")
print("未匹配的课体:")
for name in sorted(unmatched):
    print(f"  ✗ {name}")

# 统计每个课体的课例数量
ke_ti_count = {}
for ke_data in ke_li_data.values():
    matched = ke_data.get('matched_ke_jing', [])
    for ke_name in matched:
        ke_ti_count[ke_name] = ke_ti_count.get(ke_name, 0) + 1

print("\n" + "=" * 80)
print("课体课例分布统计")
print("=" * 80)
sorted_ke_ti = sorted(ke_ti_count.items(), key=lambda x: x[1], reverse=True)
for name, count in sorted_ke_ti:
    print(f"{name:10s}: {count:4d}课")
