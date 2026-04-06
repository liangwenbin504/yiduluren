#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索 PDF 中鬼墓课的内容
"""

import fitz  # PyMuPDF
import os

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'

if not os.path.exists(pdf_path):
    print(f"PDF 文件不存在：{pdf_path}")
    exit(1)

print("=" * 80)
print("搜索《白话大六壬全书》中的鬼墓课内容")
print("=" * 80)
print()

doc = fitz.open(pdf_path)

# 搜索包含"鬼墓"的页面
found_pages = []
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    
    # 搜索鬼墓
    if '鬼墓' in text:
        found_pages.append(page_num)
        print(f"\n【第{page_num + 1}页找到相关内容】")
        print("-" * 80)
        
        # 提取包含关键词的段落
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '鬼墓' in line:
                # 打印上下文
                start = max(0, i - 2)
                end = min(len(lines), i + 5)
                for j in range(start, end):
                    print(lines[j])
                print()

if not found_pages:
    print("\n未找到包含'鬼墓'的内容")
    print("\n尝试搜索相关关键词...")
    
    # 搜索其他可能的相关词
    keywords = ['墓库', '官鬼', '鬼爻', '墓神']
    for keyword in keywords:
        print(f"\n搜索'{keyword}':")
        for page_num in range(min(50, len(doc))):  # 只搜索前 50 页
            page = doc[page_num]
            text = page.get_text()
            if keyword in text:
                print(f"  第{page_num + 1}页")

doc.close()

print("\n" + "=" * 80)
print("搜索完成")
print("=" * 80)
