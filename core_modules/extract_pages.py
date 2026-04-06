#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取 PDF 第 345-355 页的内容，查找鬼墓课
"""

import fitz  # PyMuPDF
import os

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'

if not os.path.exists(pdf_path):
    print(f"PDF 文件不存在：{pdf_path}")
    exit(1)

print("=" * 80)
print("提取《白话大六壬全书》第 345-355 页内容")
print("=" * 80)
print()

doc = fitz.open(pdf_path)

# 提取第 345-355 页
for page_num in range(344, 356):  # 344-355 对应第 345-356 页
    if page_num < len(doc):
        page = doc[page_num]
        text = page.get_text()
        
        # 检查是否包含"鬼墓"
        if '鬼墓' in text or '墓' in text:
            print(f"\n{'='*80}")
            print(f"【第{page_num + 1}页】")
            print('='*80)
            print(text[:2000])  # 只显示前 2000 字符

doc.close()

print("\n" + "=" * 80)
print("提取完成")
print("=" * 80)
