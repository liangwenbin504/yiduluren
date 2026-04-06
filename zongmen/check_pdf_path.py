import os
from pathlib import Path

# PDF 目录
pdf_dir = r"d:\新建文件夹\仪度六壬择日\yiduluren"

print("=" * 70)
print("检查 PDF 文件")
print("=" * 70)

# 列出所有 PDF 文件
print(f"\n目录：{pdf_dir}")
print("\n找到的 PDF 文件：")
for file in os.listdir(pdf_dir):
    if file.endswith('.pdf'):
        full_path = os.path.join(pdf_dir, file)
        print(f"  - {file}")
        print(f"    完整路径：{full_path}")
        print(f"    存在：{os.path.exists(full_path)}")
        print()

# 目标文件
target_file = "[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf"
target_path = os.path.join(pdf_dir, target_file)

print("=" * 70)
print(f"目标文件：{target_file}")
print(f"完整路径：{target_path}")
print(f"文件存在：{os.path.exists(target_path)}")
print("=" * 70)
