#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时监控批量匹配进度
"""

import json
import os
import time
from datetime import datetime

PROGRESS_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\match_progress_optimized.json'

print("="*60)
print("  批量匹配进度实时监控")
print("="*60)
print()

last_completed = 0

while True:
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                
            completed = progress.get('completed', 0)
            total = progress.get('total', 8640)
            timestamp = progress.get('timestamp', '未知')
            errors = len(progress.get('error_log', []))
            
            # 计算进度
            percent = completed / total * 100 if total > 0 else 0
            remaining = total - completed
            
            # 显示进度
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"进度：{completed}/{total} ({percent:.1f}%) | "
                  f"成功：{completed-errors} | 失败：{errors} | "
                  f"剩余：{remaining}课", end="", flush=True)
            
            # 如果已完成，显示总结
            if completed >= total:
                print(f"\n\n✅ 匹配完成！")
                print(f"完成时间：{timestamp}")
                print(f"成功率：{(completed-errors)/total*100:.1f}%")
                break
                
            last_completed = completed
        else:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 等待进度文件生成...", end="", flush=True)
        
        time.sleep(5)  # 每 5 秒刷新一次
        
    except KeyboardInterrupt:
        print("\n\n监控已停止")
        break
    except Exception as e:
        print(f"\n错误：{str(e)}")
        time.sleep(5)
