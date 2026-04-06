#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析未匹配的 29 个课体定义
"""

import json

# 加载 64 课经数据
with open('data/64_ke_jing_accurate.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 未匹配的 29 个课体
unmatched_names = [
    '赘婿课', '涉害课', '遥克课', '昴星课', '别责课', '无禄课', '绝嗣课', 
    '芜淫课', '乱首课', '亨通课', '殃咎课', '三光失明课', '迍福课', 
    '闭口课', '灾厄课', '天祸课', '龙德课', '六阳格', '鬼墓课', 
    '伏殃课', '死绝课', '一旬周遍课', '解离课', '察奸课', '繁昌课', 
    '夹克课', '交车课', '三六相呼课', '索债课'
]

print("=" * 80)
print("未匹配的 29 个课体定义分析")
print("=" * 80)

for ke_id, ke_data in sorted(data['courses'].items(), key=lambda x: int(x[0])):
    ke_name = ke_data['ke_name']
    if ke_name in unmatched_names:
        print(f"\n{ke_id}. {ke_name} ({ke_data['ke_type']})")
        print(f"   定义：{ke_data['definition']}")
        print(f"   摘要：{ke_data['summary']}")
