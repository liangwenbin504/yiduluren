#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日HTML文档生成器
根据传统择日文书规范，生成竖排格式的HTML择日课单
包含：竖排布局、传统纸张背景、传统字体、印章样式
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu


class HTMLZeriDocument:
    """专业择日HTML文档生成器 - 传统竖排格式"""
    
    def __init__(self):
        self.liuren_duanyu = LiuRenKetiDuanyu()
        
        self.chinese_digits = {
            '0': '零', '1': '壹', '2': '贰', '3': '叁', '4': '肆',
            '5': '伍', '6': '陆', '7': '柒', '8': '捌', '9': '玖'
        }
        
        self.chinese_months = {
            '1': '正月', '2': '二月', '3': '三月', '4': '四月',
            '5': '五月', '6': '六月', '7': '七月', '8': '八月',
            '9': '九月', '10': '十月', '11': '十一月', '12': '腊月'
        }
        
        self.chinese_days = [
            '初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
            '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
            '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'
        ]
    
    def get_chinese_date(self, date_obj=None):
        if date_obj is None:
            date_obj = datetime.now()
        
        year_str = str(date_obj.year)
        year_chinese = ''.join([self.chinese_digits[c] for c in year_str])
        
        month = date_obj.month
        month_chinese = self.chinese_months.get(str(month), '%s月' % month)
        
        day = date_obj.day
        day_chinese = self.chinese_days[day - 1] if day <= 31 else '%s日' % day
        
        return {
            'full': '公元%s年%s%s' % (year_chinese, month_chinese, day_chinese),
            'year': year_chinese,
            'month': month_chinese,
            'day': day_chinese
        }
    
    def get_document_title(self, service_type='择日'):
        if service_type == '安葬':
            return '安葬吉课'
        elif service_type == '立碑':
            return '立碑吉课'
        elif service_type == '婚嫁':
            return '婚嫁吉课'
        else:
            return '择日吉课'
    
    def generate_html_document(self, service_type='择日', year_pillar='--', month_pillar='--',
                                day_pillar='--', hour_pillar='--', keti_list=None, 
                                shanxiang='', xianming=''):
        if keti_list is None:
            keti_list = []
        
        title = self.get_document_title(service_type)
        date_info = self.get_chinese_date()
        
        duanyu_content = ''
        if keti_list:
            duanyu = self.liuren_duanyu.generate_comprehensive_duanyu(keti_list=keti_list)
            if duanyu:
                duanyu_content = duanyu
        
        all_yishi = set()
        all_jishi = set()
        for keti in keti_list:
            keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
            if keti_info.get('宜事'):
                all_yishi.update(keti_info['宜事'])
            if keti_info.get('忌事'):
                all_jishi.update(keti_info['忌事'])
        
        yishi_text = '、'.join(sorted(all_yishi)) if all_yishi else ''
        jishi_text = '、'.join(sorted(all_jishi)) if all_jishi else ''
        
        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 2cm 2cm 2cm 2cm;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "楷体", "KaiTi", "楷体_GB2312", "STKaiti", serif;
            font-size: 22pt;
            line-height: 2.0;
            color: #1a1a1a;
            background: #f5e6c8;
            background-image: 
                radial-gradient(ellipse at top left, rgba(255,255,255,0.3) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(139,90,43,0.1) 0%, transparent 50%);
            min-height: 100vh;
            padding: 0cm 2cm 2cm 2cm;
            padding-top: 0.5cm;
            writing-mode: vertical-rl;
            direction: rtl;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }}
        .document-container {{
            width: 100%;
            max-width: 900px;
            min-height: 1100px;
            background: linear-gradient(135deg, #f8eed8 0%, #f0dbb8 50%, #e8d0a8 100%);
            border: 3px solid #8b5a2b;
            box-shadow: 
                inset 0 0 30px rgba(139,90,43,0.1),
                0 10px 40px rgba(0,0,0,0.2);
            position: relative;
            padding: 15px 60px 40px 60px;
            margin-top: 0;
        }}
        .document-container::before {{
            content: '';
            position: absolute;
            top: 15px;
            left: 15px;
            right: 15px;
            bottom: 15px;
            border: 2px solid #a07850;
            pointer-events: none;
        }}
        .main-title {{
            font-family: "隶书", "LiSu", "STLiti", "楷体", serif;
            font-size: 36pt;
            font-weight: bold;
            letter-spacing: 8px;
            color: #8b0000;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.15);
            margin-bottom: 25px;
            writing-mode: vertical-rl;
            text-orientation: upright;
        }}
        .content-section {{
            margin: 15px 0;
            font-size: 20pt;
            line-height: 2.2;
        }}
        .content-line {{
            margin: 5px 0;
        }}
        .highlight {{
            color: #8b0000;
            font-weight: bold;
        }}
        .pillar-section {{
            font-size: 24pt;
            line-height: 2.5;
            margin: 20px 0;
        }}
        .pillar-item {{
            margin: 8px 0;
        }}
        .seal-box {{
            position: absolute;
            bottom: 40px;
            left: 60px;
            width: 70px;
            height: 70px;
            border: 3px solid #8b0000;
            background: rgba(139, 0, 0, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "隶书", "LiSu", "STLiti", serif;
            font-size: 18pt;
            color: #8b0000;
            writing-mode: horizontal-tb;
            direction: ltr;
            transform: rotate(-15deg);
            letter-spacing: 2px;
            line-height: 1.3;
        }}
        .signature {{
            position: absolute;
            bottom: 40px;
            left: 150px;
            font-size: 18pt;
            line-height: 2.0;
            color: #333;
            writing-mode: horizontal-tb;
            direction: ltr;
        }}
        .yiji-section {{
            margin-top: 25px;
            font-size: 18pt;
            line-height: 2.2;
        }}
        .yiji-title {{
            color: #8b0000;
            font-weight: bold;
            font-size: 20pt;
        }}
        .divider {{
            width: 2px;
            height: 80%;
            background: linear-gradient(to bottom, transparent, #a07850, transparent);
            margin: 0 30px;
        }}
        .note-text {{
            font-size: 16pt;
            line-height: 2.2;
            color: #444;
            margin-top: 20px;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .document-container {{
                box-shadow: none;
                border: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="main-title">{title}</div>
        
        <div class="content-section">
            <div class="content-line">
                <span>{shanxiang if shanxiang else ''}</span>
            </div>
        </div>
        
        <div class="content-section">
            <div class="content-line">
                <span>仙命</span><span class="highlight">{xianming if xianming else '---'}</span>
            </div>
        </div>
        
        <div class="pillar-section">
            <div class="pillar-item">
                <span>太歲</span><span class="highlight">{year_pillar}</span><span>年</span>
            </div>
            <div class="pillar-item">
                <span>太陰</span><span class="highlight">{month_pillar}</span><span>月</span>
            </div>
            <div class="pillar-item">
                <span>太陽</span><span class="highlight">{day_pillar}</span><span>日</span>
            </div>
            <div class="pillar-item">
                <span>太陰</span><span class="highlight">{hour_pillar}</span><span>時</span>
            </div>
        </div>
        
        <div class="yiji-section">
            <div class="content-line">
                <span class="yiji-title">宜</span>
            </div>
            <div class="content-line">
                <span>{yishi_text}</span>
            </div>
        </div>
        
        <div class="yiji-section">
            <div class="content-line">
                <span class="yiji-title">忌</span>
            </div>
            <div class="content-line">
                <span>{jishi_text}</span>
            </div>
        </div>
        
        <div class="note-text">
            <div>地理人</div>
            <div>清虚子</div>
            <div>谨择</div>
        </div>
        
        <div class="seal-box">
            擇<br>吉
        </div>
        
        <div class="signature">
            <div>{date_info['full']}</div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def save_html_document(self, html_content, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
