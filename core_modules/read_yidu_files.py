#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取仪度六壬选日要诀注解文件
"""

import os

# 文件路径
file1 = r"1《仪度六壬选日要诀》注解 1.txt"
file2 = r"2《仪度六壬选日要诀》注解 2.txt"

print("=" * 80)
print("读取仪度六壬选日要诀注解文件")
print("=" * 80)

# 尝试不同编码读取
encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']

for encoding in encodings:
    try:
        print(f"\n尝试编码：{encoding}")
        with open(file1, 'r', encoding=encoding) as f:
            content = f.read(1000)
            print(f"✓ 成功读取文件 1（{encoding}）")
            print(f"  文件大小：{os.path.getsize(file1)} 字节")
            print(f"  前 200 字符：\n{content[:200]}")
            break
    except Exception as e:
        print(f"✗ 失败：{e}")

print("\n" + "=" * 80)
for encoding in encodings:
    try:
        print(f"\n尝试编码：{encoding}")
        with open(file2, 'r', encoding=encoding) as f:
            content = f.read(1000)
            print(f"✓ 成功读取文件 2（{encoding}）")
            print(f"  文件大小：{os.path.getsize(file2)} 字节")
            print(f"  前 200 字符：\n{content[:200]}")
            break
    except Exception as e:
        print(f"✗ 失败：{e}")
