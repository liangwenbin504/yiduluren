#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建竖排布局的模板文件
"""

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# 创建新文档
doc = Document()

# 设置页面为 A4 纵向
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(3)
section.right_margin = Cm(3)

# 设置页面背景色（浅黄色）
sectPr = section._sectPr
bg = OxmlElement('w:shd')
bg.set(qn('w:val'), 'clear')
bg.set(qn('w:color'), 'auto')
bg.set(qn('w:fill'), 'FFFFCC')  # 浅黄色背景
sectPr.append(bg)

# 设置整个 section 的文字方向为竖排（从右到左）
textDirection = OxmlElement('w:textDirection')
textDirection.set(qn('w:val'), 'tbRl')  # tbRl 表示从上到下，从右到左
sectPr.insert(0, textDirection)

# 添加红色边框
pgBorders = OxmlElement('w:pgBorders')
for edge in ('top', 'left', 'bottom', 'right'):
    edge_elem = OxmlElement(f'w:{edge}')
    edge_elem.set(qn('w:val'), 'single')
    edge_elem.set(qn('w:sz'), '8')  # 边框宽度
    edge_elem.set(qn('w:space'), '0')
    edge_elem.set(qn('w:color'), 'FF0000')  # 红色边框
    pgBorders.append(edge_elem)
sectPr.append(pgBorders)

# 设置默认字体
style = doc.styles['Normal']
style.font.name = '楷体'
style.font.size = Pt(14)
style._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 辅助函数：设置段落为竖排
def set_paragraph_vertical(paragraph):
    """设置段落为竖排文字"""
    pPr = paragraph._element.get_or_add_pPr()
    # 设置文字方向为垂直，从右到左
    textDirection = OxmlElement('w:textDirection')
    textDirection.set(qn('w:val'), 'tbRl')
    pPr.append(textDirection)

# 1. 标题：安葬吉课（竖排，右侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
set_paragraph_vertical(p)
run = p.add_run('安葬吉课')
run.font.size = Pt(24)
run.font.bold = True
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 2. 引言和日期信息（竖排，右侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
set_paragraph_vertical(p)
run = p.add_run('谨据仪度六壬择日要诀筛选此吉期公元二O二六年十二月二十一日，阴历二O二六年十月十三日：')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 3. 四柱信息（竖排，右侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
set_paragraph_vertical(p)
run = p.add_run('四柱：丙午年 己亥月 己亥日 甲子时')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 4. 天地盘、四课、三传信息（竖排，中间）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_paragraph_vertical(p)
run = p.add_run('天地盘：\n四课：\n三传：')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 5. 评价内容（竖排，左侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
set_paragraph_vertical(p)
run = p.add_run('斗首法：吉，元辰得位，五行相生，主富贵荣华，家宅兴旺。\n演禽真法：平，觜(吉)。星宿平常，无大吉凶，宜守旧业。\n大六壬法：吉，壬山日柱禄马贵人到子山。\n综合评价：')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 6. 落款（竖排，左侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
set_paragraph_vertical(p)
run = p.add_run('地理人：信林散道  谨择')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 7. 日期（竖排，左侧）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
set_paragraph_vertical(p)
run = p.add_run('公元二O二六年三月二十日')
run.font.size = Pt(14)
run.font.name = '楷体'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')

# 保存为模板文件
template_path = '模板-006.docx'
doc.save(template_path)
print(f"✅ 已创建竖排布局模板：{template_path}")
print("模板包含：")
print("- 竖排文字布局（从右到左）")
print("- 浅黄色背景")
print("- 红色边框")
print("- 楷体字体")
print("- 完整的竖排布局结构")
