#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用不同方法提取 PDF 第 348 页内容
"""

import fitz  # PyMuPDF
import os

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'

if not os.path.exists(pdf_path):
    print(f"PDF 文件不存在：{pdf_path}")
    exit(1)

print("=" * 80)
print("使用不同方法提取 PDF 第 348 页内容")
print("=" * 80)
print()

doc = fitz.open(pdf_path)

# 方法 1：直接获取第 348 页
page_num = 347  # 索引从 0 开始
page = doc[page_num]

print(f"【方法 1：get_text()】")
print("=" * 80)
text1 = page.get_text()
print(repr(text1[:500]))  # 显示原始字符
print()

print(f"【方法 2：get_text('text')】")
print("=" * 80)
text2 = page.get_text('text')
print(text2[:500])
print()

print(f"【方法 3：get_text('html')】")
print("=" * 80)
try:
    html = page.get_text('html')
    print(f"HTML 长度：{len(html)}")
    # 简单清理 HTML 标签
    import re
    clean_text = re.sub(r'<[^>]+>', '', html)
    print(clean_text[:500])
except Exception as e:
    print(f"错误：{e}")

print()
print(f"【方法 4：get_text('dict')】")
print("=" * 80)
try:
    blocks = page.get_text('dict')['blocks']
    print(f"找到{len(blocks)}个块")
    for i, block in enumerate(blocks[:5]):  # 只显示前 5 个块
        if 'lines' in block:
            for line in block['lines'][:3]:
                text = ''.join([span['text'] for span in line['spans']])
                print(f"  {text}")
except Exception as e:
    print(f"错误：{e}")

doc.close()

print("\n" + "=" * 80)
print("提取完成")
print("=" * 80)
