#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建符合要求的新模板文件
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def set_page_background(doc, color='FFFFE0'):
    """设置页面背景为淡黄色"""
    for section in doc.sections:
        # 获取sectPr元素
        sectPr = section._sectPr
        
        # 创建背景元素
        bg = OxmlElement('w:bg')
        bg.set(qn('w:color'), color)
        bg.set(qn('w:fill'), color)
        
        # 添加到sectPr
        sectPr.append(bg)

def set_page_border(doc, border_width=24):
    """设置页面边框为双线设计，外粗内细"""
    for section in doc.sections:
        sectPr = section._sectPr
        
        # 创建页面边框元素
        pgBorders = OxmlElement('w:pgBorders')
        pgBorders.set(qn('w:offsetFrom'), 'page')
        
        # 为四个边添加双线边框
        for border_name in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'double')  # 双线
            border.set(qn('w:sz'), str(border_width))  # 粗线宽度
            border.set(qn('w:space'), '24')  # 间距
            border.set(qn('w:color'), '000000')  # 黑色
            pgBorders.append(border)
        
        # 添加到sectPr
        sectPr.append(pgBorders)

def set_paragraph_vertical(paragraph):
    """设置段落为竖排文字"""
    pPr = paragraph._element.get_or_add_pPr()
    textDirection = OxmlElement('w:textDirection')
    textDirection.set(qn('w:val'), 'tbRl')  # 从右到左竖排
    pPr.append(textDirection)

def set_run_font(run, font_name='李白赋诗游龙惊鸿', font_size=16):
    """设置文本字体"""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    # 设置东亚字体
    r = run._element.get_or_add_rPr()
    rFonts = r.get_or_add_rFonts()
    rFonts.set(qn('w:eastAsia'), font_name)

def add_paragraph_with_style(doc, text, font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT, vertical=True):
    """添加带样式的段落"""
    paragraph = doc.add_paragraph()
    paragraph.alignment = alignment
    
    if vertical:
        set_paragraph_vertical(paragraph)
    
    run = paragraph.add_run(text)
    set_run_font(run, font_size=font_size)
    
    return paragraph

def create_template():
    """创建新模板"""
    doc = Document()
    
    # 设置页面背景为淡黄色
    set_page_background(doc, 'FFFFE0')
    
    # 设置页面边框为双线设计
    set_page_border(doc, border_width=24)
    
    # 设置页面边距
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    
    # 添加标题
    title = add_paragraph_with_style(doc, '开业课单', font_size=46, alignment=WD_ALIGN_PARAGRAPH.CENTER)
    
    # 添加开头固定文本
    intro = add_paragraph_with_style(doc, 
        '伏以，天地定位，山向合机；理气相通，福泽攸关。谨奉《穿山透地真传》之旨，依《仪度六壬选日要诀》之法，为孝眷择取立碑吉期，安妥先灵，庇荫后昆。',
        font_size=16)
    
    # 添加仙命信息（占位符）
    xianming = add_paragraph_with_style(doc, '仙命：{{仙命}}', font_size=16)
    
    # 添加山向信息（占位符）
    shanxiang = add_paragraph_with_style(doc, '山向：{{山向}}', font_size=16)
    
    # 添加来龙信息（占位符）
    lailong = add_paragraph_with_style(doc, '来龙：{{来龙}}', font_size=16)
    
    # 添加四柱信息（占位符）
    sizhu = add_paragraph_with_style(doc, '择取岁次{{四柱}}', font_size=16)
    
    # 添加六壬课格（占位符）
    liuren = add_paragraph_with_style(doc, '六壬课格：{{六壬课格}}', font_size=16)
    
    # 添加批语内容（占位符）
    piyu = add_paragraph_with_style(doc, '批语：{{批语}}', font_size=16)
    
    # 添加避忌事宜（占位符）
    biji = add_paragraph_with_style(doc, '避忌事宜：{{避忌}}', font_size=16)
    
    # 添加地理师落款（占位符）
    luokuan = add_paragraph_with_style(doc, '{{地理师}}沐手谨择', font_size=16)
    
    # 添加印章图片占位符
    seal = add_paragraph_with_style(doc, '[印章]', font_size=16, alignment=WD_ALIGN_PARAGRAPH.CENTER)
    
    # 添加日期落款（占位符）
    date = add_paragraph_with_style(doc, '日期：岁次{{日期}}榖旦 勒石', font_size=16)
    
    # 保存模板
    template_path = os.path.join(os.path.dirname(__file__), '新模板.docx')
    doc.save(template_path)
    print(f"✅ 新模板已创建：{template_path}")
    
    return template_path

if __name__ == '__main__':
    create_template()
