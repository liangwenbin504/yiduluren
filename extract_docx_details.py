# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_COLOR_INDEX, WD_PARAGRAPH_ALIGNMENT

def extract_docx_content(docx_path):
    doc = Document(docx_path)
    
    print("=== 文档详细信息 ===")
    print(f"段落数: {len(doc.paragraphs)}")
    print(f"表格数: {len(doc.tables)}")
    print(f"图片数: {len(doc.inline_shapes) + len(doc.sections)}")
    print()
    
    print("=== 文档内容（保留格式）===")
    
    for i, para in enumerate(doc.paragraphs):
        if not para.text.strip():
            print()
            continue
        
        # 提取段落格式信息
        alignment = ""
        if para.paragraph_format.alignment == WD_PARAGRAPH_ALIGNMENT.CENTER:
            alignment = "[居中]"
        elif para.paragraph_format.alignment == WD_PARAGRAPH_ALIGNMENT.RIGHT:
            alignment = "[右对齐]"
        elif para.paragraph_format.alignment == WD_PARAGRAPH_ALIGNMENT.LEFT:
            alignment = "[左对齐]"
        
        # 提取文本格式
        runs_info = []
        for run in para.runs:
            run_info = {
                "text": run.text,
                "bold": run.bold,
                "italic": run.italic,
                "underline": run.underline,
                "font_size": run.font.size.pt if run.font.size else None,
                "font_name": run.font.name,
                "color": run.font.color.rgb if run.font.color and run.font.color.rgb else None
            }
            runs_info.append(run_info)
        
        # 输出段落内容
        print(f"第{i+1}段{alignment}:")
        for run in runs_info:
            formatting = []
            if run["bold"]:
                formatting.append("粗体")
            if run["italic"]:
                formatting.append("斜体")
            if run["underline"]:
                formatting.append("下划线")
            if run["font_size"]:
                formatting.append(f"字体大小:{run['font_size']}pt")
            if run["font_name"]:
                formatting.append(f"字体:{run['font_name']}")
            
            format_str = "[" + ", ".join(formatting) + "]" if formatting else ""
            print(f"  {run['text']} {format_str}")
        print()
    
    # 处理表格
    if doc.tables:
        print("=== 表格内容 ===")
        for i, table in enumerate(doc.tables):
            print(f"表格 {i+1}:")
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                print(" | ".join(row_cells))
            print()

if __name__ == "__main__":
    docx_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\择日课单_20260330_091220.docx'
    extract_docx_content(docx_path)
