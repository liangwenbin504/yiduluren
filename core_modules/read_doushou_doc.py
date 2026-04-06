#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取斗首择日秘本 Word 文档
"""

try:
    from docx import Document
    import os
    
    doc_path = "斗首择日秘本 word 下载.doc"
    
    if os.path.exists(doc_path):
        doc = Document(doc_path)
        
        print("=" * 70)
        print("斗首择日秘本内容")
        print("=" * 70)
        
        full_text = ""
        for i, para in enumerate(doc.paragraphs, 1):
            text = para.text.strip()
            if text:
                print(f"{i}. {text}")
                full_text += text + "\n"
        
        # 保存到文本文件
        with open("斗首择日秘本内容.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"\n已保存到：斗首择日秘本内容.txt")
    else:
        print(f"文件不存在：{doc_path}")
        
except ImportError:
    print("未安装 python-docx，请先安装：pip install python-docx")
except Exception as e:
    print(f"读取失败：{e}")
    print("尝试使用其他方法读取...")
