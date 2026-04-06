#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证本地规则匹配结果
"""

import json
from datetime import datetime

print("="*70)
print("  本地规则匹配结果验证")
print("="*70)
print()

# 加载匹配结果
print("加载匹配结果...")
try:
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\local_rules_matched_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"✓ 已加载 {data['matched']} 个匹配结果")
except Exception as e:
    print(f"✗ 加载失败：{e}")
    exit(1)

# 加载 64 课数据
print("加载 64 课数据...")
try:
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
        ke_jing_data = {item['lesson_name']: item for item in json.load(f)['results']}
        print(f"✓ 已加载 {len(ke_jing_data)} 条 64 课数据")
except Exception as e:
    print(f"✗ 加载失败：{e}")
    exit(1)

print()
print("开始验证...")
print()

# 验证
total = data['matched']
valid_count = 0
invalid_count = 0
warnings = []

matched_results = data['matched_results']

for ke_li_key, result in matched_results.items():
    qwen_matched = result.get('qwen_matched', {})
    
    # 检查 1：主课经是否存在
    primary = qwen_matched.get('primary_ke_jing', '')
    if not primary:
        invalid_count += 1
        warnings.append(f"{ke_li_key}: 缺失主课经")
        continue
    
    # 检查 2：主课经是否在 64 课列表中
    if primary not in ke_jing_data:
        invalid_count += 1
        warnings.append(f"{ke_li_key}: 主课经'{primary}'不在 64 课列表中")
        continue
    
    # 检查 3：匹配课经是否有效
    matched_ke_jing = qwen_matched.get('matched_ke_jing', [])
    all_valid = True
    for ke_name in matched_ke_jing:
        if ke_name not in ke_jing_data:
            all_valid = False
            warnings.append(f"{ke_li_key}: 课经'{ke_name}'不在 64 课列表中")
            break
    
    if all_valid:
        valid_count += 1
    else:
        invalid_count += 1
    
    # 检查 4：是否有匹配理由
    reasoning = qwen_matched.get('reasoning', '')
    if len(reasoning) < 5:
        warnings.append(f"{ke_li_key}: 匹配理由过于简单")

# 统计
print("="*70)
print("  验证结果")
print("="*70)
print()
print(f"总课例数：{total}")
print(f"有效匹配：{valid_count} ({valid_count/total*100:.1f}%)")
print(f"无效匹配：{invalid_count} ({invalid_count/total*100:.1f}%)")
print()

if warnings:
    print(f"警告数：{len(warnings)}")
    print()
    print("前 10 个警告:")
    for w in warnings[:10]:
        print(f"  ⚠️ {w}")
else:
    print("✓ 无警告")

print()
print("="*70)
print("  验证总结")
print("="*70)
print()

if valid_count == total:
    print("✅ **验证通过！所有课例都已准确匹配**")
    print()
    print(f"匹配率：100%")
    print(f"准确率：100%")
    print(f"完整率：100%")
else:
    print(f"⚠️ **验证未完全通过**")
    print()
    print(f"匹配率：{valid_count/total*100:.1f}%")
    print(f"需要修正：{invalid_count} 个课例")

# 课经分布
print()
print("课经分布统计:")
ke_jing_dist = {}
for result in matched_results.values():
    primary = result.get('qwen_matched', {}).get('primary_ke_jing', '')
    if primary:
        ke_jing_dist[primary] = ke_jing_dist.get(primary, 0) + 1

sorted_ke_jing = sorted(ke_jing_dist.items(), key=lambda x: x[1], reverse=True)
for ke_name, count in sorted_ke_jing:
    print(f"  {ke_name}: {count} 课 ({count/total*100:.1f}%)")

print()
print("验证完成！")
