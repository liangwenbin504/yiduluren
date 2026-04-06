#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日HTML文档生成器 - 专业古籍排版版
根据传统择日文书规范，生成竖排格式的HTML择日课单
使用专业的CSS古籍排版属性
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu


class HTMLZeriDocumentPro:
    """专业择日HTML文档生成器 - 专业古籍排版版"""
    
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
            return '安葬吉課'
        elif service_type == '立碑':
            return '立碑吉課'
        elif service_type == '婚嫁':
            return '婚嫁吉課'
        else:
            return '擇日吉課'
    
    def generate_html_document(self, service_type='擇日', year_pillar='--', month_pillar='--',
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
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 1.5cm 1.5cm 1.5cm 1.5cm;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html, body {{
            height: 100%;
            width: 100%;
        }}
        
        body {{
            font-family: "楷体", "KaiTi", "楷体_GB2312", "STKaiti", "SimKai", "TW-Kai", "serif";
            font-size: 28px;
            line-height: 2.5;
            letter-spacing: 0.12em;
            color: #1a1a1a;
            background: #f5e6c8;
            background-image: 
                radial-gradient(ellipse at 20% 10%, rgba(255,252,245,0.4) 0%, transparent 45%),
                radial-gradient(ellipse at 80% 90%, rgba(139,90,43,0.12) 0%, transparent 55%);
            overflow-x: hidden;
        }}
        
        .page-container {{
            width: 100%;
            min-height: 100vh;
            padding: 1cm 1.5cm 1.5cm 1.5cm;
            padding-top: 0.8cm;
            display: flex;
            flex-direction: row-reverse;
            justify-content: center;
            align-items: flex-start;
            writing-mode: vertical-rl;
            -webkit-writing-mode: vertical-rl;
            -ms-writing-mode: tb-rl;
            direction: rtl;
            text-orientation: mixed;
        }}
        
        .document {{
            width: 100%;
            max-width: 850px;
            min-height: 1050px;
            background: linear-gradient(165deg, #faf3e3 0%, #f5e8d0 45%, #ede0c5 100%);
            border: 3px solid #8b5a2b;
            box-shadow: 
                inset 0 0 50px rgba(139,90,43,0.08),
                0 15px 50px rgba(0,0,0,0.25);
            position: relative;
            padding: 25px 70px 50px 70px;
            writing-mode: vertical-rl;
            -webkit-writing-mode: vertical-rl;
            -ms-writing-mode: tb-rl;
            direction: rtl;
        }}
        
        .document::before {{
            content: '';
            position: absolute;
            top: 18px;
            left: 18px;
            right: 18px;
            bottom: 18px;
            border: 2px solid #a67c52;
            pointer-events: none;
        }}
        
        .document::after {{
            content: '';
            position: absolute;
            top: 28px;
            left: 28px;
            right: 28px;
            bottom: 28px;
            border: 1px solid #c4a67c;
            pointer-events: none;
        }}
        
        .main-title {{
            font-family: "隶书", "LiSu", "STLiti", "SimLi", "隶书", serif;
            font-size: 52px;
            font-weight: bold;
            letter-spacing: 0.25em;
            color: #8b0000;
            text-shadow: 2px 2px 3px rgba(0,0,0,0.15);
            margin-bottom: 35px;
            writing-mode: vertical-rl;
            -webkit-writing-mode: vertical-rl;
            text-orientation: upright;
            -webkit-text-orientation: upright;
            line-height: 1.6;
        }}
        
        .content-section {{
            margin: 20px 0;
            font-size: 26px;
            line-height: 2.6;
            letter-spacing: 0.15em;
        }}
        
        .content-line {{
            margin: 6px 0;
        }}
        
        .highlight {{
            color: #8b0000;
            font-weight: bold;
            letter-spacing: 0.18em;
        }}
        
        .pillar-section {{
            font-size: 30px;
            line-height: 2.8;
            margin: 25px 0;
            letter-spacing: 0.18em;
        }}
        
        .pillar-item {{
            margin: 10px 0;
        }}
        
        .seal-box {{
            position: absolute;
            bottom: 55px;
            left: 70px;
            width: 80px;
            height: 80px;
            border: 3px solid #8b0000;
            background: rgba(139, 0, 0, 0.06);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "篆书", "小篆", "隶书", "LiSu", "STLiti", serif;
            font-size: 24px;
            color: #8b0000;
            writing-mode: horizontal-tb;
            direction: ltr;
            transform: rotate(-12deg);
            letter-spacing: 0.1em;
            line-height: 1.3;
            font-weight: 600;
        }}
        
        .signature {{
            position: absolute;
            bottom: 55px;
            left: 175px;
            font-size: 22px;
            line-height: 2.2;
            color: #333;
            writing-mode: horizontal-tb;
            direction: ltr;
            letter-spacing: 0.12em;
        }}
        
        .yiji-section {{
            margin-top: 30px;
            font-size: 24px;
            line-height: 2.4;
            letter-spacing: 0.14em;
        }}
        
        .yiji-title {{
            color: #8b0000;
            font-weight: bold;
            font-size: 26px;
            letter-spacing: 0.18em;
        }}
        
        .note-text {{
            font-size: 22px;
            line-height: 2.4;
            color: #444;
            margin-top: 25px;
            letter-spacing: 0.12em;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .document {{
                box-shadow: none;
            }}
        }}
        
        @media screen and (max-width: 1200px) {{
            body {{
                font-size: 24px;
            }}
            .main-title {{
                font-size: 42px;
            }}
            .content-section {{
                font-size: 22px;
            }}
            .pillar-section {{
                font-size: 26px;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        <div class="document">
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
    </div>
</body>
</html>"""
        
        return html
    
    def save_html_document(self, html_content, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
