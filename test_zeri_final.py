#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试最终版择日HTML文档生成器"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from core_modules.html_zeri_final import HTMLZeriDocumentFinal

def test_zeri_document():
    """测试择日文档生成"""
    print("正在生成择日HTML文档...")
    
    generator = HTMLZeriDocumentFinal()
    
    html_content = generator.generate_html_document(
        service_type='安葬',
        year_pillar='丙午',
        month_pillar='己亥',
        day_pillar='己亥',
        hour_pillar='甲子',
        keti_list=[],
        shanxiang='壬山丙向',
        xianming='亥'
    )
    
    output_path = os.path.join(os.path.dirname(__file__), 'test_zeri_final.html')
    generator.save_html_document(html_content, output_path)
    
    print(f"HTML文档已生成: {output_path}")
    print("\n请在浏览器中打开该文件查看效果！")
    
    return output_path

if __name__ == '__main__':
    test_zeri_document()
