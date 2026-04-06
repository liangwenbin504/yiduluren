#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复导出文档功能 - 确保断语库内容正确显示
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的导出代码（直接获取 textContent）
old_code = """            // 准备导出数据
            const exportData = {
                title_type: titleType,
                mountain: zuoshan,
                xiangshan: xiangshan,
                four_pillars: {
                    year: yearPillar,
                    month: monthPillar,
                    day: dayPillar,
                    hour: hourPillar
                },
                dates: [],
                keti_list: [],  // 课格列表
                evaluation: aiEvaluationEl ? aiEvaluationEl.textContent : ''
            };"""

# 新的导出代码（获取 innerText，保留格式）
new_code = """            // 准备导出数据
            const exportData = {
                title_type: titleType,
                mountain: zuoshan,
                xiangshan: xiangshan,
                four_pillars: {
                    year: yearPillar,
                    month: monthPillar,
                    day: dayPillar,
                    hour: hourPillar
                },
                dates: [],
                keti_list: [],  // 课格列表
                // 使用 innerText 保留换行和格式，确保断语库内容完整
                evaluation: aiEvaluationEl ? aiEvaluationEl.innerText : ''
            };"""

# 查找并替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 导出文档功能已修复！")
    print("📝 修改内容:")
    print("  1. 使用 innerText 代替 textContent")
    print("  2. 保留换行和格式")
    print("  3. 确保断语库内容完整导出")
else:
    print("❌ 未找到需要修改的代码")
