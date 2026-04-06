import os

pdf_dir = r'd:\新建文件夹\仪度六壬择日\yiduluren'

print("目录中的 PDF 文件：")
for f in os.listdir(pdf_dir):
    if f.endswith('.pdf'):
        print(f"  - {f}")
        full_path = os.path.join(pdf_dir, f)
        print(f"    完整路径：{full_path}")
        print(f"    存在：{os.path.exists(full_path)}")
