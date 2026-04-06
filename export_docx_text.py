#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""严格按照要求导出DOCX文件的文本内容"""

from docx import Document
import os

def export_docx_text(input_path, output_path):
    """
    严格按照DOCX文件的格式导出文本
    
    Args:
        input_path: 输入DOCX文件路径
        output_path: 输出文本文件路径
    """
    try:
        doc = Document(input_path)
        
        text_content = []
        
        # 遍历文档中的所有段落
        for paragraph in doc.paragraphs:
            # 严格按照原文格式添加段落
            text = paragraph.text
            if text.strip():
                text_content.append(text)
            else:
                # 保留空行
                text_content.append('')
        
        # 遍历文档中的所有表格
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_text.append(cell_text)
                if row_text:
                    text_content.append('\t'.join(row_text))
                else:
                    text_content.append('')
        
        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_content))
        
        print(f"文本内容已严格按照要求导出至: {output_path}")
        return True
        
    except Exception as e:
        print(f"导出文本时出错: {e}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "文字排版.docx")
    output_file = os.path.join(base_dir, "文字排版.txt")
    
    if os.path.exists(input_file):
        print(f"正在处理文件: {input_file}")
        export_docx_text(input_file, output_file)
    else:
        print(f"找不到输入文件: {input_file}")
