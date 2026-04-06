#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日文档生成器
根据传统择日文书规范，生成专业的择日课单文档
包含：四柱信息、六壬课盘、断语内容、宜忌事项、择日师落款等
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu


class ProfessionalZeriDocument:
    """专业择日文档生成器"""
    
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
        
        self.tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        self.dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    def number_to_chinese(self, num):
        if num < 10:
            return self.chinese_digits[str(num)]
        elif num < 20:
            if num == 10:
                return '拾'
            return '拾' + self.chinese_digits[str(num - 10)]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            result = self.chinese_digits[str(tens)] + '拾'
            if ones > 0:
                result += self.chinese_digits[str(ones)]
            return result
        return str(num)
    
    def get_chinese_date(self, date_obj=None):
        if date_obj is None:
            date_obj = datetime.now()
        
        year_str = str(date_obj.year)
        year_chinese = ''.join([self.chinese_digits[c] for c in year_str])
        
        month = date_obj.month
        month_chinese = self.chinese_months.get(str(month), '%s月' % month)
        
        day = date_obj.day
        day_chinese = self.chinese_days[day - 1] if day <= 31 else '%s日' % day
        
        return '公元%s年%s%s' % (year_chinese, month_chinese, day_chinese)
    
    def get_document_title(self, service_type='择日'):
        if service_type == '安葬':
            return '安葬日课单'
        elif service_type == '立碑':
            return '立碑日课单'
        elif service_type == '婚嫁':
            return '婚嫁日课单'
        else:
            return '择日课单'
    
    def generate_four_pillars_section(self, year_pillar, month_pillar, day_pillar, hour_pillar):
        section = []
        section.append("【四柱信息】")
        section.append("年柱：%s" % year_pillar)
        section.append("月柱：%s" % month_pillar)
        section.append("日柱：%s" % day_pillar)
        section.append("时柱：%s" % hour_pillar)
        return '\n'.join(section)
    
    def generate_liuren_pan_section(self, tianpan=None, sike=None, sanchuan=None):
        section = []
        section.append("【六壬课盘】")
        
        if tianpan:
            section.append("\n天盘：")
            section.append('  ' + '  '.join(tianpan))
        
        if sike:
            section.append("\n四课：")
            for i, ke in enumerate(sike):
                section.append("  第%s课：%s" % (i+1, ke))
        
        if sanchuan:
            section.append("\n三传：")
            section.append("  初传：%s" % (sanchuan[0] if len(sanchuan) > 0 else '--'))
            section.append("  中传：%s" % (sanchuan[1] if len(sanchuan) > 1 else '--'))
            section.append("  末传：%s" % (sanchuan[2] if len(sanchuan) > 2 else '--'))
        
        return '\n'.join(section)
    
    def generate_duanyu_section(self, keti_list, daliuren_detail=None):
        duanyu = self.liuren_duanyu.generate_comprehensive_duanyu(
            keti_list=keti_list,
            luma_info=daliuren_detail
        )
        return duanyu
    
    def generate_yiji_section(self, keti_list):
        section = []
        section.append("【宜忌事项】")
        
        all_yishi = set()
        all_jishi = set()
        
        for keti in keti_list:
            keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
            if keti_info.get('宜事'):
                all_yishi.update(keti_info['宜事'])
            if keti_info.get('忌事'):
                all_jishi.update(keti_info['忌事'])
        
        if all_yishi:
            section.append("\n宜：%s" % ', '.join(sorted(all_yishi)))
        
        if all_jishi:
            section.append("\n忌：%s" % ', '.join(sorted(all_jishi)))
        
        return '\n'.join(section)
    
    def generate_signature_section(self):
        section = []
        section.append("\n" + "=" * 50)
        section.append("择日师：清虚子")
        section.append("日期：%s" % self.get_chinese_date())
        return '\n'.join(section)
    
    def generate_document(self, service_type='择日', year_pillar='--', month_pillar='--', 
                        day_pillar='--', hour_pillar='--', keti_list=None, tianpan=None, 
                        sike=None, sanchuan=None, daliuren_detail=None, shanxiang=''):
        if keti_list is None:
            keti_list = []
        
        doc = []
        
        title = self.get_document_title(service_type)
        doc.append("=" * 60)
        doc.append("%s%s" % (' ' * 20, title))
        doc.append("=" * 60)
        
        if shanxiang:
            doc.append("\n山向：%s" % shanxiang)
        
        doc.append("\n" + self.generate_four_pillars_section(
            year_pillar, month_pillar, day_pillar, hour_pillar
        ))
        
        doc.append("\n" + self.generate_liuren_pan_section(
            tianpan, sike, sanchuan
        ))
        
        if keti_list:
            duanyu = self.generate_duanyu_section(keti_list, daliuren_detail)
            if duanyu:
                doc.append("\n" + duanyu)
        
        if keti_list:
            doc.append("\n" + self.generate_yiji_section(keti_list))
        
        doc.append("\n" + self.generate_signature_section())
        
        return '\n'.join(doc)
