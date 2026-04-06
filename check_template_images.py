#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查模板文件的图片布局
"""

from docx import Document

# 打开模板文件
doc = Document('模板-003.docx')

print('=== 模板-003.docx 图片分析 ===')
print('内联图片数:', len(doc.inline_shapes))

for i, shape in enumerate(doc.inline_shapes):
    print(f'图片{i}: 类型={shape.type}, 宽度={shape.width}, 高度={shape.height}')

# 复制模板-003.docx到模板-006.docx
import shutil
shutil.copy2('模板-003.docx', '模板-006.docx')
print('\n已将模板-003.docx复制为模板-006.docx')
