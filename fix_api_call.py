#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确修复主界面.html 的日期分析 API 调用
"""

import os
import re

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 使用正则表达式查找并替换
# 查找：fetchApi(`${API_BASE_URL}/doushou/full_range_analyze`, { ... })
pattern = r'(fetchApi\(\$\{API_BASE_URL\}/doushou/full_range_analyze,\s*\{[^}]*headers:\s*\{[^}]*\}[^}]*body:\s*JSON\.stringify\(\{[^}]*\}\)[^}]*\}\))'

match = re.search(pattern, content, re.DOTALL)

if match:
    old_call = match.group(1)
    print("✅ 找到日期分析 API 调用")
    print(f"📝 原始代码位置：{match.start()}-{match.end()}")
    
    # 在 body 后面添加 timeout 参数
    # 找到最后的 }) 并替换为 }), timeout: 120000
    new_call = old_call.replace('})\n                });', '}),\n                    timeout: 120000  // 增加到 120 秒超时\n                });')
    
    content = content.replace(old_call, new_call)
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 日期分析 API 调用已修复！")
    print("📝 修改内容:")
    print("  - 增加了 timeout: 120000 (120 秒超时)")
else:
    print("❌ 未找到日期分析 API 调用")
    print("尝试使用备用方案...")
    
    # 备用方案：直接替换
    old_text = """fetchApi(`${API_BASE_URL}/doushou/full_range_analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mountain: currentMountain,
                        start_date: startStr,
                        end_date: endStr,
                        min_daliuren_score: minDaliurenScore,
                        max_results: count || 10
                    })
                });"""
    
    new_text = """fetchApi(`${API_BASE_URL}/doushou/full_range_analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mountain: currentMountain,
                        start_date: startStr,
                        end_date: endStr,
                        min_daliuren_score: minDaliurenScore,
                        max_results: count || 10
                    }),
                    timeout: 120000  // 增加到 120 秒超时
                });"""
    
    if old_text in content:
        content = content.replace(old_text, new_text)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 使用备用方案修复成功！")
    else:
        print("❌ 备用方案也失败了，请手动检查代码")
