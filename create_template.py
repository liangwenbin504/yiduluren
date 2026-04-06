#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建模板文档
生成四柱、天地盘、四课、三传图片并嵌入到Word文档中
"""

import os
import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.shape import WD_INLINE_SHAPE_TYPE

from generate_images import generate_sizhu_image, generate_tiandi_image, generate_sike_image, generate_sanchuan_image

def set_paragraph_vertical(paragraph):
    """设置段落为竖排文字，确保字符直立"""
    pPr = paragraph._element.get_or_add_pPr()
    # 设置文字方向为垂直，字符保持直立
    textDirection = OxmlElement('w:textDirection')
    textDirection.set(qn('w:val'), 'tbRl')
    pPr.append(textDirection)
    # 设置东亚文字布局为垂直
    eastAsiaLayout = OxmlElement('w:eastAsiaLayout')
    eastAsiaLayout.set(qn('w:vertical'), '1')
    eastAsiaLayout.set(qn('w:ideographic'), '1')
    eastAsiaLayout.set(qn('w:hangingPunctuation'), '1')
    pPr.append(eastAsiaLayout)

def add_floating_image(doc, image_path, width, height, left, top):
    """添加浮动图片，允许用户自由调整位置和环绕方式"""
    from docx.oxml import parse_xml
    from docx.shared import Inches
    
    # 创建一个新的段落用于放置图片
    paragraph = doc.add_paragraph()
    
    # 添加图片作为嵌入式
    run = paragraph.add_run()
    inline_shape = run.add_picture(image_path, width=width, height=height)
    
    # 获取图片的 XML 元素
    inline = inline_shape._inline
    
    # 转换为浮动图片
    graphic = inline.graphic
    graphic_data = graphic.graphicData
    pic = graphic_data.get_or_add_pic()
    
    # 设置图片属性，允许自由编辑
    pic.nvPicPr.cNvPr.id = 0
    pic.nvPicPr.cNvPr.name = "Picture"
    pic.nvPicPr.cNvPr.descr = "可编辑图片"
    
    # 移除锁定，允许用户编辑
    if pic.nvPicPr.cNvPicPr:
        pic.nvPicPr.cNvPicPr.clear()
    
    return inline_shape

def create_template():
    """
    创建模板文档
    """
    try:
        # 测试数据
        test_data = {
            'four_pillars': {'年': '丙午', '月': '辛卯', '日': '己亥', '时': '甲戌'},
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
        
        # 生成所有图片
        print("生成四柱图片...")
        sizhu_data = test_data['four_pillars']
        sizhu_image = generate_sizhu_image(sizhu_data)
        
        print("生成天地盘图片...")
        tian_pan = test_data['daliuren_data']['tianPan']
        tiandi_image = generate_tiandi_image(tian_pan)
        
        print("生成四课图片...")
        sike = test_data['daliuren_data']['sike']
        sike_image = generate_sike_image(sike)
        
        print("生成三传图片...")
        sanchuan = test_data['daliuren_data']['sanchuan']
        sanchuan_image = generate_sanchuan_image(sanchuan)
        
        # 创建新文档
        doc = Document()
        
        # 设置页面为 A4 横向
        section = doc.sections[0]
        section.page_width = Cm(29.7)
        section.page_height = Cm(21)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
        
        # 设置页面背景色（浅黄色）
        sectPr = section._sectPr
        bg = OxmlElement('w:shd')
        bg.set(qn('w:val'), 'clear')
        bg.set(qn('w:color'), 'auto')
        bg.set(qn('w:fill'), 'FFFFCC')  # 浅黄色背景
        sectPr.append(bg)
        
        # 设置整个 section 的文字方向为竖排
        textDirection = OxmlElement('w:textDirection')
        textDirection.set(qn('w:val'), 'tbRl')
        sectPr.insert(0, textDirection)
        
        # 设置默认字体
        style = doc.styles['Normal']
        style.font.name = '楷体'
        style.font.size = Pt(14)
        style._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 1. 标题：顶部居中，竖排，无边框
        title = '擇日課單'
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # 设置标题为竖排
        set_paragraph_vertical(p)
        run = p.add_run(title)
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.name = '楷体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 添加空行
        doc.add_paragraph()
        
        # 2. 引言部分（竖排）
        p = doc.add_paragraph()
        set_paragraph_vertical(p)
        run = p.add_run('谨据《仪度六壬择日要诀》筛选此吉期：')
        run.font.size = Pt(15)  # 小三
        run.font.name = '楷体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 3. 添加可编辑图片（支持裁剪）
        # 先添加空行，让天盘位置更靠下
        for i in range(3):
            doc.add_paragraph()
        
        if tiandi_image:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # 设置段落间距，确保图片有足够空间
            p.space_before = Pt(12)
            p.space_after = Pt(12)
            run = p.add_run()
            # 保持天盘尺寸，但确保完整显示
            shape = run.add_picture(tiandi_image, width=Cm(10), height=Cm(10))
        
        # 添加空行作为分隔
        doc.add_paragraph()
        
        if sizhu_image:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # 添加图片作为可编辑对象，支持裁剪
            run = p.add_run()
            # 直接添加图片，确保Word将其识别为可裁剪对象
            run.add_picture(sizhu_image, width=Cm(5))
        
        # 添加空行作为分隔
        doc.add_paragraph()
        
        if sike_image:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(sike_image, width=Cm(5))
        
        # 添加空行作为分隔
        doc.add_paragraph()
        
        if sanchuan_image:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(sanchuan_image, width=Cm(5))
        
        # 4. 综合评价（精简到 500 字左右，竖排）
        evaluation = test_data.get('evaluation', '')
        if evaluation:
            # 截取前 500 字
            if len(evaluation) > 500:
                evaluation = evaluation[:500] + '...'
            
            p = doc.add_paragraph()
            set_paragraph_vertical(p)
            run = p.add_run('\n【综合评价】')
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.name = '楷体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
            
            p = doc.add_paragraph()
            set_paragraph_vertical(p)
            run = p.add_run(evaluation)
            run.font.size = Pt(15)  # 小三
            run.font.name = '楷体'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 5. 日期标注（当前系统日期，竖排）
        today = datetime.datetime.now()
        year_cn = str(today.year)
        month_cn = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'][today.month - 1]
        day_num = today.day
        if day_num <= 10:
            day_cn = '初' + ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][day_num - 1]
        elif day_num == 10:
            day_cn = '初十'
        elif day_num <= 19:
            day_cn = '十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九'][day_num - 11]
        elif day_num == 20:
            day_cn = '二十'
        elif day_num <= 29:
            day_cn = '二十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九'][day_num - 21]
        else:
            day_cn = '三十'
        
        p = doc.add_paragraph()
        set_paragraph_vertical(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f'公元{year_cn}年{month_cn}月{day_cn}日')
        run.font.size = Pt(15)  # 小三
        run.font.name = '楷体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 6. 添加真实印章图片（在日期上方）
        seal_image_path = os.path.join(os.path.dirname(__file__), '印章.png')
        if os.path.exists(seal_image_path):
            # 添加印章图片，居中对齐
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(seal_image_path, width=Cm(3), height=Cm(3))
        
        # 7. 落款信息（竖排）
        p = doc.add_paragraph()
        set_paragraph_vertical(p)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run('\n地理人：信林散道  谨择')
        run.font.size = Pt(15)  # 小三
        run.font.name = '楷体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
        
        # 保存文档（使用新文件名避免权限问题）
        output_path = os.path.join(os.path.dirname(__file__), '模板-006.docx')
        doc.save(output_path)
        
        print(f"✅ 模板文档创建成功：{output_path}")
        
        # 清理临时图片文件
        try:
            if sizhu_image:
                os.remove(sizhu_image)
            if tiandi_image:
                os.remove(tiandi_image)
            if sike_image:
                os.remove(sike_image)
            if sanchuan_image:
                os.remove(sanchuan_image)
        except:
            pass
        
        return output_path
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 创建模板文档失败：{e}")
        print(f"详细错误：{error_detail}")
        return None

if __name__ == '__main__':
    create_template()
