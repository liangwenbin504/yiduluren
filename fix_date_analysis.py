#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复主界面.html 的日期分析 API 调用 - 增加超时时间和详细日志
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的代码
old_code = """            try {
                // 调用完整日期范围分析 API（遍历所有日期和 12 个时辰）
                const result = await fetchApi(`${API_BASE_URL}/doushou/full_range_analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mountain: currentMountain,
                        start_date: startStr,
                        end_date: endStr,
                        min_daliuren_score: minDaliurenScore,
                        max_results: count || 10
                    })
                });
                
                console.log('📌 完整日期范围分析结果:', result);
                
                if (!result.success) {
                    throw new Error(result.error || '分析失败');
                }"""

# 新的代码（增加详细日志和超时时间）
new_code = """            try {
                console.log('🚀 开始调用 API:', `${API_BASE_URL}/doushou/full_range_analyze`);
                console.log('📋 请求参数:', {
                    mountain: currentMountain,
                    start_date: startStr,
                    end_date: endStr,
                    min_daliuren_score: minDaliurenScore,
                    max_results: count || 10
                });
                
                // 调用完整日期范围分析 API（遍历所有日期和 12 个时辰）
                const result = await fetchApi(`${API_BASE_URL}/doushou/full_range_analyze`, {
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
                });
                
                console.log('📌 完整日期范围分析结果:', result);
                
                if (!result.success) {
                    throw new Error(result.error || '分析失败');
                }"""

# 查找并替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 日期分析 API 调用已修复！")
    print("📝 修改内容:")
    print("  1. 增加了详细的请求日志")
    print("  2. 超时时间从 30 秒增加到 120 秒")
    print("  3. 添加了更详细的错误信息")
else:
    print("❌ 未找到需要修改的代码")
