#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取古籍文件，查找六相六替相关内容
"""

import os
from pathlib import Path

base_dir = Path(r"d:\新建文件夹\仪度六壬择日\yiduluren\data\raw")

# 查找所有相关文件
files_to_read = []
for f in base_dir.iterdir():
    if '仪度' in f.name or '斗首' in f.name:
        files_to_read.append(f)

print(f"找到 {len(files_to_read)} 个相关文件\n")

for file_path in files_to_read:
    print(f"\n{'='*80}")
    print(f"读取文件：{file_path.name}")
    print('='*80)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件大小：{len(content)} 字")
            
            # 搜索六相六替
            keywords = ['六相', '六替', '六气', '三才', '番化', '三元']
            found = False
            
            for keyword in keywords:
                if keyword in content:
                    found = True
                    print(f"\n*** 找到关键词【{keyword}】***")
                    # 找到所有包含该关键词的行
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line:
                            # 打印该行及前后各 1 行
                            start = max(0, i-1)
                            end = min(len(lines), i+2)
                            for j in range(start, end):
                                marker = ">>>" if j == i else "   "
                                print(f"{marker} {lines[j]}")
            
            if not found:
                print("未找到六相六替相关内容")
                
    except Exception as e:
        print(f"读取失败：{e}")
