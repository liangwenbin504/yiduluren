#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试择日文档生成器"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_modules.professional_zeri_document import ProfessionalZeriDocument

print("=" * 80)
print("测试择日文档生成器")
print("=" * 80)

generator = ProfessionalZeriDocument()

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

print("\n【生成文本文档】")
text_doc = generator.generate_document(**test_data)
if len(text_doc) &gt; 1000:
    print(text_doc[:1000] + '...')
else:
    print(text_doc)

print("\n\n【生成HTML文档】")
html_doc = generator.generate_html_document(**test_data)

output_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\test_zeri_document.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_doc)

print("HTML文档已保存到：%s" % output_path)
print("\n测试完成！")
