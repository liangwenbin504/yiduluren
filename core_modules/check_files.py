#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取仪度六壬选日要诀注解文件
"""

import os
import glob

# 获取当前目录
cwd = os.getcwd()
print(f"当前目录：{cwd}")

# 查找文件
files = glob.glob(r"*仪度*.txt")
print(f"\n找到的文件：{files}")

for file in files:
    print(f"\n文件：{file}")
    print(f"绝对路径：{os.path.abspath(file)}")
    print(f"文件大小：{os.path.getsize(file)} 字节")
    
    # 尝试读取
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin1']
    for encoding in encodings:
        try:
            with open(file, 'r', encoding=encoding) as f:
                content = f.read(500)
                print(f"\n✓ 成功读取（{encoding}）")
                print(f"前 300 字符:\n{content[:300]}")
                break
        except Exception as e:
            print(f"✗ {encoding}: {e}")
