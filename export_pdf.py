#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文档导出功能
使用HTML转PDF的方式实现
"""

import os
import sys
import datetime
import webbrowser
from PIL import Image, ImageDraw, ImageFont

# 尝试导入weasyprint，如果没有则使用替代方案
try:
    from weasyprint import HTML
    has_weasyprint = True
except ImportError:
    has_weasyprint = False

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

def export_pdf_document(data):
    """
    导出 PDF 格式文档
    """
    try:
        # 生成HTML内容
        html_content = generate_html_content(data)
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'择日课单_{timestamp}'
        output_path = os.path.join(os.path.dirname(__file__), output_filename)
        
        if has_weasyprint:
            # 使用weasyprint生成PDF
            pdf_path = output_path + '.pdf'
            HTML(string=html_content).write_pdf(pdf_path)
            
            return {
                'success': True,
                'file_path': pdf_path,
                'filename': output_filename + '.pdf'
            }
        else:
            # 生成HTML文件，让用户手动转换
            html_path = output_path + '.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 打开HTML文件
            webbrowser.open(f'file://{html_path}')
            
            return {
                'success': True,
                'file_path': html_path,
                'filename': output_filename + '.html',
                'message': '已生成HTML文件，请在浏览器中打开并使用浏览器的打印功能保存为PDF'
            }
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {
            'success': False,
            'error': str(e),
            'detail': error_detail
        }

def generate_html_content(data):
    """
    生成HTML内容
    """
    # 生成天地盘图片
    daliuren_data = data.get('daliuren_data', {})
    tiandi_image_path = None
    if daliuren_data:
        tian_pan = daliuren_data.get('tianPan', {})
        tiandi_image_path = generate_tiandi_image(tian_pan)
    
    # 准备数据
    title = data.get('title', '擇日課單')
    four_pillars = data.get('four_pillars', {})
    evaluation = data.get('evaluation', '')
    
    # 截取评价内容
    if len(evaluation) > 500:
        evaluation = evaluation[:500] + '...'
    
    # 生成日期
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
        # 处理21-31日
        if day_num <= 29:
            day_cn = '二十' + ['一', '二', '三', '四', '五', '六', '七', '八', '九'][day_num - 21]
        elif day_num == 30:
            day_cn = '三十'
        else:
            day_cn = '三十一'
    
    # 生成HTML
    tiandi_image_html = ''
    if tiandi_image_path:
        tiandi_image_html = f'<img src="{tiandi_image_path}" class="tiandi-image" alt="天地盘" />'
    
    yuejiang_shichen_html = ''
    if daliuren_data:
        yuejiang_shichen_html = f'<p>月将：{daliuren_data.get("yueJiang", "--")}  时辰：{daliuren_data.get("shiChen", "--")}</p>'
    
    seal_html = ''
    if os.path.exists('印章.png'):
        seal_html = '<img src="印章.png" class="seal-image" alt="印章" />'
    
    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>''' + title + '''</title>
        <style>
            body {
                font-family: "SimHei", "Arial", sans-serif;
                margin: 0;
                padding: 0;
                background-color: #FFFFCC;
            }
            .container {
                width: 210mm;
                height: 297mm;
                margin: 0 auto;
                background-color: white;
                padding: 20mm;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                box-sizing: border-box;
                writing-mode: vertical-rl;
                text-orientation: upright;
            }
            h1 {
                text-align: center;
                font-size: 24pt;
                font-weight: bold;
                margin-bottom: 30px;
                margin-top: 0;
            }
            .intro {
                text-align: center;
                font-size: 15pt;
                margin-bottom: 30px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section-title {
                font-size: 12pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 10px;
            }
            .table-container {
                margin: 20px 0;
            }
            table {
                width: auto;
                border-collapse: collapse;
                margin: 20px auto;
                writing-mode: horizontal-tb;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
                font-size: 10pt;
            }
            .tiandi-pan {
                text-align: center;
                margin: 20px 0;
            }
            .tiandi-image {
                max-width: 300px;
                height: auto;
            }
            .evaluation {
                font-size: 10pt;
                line-height: 1.5;
                text-align: left;
            }
            .date {
                text-align: center;
                font-size: 15pt;
                margin: 30px 0;
            }
            .seal {
                text-align: center;
                margin: 20px 0;
            }
            .seal-image {
                max-width: 100px;
                height: auto;
            }
            .signature {
                text-align: center;
                font-size: 15pt;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>''' + title + '''</h1>
            
            <div class="intro">
                谨据《仪度六壬择日要诀》筛选此吉期：
            </div>
            
            <div class="section">
                <div class="section-title">四柱信息</div>
                <div class="table-container">
                    <table>
                        <tr>
                            <td>年: ''' + four_pillars.get('year', '--') + '''</td>
                            <td>月: ''' + four_pillars.get('month', '--') + '''</td>
                            <td>日: ''' + four_pillars.get('day', '--') + '''</td>
                            <td>时: ''' + four_pillars.get('hour', '--') + '''</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">【天地盘】</div>
                <div class="tiandi-pan">
                    ''' + tiandi_image_html + '''
                    ''' + yuejiang_shichen_html + '''
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">【四课】</div>
                <div class="table-container">
                    <table>
                        ''' + generate_sike_table(daliuren_data.get('sike', [])) + '''
                    </table>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">【三传】</div>
                <div class="table-container">
                    <table>
                        ''' + generate_sanchuan_table(daliuren_data.get('sanchuan', {})) + '''
                    </table>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">【综合评价】</div>
                <div class="evaluation">
                    ''' + evaluation.replace('\n', '<br>') + '''
                </div>
            </div>
            
            <div class="date">
                公元''' + year_cn + '''年''' + month_cn + '''月''' + day_cn + '''日
            </div>
            
            <div class="seal">
                ''' + seal_html + '''
            </div>
            
            <div class="signature">
                地理人：信林散道  谨择
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

def generate_sike_table(sike):
    """
    生成四课表格HTML
    """
    if not sike:
        return '<tr><td colspan="4">无四课数据</td></tr>'
    
    rows = []
    for ke in sike:
        top = ke.get('top', '--')
        bottom = ke.get('bottom', '--')
        rows.append(f'<tr><td>上: {top}</td><td>下: {bottom}</td><td colspan="2"></td></tr>')
    
    return '\n'.join(rows)

def generate_sanchuan_table(sanchuan):
    """
    生成三传表格HTML
    """
    if not sanchuan:
        return '<tr><td colspan="4">无三传数据</td></tr>'
    
    rows = []
    chuan_names = ['初传', '中传', '末传']
    for name in chuan_names:
        chuan = sanchuan.get(name, {})
        if chuan:
            text = f'{name}：{chuan.get("tiangan", "--")}{chuan.get("dizhi", "--")}'
            if chuan.get('liuqin'):
                text += f'（{chuan.get("liuqin")}）'
            rows.append(f'<tr><td colspan="4">{text}</td></tr>')
    
    return '\n'.join(rows)


if __name__ == '__main__':
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
    
    result = export_pdf_document(test_data)
    if result['success']:
        print(f"✅ PDF文档导出成功：{result['file_path']}")
    else:
        print(f"❌ PDF文档导出失败：{result['error']}")
        print(f"详细错误：{result['detail']}")
