#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业择日文档生成器 - 使用示例

本模块提供专业的择日文档生成功能，包含：
1. 文档标题（安葬日课单/立碑日课单/婚嫁日课单/择日课单）
2. 四柱信息展示
3. 六壬课盘展示（天盘、四课、三传）
4. 丰富的断语内容
5. 宜忌事项分类
6. 择日师落款（清虚子）
7. 中文大写日期
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 80)
print("专业择日文档生成器 - 使用示例")
print("=" * 80)

try:
    from core_modules.professional_zeri_document import ProfessionalZeriDocument
    
    print("\n1. 初始化文档生成器...")
    generator = ProfessionalZeriDocument()
    print("   ✓ 初始化成功")
    
    print("\n2. 测试中文日期转换...")
    chinese_date = generator.get_chinese_date()
    print("   今天的中文日期:", chinese_date)
    
    print("\n3. 测试文档标题生成...")
    print("   安葬标题:", generator.get_document_title('安葬'))
    print("   立碑标题:", generator.get_document_title('立碑'))
    print("   婚嫁标题:", generator.get_document_title('婚嫁'))
    print("   通用标题:", generator.get_document_title('择日'))
    
    print("\n4. 准备测试数据...")
    test_data = {
        'service_type': '安葬',
        'year_pillar': '丙午',
        'month_pillar': '辛卯',
        'day_pillar': '己亥',
        'hour_pillar': '甲子',
        'keti_list': ['龙德课', '富贵课', '官爵课'],
        'tianpan': ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
        'sike': ['元首课', '重审课', '知一课', '涉害课'],
        'sanchuan': ['初传', '中传', '末传'],
        'daliuren_detail': {
            'ri_qualified': True,
            'ri_shan_count': 1,
            'ri_xiang_count': 1,
            'yue_qualified': True,
            'yue_shan_count': 1,
            'yue_xiang_count': 0,
            'nian_qualified': False,
            'qualified_count': 2
        },
        'shanxiang': '壬山丙向'
    }
    print("   ✓ 测试数据准备完成")
    
    print("\n5. 生成文本文档...")
    text_doc = generator.generate_document(**test_data)
    print("   ✓ 文本文档生成成功（长度: %s字符）" % len(text_doc))
    
    print("\n6. 保存文本文档...")
    text_output = r'd:\新建文件夹\仪度六壬择日\yiduluren\示例_择日课单.txt'
    with open(text_output, 'w', encoding='utf-8') as f:
        f.write(text_doc)
    print("   ✓ 已保存到: %s" % text_output)
    
    print("\n" + "=" * 80)
    print("文档预览（前800字符）：")
    print("=" * 80)
    if len(text_doc) &gt; 800:
        print(text_doc[:800] + "...")
    else:
        print(text_doc)
    print("=" * 80)
    
    print("\n使用方法：")
    print("  1. 导入模块：from core_modules.professional_zeri_document import ProfessionalZeriDocument")
    print("  2. 初始化：generator = ProfessionalZeriDocument()")
    print("  3. 生成文档：text_doc = generator.generate_document(service_type='安葬', ...)")
    print("  4. 保存到文件：with open('filename.txt', 'w', encoding='utf-8') as f: f.write(text_doc)")
    
    print("\n✓ 所有测试完成！")
    
except Exception as e:
    print("\n✗ 发生错误：%s" % str(e))
    import traceback
    traceback.print_exc()
