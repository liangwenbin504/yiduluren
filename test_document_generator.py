#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_modules.professional_zeri_document import ProfessionalZeriDocument

print("测试文档生成器")
print("=" * 60)

generator = ProfessionalZeriDocument()

# 测试中文日期
print("\n中文日期:", generator.get_chinese_date())

# 测试标题
print("\n文档标题:")
print("  安葬:", generator.get_document_title('安葬'))
print("  立碑:", generator.get_document_title('立碑'))
print("  婚嫁:", generator.get_document_title('婚嫁'))
print("  通用:", generator.get_document_title('择日'))

# 准备测试数据
test_data = {
    'service_type': '安葬',
    'year_pillar': '丙午',
    'month_pillar': '辛卯',
    'day_pillar': '己亥',
    'hour_pillar': '甲子',
    'keti_list': ['龙德课', '富贵课'],
    'tianpan': ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
    'sike': ['元首课', '重审课', '知一课', '涉害课'],
    'sanchuan': ['初传', '中传', '末传'],
    'shanxiang': '壬山丙向'
}

# 生成文档
print("\n生成文档...")
doc = generator.generate_document(**test_data)
print(doc)

# 保存文档
output_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\test_zeri_document.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(doc)
print("\n文档已保存到:", output_file)
