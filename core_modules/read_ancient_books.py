#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取古籍文件，查找六相六替相关内容
"""

import os

# 尝试不同的编码读取文件
file_paths = [
    r"d:\新建文件夹\仪度六壬择日\yiduluren\data\raw\1《仪度六壬选日要诀》注解 1.txt",
    r"d:\新建文件夹\仪度六壬择日\yiduluren\data\raw\2《仪度六壬选日要诀》注解 2.txt",
    r"d:\新建文件夹\仪度六壬择日\yiduluren\data\raw\斗首择日秘本.txt"
]

encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']

for file_path in file_paths:
    print(f"\n{'='*80}")
    print(f"读取文件：{file_path}")
    print('='*80)
    
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        continue
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read(2000)  # 读取前 2000 字
                print(f"成功！编码：{encoding}")
                print(f"\n内容摘要：\n{content[:500]}")
                
                # 搜索六相六替
                if '六相' in content or '六替' in content:
                    print("\n*** 找到六相六替相关内容！***")
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '六相' in line or '六替' in line:
                            # 打印该行及前后各 2 行
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            for j in range(start, end):
                                print(f"  {lines[j]}")
                break
        except Exception as e:
            print(f"编码{encoding}失败：{str(e)[:100]}")
            continue
