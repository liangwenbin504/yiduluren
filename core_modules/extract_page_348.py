#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取 PDF 第 348 页鬼墓课的内容
"""

import fitz  # PyMuPDF
import os

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'

if not os.path.exists(pdf_path):
    print(f"PDF 文件不存在：{pdf_path}")
    exit(1)

print("=" * 80)
print("提取《白话大六壬全书》第 348 页内容")
print("=" * 80)
print()

doc = fitz.open(pdf_path)

# 提取第 348 页（索引从 0 开始，所以是 347）
page_num = 347  # 第 348 页
if page_num < len(doc):
    page = doc[page_num]
    text = page.get_text()
    
    print(f"【第{page_num + 1}页原文】")
    print("=" * 80)
    print(text)
    print("=" * 80)
else:
    print(f"页码超出范围，PDF 总页数：{len(doc)}")

doc.close()
