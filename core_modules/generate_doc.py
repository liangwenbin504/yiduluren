#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将未匹配课体清单转换为 DOC 格式文档
"""

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import json
import os

# 设置中文字体支持
from docx.oxml.ns import nsmap
nsmap['w'] = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def create_doc_document():
    """创建 DOC 格式文档"""
    
    doc = Document()
    
    # 设置文档样式
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(12)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    
    # 标题
    title = doc.add_heading('大六壬 64 课经未匹配课体清单', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 基本信息
    doc.add_heading('📋 基本信息', level=1)
    info_para = doc.add_paragraph()
    info_para.add_run('文档生成时间：').bold = True
    info_para.add_run('2026-03-15\n')
    info_para.add_run('系统版本：').bold = True
    info_para.add_run('v2.0.0（专业版）\n')
    info_para.add_run('数据来源：').bold = True
    info_para.add_run('data/64_ke_jing_accurate.json、data/720_ke_li_matched_pro.json\n')
    info_para.add_run('统计范围：').bold = True
    info_para.add_run('8640 个课例\n')
    info_para.add_run('匹配状态：').bold = True
    info_para.add_run('45/64 课体已匹配，19/64 课体待匹配')
    
    # 未匹配课体列表
    doc.add_heading('📊 未匹配课体完整列表（19 个）', level=1)
    
    # 分类标题
    doc.add_heading('一、需要天将系统配合的课体（8 个）', level=2)
    
    # 创建表格
    table1 = doc.add_table(rows=1, cols=5)
    table1.style = 'Table Grid'
    
    # 表头
    hdr_cells = table1.rows[0].cells
    headers = ['序号', '课体名称', '课经编号', '定义', '匹配难点']
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        hdr_cells[i].paragraphs[0].runs[0].bold = True
    
    # 第一类课体数据
    ke_ti_data_1 = [
        (1, '龙德课', '42', '太岁月将乘贵人发用', '需要天将贵人判断，太岁月将配合'),
        (2, '夹克课', '61', '用神被天将地盘同克', '需要十二天将属性及克战判断'),
        (3, '殃咎课', '28', '三传递克日，神将克战，或干支乘墓', '需要天将克战、墓神判断'),
        (4, '灾厄课', '37', '丧魄、游魂、伏殃、病符等凶煞发用', '需要天将凶煞系统'),
        (5, '天祸课', '40', '四立前一日绝辰加立辰，或立辰加绝辰', '需要节气、天鬼神煞判断'),
        (6, '伏殃课', '51', '天鬼临日辰发用或临年命发用', '需要天鬼神煞、年命判断'),
        (7, '死绝课', '52', '日干之死气加于本身之绝乡', '需要死气神煞、绝乡判断'),
        (8, '乘轩落马课', '33', '轩盖课 + 驿马', '需要驿马神煞判断'),
    ]
    
    for data in ke_ti_data_1:
        row_cells = table1.add_row().cells
        for i, cell_data in enumerate(data):
            row_cells[i].text = str(cell_data)
    
    doc.add_paragraph()  # 空行
    
    # 第二类课体
    doc.add_heading('二、需要特殊条件判断的课体（11 个）', level=2)
    
    table2 = doc.add_table(rows=1, cols=5)
    table2.style = 'Table Grid'
    
    # 表头
    hdr_cells = table2.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        hdr_cells[i].paragraphs[0].runs[0].bold = True
    
    # 第二类课体数据
    ke_ti_data_2 = [
        (9, '一旬周遍课', '54', '旬尾在干上，旬首在支上', '需要旬空完整判断'),
        (10, '三六相呼课', '63', '三传三合，支上神与中神相合', '需要三合局、六合判断'),
        (11, '交车课', '62', '干上神与支合，支上神与干合', '需要六合关系判断'),
        (12, '亨通课', '27', '三传递生，或干支互生俱生', '需要三传递生判断'),
        (13, '别责课', '13', '四课中有两课相同，取别支为用', '需要四课不备判断'),
        (14, '绝嗣课', '17', '四课不备，且无生气', '需要四课不备、生气判断'),
        (15, '芜淫课', '19', '四课不备且上下有克，或干支交克', '需要四课不备判断'),
        (16, '解离课', '55', '夫妻行年上下相冲克，或干支互克上神', '需要行年计算'),
        (17, '索债课', '64', '三传合局脱气，生起干支上财神', '需要脱气、财神判断'),
        (18, '遥克课', '11', '四课无克贼，取遥相克者为用', '需要遥克法起课判断'),
        (19, '六阳格', '45', '六阳数足，事须公用', '已部分实现，需完善'),
    ]
    
    for data in ke_ti_data_2:
        row_cells = table2.add_row().cells
        for i, cell_data in enumerate(data):
            row_cells[i].text = str(cell_data)
    
    doc.add_page_break()
    
    # 分类统计
    doc.add_heading('📈 分类统计', level=1)
    
    doc.add_heading('按匹配难度分类', level=2)
    table3 = doc.add_table(rows=1, cols=4)
    table3.style = 'Table Grid'
    
    hdr_cells = table3.rows[0].cells
    difficulty_headers = ['难度等级', '课体数量', '占比', '说明']
    for i, header in enumerate(difficulty_headers):
        hdr_cells[i].text = header
        hdr_cells[i].paragraphs[0].runs[0].bold = True
    
    difficulty_data = [
        ('高难度', '8 个', '42.1%', '需要天将系统'),
        ('中难度', '7 个', '36.8%', '需要特殊神煞'),
        ('低难度', '4 个', '21.1%', '已部分实现或简单条件'),
    ]
    
    for data in difficulty_data:
        row_cells = table3.add_row().cells
        for i, cell_data in enumerate(data):
            row_cells[i].text = cell_data
    
    doc.add_paragraph()
    
    # 按课体类型分类
    doc.add_heading('按课体类型分类', level=2)
    table4 = doc.add_table(rows=1, cols=2)
    table4.style = 'Table Grid'
    
    hdr_cells = table4.rows[0].cells
    type_headers = ['类型', '课体名称']
    for i, header in enumerate(type_headers):
        hdr_cells[i].text = header
        hdr_cells[i].paragraphs[0].runs[0].bold = True
    
    type_data = [
        ('凶格课', '6 个：灾厄课、天祸课、伏殃课、死绝课、夹克课、殃咎课'),
        ('特殊课', '6 个：一旬周遍课、三六相呼课、交车课、解离课、索债课、六阳格'),
        ('九宗门变体', '4 个：亨通课、绝嗣课、芜淫课、遥克课'),
        ('吉格课', '2 个：龙德课、乘轩落马课'),
        ('九宗门', '1 个：别责课'),
    ]
    
    for data in type_data:
        row_cells = table4.add_row().cells
        row_cells[0].text = data[0]
        row_cells[1].text = data[1]
    
    doc.add_page_break()
    
    # 后续改进建议
    doc.add_heading('🎯 后续改进建议', level=1)
    
    doc.add_heading('优先级 1：完善天将系统（可匹配 8 个课体）', level=2)
    p = doc.add_paragraph()
    p.add_run('1. 十二天将详细属性\n').bold = True
    p.add_run('   - 五行属性\n   - 吉凶特性\n   - 基本含义\n\n')
    p.add_run('2. 天将克战判断\n').bold = True
    p.add_run('   - 天将相生相克\n   - 天将与地盘关系\n\n')
    p.add_run('3. 特殊神煞\n').bold = True
    p.add_run('   - 天鬼、丧魄、游魂、病符\n   - 死气、月厌等\n\n')
    p.add_run('预期效果：').bold = True
    p.add_run('匹配率提升至 85%+（53/64）')
    
    doc.add_heading('优先级 2：完善特殊条件（可匹配 7 个课体）', level=2)
    p = doc.add_paragraph()
    p.add_run('1. 旬空系统\n').bold = True
    p.add_run('   - 完整旬空计算\n   - 旬首旬尾判断\n\n')
    p.add_run('2. 行年计算\n').bold = True
    p.add_run('   - 年支行年\n   - 行年冲克判断\n\n')
    p.add_run('3. 三合六合\n').bold = True
    p.add_run('   - 三合局完整判断\n   - 六合关系应用\n\n')
    p.add_run('4. 四立日判断\n').bold = True
    p.add_run('   - 立春、立夏、立秋、立冬\n   - 绝辰判断\n\n')
    p.add_run('预期效果：').bold = True
    p.add_run('匹配率提升至 95%+（61/64）')
    
    doc.add_heading('优先级 3：完善四课不备判断（可匹配 4 个课体）', level=2)
    p = doc.add_paragraph()
    p.add_run('1. 四课不备判断\n').bold = True
    p.add_run('   - 别责课\n   - 绝嗣课\n   - 芜淫课\n\n')
    p.add_run('2. 脱气财神\n').bold = True
    p.add_run('   - 索债课\n\n')
    p.add_run('预期效果：').bold = True
    p.add_run('匹配率接近 100%（64/64）')
    
    doc.add_page_break()
    
    # 技术说明
    doc.add_heading('📝 技术说明', level=1)
    
    doc.add_heading('当前匹配状态', level=2)
    p = doc.add_paragraph()
    p.add_run('已匹配课体：').bold = True
    p.add_run('45 个（70.3%）\n')
    p.add_run('待匹配课体：').bold = True
    p.add_run('19 个（29.7%）\n')
    p.add_run('课例总数：').bold = True
    p.add_run('8640 个\n')
    p.add_run('课例匹配率：').bold = True
    p.add_run('100%')
    
    doc.add_heading('匹配数据来源', level=2)
    p = doc.add_paragraph()
    p.add_run('课经数据：').bold = True
    p.add_run('data/64_ke_jing_accurate.json\n')
    p.add_run('课例数据：').bold = True
    p.add_run('data/720_ke_li_matched_pro.json\n')
    p.add_run('匹配工具：').bold = True
    p.add_run('batch_match_pro.py\n')
    p.add_run('判断模块：').bold = True
    p.add_run('src/engine/ke_ti_judge_pro.py')
    
    doc.add_heading('验证方法', level=2)
    code_text = """
import json

# 加载数据
ke_jing = json.load(open('data/64_ke_jing_accurate.json', 'r', encoding='utf-8'))
matched_pro = json.load(open('data/720_ke_li_matched_pro.json', 'r', encoding='utf-8'))

# 获取所有课体名称
all_names = [v['ke_name'] for v in ke_jing['courses'].values()]

# 获取已匹配课体名称
matched_names = set()
for ke in matched_pro.values():
    matched_names.update(ke.get('matched_ke_jing', []))

# 计算未匹配课体
unmatched = [n for n in all_names if n not in matched_names]

print(f"未匹配课体：{len(unmatched)}个")
for i, name in enumerate(sorted(unmatched), 1):
    print(f"{i}. {name}")
"""
    doc.add_paragraph(code_text, style='No Spacing')
    
    # 页脚
    doc.add_page_break()
    footer_para = doc.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_para.add_run('文档结束\n\n')
    footer_run.bold = True
    footer_run = footer_para.add_run('生成工具：仪度六壬排盘系统 v2.0.0\n')
    footer_run = footer_para.add_run('文档格式：DOC（Microsoft Word）\n')
    footer_run = footer_para.add_run('保存路径：docs/未匹配课体清单_19 个.docx\n')
    footer_run = footer_para.add_run('最后更新：2026-03-15')
    
    # 保存文档
    output_path = os.path.join('docs', '未匹配课体清单_19 个.docx')
    doc.save(output_path)
    print(f"✅ DOC 文档已成功生成：{output_path}")
    
    return output_path


if __name__ == '__main__':
    create_doc_document()
