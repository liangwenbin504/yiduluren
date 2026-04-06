#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找包含竖排布局的模板文件
"""

import os
from docx import Document

# 查找所有模板文件
template_files = []
for file in os.listdir('.'):
    if '模板' in file and file.endswith('.docx'):
        template_files.append(file)

print('找到的模板文件:')
for f in template_files:
    print(f'  - {f}')

# 检查每个模板文件的内容
for template_file in template_files:
    print(f'\n=== 检查 {template_file} ===')
    try:
        doc = Document(template_file)
        print(f'段落数: {len(doc.paragraphs)}')
        print(f'表格数: {len(doc.tables)}')
        print(f'内联图片数: {len(doc.inline_shapes)}')
        
        # 显示前几个段落
        print('前5个段落:')
        for i, para in enumerate(doc.paragraphs[:5]):
            text = para.text.strip()
            if text:
                print(f'  段落{i}: {text[:50]}')
            else:
                print(f'  段落{i}: [空]')
                
    except Exception as e:
        print(f'错误: {e}')
