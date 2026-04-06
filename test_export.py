#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 DOCX 导出功能
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.daliuren_engine import DaLiuRenEngine
from src.export.docx_exporter import LiuRenExporter


def test_export():
    """测试导出功能"""
    print("开始测试 DOCX 导出功能...")
    
    # 创建大六壬引擎
    engine = DaLiuRenEngine()
    
    # 测试数据：农历二月，占时寅，日柱甲子
    lunar_month = 2
    shichen = '寅'
    ri_gan = '甲'
    ri_zhi = '子'
    
    # 排盘
    print(f"排盘参数：农历{lunar_month}月，占时{shichen}，日柱{ri_gan}{ri_zhi}")
    result = engine.full_pai_pan(lunar_month, shichen, ri_gan, ri_zhi)
    
    # 打印排盘结果
    print("\n排盘结果：")
    print(f"月将：{result['月将']}")
    print(f"占时：{result['占时']}")
    print(f"日柱：{result['日柱']}")
    print("天地盘：")
    for di, tian in result['天地盘']['天地对应'].items():
        print(f"  {di}: {tian}")
    print("四课：")
    for ke in result['四课']:
        print(f"  {ke['name']}: {ke['top']} {ke['bottom']}")
    print("三传：")
    print(f"  三传：{result['三传']['三传']}")
    print(f"  课体：{result['三传']['课体']}")
    print(f"  起法：{result['三传']['起法']}")
    print("禄马贵：")
    print(f"  禄：{result['禄马贵']['禄']}")
    print(f"  驿马：{result['禄马贵']['驿马']}")
    print(f"  贵人：{result['禄马贵']['贵人']}")
    
    # 导出到 DOCX
    exporter = LiuRenExporter()
    output_path = os.path.join(os.path.dirname(__file__), 'test_export.docx')
    
    print(f"\n导出到：{output_path}")
    exporter.export_to_docx(result, output_path)
    
    print("\n导出成功！")
    print(f"请打开 {output_path} 查看导出结果")


if __name__ == '__main__':
    test_export()
