"""
查看 PDF 目录，确定 64 课的页码范围
"""

import fitz  # PyMuPDF
import os

# PDF 目录
PDF_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren'

# 自动查找目标 PDF
target_pdf = None
for f in os.listdir(PDF_DIR):
    if '图解六壬大全' in f and '吉凶占断' in f:
        target_pdf = os.path.join(PDF_DIR, f)
        break

if not target_pdf:
    print("✗ 未找到目标 PDF 文件")
    print("\n目录中的 PDF 文件：")
    for f in os.listdir(PDF_DIR):
        if f.endswith('.pdf'):
            print(f"  - {f}")
else:
    print(f"✓ PDF 文件已找到：{os.path.basename(target_pdf)}")
    
    # 打开 PDF
    doc = fitz.open(target_pdf)
    total_pages = len(doc)
    print(f"PDF 总页数：{total_pages} 页")
    
    # 扫描包含"课"的页面
    print("\n" + "=" * 70)
    print("搜索 64 课相关页面...")
    print("=" * 70)
    
    found_pages = []
    ke_names = []
    
    # 查找课名
    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        
        # 查找课名模式
        lines = text.split('\n')
        for line in lines[:15]:  # 只看前 15 行
            # 匹配"第 X 课"或"第十一课"等
            import re
            match = re.search(r'第 [零一二三四五六七八九十百\d]+课', line)
            if match:
                ke_name = match.group()
                found_pages.append(page_num + 1)
                ke_names.append(ke_name)
                print(f"第 {page_num + 1} 页：{ke_name}")
                break
    
    print("\n" + "=" * 70)
    print(f"共找到 {len(found_pages)} 个课")
    print("=" * 70)
    
    if found_pages:
        print(f"\n64 课范围：第 {found_pages[0]} 页 到 第 {found_pages[-1]} 页")
        
        if len(found_pages) >= 64:
            print(f"✓ 找到全部 64 课")
        else:
            print(f"⚠ 只找到 {len(found_pages)} 课，可能还有遗漏")
        
        # 显示所有课
        print("\n完整课目列表：")
        for i, (page, name) in enumerate(zip(found_pages, ke_names), 1):
            print(f"  {i:2d}. {name}: 第{page}页")
    
    # 关闭文档
    doc.close()
    
    print("\n" + "=" * 70)
    print("目录扫描完成！")
    print("=" * 70)
