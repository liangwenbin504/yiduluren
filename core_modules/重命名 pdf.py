"""
重命名 PDF 文件为简单名称
"""

import os
import shutil

pdf_dir = r'd:\新建文件夹\仪度六壬择日\yiduluren'

# 查找目标文件
target = None
for f in os.listdir(pdf_dir):
    if '图解六壬大全' in f and '吉凶占断' in f:
        target = f
        break

if not target:
    print("✗ 未找到目标文件")
else:
    src = os.path.join(pdf_dir, target)
    dst = os.path.join(pdf_dir, '[图解六壬大全 2].pdf')
    
    print(f"原文件：{target}")
    print(f"新文件：[图解六壬大全 2].pdf")
    
    # 尝试重命名
    try:
        os.rename(src, dst)
        print("✓ 重命名成功！")
    except Exception as e:
        print(f"✗ 重命名失败：{e}")
        print("\n文件可能被占用，请关闭所有程序后重试")
