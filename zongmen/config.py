"""
统一配置文件路径
所有脚本都从这里获取文件路径
"""

import os

# 项目根目录
PROJECT_ROOT = r'd:\新建文件夹\仪度六壬择日\yiduluren'

# PDF 文件路径
PDF_FILE = os.path.join(PROJECT_ROOT, '[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf')

# 检查文件是否存在
if not os.path.exists(PDF_FILE):
    # 尝试新文件名
    PDF_FILE_NEW = os.path.join(PROJECT_ROOT, '[图解六壬大全 2].pdf')
    if os.path.exists(PDF_FILE_NEW):
        PDF_FILE = PDF_FILE_NEW
        print("✓ 使用新文件名：[图解六壬大全 2].pdf")
    else:
        print("✗ PDF 文件不存在")
        print(f"尝试路径 1: {PDF_FILE}")
        print(f"尝试路径 2: {PDF_FILE_NEW}")
else:
    print("✓ 使用原文件名")

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'zongmen', 'pdf_extract')

# 64 课输出目录
KE_64_OUTPUT = os.path.join(OUTPUT_DIR, '64_ke_baidu')

# 三光课输出目录
SANGUANG_OUTPUT = os.path.join(OUTPUT_DIR, 'sanguang')

# 720 课例数据库
KE_LI_720 = os.path.join(PROJECT_ROOT, 'zongmen', 'data', '720_ke_li_jiu_zong_men.json')

print(f"\n项目根目录：{PROJECT_ROOT}")
print(f"PDF 文件：{PDF_FILE}")
print(f"输出目录：{OUTPUT_DIR}")
