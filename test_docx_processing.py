#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文档处理系统功能
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine.daliuren_engine import DaLiuRenEngine
from src.export.docx_formatter import DocxFormatter
from src.export.docx_automator import DocxAutomator


def test_document_processing():
    """测试文档处理功能"""
    print("开始测试文档处理系统功能...")
    
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
    
    # 1. 测试模板管理功能
    print("\n1. 测试模板管理功能...")
    formatter = DocxFormatter()
    
    # 列出可用模板
    templates = formatter.list_templates()
    print(f"可用模板：{templates}")
    
    # 创建自定义模板
    custom_format = {
        'font': {
            'name': '宋体',
            'size': 14,
            'color': (0, 0, 0)
        },
        'heading': {
            'h1': {
                'font': '黑体',
                'size': 24,
                'color': (255, 0, 0)
            }
        },
        'image': {
            'width': 5.0,
            'alignment': 'center'
        }
    }
    
    formatter.update_format(custom_format)
    template_name = '测试模板'
    if formatter.save_template(template_name):
        print(f"成功创建模板：{template_name}")
    else:
        print(f"创建模板失败：{template_name}")
    
    # 列出可用模板
    templates = formatter.list_templates()
    print(f"更新后可用模板：{templates}")
    
    # 2. 测试文档生成功能
    print("\n2. 测试文档生成功能...")
    doc = formatter.generate_document(result, template_name)
    if doc:
        output_path = os.path.join(os.path.dirname(__file__), 'test_generated.docx')
        if formatter.export_document(doc, output_path):
            print(f"成功生成文档：{output_path}")
        else:
            print("生成文档失败")
    else:
        print("创建文档失败")
    
    # 3. 测试文档导入功能
    print("\n3. 测试文档导入功能...")
    input_file = output_path
    if os.path.exists(input_file):
        imported_doc = formatter.import_document(input_file)
        if imported_doc:
            print("成功导入文档")
            # 应用不同的格式
            formatter.reset_format()
            formatter.apply_format(imported_doc)
            modified_output = os.path.join(os.path.dirname(__file__), 'test_modified.docx')
            if formatter.export_document(imported_doc, modified_output):
                print(f"成功导出修改后的文档：{modified_output}")
            else:
                print("导出修改后的文档失败")
        else:
            print("导入文档失败")
    else:
        print(f"输入文件不存在：{input_file}")
    
    # 4. 测试自动化处理功能
    print("\n4. 测试自动化处理功能...")
    automator = DocxAutomator()
    
    # 测试基于数据生成文档
    auto_output = os.path.join(os.path.dirname(__file__), 'test_auto_generated.docx')
    if automator.auto_process(output_file=auto_output, template_name=template_name, result_data=result):
        print(f"成功自动生成文档：{auto_output}")
    else:
        print("自动生成文档失败")
    
    # 测试批量处理功能
    print("\n5. 测试批量处理功能...")
    input_dir = os.path.dirname(__file__)
    output_dir = os.path.join(os.path.dirname(__file__), 'batch_output')
    success_count = automator.batch_process(input_dir, output_dir, template_name)
    print(f"批量处理完成，成功处理 {success_count} 个文件")
    
    print("\n所有测试完成！")


if __name__ == '__main__':
    test_document_processing()
