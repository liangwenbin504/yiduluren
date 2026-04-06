#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取 PDF 第 348 页并保存到文件
"""

import fitz
import sys

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'
output_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\page_348_content.txt'

try:
    doc = fitz.open(pdf_path)
    
    # 第 348 页（索引 347）
    page_num = 347
    page = doc[page_num]
    
    # 获取文本
    text = page.get_text()
    
    # 保存到文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"《白话大六壬全书》第{page_num + 1}页\n")
        f.write("=" * 80 + "\n\n")
        f.write(text)
    
    print(f"成功提取第{page_num + 1}页内容")
    print(f"保存到：{output_path}")
    print(f"文本长度：{len(text)}字符")
    print()
    print("内容预览：")
    print("=" * 80)
    print(text[:1000])
    print("=" * 80)
    
    doc.close()
    
except Exception as e:
    print(f"错误：{e}")
    sys.exit(1)
