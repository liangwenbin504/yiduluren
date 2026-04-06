"""
查看 PDF 指定页面内容
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
    print("✗ 未找到 PDF 文件")
else:
    print(f"✓ PDF 文件：{os.path.basename(target_pdf)}")
    
    doc = fitz.open(target_pdf)
    
    # 查看第 291-298 页（三光课应该在 292 页左右）
    print("\n查看第 291-298 页内容：")
    print("=" * 70)
    
    for page_num in range(290, min(298, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        
        print(f"\n第 {page_num + 1} 页：")
        print("-" * 70)
        # 显示前 500 字符
        print(text[:500] if text else "(无法提取文本，可能是扫描图片)")
        print("-" * 70)
    
    doc.close()
