#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复日期选择问题 - 在打开新弹窗前先关闭旧弹窗
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 旧的代码（在 setTimeout 中直接调用 openDateDetail）
old_code = """            // 延迟显示弹窗，确保 UI 更新完成
            setTimeout(() => {
                openDateDetail(dateInfo);
            }, 100);"""

# 新的代码（先关闭旧弹窗，再打开新弹窗）
new_code = """            // 延迟显示弹窗，确保 UI 更新完成
            setTimeout(() => {
                // 先关闭旧的弹窗（如果有）
                const oldModal = document.getElementById('dateDetailModal');
                if (oldModal) {
                    oldModal.classList.remove('show');
                }
                // 打开新的弹窗
                openDateDetail(dateInfo);
            }, 100);"""

# 查找并替换
if old_code in content:
    content = content.replace(old_code, new_code)
    
    # 保存文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 日期选择弹窗问题已修复！")
    print("📝 修改内容:")
    print("  1. 在打开新弹窗前先关闭旧弹窗")
    print("  2. 确保每次只显示一个弹窗")
    print("  3. 避免弹窗累积或显示异常")
else:
    print("❌ 未找到需要修改的代码")
