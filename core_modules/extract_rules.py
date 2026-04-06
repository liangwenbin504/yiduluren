#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
深入分析《仪度六壬选日要诀》注解
提取六壬课格评分标准和斗首六壬权衡规则
"""

def read_file(filename):
    """读取文件"""
    with open(filename, 'r', encoding='gbk') as f:
        return f.read()

# 读取文件
content1 = read_file_content(r"1《仪度六壬选日要诀》注解 1.txt")
content2 = read_file_content(r"2《仪度六壬选日要诀》注解 2.txt")

print("=" * 80)
print("《仪度六壬选日要诀》核心内容提取")
print("=" * 80)

# 提取文件 1 的章节标题
print("\n【文件 1 章节结构】")
import re
# 查找章节标题（第一章、第二章等）
zhang_pattern = r'第 [一二三四五六七八九十]+章.*?(?=\n第 [一二三四五六七八九十]+章|$)'
zhangs = re.findall(zhang_pattern, content1, re.DOTALL)

for i, zhang in enumerate(zhangs[:5], 1):
    title = zhang.split('\n')[0]
    print(f"\n{title}")
    # 提取小节
    xiao_pattern = r'第 [一二三四五六七八九十]+节[^\n]+'
    xiaojies = re.findall(xiao_pattern, zhang)
    for xj in xiaojies[:5]:
        print(f"  - {xj}")

# 提取关于六壬课格吉凶的关键描述
print("\n" + "=" * 80)
print("【六壬课格吉凶判断要点】")

# 查找与贵人、禄、马相关的内容
guiren_content = []
for sentence in content1.split('。'):
    if any(kw in sentence for kw in ['贵人', '禄', '马', '三吉']):
        if len(sentence) < 150:
            guiren_content.append(sentence.strip())

print("\n关于三吉（贵人、禄、马）的描述：")
for i, s in enumerate(guiren_content[:15], 1):
    print(f"{i}. {s}")

# 查找权衡规则
print("\n" + "=" * 80)
print("【权衡选择规则】")

# 查找优先级相关的描述
priority_keywords = ['先', '后', '宜', '忌', '最', '首', '次', '重']
priority_rules = []

for sentence in content1.split('。'):
    for kw in priority_keywords:
        if kw in sentence and len(sentence) < 100:
            priority_rules.append((kw, sentence.strip()))
            break

print("\n优先级规则（前 20 条）:")
for i, (kw, rule) in enumerate(priority_rules[:20], 1):
    print(f"{i}. [{kw}] {rule}")

# 查找斗首与六壬配合的内容
print("\n" + "=" * 80)
print("【斗首与六壬配合规则】")

doushou_liuren = []
for sentence in content1.split('。'):
    if ('斗首' in sentence or '六壬' in sentence) and len(sentence) < 120:
        doushou_liuren.append(sentence.strip())

for i, s in enumerate(doushou_liuren[:15], 1):
    print(f"{i}. {s}")

print("\n" + "=" * 80)
