#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试批量匹配系统
"""

import json
import os
import sys

# 测试数据加载
print("="*60)
print("  测试数据加载")
print("="*60)

# 1. 测试加载 64 课数据
analysis_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json'
if os.path.exists(analysis_file):
    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"✓ 64 课数据：{len(data['results'])} 条")
else:
    print(f"✗ 64 课数据文件不存在")
    sys.exit(1)

# 2. 测试加载课例数据
ke_li_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json'
if os.path.exists(ke_li_file):
    with open(ke_li_file, 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
        print(f"✓ 课例数据：{len(ke_li_data)} 个")
else:
    print(f"✗ 课例数据文件不存在")
    sys.exit(1)

# 3. 测试 API 调用
print("\n" + "="*60)
print("  测试 Qwen Max API 调用")
print("="*60)

import dashscope
from dashscope import Generation

API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

test_prompt = """你是一位大六壬专家。请分析这个课例：
日干支：甲子
月份：子
时辰：子
月将：丑

请匹配最合适的课经（1-2 个）。

以 JSON 格式返回：
{
    "matched_ke_jing": ["课经 1"],
    "confidence_scores": [95],
    "primary_ke_jing": "课经 1",
    "reasoning": "理由"
}
"""

print("正在调用 Qwen Max API...")
response = Generation.call(
    model='qwen-max',
    messages=[
        {'role': 'system', 'content': '你是一位精通大六壬的专家。'},
        {'role': 'user', 'content': test_prompt}
    ],
    timeout=90,
    stream=False
)

if response.status_code == 200:
    result_text = response.output.get('text', '')
    print(f"✓ API 调用成功")
    print(f"返回内容长度：{len(result_text)}")
    print(f"前 200 字符：{result_text[:200]}")
else:
    print(f"✗ API 调用失败：{response.status_code}")

print("\n" + "="*60)
print("  测试完成")
print("="*60)
