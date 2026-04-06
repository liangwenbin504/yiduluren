#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改主界面.html 的导出文档函数
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的导出函数（从第 4650 行到 4955 行）
old_function_start = "// 导出文档（古籍竖排格式）\n        function exportDocument() {"
old_function_end = "            alert('古籍格式課單已導出！');\n        }"

# 新的导出函数
new_function = """// 导出文档（使用模板生成标准docx格式）
        function exportDocument() {
            const shanxiangEl = document.getElementById('shanxiang');
            const shanxiangValue = shanxiangEl ? shanxiangEl.value : '';
            const zetiriTypeSelectEl = document.getElementById('zetiriTypeSelect');
            const zetiriTypeValue = zetiriTypeSelectEl ? zetiriTypeSelectEl.value : '';
            
            const yearPillarEl = document.getElementById('yearPillar');
            const monthPillarEl = document.getElementById('monthPillar');
            const dayPillarEl = document.getElementById('dayPillar');
            const hourPillarEl = document.getElementById('hourPillar');
            
            const aiEvaluationEl = document.getElementById('aiEvaluation');
            
            const dateListEl = document.getElementById('dateList');
            const dateItems = dateListEl ? dateListEl.querySelectorAll('.date-item') : [];
            
            const yearPillar = yearPillarEl ? yearPillarEl.textContent : '--';
            const monthPillar = monthPillarEl ? monthPillarEl.textContent : '--';
            const dayPillar = dayPillarEl ? dayPillarEl.textContent : '--';
            const hourPillar = hourPillarEl ? hourPillarEl.textContent : '--';
            
            const titleType = zetiriTypeValue === '安葬' ? '安葬吉日' : 
                            zetiriTypeValue === '立碑' ? '立碑吉日' :
                            zetiriTypeValue === '婚嫁' ? '婚嫁吉日' : '擇日課單';
            
            const shanxiangParts = shanxiangValue ? shanxiangValue.split('山') : ['', ''];
            const zuoshan = shanxiangParts[0] || '';
            const xiangshan = shanxiangParts[1] ? shanxiangParts[1].replace('向', '') : '';
            
            // 准备导出数据
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
            };
            
            // 收集日期数据
            if (dateItems.length > 0) {
                dateItems.forEach((item) => {
                    const date = item.dataset.date || '--';
                    const hour = item.dataset.hour || '--';
                    const score = item.dataset.score || '--';
                    exportData.dates.push({
                        date: date,
                        hour: hour,
                        score: score
                    });
                });
            }
            
            console.log('📄 导出文档数据:', exportData);
            
            // 调用后端 API 导出 docx 文档
            fetch(`${API_BASE_URL}/export/docx`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(exportData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(result => {
                console.log('📄 导出结果:', result);
                
                if (result.success) {
                    // 下载文件
                    const downloadUrl = `${API_BASE_URL}/export/download/${result.filename}`;
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = result.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    
                    alert(`✅ 文档导出成功！\\n文件：${result.filename}\\n\\n文档已使用模板格式保存为标准的 docx 格式。`);
                } else {
                    alert(`❌ 文档导出失败：${result.error || '未知错误'}`);
                }
            })
            .catch(error => {
                console.error('❌ 导出文档失败:', error);
                alert(`❌ 文档导出失败：${error.message}\\n\\n请确保 API 服务器正在运行。`);
            });
        }"""

# 查找并替换
if old_function_start in content and old_function_end in content:
    # 找到旧函数的起始和结束位置
    start_idx = content.find(old_function_start)
    end_idx = content.find(old_function_end) + len(old_function_end)
    
    # 替换函数
    new_content = content[:start_idx] + new_function + content[end_idx:]
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 导出文档函数已更新！")
    print("📄 新函数将调用后端 API 生成标准 docx 格式文档")
else:
    print("❌ 未找到旧的导出函数")
