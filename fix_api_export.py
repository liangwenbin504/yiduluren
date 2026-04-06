#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 API 服务器的导出文档功能，添加课格列表参数
"""

import os

api_file = os.path.join(os.path.dirname(__file__), 'api_server.py')

print(f"正在读取文件：{api_file}")
with open(api_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的导出数据代码
old_code = """        # 准备导出数据
        export_data = {
            'title': data.get('title_type', '擇日課單'),
            'zuoshan': data.get('mountain', ''),
            'xiangshan': data.get('xiangshan', ''),
            'four_pillars': data.get('four_pillars', {}),
            'dates': data.get('dates', []),
            'evaluation': data.get('evaluation', '')
        }"""

# 新的导出数据代码（添加课格列表）
new_code = """        # 准备导出数据
        export_data = {
            'title': data.get('title_type', '擇日課單'),
            'mountain': data.get('mountain', ''),
            'dates': data.get('dates', []),
            'keti_list': data.get('keti_list', []),  # 课格列表
            'evaluation': data.get('evaluation', '')
        }"""

# 查找并替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 保存文件
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ API 服务器导出功能已修复！")
    print("📝 修改内容:")
    print("  1. 添加了 keti_list 参数传递")
    print("  2. 移除了不需要的 xiangshan 和 four_pillars 参数")
    print("  3. 使导出数据与导出模块一致")
else:
    print("❌ 未找到需要修改的代码")
