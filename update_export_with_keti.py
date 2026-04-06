#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改主界面.html 的导出函数，添加课格列表数据
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的导出数据代码
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
                evaluation: aiEvaluationEl ? aiEvaluationEl.textContent : ''
            };"""

# 新的导出数据代码（添加课格列表）
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
                evaluation: aiEvaluationEl ? aiEvaluationEl.textContent : ''
            };
            
            // 从 AI 评价中提取课格信息（如果有）
            const aiEvalText = aiEvaluationEl ? aiEvaluationEl.textContent : '';
            if (aiEvalText.includes('元首课')) exportData.keti_list.push('元首课');
            if (aiEvalText.includes('重审课')) exportData.keti_list.push('重审课');
            if (aiEvalText.includes('知一课')) exportData.keti_list.push('知一课');
            if (aiEvalText.includes('龙德课')) exportData.keti_list.push('龙德课');
            if (aiEvalText.includes('福德课')) exportData.keti_list.push('福德课');
            if (aiEvalText.includes('旺相课')) exportData.keti_list.push('旺相课');
            if (aiEvalText.includes('比和课')) exportData.keti_list.push('比和课');
            if (aiEvalText.includes('贵人课')) exportData.keti_list.push('贵人课');
            if (aiEvalText.includes('禄马课')) exportData.keti_list.push('禄马课');
            
            console.log('📋 课格列表:', exportData.keti_list);"""

# 查找并替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 导出函数已更新！")
    print("📝 修改内容:")
    print("  1. 添加了 keti_list 字段")
    print("  2. 从 AI 评价中提取课格信息")
    print("  3. 支持 10 种常见课格的自动识别")
else:
    print("❌ 未找到需要修改的代码")
