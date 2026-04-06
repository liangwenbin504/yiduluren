"""
使用 PyMuPDF (fitz) 从扫描版 PDF 中提取指定页面内容
不需要 Poppler，但需要 Tesseract-OCR 进行文字识别

使用方法：
python extract_pdf_page_simple.py
"""

import os
import sys

# PDF 目录
PDF_DIR = r"d:\新建文件夹\仪度六壬择日\yiduluren"
TARGET_PAGE = 290  # 目标页码
OUTPUT_DIR = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract"

# 自动查找 PDF 文件
def find_target_pdf():
    """查找目标 PDF 文件"""
    keywords = ["图解六壬大全", "吉凶占断", "许颐平"]
    
    for file in os.listdir(PDF_DIR):
        if file.endswith('.pdf') and all(kw in file for kw in keywords):
            return os.path.join(PDF_DIR, file)
    
    return None

# 获取 PDF 文件路径
PDF_FILE = find_target_pdf()

if not PDF_FILE:
    print("=" * 70)
    print("错误：未找到目标 PDF 文件")
    print("=" * 70)
    sys.exit(1)

print(f"找到 PDF 文件：{PDF_FILE}")

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 检查 PyMuPDF 是否安装
try:
    import fitz  # PyMuPDF
    print("✓ PyMuPDF (fitz) 已安装")
except ImportError:
    print("✗ PyMuPDF 未安装")
    print("\n请运行以下命令安装：")
    print("pip install pymupdf")
    sys.exit(1)

# 检查 pytesseract 是否安装
try:
    import pytesseract
    print("✓ pytesseract 已安装")
except ImportError:
    print("✗ pytesseract 未安装")
    print("\n请运行以下命令安装：")
    print("pip install pytesseract")
    sys.exit(1)


def extract_page_with_pymupdf(pdf_path, page_num, output_image, output_text):
    """
    使用 PyMuPDF 提取 PDF 页面为图片
    
    参数：
        pdf_path: PDF 文件路径
        page_num: 页码（从 1 开始）
        output_image: 输出图片路径
        output_text: OCR 输出文本路径
    """
    print(f"\n正在使用 PyMuPDF 提取第 {page_num} 页...")
    
    try:
        # 打开 PDF
        doc = fitz.open(pdf_path)
        
        # 获取页面（页码从 0 开始）
        page = doc[page_num - 1]
        
        # 设置缩放比例（提高分辨率）
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        
        # 渲染页面为图片
        pix = page.get_pixmap(matrix=mat)
        
        # 保存图片
        pix.save(output_image)
        print(f"✓ 图片已保存：{output_image}")
        
        # 关闭文档
        doc.close()
        
        # 尝试 OCR 识别
        print("\n正在进行 OCR 识别...")
        try:
            text = pytesseract.image_to_string(
                output_image, 
                lang='chi_sim+eng'
            )
            
            # 保存文本
            with open(output_text, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✓ OCR 完成，文本已保存：{output_text}")
            
            # 显示预览
            print("\n" + "=" * 70)
            print("提取完成！预览（前 500 字符）：")
            print("=" * 70)
            print(text[:500])
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"✗ OCR 失败：{e}")
            print("\n提示：请确保已安装 Tesseract-OCR 并添加到 PATH")
            print("下载地址：https://github.com/UB-Mannheim/tesseract/wiki")
            return False
            
    except Exception as e:
        print(f"✗ 提取失败：{e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("PDF 页面提取工具（PyMuPDF 版本）")
    print("=" * 70)
    print(f"PDF 文件：{PDF_FILE}")
    print(f"目标页码：第 {TARGET_PAGE} 页")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 70)
    
    # 定义输出文件路径
    image_path = os.path.join(OUTPUT_DIR, f"page_{TARGET_PAGE}.png")
    text_path = os.path.join(OUTPUT_DIR, f"page_{TARGET_PAGE}_ocr.txt")
    
    # 提取页面
    success = extract_page_with_pymupdf(PDF_FILE, TARGET_PAGE, image_path, text_path)
    
    if success:
        print("\n" + "=" * 70)
        print("提取成功！")
        print("=" * 70)
        print(f"图片文件：{image_path}")
        print(f"文本文件：{text_path}")
        print("\n提示：OCR 识别可能存在错误，建议人工校对")
        print("校对后的文本可保存为：page_290_corrected.txt")
    else:
        print("\n提取失败，请检查错误信息")


if __name__ == "__main__":
    main()
