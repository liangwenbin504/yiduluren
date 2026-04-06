#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业PDF表单生成功能
使用reportlab库创建可编辑的PDF模板
"""

import os
import sys
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

# 注册中文字体
try:
    pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))
except:
    print("⚠️ 未找到simhei.ttf字体，使用默认字体")

def generate_tiandi_image(tian_pan):
    """
    生成天地盘图片
    """
    try:
        # 创建图片，尺寸为 300x300 像素
        img = Image.new('RGB', (300, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # 定义地盘顺序
        di_pan_order = [
            ['巳', '午', '未', '申'],
            ['辰', '', '', '酉'],
            ['卯', '', '', '戌'],
            ['寅', '丑', '子', '亥']
        ]
        
        # 单元格大小
        cell_size = 75
        
        # 绘制网格
        for i in range(5):
            # 横线
            draw.line([(0, i*cell_size), (300, i*cell_size)], fill='gray', width=1)
            # 竖线
            draw.line([(i*cell_size, 0), (i*cell_size, 300)], fill='gray', width=1)
        
        # 绘制文字
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype('simhei.ttf', 18)
        except:
            # 如果找不到字体，使用默认字体
            font = ImageFont.load_default()
        
        for row_idx, row_data in enumerate(di_pan_order):
            for col_idx, zhi in enumerate(row_data):
                if zhi:
                    # 获取天盘地支
                    tian_zhi = tian_pan.get(zhi, zhi)
                    
                    # 计算文字位置
                    x = col_idx * cell_size + cell_size // 2
                    y1 = row_idx * cell_size + cell_size // 3
                    y2 = row_idx * cell_size + 2 * cell_size // 3
                    
                    # 绘制地盘
                    draw.text((x, y1), zhi, fill='blue', font=font, anchor='mm')
                    # 绘制天盘
                    draw.text((x, y2), tian_zhi, fill='red', font=font, anchor='mm')
        
        # 保存图片
        temp_path = os.path.join(os.path.dirname(__file__), 'tiandi_temp_pdf.png')
        img.save(temp_path)
        return temp_path
    except Exception as e:
        print(f"⚠️ 生成天地盘图片失败: {e}")
        return None

def create_pdf_template():
    """
    创建可编辑的PDF模板
    """
    # 创建PDF文档
    template_path = os.path.join(os.path.dirname(__file__), 'template_form.pdf')
    doc = SimpleDocTemplate(template_path, pagesize=A4)
    
    # 样式
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.fontName = 'SimHei'
    title_style.fontSize = 24
    title_style.alignment = 1  # 居中
    
    normal_style = styles['Normal']
    normal_style.fontName = 'SimHei'
    normal_style.fontSize = 12
    
    # 内容列表
    story = []
    
    # 1. 标题
    title = Paragraph('择日課單', title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # 2. 引言
    intro = Paragraph('谨据《仪度六壬择日要诀》筛选此吉期：', normal_style)
    intro.alignment = 1
    story.append(intro)
    story.append(Spacer(1, 20))
    
    # 3. 四柱信息
    pillars_title = Paragraph('四柱信息', title_style)
    pillars_title.fontSize = 16
    story.append(pillars_title)
    
    # 四柱表格
    pillars_data = [
        ['年:', '', '月:', ''],
        ['日:', '', '时:', '']
    ]
    pillars_table = Table(pillars_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
    pillars_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, 1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(pillars_table)
    story.append(Spacer(1, 20))
    
    # 4. 天地盘
    tiandi_title = Paragraph('天地盘', title_style)
    tiandi_title.fontSize = 16
    story.append(tiandi_title)
    
    # 天地盘图片占位
    tiandi_placeholder = Table([['天地盘图片']], colWidths=[15*cm], rowHeights=[10*cm])
    tiandi_placeholder.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 1, colors.black)
    ]))
    story.append(tiandi_placeholder)
    
    # 月将时辰
    yuejiang_data = [['月将:', '', '时辰:', '']]
    yuejiang_table = Table(yuejiang_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
    yuejiang_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(yuejiang_table)
    story.append(Spacer(1, 20))
    
    # 5. 四课
    sike_title = Paragraph('四课', title_style)
    sike_title.fontSize = 16
    story.append(sike_title)
    
    # 四课表格
    sike_data = []
    for i in range(4):
        sike_data.append([f'课{i+1}上:', '', f'课{i+1}下:', ''])
    sike_table = Table(sike_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
    sike_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(sike_table)
    story.append(Spacer(1, 20))
    
    # 6. 三传
    sanchuan_title = Paragraph('三传', title_style)
    sanchuan_title.fontSize = 16
    story.append(sanchuan_title)
    
    # 三传表格
    sanchuan_data = []
    chuan_names = ['初传', '中传', '末传']
    for name in chuan_names:
        sanchuan_data.append([f'{name}:', ''])
    sanchuan_table = Table(sanchuan_data, colWidths=[3*cm, 12*cm])
    sanchuan_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(sanchuan_table)
    story.append(Spacer(1, 20))
    
    # 7. 综合评价
    evaluation_title = Paragraph('综合评价', title_style)
    evaluation_title.fontSize = 16
    story.append(evaluation_title)
    
    # 评价文本域
    evaluation_placeholder = Table([['综合评价内容']], colWidths=[15*cm], rowHeights=[6*cm])
    evaluation_placeholder.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('BOX', (0, 0), (0, 0), 1, colors.black)
    ]))
    story.append(evaluation_placeholder)
    story.append(Spacer(1, 20))
    
    # 8. 日期标注
    today = datetime.datetime.now()
    year_cn = str(today.year)
    month_cn = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'][today.month - 1]
    day_num = today.day
    if day_num <= 10:
        day_cn = '初' + ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][day_num - 1]
    elif day_num <= 20:
        day_cn = '十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][day_num - 11]
    elif day_num == 20:
        day_cn = '二十'
    else:
        if day_num <= 29:
            day_cn = '二十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九'][day_num - 21]
        elif day_num == 30:
            day_cn = '三十'
        else:
            day_cn = '三十一'
    
    date_text = f'公元{year_cn}年{month_cn}月{day_cn}日'
    date_para = Paragraph(date_text, normal_style)
    date_para.alignment = 1
    story.append(date_para)
    story.append(Spacer(1, 15))
    
    # 9. 落款信息
    signature_text = '地理人：信林散道  谨择'
    signature_para = Paragraph(signature_text, normal_style)
    signature_para.alignment = 1
    story.append(signature_para)
    
    # 生成PDF
    doc.build(story)
    return template_path

def export_pdf_form(data):
    """
    导出PDF表单
    """
    try:
        # 创建PDF文档
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'择日课单_{timestamp}.pdf'
        output_path = os.path.join(os.path.dirname(__file__), output_filename)
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        
        # 样式
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.fontName = 'SimHei'
        title_style.fontSize = 24
        title_style.alignment = 1  # 居中
        
        normal_style = styles['Normal']
        normal_style.fontName = 'SimHei'
        normal_style.fontSize = 12
        
        # 内容列表
        story = []
        
        # 1. 标题
        title = data.get('title', '擇日課單')
        title_para = Paragraph(title, title_style)
        story.append(title_para)
        story.append(Spacer(1, 20))
        
        # 2. 引言
        intro = Paragraph('谨据《仪度六壬择日要诀》筛选此吉期：', normal_style)
        intro.alignment = 1
        story.append(intro)
        story.append(Spacer(1, 20))
        
        # 3. 四柱信息
        four_pillars = data.get('four_pillars', {})
        pillars_title = Paragraph('四柱信息', title_style)
        pillars_title.fontSize = 16
        story.append(pillars_title)
        
        # 四柱表格
        pillars_data = [
            ['年:', four_pillars.get('year', ''), '月:', four_pillars.get('month', '')],
            ['日:', four_pillars.get('day', ''), '时:', four_pillars.get('hour', '')]
        ]
        pillars_table = Table(pillars_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        pillars_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, 1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(pillars_table)
        story.append(Spacer(1, 20))
        
        # 4. 天地盘
        daliuren_data = data.get('daliuren_data', {})
        tiandi_title = Paragraph('天地盘', title_style)
        tiandi_title.fontSize = 16
        story.append(tiandi_title)
        
        # 生成天地盘图片
        if daliuren_data:
            tian_pan = daliuren_data.get('tianPan', {})
            tiandi_image_path = generate_tiandi_image(tian_pan)
            if tiandi_image_path:
                # 添加图片
                from reportlab.platypus import Image as RLImage
                img = RLImage(tiandi_image_path, width=8*cm, height=8*cm)
                img.hAlign = 'CENTER'
                story.append(img)
                
                # 清理临时图片
                try:
                    os.remove(tiandi_image_path)
                except:
                    pass
        
        # 月将时辰
        yuejiang_data = [['月将:', daliuren_data.get('yueJiang', ''), '时辰:', daliuren_data.get('shiChen', '')]]
        yuejiang_table = Table(yuejiang_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        yuejiang_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(yuejiang_table)
        story.append(Spacer(1, 20))
        
        # 5. 四课
        sike_title = Paragraph('四课', title_style)
        sike_title.fontSize = 16
        story.append(sike_title)
        
        # 四课表格
        sike = daliuren_data.get('sike', [])
        sike_data = []
        for i, ke in enumerate(sike):
            sike_data.append([f'课{i+1}上:', ke.get('top', ''), f'课{i+1}下:', ke.get('bottom', '')])
        sike_table = Table(sike_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        sike_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(sike_table)
        story.append(Spacer(1, 20))
        
        # 6. 三传
        sanchuan_title = Paragraph('三传', title_style)
        sanchuan_title.fontSize = 16
        story.append(sanchuan_title)
        
        # 三传表格
        sanchuan = daliuren_data.get('sanchuan', {})
        sanchuan_data = []
        chuan_names = ['初传', '中传', '末传']
        for name in chuan_names:
            chuan = sanchuan.get(name, {})
            if chuan:
                text = f'{chuan.get("tiangan", "")}{chuan.get("dizhi", "")}'
                if chuan.get('liuqin'):
                    text += f'（{chuan.get("liuqin")}）'
                sanchuan_data.append([f'{name}:', text])
        sanchuan_table = Table(sanchuan_data, colWidths=[3*cm, 12*cm])
        sanchuan_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(sanchuan_table)
        story.append(Spacer(1, 20))
        
        # 7. 综合评价
        evaluation = data.get('evaluation', '')
        evaluation_title = Paragraph('综合评价', title_style)
        evaluation_title.fontSize = 16
        story.append(evaluation_title)
        
        # 评价内容
        evaluation_para = Paragraph(evaluation.replace('\n', '<br/>'), normal_style)
        evaluation_para.alignment = 0  # 左对齐
        story.append(evaluation_para)
        story.append(Spacer(1, 20))
        
        # 8. 日期标注
        today = datetime.datetime.now()
        year_cn = str(today.year)
        month_cn = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'][today.month - 1]
        day_num = today.day
        if day_num <= 10:
            day_cn = '初' + ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][day_num - 1]
        elif day_num <= 20:
            day_cn = '十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][day_num - 11]
        elif day_num == 20:
            day_cn = '二十'
        else:
            if day_num <= 29:
                day_cn = '二十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九'][day_num - 21]
            elif day_num == 30:
                day_cn = '三十'
            else:
                day_cn = '三十一'
        
        date_text = f'公元{year_cn}年{month_cn}月{day_cn}日'
        date_para = Paragraph(date_text, normal_style)
        date_para.alignment = 1
        story.append(date_para)
        story.append(Spacer(1, 15))
        
        # 9. 落款信息
        signature_text = '地理人：信林散道  谨择'
        signature_para = Paragraph(signature_text, normal_style)
        signature_para.alignment = 1
        story.append(signature_para)
        
        # 生成PDF
        doc.build(story)
        
        return {
            'success': True,
            'file_path': output_path,
            'filename': output_filename
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'detail': error_detail
        }

if __name__ == '__main__':
    # 创建PDF模板
    template_path = create_pdf_template()
    print(f"✅ PDF模板创建成功：{template_path}")
    
    # 测试导出
    test_data = {
        'title': '安葬吉日',
        'four_pillars': {'year': '丙午', 'month': '辛卯', 'day': '己亥', 'hour': '甲戌'},
        'daliuren_data': {
            'yueJiang': '卯',
            'shiChen': '子',
            'tianPan': {'子': '丑', '丑': '寅', '寅': '卯', '卯': '辰', '辰': '巳', '巳': '午', '午': '未', '未': '申', '申': '酉', '酉': '戌', '戌': '亥', '亥': '子'},
            'sike': [
                {'top': '申', 'bottom': '己'},
                {'top': '酉', 'bottom': '申'},
                {'top': '子', 'bottom': '亥'},
                {'top': '丑', 'bottom': '子'}
            ],
            'sanchuan': {
                '初传': {'tiangan': '辛', 'dizhi': '丑', 'liuqin': '兄弟'},
                '中传': {'tiangan': '壬', 'dizhi': '寅', 'liuqin': '官鬼'},
                '末传': {'tiangan': '癸', 'dizhi': '卯', 'liuqin': '官鬼'}
            }
        },
        'evaluation': '【传统课体断语】\n◆ 元首课（上吉）\n  总断：元首课，一上克下，事顺利成，男子占之尤吉。\n  断曰：天地得位，万物化生，凡事顺遂，谋为皆吉。'
    }
    
    result = export_pdf_form(test_data)
    if result['success']:
        print(f"✅ PDF表单导出成功：{result['file_path']}")
    else:
        print(f"❌ PDF表单导出失败：{result['error']}")
        print(f"详细错误：{result['detail']}")
