#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_modules.html_zeri_document import HTMLZeriDocument

print("=" * 80)
print("专业择日HTML文档生成器 - 测试")
print("=" * 80)

try:
    generator = HTMLZeriDocument()
    print("\n1. 初始化成功！")
    
    test_data = {
        'service_type': '安葬',
        'year_pillar': '丙午',
        'month_pillar': '己亥',
        'day_pillar': '己亥',
        'hour_pillar': '甲子',
        'keti_list': ['龙德课', '富贵课'],
        'shanxiang': '壬山丙向',
        'xianming': '亥'
    }
    
    print("\n2. 生成HTML文档...")
    html_content = generator.generate_html_document(**test_data)
    print("   ✓ HTML文档生成成功")
    
    output_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\安葬日课单_测试.html'
    print(f"\n3. 保存到文件: {output_file}")
    generator.save_html_document(html_content, output_file)
    print("   ✓ 文件保存成功")
    
    print("\n" + "=" * 80)
    print("文档预览（前500字符）:")
    print("=" * 80)
    print(html_content[:500])
    print("=" * 80)
    
    print("\n✓ 测试完成！请在浏览器中打开文件查看效果。")
    
except Exception as e:
    print(f"\n✗ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
