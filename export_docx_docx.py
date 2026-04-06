#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档导出功能 - python-docx版本
参照完美模板.docx格式标准
"""

import os
import sys
import datetime
import traceback
from docx import Document
from docx.shared import Inches, Pt, Cm, Twips, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TEMPLATE_FONT_NAME = '李白赋诗游龙惊鸿'
FALLBACK_FONT_NAME = '楷体'
SEAL_IMAGE_NAME = 'seal.png'

def check_font_available(font_name):
    """检查字体是否可用"""
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-Command', f'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts" | Select-Object -ExpandProperty PSObject | Where-Object {{ $_.Value -like "*{font_name}*" }}'],
            capture_output=True, text=True, timeout=5
        )
        return font_name in result.stdout
    except:
        return False

FONT_NAME = TEMPLATE_FONT_NAME if check_font_available(TEMPLATE_FONT_NAME) else FALLBACK_FONT_NAME

def set_chinese_font(run, font_name=FONT_NAME, font_size=16):
    """设置中文字体"""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:eastAsia'), font_name)

def set_paragraph_format(para, alignment=WD_ALIGN_PARAGRAPH.RIGHT, 
                         first_line_indent=Cm(1.13), line_spacing=1.0):
    """设置段落格式"""
    para.alignment = alignment
    pf = para.paragraph_format
    if first_line_indent:
        pf.first_line_indent = first_line_indent
    pf.line_spacing = line_spacing

def add_styled_paragraph(doc, text, font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT,
                         first_line_indent=Cm(1.13), line_spacing=1.0):
    """添加带格式的段落"""
    para = doc.add_paragraph()
    run = para.add_run(text)
    set_chinese_font(run, FONT_NAME, font_size)
    set_paragraph_format(para, alignment, first_line_indent, line_spacing)
    return para

def find_seal_image():
    """查找印章图片"""
    script_dir = os.path.dirname(__file__)
    seal_path = os.path.join(script_dir, SEAL_IMAGE_NAME)
    if os.path.exists(seal_path):
        return seal_path
    
    extracted_path = os.path.join(script_dir, 'extracted_images', 'image1.png')
    if os.path.exists(extracted_path):
        return extracted_path
    
    return None

def add_inline_image_with_size(paragraph, image_path, width_cm=2.5, height_cm=2.5):
    """在段落中添加内联图片（指定大小）"""
    if not os.path.exists(image_path):
        print(f"⚠️ 印章图片不存在: {image_path}")
        return None
    
    run = paragraph.add_run()
    run.add_picture(image_path, width=Cm(width_cm), height=Cm(height_cm))
    return run

def export_docx_document(data):
    """导出择日课单为DOCX文档（参照完美模板格式）"""
    print("=" * 80)
    print("📄 开始导出文档（参照完美模板格式）...")
    print(f"📄 使用字体: {FONT_NAME}")
    print("=" * 80)
    
    try:
        title = data.get('title_type', data.get('title', '择日课单'))
        zuoshan = data.get('mountain', data.get('zuoshan', ''))
        xiangshan = data.get('xiangshan', '')
        
        four_pillars = data.get('four_pillars', {})
        year_pillar = four_pillars.get('year', '')
        month_pillar = four_pillars.get('month', '')
        day_pillar = four_pillars.get('day', '')
        hour_pillar = four_pillars.get('hour', '')
        
        daliuren_data = data.get('daliuren_data', {})
        yuejiang = daliuren_data.get('yueJiang', '')
        shichen = daliuren_data.get('shiChen', '')
        
        liuren_kege = ''
        if yuejiang or shichen:
            liuren_kege_parts = []
            if yuejiang:
                liuren_kege_parts.append(f'{yuejiang}将')
            if shichen:
                liuren_kege_parts.append(f'{shichen}时')
            liuren_kege = ' '.join(liuren_kege_parts)
        
        piyu = data.get('evaluation', '')
        piyu_lines = []
        if piyu:
            piyu_lines = [line.strip() for line in piyu.split('\n') if line.strip()]
        
        dates = data.get('dates', [])
        biji = ''
        if dates and len(dates) > 0:
            first_date = dates[0]
            date_str = first_date.get('date', '')
            hour_str = first_date.get('hour', '')
            score_str = first_date.get('score', '')
            if date_str:
                biji = f'参考日期：{date_str}'
                if hour_str:
                    biji += f' {hour_str}时'
                if score_str:
                    biji += f' 评分：{score_str}'
        
        diliishi = data.get('diliishi', '信林居士')
        date = datetime.datetime.now().strftime('%Y年%m月%d日')
        
        print(f"📌 导出数据 - 标题: {title}")
        
        print("📝 创建文档...")
        doc = Document()
        
        for section in doc.sections:
            section.page_width = Cm(27.94)
            section.page_height = Cm(21.59)
            section.orientation = WD_ORIENT.LANDSCAPE
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2)
            section.right_margin = Cm(2)
            section.header_distance = Cm(1.27)
            section.footer_distance = Cm(1.27)
        
        title_para = doc.add_paragraph()
        title_run = title_para.add_run(title)
        set_chinese_font(title_run, FONT_NAME, 24)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        add_styled_paragraph(doc, 
            "伏以，天地定位，山向合机；理气相通，福泽攸关。谨奉《穿山透地真传》之旨，依《仪度六壬选日要诀》之法，为孝眷择取立碑吉期，安妥先灵，庇荫后昆。",
            font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        if zuoshan and xiangshan:
            add_styled_paragraph(doc, f"山向：{zuoshan}山{xiangshan}向",
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        elif zuoshan:
            add_styled_paragraph(doc, f"山向：{zuoshan}山",
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        if year_pillar and month_pillar and day_pillar and hour_pillar:
            add_styled_paragraph(doc, 
                f"择取岁次{year_pillar}年{month_pillar}月{day_pillar}日{hour_pillar}时（干支：{year_pillar}年{month_pillar}月{day_pillar}日{hour_pillar}时）",
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        if liuren_kege:
            add_styled_paragraph(doc, f"六壬课格：{liuren_kege}",
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        if piyu_lines and len(piyu_lines) > 0:
            for line in piyu_lines:
                add_styled_paragraph(doc, line,
                    font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        elif piyu:
            add_styled_paragraph(doc, f"批语：{piyu}",
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        if biji:
            add_styled_paragraph(doc, biji,
                font_size=16, alignment=WD_ALIGN_PARAGRAPH.RIGHT)
        
        luokuan_para = doc.add_paragraph()
        luokuan_run = luokuan_para.add_run(f"{diliishi}沐手谨择")
        set_chinese_font(luokuan_run, FONT_NAME, 16)
        set_paragraph_format(luokuan_para, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=Cm(1.13))
        
        seal_path = find_seal_image()
        if seal_path:
            print(f"  - 添加印章图片: {seal_path}")
            seal_run = luokuan_para.add_run()
            seal_run.add_picture(seal_path, width=Cm(2.5), height=Cm(2.5))
        
        date_para = doc.add_paragraph()
        date_run = date_para.add_run(f"日期：岁次{date}榖旦 勒石")
        set_chinese_font(date_run, FONT_NAME, 16)
        set_paragraph_format(date_para, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=Cm(0.78))
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'择日课单_{timestamp}.docx'
        
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(downloads_dir):
            downloads_dir = os.path.dirname(__file__)
        output_path = os.path.join(downloads_dir, filename)
        
        print(f"  - 保存文档: {filename}")
        print(f"  - 保存路径: {output_path}")
        
        doc.save(output_path)
        
        print(f"✅ 文档导出成功: {filename}")
        
        return {
            'success': True,
            'file_path': os.path.abspath(output_path),
            'filename': filename
        }
        
    except Exception as e:
        print(f"❌ 文档导出失败: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    test_data = {
        'title_type': '立碑吉课',
        'mountain': '壬',
        'xiangshan': '丙',
        'four_pillars': {
            'year': '丙午',
            'month': '甲午',
            'day': '丙午',
            'hour': '甲午'
        },
        'daliuren_data': {
            'yueJiang': '巳',
            'shiChen': '午',
            'tianPan': {},
            'sike': [],
            'sanchuan': {}
        },
        'dates': [
            {
                'date': '2026-04-01',
                'hour': '午时',
                'score': '98'
            }
        ],
        'keti_list': ['元首课', '龙德课'],
        'evaluation': '此课大吉，主子孙昌盛，福禄双全。课体平稳，无大吉凶。'
    }
    
    result = export_docx_document(test_data)
    print(result)
