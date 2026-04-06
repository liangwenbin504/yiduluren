#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日HTML文档生成器 - 最终版本
完全按照传统择日课单图片样式设计
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu


class HTMLZeriDocumentFinal:
    """专业择日HTML文档生成器 - 最终版本"""
    
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
            'full': '公元%s年%s%s'