#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""将DOCX文件转换为HTML格式，保留原文档的排版结构和样式"""

from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def docx_to_html(input_path, output_path):
    """
    将DOCX文件转换为HTML格式
    
    Args:
        input_path: 输入DOCX文件路径
        output_path: 输出HTML文件路径
    """
    try:
        doc = Document(input_path)
        
        html_content = []
        html_content.append('<!DOCTYPE html>')
        html_content.append('<html lang="zh-CN">')
        html_content.append('<head>')
        html_content.append('<meta charset="UTF-8">')
        html_content.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_content.append('<title>文档转换</title>')
        html_content.append('<style>')
        html_content.append('body { font-family: "微软雅黑", "SimHei", sans-serif; line-height: 1.6; margin: 20px; }')
        html_content.append('h1, h2, h3, h4, h5, h6 { color: #333; margin-top: 20px; margin-bottom: 10px; }')
        html_content.append('h1 { font-size: 24px; }')
        html_content.append('h2 { font-size: 20px; }')
        html_content.append('h3 { font-size: 18px; }')
        html_content.append('p { margin-bottom: 10px; }')
        html_content.append('table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
        html_content.append('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        html_content.append('th { background-color: #f2f2f2; font-weight: bold; }')
        html_content.append('tr:nth-child(even) { background-color: #f9f9f9; }')
        html_content.append('.center { text-align: center; }')
        html_content.append('.bold { font-weight: bold; }')
        html_content.append('</style>')
        html_content.append('</head>')
        html_content.append('<body>')
        
        # 处理段落
        for paragraph in doc.paragraphs:
            if not paragraph.text.strip():
                html_content.append('<p>&nbsp;</p>')
                continue
            
            # 检查段落样式
            text = paragraph.text
            style_name = paragraph.style.name
            
            if style_name.startswith('Heading'):
                level = style_name[-1]
                if level.isdigit():
                    html_content.append(f'<h{level}>{text}</h{level}>')
                else:
                    html_content.append(f'<p>{text}</p>')
            else:
                # 检查段落对齐方式
                alignment = paragraph.alignment
                align_class = ''
                if alignment == WD_ALIGN_PARAGRAPH.CENTER:
                    align_class = ' class="center"'
                
                # 处理段落中的运行
                runs_html = []
                for run in paragraph.runs:
                    run_text = run.text
                    if not run_text:
                        continue
                    
                    # 处理运行的样式
                    run_html = ''
                    if run.bold:
                        run_html = f'<span class="bold">{run_text}</span>'
                    else:
                        run_html = run_text
                    runs_html.append(run_html)
                
                paragraph_html = ''.join(runs_html)
                html_content.append(f'<p{align_class}>{paragraph_html}</p>')
        
        # 处理表格
        for table in doc.tables:
            html_content.append('<table>')
            
            # 处理表头
            for i, row in enumerate(table.rows):
                html_content.append('<tr>')
                for j, cell in enumerate(row.cells):
                    cell_text = cell.text.strip()
                    if i == 0:
                        html_content.append(f'<th>{cell_text}</th>')
                    else:
                        html_content.append(f'<td>{cell_text}</td>')
                html_content.append('</tr>')
            
            html_content.append('</table>')
        
        html_content.append('</body>')
        html_content.append('</html>')
        
        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        print(f"DOCX文件已成功转换为HTML格式，保存至: {output_path}")
        return True
        
    except Exception as e:
        print(f"转换过程中出错: {e}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "文字排版.docx")
    output_file = os.path.join(base_dir, "文字排版.html")
    
    if os.path.exists(input_file):
        print(f"正在处理文件: {input_file}")
        docx_to_html(input_file, output_file)
    else:
        print(f"找不到输入文件: {input_file}")
