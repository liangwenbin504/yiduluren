#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取 PDF 第 340-360 页，查找鬼墓课
"""

import fitz

pdf_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\白话大六壬全书（有目录）.pdf'
doc = fitz.open(pdf_path)

print("=" * 80)
print("搜索第 340-360 页中包含'鬼'或'墓'的页面")
print("=" * 80)

found_keywords = []

for page_num in range(339, 361):  # 340-360 页
    if page_num < len(doc):
        page = doc[page_num]
        text = page.get_text()
        
        # 检查关键词
        if '鬼墓' in text:
            found_keywords.append((page_num + 1, '鬼墓', len(text)))
            print(f"\n✓ 第{page_num + 1}页找到'鬼墓'，文本长度：{len(text)}")
        elif '鬼' in text and '墓' in text:
            found_keywords.append((page_num + 1, '鬼 + 墓', len(text)))
            print(f"\n✓ 第{page_num + 1}页找到'鬼'和'墓'，文本长度：{len(text)}")

doc.close()

if found_keywords:
    print("\n" + "=" * 80)
    print(f"共找到{len(found_keywords)}页相关内容")
    print("=" * 80)
    
    # 提取第一页的详细内容
    first_page = found_keywords[0][0]
    print(f"\n提取第{first_page}页详细内容：")
    print("=" * 80)
    
    doc2 = fitz.open(pdf_path)
    page = doc2[first_page - 1]
    text = page.get_text()
    print(text)
    print("=" * 80)
    doc2.close()
else:
    print("\n未找到包含'鬼墓'的页面")
