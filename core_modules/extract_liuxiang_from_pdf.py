#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取《仪度六壬选日要诀》注解中的六相六替理论
"""

import fitz  # PyMuPDF
import os

pdf_files = [
    r'd:\新建文件夹\仪度六壬择日\yiduluren\1《仪度六壬选日要诀》注解 1.pdf',
    r'd:\新建文件夹\仪度六壬择日\yiduluren\2《仪度六壬选日要诀》注解 2.pdf'
]

keywords = ['六相', '六替', '化气', '番化', '三元', '斗首']

print('=' * 80)
print('提取《仪度六壬选日要诀》中的六相六替理论')
print('=' * 80)

for pdf_path in pdf_files:
    if not os.path.exists(pdf_path):
        print(f"\n文件不存在：{pdf_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"读取：{os.path.basename(pdf_path)}")
    print('='*80)
    
    doc = fitz.open(pdf_path)
    
    found_content = []
    
    # 遍历所有页面
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # 检查是否包含关键词
        for keyword in keywords:
            if keyword in text:
                print(f"\n【第{page_num + 1}页】包含关键词：{keyword}")
                print('-' * 80)
                
                # 提取相关段落
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if any(kw in line for kw in keywords):
                        # 打印该行及前后各 2 行
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        for j in range(start, end):
                            marker = ">>>" if j == i else "   "
                            print(f"{marker} {lines[j]}")
                
                found_content.append({
                    'page': page_num + 1,
                    'keyword': keyword,
                    'content': text
                })
                break  # 每个页面只处理一次
    
    doc.close()
    
    if not found_content:
        print("\n未找到六相六替相关内容")
    else:
        print(f"\n共找到 {len(found_content)} 个相关页面")

print('\n' + '=' * 80)
print('提取完成')
print('=' * 80)
