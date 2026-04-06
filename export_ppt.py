#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT 文档导出模块

功能：
1. 基于模板生成 PPT 文档
2. 支持自定义标题、坐山、向山、四柱信息
3. 支持添加日期列表和评价文本
4. 支持导出为 PPTX 格式
"""

import os
import sys
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def export_ppt_document(export_data):
    """
    导出 PPT 文档
    
    参数:
        export_data: 导出数据字典
            - title: 标题
            - mountain: 坐山
            - xiangshan: 向山
            - four_pillars: 四柱信息
            - daliuren_data: 大六壬数据
            - dates: 日期列表
            - keti_list: 课格列表
            - evaluation: 评价文本
            - template_path: 模板文件路径（可选）
    
    返回:
        dict: {success: bool, file_path: str, filename: str, error: str}
    """
    try:
        # 验证必要参数
        if not export_data:
            return {'success': False, 'error': '未提供导出数据'}
        
        title = export_data.get('title', '擇日課單')
        mountain = export_data.get('mountain', '')
        xiangshan = export_data.get('xiangshan', '')
        four_pillars = export_data.get('four_pillars', {})
        daliuren_data = export_data.get('daliuren_data', {})
        dates = export_data.get('dates', [])
        keti_list = export_data.get('keti_list', [])
        evaluation = export_data.get('evaluation', '')
        template_path = export_data.get('template_path', '')
        
        # 使用模板文件或创建新的PPT文档
        if template_path and os.path.exists(template_path):
            print(f"使用模板文件: {template_path}")
            prs = Presentation(template_path)
        else:
            print("使用默认模板创建新文档")
            prs = Presentation()
        
        # 清理现有幻灯片（保留模板样式）
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]
        
        # 确保有可用的幻灯片布局
        def get_layout(prs, layout_idx):
            """获取幻灯片布局，如果索引不存在则使用第一个可用布局"""
            if len(prs.slide_layouts) > layout_idx:
                return prs.slide_layouts[layout_idx]
            elif len(prs.slide_layouts) > 0:
                return prs.slide_layouts[0]
            else:
                # 如果没有布局，创建一个默认的
                from pptx.enum.shapes import MSO_SHAPE_TYPE
                from pptx.oxml.xmlchemy import OxmlElement
                
                # 创建一个新的幻灯片布局
                slide_layout = prs.slide_layouts.add_slide_layout()
                return slide_layout
        
        # ========== 第一页：标题页 ==========
        slide_layout = get_layout(prs, 0)  # 标题幻灯片
        slide = prs.slides.add_slide(slide_layout)
        
        # 设置标题
        title_shape = slide.shapes.title
        title_shape.text = title
        title_shape.text_frame.paragraphs[0].font.size = Pt(32)
        title_shape.text_frame.paragraphs[0].font.bold = True
        
        # 设置副标题
        subtitle_shape = slide.shapes.placeholders[1]
        subtitle_text = f"坐山：{mountain}\n向山：{xiangshan}"
        if four_pillars:
            nian = four_pillars.get('year', '')
            yue = four_pillars.get('month', '')
            ri = four_pillars.get('day', '')
            shi = four_pillars.get('hour', '')
            subtitle_text += f"\n四柱：{nian} {yue} {ri} {shi}"
        subtitle_shape.text = subtitle_text
        subtitle_shape.text_frame.paragraphs[0].font.size = Pt(20)
        
        # ========== 第二页：六壬信息 ==========
        if daliuren_data:
            slide_layout = get_layout(prs, 1)  # 标题和内容
            slide = prs.slides.add_slide(slide_layout)
            
            title_shape = slide.shapes.title
            title_shape.text = '大六壬信息'
            
            content_shape = slide.shapes.placeholders[1]
            text_frame = content_shape.text_frame
            
            # 添加六壬数据
            if daliuren_data.get('score'):
                p = text_frame.add_paragraph()
                p.text = f"综合评分：{daliuren_data['score']}"
                p.font.size = Pt(16)
            
            if daliuren_data.get('shan') and daliuren_data.get('xiang'):
                p = text_frame.add_paragraph()
                p.text = f"山：{daliuren_data['shan']}，向：{daliuren_data['xiang']}"
                p.font.size = Pt(16)
            
            if daliuren_data.get('keti'):
                p = text_frame.add_paragraph()
                p.text = f"课体：{daliuren_data['keti']}"
                p.font.size = Pt(16)
            
            if daliuren_data.get('sanchuan'):
                sanchuan = daliuren_data['sanchuan']
                p = text_frame.add_paragraph()
                p.text = f"三传：{sanchuan.get('chuChuan', '')} → {sanchuan.get('zhongChuan', '')} → {sanchuan.get('moChuan', '')}"
                p.font.size = Pt(16)
        
        # ========== 第三页：课格信息 ==========
        if keti_list:
            slide_layout = get_layout(prs, 1)  # 标题和内容
            slide = prs.slides.add_slide(slide_layout)
            
            title_shape = slide.shapes.title
            title_shape.text = '课格信息'
            
            content_shape = slide.shapes.placeholders[1]
            text_frame = content_shape.text_frame
            
            for keti in keti_list:
                p = text_frame.add_paragraph()
                p.text = keti
                p.font.size = Pt(16)
        
        # ========== 第四页：日期列表 ==========
        if dates:
            slide_layout = get_layout(prs, 1)  # 标题和内容
            slide = prs.slides.add_slide(slide_layout)
            
            title_shape = slide.shapes.title
            title_shape.text = '吉日列表'
            
            content_shape = slide.shapes.placeholders[1]
            text_frame = content_shape.text_frame
            
            for i, date_info in enumerate(dates[:10], 1):  # 最多显示10个日期
                date_str = date_info.get('date', '')
                hour = date_info.get('hour', '')
                score = date_info.get('score', '')
                
                p = text_frame.add_paragraph()
                p.text = f"{i}. 日期：{date_str}，时辰：{hour}，评分：{score}"
                p.font.size = Pt(16)
        
        # ========== 第五页：评价文本 ==========
        if evaluation:
            slide_layout = get_layout(prs, 1)  # 标题和内容
            slide = prs.slides.add_slide(slide_layout)
            
            title_shape = slide.shapes.title
            title_shape.text = '综合评价'
            
            content_shape = slide.shapes.placeholders[1]
            content_shape.text = evaluation
            content_shape.text_frame.paragraphs[0].font.size = Pt(16)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{title}_{mountain}_{timestamp}.pptx"
        file_path = os.path.join(os.path.dirname(__file__), filename)
        
        # 保存PPT文件
        prs.save(file_path)
        
        return {
            'success': True,
            'file_path': file_path,
            'filename': filename
        }
        
    except ImportError as e:
        # 处理python-pptx库缺失的情况
        if 'pptx' in str(e):
            return {
                'success': False,
                'error': '缺少python-pptx库，请安装：pip install python-pptx',
                'detail': str(e)
            }
        return {
            'success': False,
            'error': f'导入模块失败：{str(e)}',
            'detail': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'导出PPT失败：{str(e)}',
            'detail': str(e)
        }

if __name__ == '__main__':
    # 测试PPT导出
    test_data = {
        'title': '安葬吉日',
        'mountain': '壬',
        'xiangshan': '丙',
        'four_pillars': {
            'year': '丙午',
            'month': '辛卯',
            'day': '己亥',
            'hour': '甲子'
        },
        'daliuren_data': {
            'score': 95,
            'shan': '壬',
            'xiang': '丙',
            'keti': '青龙返首',
            'sanchuan': {
                'chuChuan': '寅',
                'zhongChuan': '卯',
                'moChuan': '辰'
            }
        },
        'dates': [
            {'date': '2026-01-01', 'hour': '子时', 'score': 95},
            {'date': '2026-01-02', 'hour': '丑时', 'score': 90}
        ],
        'keti_list': ['青龙返首', '贵人到山'],
        'evaluation': '此日课格局优美，禄马贵人到山到向，为上等吉课。'
    }
    
    result = export_ppt_document(test_data)
    print(result)