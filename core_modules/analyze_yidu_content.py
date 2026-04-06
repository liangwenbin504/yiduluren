#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析《仪度六壬选日要诀》注解内容
提取六壬课格评分标准和权衡算法规则
"""

import os

def read_file_content(filename):
    """读取文件内容"""
    with open(filename, 'r', encoding='gbk') as f:
        return f.read()

# 读取两个文件
content1 = read_file_content(r"1《仪度六壬选日要诀》注解 1.txt")
content2 = read_file_content(r"2《仪度六壬选日要诀》注解 2.txt")

print("=" * 80)
print("《仪度六壬选日要诀》注解内容分析")
print("=" * 80)

# 分析文件 1 结构
print("\n【文件 1 结构】")
print(f"总字数：{len(content1)}")

# 查找关键章节
keywords = ['课格', '吉凶', '评分', '权衡', '选择', '斗首', '六壬', '贵', '禄', '马']
for keyword in keywords:
    count = content1.count(keyword)
    if count > 0:
        print(f"  - '{keyword}' 出现 {count} 次")

# 提取目录
print("\n【文件 1 目录结构】")
if '目  录' in content1:
    mu_start = content1.index('目  录')
    mu_content = content1[mu_start:mu_start+2000]
    print(mu_content[:1500])

# 分析文件 2
print("\n【文件 2 内容概览】")
print(f"总字数：{len(content2)}")

# 查找关于课格吉凶的描述
print("\n【查找课格吉凶相关描述】")
if '吉' in content1:
    ji_sentences = [s.strip() for s in content1.split('。') if '吉' in s and len(s) < 100]
    print(f"包含'吉'的句子（前 10 条）:")
    for i, sentence in enumerate(ji_sentences[:10], 1):
        print(f"{i}. {sentence}")

# 查找权衡规则
print("\n【查找权衡选择规则】")
weight_keywords = ['宜', '忌', '先', '后', '重', '轻', '主', '次']
for kw in weight_keywords:
    sentences = [s.strip() for s in content1.split('。') if kw in s and len(s) < 80]
    if sentences:
        print(f"\n包含'{kw}'的规则（前 3 条）:")
        for i, s in enumerate(sentences[:3], 1):
            print(f"{i}. {s}")

print("\n" + "=" * 80)
print("分析完成！")
print("=" * 80)
