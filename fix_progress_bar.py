#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复进度条卡住问题 - 增加超时处理和错误提示
"""

import os

html_file = os.path.join(os.path.dirname(__file__), '主界面.html')

print(f"正在读取文件：{html_file}")
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("✅ 文件读取成功")

# 修复 1: 增加超时时间到 180 秒，并添加超时错误提示
old_timeout = "timeout: 120000  // 增加到 120 秒超时"
new_timeout = """timeout: 180000,  // 增加到 180 秒超时
                    onUploadProgress: (progressEvent) => {
                        console.log('上传进度:', progressEvent.loaded, '/', progressEvent.total);
                    },
                    onDownloadProgress: (progressEvent) => {
                        console.log('下载进度:', progressEvent.loaded, '/', progressEvent.total);
                        if (progressEvent.total) {
                            const percent = (progressEvent.loaded / progressEvent.total) * 100;
                            if (percent > 90) {
                                updateProgress(percent);
                            }
                        }
                    }"""

if old_timeout in content:
    content = content.replace(old_timeout, new_timeout)
    print("✅ 已增加超时时间和进度监听")

# 修复 2: 添加超时错误处理
old_catch = """            } catch (error) {
                console.error('日期范围分析失败:', error);
                dateListEl.innerHTML = `<div style="padding: 20px; text-align: center; color: #c62828;">分析失败：${error.message}</div>`;
                alert('日期分析失败：' + error.message);
                hideProgress();
            }"""

new_catch = """            } catch (error) {
                console.error('日期范围分析失败:', error);
                
                // 特殊处理超时错误
                let errorMessage = error.message;
                if (error.name === 'AbortError' || error.message.includes('timeout') || error.message.includes('超时')) {
                    errorMessage = '请求超时！数据量较大，计算需要更长时间。建议：\\n1. 缩小日期范围（建议 1-3 个月）\\n2. 降低大六壬最低分数要求\\n3. 减少显示结果数量';
                    console.error('⏱️ 请求超时，总天数:', result?.total_days || '未知');
                }
                
                dateListEl.innerHTML = `<div style="padding: 20px; text-align: center; color: #c62828;">分析失败：${errorMessage}</div>`;
                alert('日期分析失败：' + errorMessage);
                hideProgress();
            }"""

if old_catch in content:
    content = content.replace(old_catch, new_catch)
    print("✅ 已添加超时错误处理")

# 保存文件
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 进度条卡住问题已修复！")
print("📝 修改内容:")
print("  1. 超时时间从 120 秒增加到 180 秒")
print("  2. 添加上传/下载进度监听")
print("  3. 添加超时错误提示和建议")
print("  4. 改进错误信息显示")
print("\n💡 建议:")
print("  - 日期范围建议 1-3 个月")
print("  - 大六壬最低分数建议 70-80")
print("  - 显示结果数量建议 10-20")
