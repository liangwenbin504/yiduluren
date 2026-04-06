#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取斗首择日秘本 Word 文档
"""

import os

# 获取当前工作目录
cwd = os.getcwd()
print(f"当前目录：{cwd}")

# 检查文件
doc_path = os.path.join(cwd, "斗首择日秘本 word 下载.doc")
print(f"检查路径：{doc_path}")
print(f"文件存在：{os.path.exists(doc_path)}")

# 列出所有 doc 文件
print("\n目录中的 doc 文件:")
for f in os.listdir(cwd):
    if f.endswith('.doc') or f.endswith('.docx'):
        print(f"  - {f}")
