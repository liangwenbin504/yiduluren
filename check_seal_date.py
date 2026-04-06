#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查印章图片和日期段落
"""

import os
import glob
from docx import Document
from docx.oxml.ns import qn

def check_seal_and_date(file_path):
    """详细检查印章图片和日期段落"""
    print(f"\n{'='*80}")
    print(f"详细检查印章图片和日期段落")
    print(f"{'='*80}\n")
    
    try:
        doc = Document(file_path)
        
        # 1. 检查所有段落的内容
        print("【1. 所有段落内容】")
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if text:
                print(f"  段落 {i+1}: {text}")
            else:
                print(f"  段落 {i+1}: [空段落]")
        
        # 2. 详细检查印章图片
        print("\n【2. 印章图片检查】")
        seal_found = False
        for i, paragraph in enumerate(doc.paragraphs):
            for run in paragraph.runs:
                # 检查是否包含图片
                drawings = run._element.xpath('.//a:blip')
                if drawings:
                    seal_found = True
                    print(f"  ✅ 在段落 {i+1} 发现印章图片")
                    
                    # 检查图片属性
                    drawing = run._element.xpath('.//wp:inline')
                    if drawing:
                        inline = drawing[0]
                        extent = inline.find('.//a:ext', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                        if extent is not None:
                            cx = extent.get('cx')
                            cy = extent.get('cy')
                            print(f"    - 图片宽度：{int(cx) / 914400:.2f} 英寸")
                            print(f"    - 图片高度：{int(cy) / 914400:.2f} 英寸")
                        
                        # 检查图片是否浮于文字上方
                        docPr = inline.find('.//wp:docPr', namespaces={'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'})
                        if docPr is not None:
                            name = docPr.get('name')
                            descr = docPr.get('descr')
                            print(f"    - 图片名称：{name}")
                            print(f"    - 图片描述：{descr}")
        
        if not seal_found:
            print("  ⚠️ 未发现印章图片")
        
        # 3. 检查日期段落
        print("\n【3. 日期段落检查】")
        date_found = False
        for i, paragraph in enumerate(doc.paragraphs):
            if '榖旦' in paragraph.text or '勒石' in paragraph.text:
                date_found = True
                print(f"  ✅ 在段落 {i+1} 发现日期落款")
                print(f"    - 内容：{paragraph.text}")
                
                # 检查字体
                for run in paragraph.runs:
                    if run.text.strip():
                        font_name = run.font.name
                        font_size = run.font.size.pt if run.font.size else "未设置"
                        
                        # 检查东亚字体
                        rPr = run._element.get_or_add_rPr()
                        rFonts = rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
                        east_asia_font = None
                        if rFonts is not None:
                            east_asia_font = rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
                        
                        print(f"    - 字体：{font_name}, 东亚字体：{east_asia_font}, 大小：{font_size}pt")
                        break
        
        if not date_found:
            print("  ⚠️ 未发现日期落款")
        
        # 4. 检查印章图片位置
        print("\n【4. 印章图片位置检查】")
        if seal_found and date_found:
            seal_paragraph = None
            date_paragraph = None
            
            for i, paragraph in enumerate(doc.paragraphs):
                for run in paragraph.runs:
                    if run._element.xpath('.//a:blip'):
                        seal_paragraph = i
                        break
                
                if '榖旦' in paragraph.text or '勒石' in paragraph.text:
                    date_paragraph = i
            
            if seal_paragraph is not None and date_paragraph is not None:
                if seal_paragraph < date_paragraph:
                    print(f"  ✅ 印章图片在日期落款之前（印章段落：{seal_paragraph+1}，日期段落：{date_paragraph+1}）")
                else:
                    print(f"  ⚠️ 印章图片在日期落款之后（印章段落：{seal_paragraph+1}，日期段落：{date_paragraph+1}）")
                    print("     建议：印章图片应该在落款行与日期行之间")
        
        print(f"\n{'='*80}")
        print("检查完成")
        print(f"{'='*80}\n")
        
    except Exception as e:
        import traceback
        print(f"❌ 检查失败：{e}")
        print(traceback.format_exc())

if __name__ == '__main__':
    # 找到最新的导出文档
    output_dir = os.path.dirname(__file__)
    docx_files = glob.glob(os.path.join(output_dir, '择日课单_*.docx'))
    
    if docx_files:
        # 按修改时间排序，获取最新的文件
        latest_file = max(docx_files, key=os.path.getmtime)
        check_seal_and_date(latest_file)
    else:
        print("❌ 未找到导出的文档")
