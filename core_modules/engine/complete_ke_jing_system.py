#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经完整系统 - 集成版

功能：
1. 从 PDF 提取课经
2. 生成 720 课例数据库
3. 根据年月日时自动匹配
4. 生成完整的课经报告
"""

import json
import os
import sys
from datetime import datetime

# 路径设置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_ke_jing_extractor import PDFKeJingExtractor
from 720_ke_database import SevenTwentyKeDatabase, KeJingMatcher
from ke_jing_engine import LiuShiSiKeEngine


class CompleteKeJingSystem:
    """64 课经完整系统"""
    
    def __init__(self):
        self.ke_jing_engine = LiuShiSiKeEngine()
        self.db = SevenTwentyKeDatabase()
        self.matcher = KeJingMatcher()
        self.pdf_extractor = None
    
    def extract_from_pdf(self, pdf_path):
        """
        从 PDF 提取课经
        
        :param pdf_path: PDF 文件路径
        :return: 课经数据
        """
        try:
            self.pdf_extractor = PDFKeJingExtractor(pdf_path)
            data = self.pdf_extractor.extract_all()
            self.pdf_extractor.save_to_json()
            
            # 更新到引擎
            for ke_name, ke_data in data.items():
                self.ke_jing_engine.ke_jing_data[ke_name] = ke_data
            
            print(f"✓ 从 PDF 提取 {len(data)} 课经")
            return data
        except Exception as e:
            print(f"✗ PDF 提取失败：{e}")
            return {}
    
    def generate_720_ke(self):
        """生成 720 课例数据库"""
        count = self.db.generate_720_ke()
        print(f"✓ 生成 {count} 个课例")
        return count
    
    def match_ke_jing(self, qi_ke_result, year, month, day, hour):
        """
        匹配课经到课例
        
        :param qi_ke_result: 起课结果
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :return: 匹配结果
        """
        result = self.matcher.match_and_associate(
            qi_ke_result, year, month, day, hour
        )
        return result
    
    def generate_full_report(self, qi_ke_result, year, month, day, hour):
        """
        生成完整的课经报告
        
        :param qi_ke_result: 起课结果
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :return: 完整报告文本
        """
        # 匹配课经
        match_result = self.match_ke_jing(qi_ke_result, year, month, day, hour)
        
        # 生成报告
        report = []
        report.append("=" * 70)
        report.append("大六壬 64 课经完整报告")
        report.append("=" * 70)
        
        # 时间信息
        report.append("\n【时间信息】")
        report.append(f"  公元：{year}年{month}月{day}日{hour}时")
        report.append(f"  干支：{qi_ke_result.get('日干支', '未知')}")
        
        # 起课结果
        report.append("\n【起课结果】")
        report.append(f"  课体：{qi_ke_result.get('课体', '')}")
        report.append(f"  起法：{qi_ke_result.get('起法', '')}")
        report.append(f"  三传：{qi_ke_result.get('初传', '')} {qi_ke_result.get('中传', '')} {qi_ke_result.get('末传', '')}")
        if '格局' in qi_ke_result:
            report.append(f"  格局：{qi_ke_result.get('格局', '')}")
        
        # 匹配课经
        report.append("\n【匹配课经】")
        matched = match_result['matched_ke_jing']
        if matched:
            for i, item in enumerate(matched[:5], 1):  # 显示前 5 个
                ke_data = item['ke_data']
                report.append(f"\n  {i}. {item['ke_name']} (匹配度：{item['score']}分)")
                report.append(f"     课体：{ke_data.get('ke_type', '')}")
                report.append(f"     原文：{ke_data.get('description', '')[:100]}")
                report.append(f"     断语：{ke_data.get('judgment', '')[:100]}")
        else:
            report.append("  未找到匹配的课经")
        
        # 课例信息
        report.append("\n【课例信息】")
        ke_li = match_result['ke_li']
        if ke_li:
            report.append(f"  课例 ID: {ke_li.get('ri_gan_zhi', '')}_{ke_li.get('yue', '')}_{ke_li.get('shi', '')}")
            report.append(f"  月将：{ke_li.get('yue_jiang', '')}")
        else:
            report.append("  课例未在数据库中")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def save_report(self, report, output_path):
        """保存报告"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ 报告已保存到：{output_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("大六壬 64 课经完整系统")
    print("=" * 70)
    
    # 初始化系统
    system = CompleteKeJingSystem()
    
    # 1. 从 PDF 提取课经
    pdf_file = "白话大六壬全书（有目录）.pdf"
    if os.path.exists(pdf_file):
        print(f"\n正在从 PDF 提取课经...")
        system.extract_from_pdf(pdf_file)
    else:
        print(f"\n未找到 PDF 文件：{pdf_file}")
        print("将使用示例课经数据")
    
    # 2. 生成 720 课例
    print(f"\n正在生成 720 课例...")
    system.generate_720_ke()
    
    # 3. 测试匹配
    print(f"\n测试匹配...")
    test_qi_ke = {
        '课体': '涉害课',
        '起法': '涉害法',
        '日干支': '甲子',
        '初传': '酉',
        '中传': '申',
        '末传': '未',
        '格局': '见机格'
    }
    
    report = system.generate_full_report(test_qi_ke, 2024, 3, 15, 10)
    print(report)
    
    # 保存报告
    system.save_report(report, "output/课经测试报告.txt")
    
    print("\n" + "=" * 70)
    print("系统初始化完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
