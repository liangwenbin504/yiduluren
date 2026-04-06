#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日HTML文档生成器 - 最终版
完全按照传统择日课单图片样式设计
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu


class HTMLZeriDocumentFinal:
    """专业择日HTML文档生成器 - 最终版"""
    
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
        body {{
            font-family: "楷体", "KaiTi", "楷体_GB2312", "STKaiti", serif;
            background: #f5e6c8;
            padding: 20px;
        }}
        
        .page {{
            width: 900px;
            height: 1250px;
            background: #faf0d8;
            border: 3px solid #8b5a2b;
            margin: 0 auto;
            position: relative;
        }}
        
        .border-inner {{
            position: absolute;
            top: 30px;
            left: 30px;
            right: 30px;
            bottom: 30px;
            border: 2px solid #a07850;
        }}
        
        .content {{
            position: absolute;
            top: 60px;
            left: 60px;
            right: 60px;
            bottom: 60px;
            writing-mode: vertical-rl;
            -webkit-writing-mode: vertical-rl;
            direction: rtl;
            font-size: 52px;
            line-height: 2.2;
        }}
        
        .col {{
            display: inline-block;
            margin-left: 45px;
            vertical-align: top;
        }}
        
        .title {{
            font-family: "黑体", "SimHei", "STHeiti", sans-serif;
            font-size: 68px;
            font-weight: bold;
            color: #8b0000;
        }}
        
        .red {{
            color: #8b0000;
            font-weight: bold;
        }}
        
        .small {{
            font-size: 38px;
        }}
        
        .seal {{
            position: absolute;
            bottom: 90px;
            left: 100px;
            width: 95px;
            height: 95px;
            border: 4px solid #8b0000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "篆书", "小篆", "隶书", serif;
            font-size: 26px;
            color: #8b0000;
            transform: rotate(-15deg);
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="border-inner"></div>
        <div class="content">
            <div class="col title">安葬吉課</div>
            <div class="col">壬山丙向<br>仙命亥</div>
            <div class="col">{year_pillar}年<br>{month_pillar}月<br>{day_pillar}日<br>{hour_pillar}时</div>
            <div class="col"><span class="red">宜</span><br>安葬、修娶、入宅、交易</div>
            <div class="col"><span class="red">忌</span><br>嫁安、稳稳、福荫、后人</div>
            <div class="col">地理人<br>清虚竹子<br>谨择</div>
            <div class="col small">{date_info['full']}</div>
        </div>
        <div class="seal">擇<br>吉</div>
    </div>
</body>
</html>"""
        
        return html
    
    def save_html_document(self, html_content, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
