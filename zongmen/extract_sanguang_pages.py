"""
批量提取 PDF 指定页面范围（三光课专题：292-297 页）
使用 PyMuPDF (fitz) + Tesseract OCR

使用方法：
python extract_sanguang_pages.py
"""

import os
import sys
import fitz  # PyMuPDF
import pytesseract

# PDF 目录
PDF_DIR = r"d:\新建文件夹\仪度六壬择日\yiduluren"
PAGE_START = 292  # 起始页码
PAGE_END = 297    # 结束页码
OUTPUT_DIR = r"d:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang"

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

# 检查依赖
try:
    import fitz
    print("✓ PyMuPDF (fitz) 已安装")
except ImportError:
    print("✗ PyMuPDF 未安装")
    print("请运行：pip install pymupdf")
    sys.exit(1)

try:
    import pytesseract
    print("✓ pytesseract 已安装")
except ImportError:
    print("✗ pytesseract 未安装")
    print("请运行：pip install pytesseract")
    sys.exit(1)


def extract_page_with_pymupdf(pdf_path, page_num, output_image):
    """
    使用 PyMuPDF 提取 PDF 页面为图片
    
    参数：
        pdf_path: PDF 文件路径
        page_num: 页码（从 1 开始）
        output_image: 输出图片路径
    
    返回：
        成功返回 True，失败返回 False
    """
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
        
        # 关闭文档
        doc.close()
        
        return True
            
    except Exception as e:
        print(f"✗ 提取第 {page_num} 页失败：{e}")
        return False


def perform_ocr(image_path, output_txt, lang='chi_sim+eng'):
    """
    对图片进行 OCR 识别
    
    参数：
        image_path: 图片路径
        output_txt: 输出文本文件路径
        lang: 识别语言
    
    返回：
        识别的文本，失败返回 None
    """
    try:
        from PIL import Image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=lang)
        
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return text
        
    except Exception as e:
        print(f"✗ OCR 失败：{e}")
        return None


def extract_pages_batch():
    """批量提取页面"""
    print("\n" + "=" * 70)
    print("批量提取三光课内容（第 292-297 页）")
    print("=" * 70)
    print(f"PDF 文件：{PDF_FILE}")
    print(f"页码范围：{PAGE_START} - {PAGE_END}")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 70)
    
    results = []
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        print(f"\n正在处理第 {page_num} 页...")
        
        # 定义输出文件路径
        image_path = os.path.join(OUTPUT_DIR, f"page_{page_num}.png")
        text_path = os.path.join(OUTPUT_DIR, f"page_{page_num}_ocr.txt")
        
        # 提取页面为图片
        success = extract_page_with_pymupdf(PDF_FILE, page_num, image_path)
        
        if not success:
            print(f"  ✗ 第 {page_num} 页提取失败")
            results.append({
                'page': page_num,
                'success': False,
                'image': None,
                'text': None
            })
            continue
        
        print(f"  ✓ 图片已保存：{image_path}")
        
        # OCR 识别
        print(f"  正在进行 OCR 识别...")
        ocr_text = perform_ocr(image_path, text_path)
        
        if ocr_text:
            print(f"  ✓ OCR 完成：{text_path}")
            results.append({
                'page': page_num,
                'success': True,
                'image': image_path,
                'text': ocr_text,
                'char_count': len(ocr_text)
            })
        else:
            print(f"  ✗ OCR 失败")
            results.append({
                'page': page_num,
                'success': False,
                'image': image_path,
                'text': None
            })
    
    return results


def generate_summary(results):
    """生成提取摘要报告"""
    print("\n" + "=" * 70)
    print("提取完成摘要")
    print("=" * 70)
    
    total_pages = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_pages - successful
    
    print(f"总页数：{total_pages}")
    print(f"成功：{successful} 页")
    print(f"失败：{failed} 页")
    
    if failed > 0:
        print(f"\n失败的页码：{[r['page'] for r in results if not r['success']]}")
    
    print("\n各页提取情况：")
    for r in results:
        if r['success']:
            print(f"  第 {r['page']} 页：✓ ({r['char_count']} 字符)")
        else:
            print(f"  第 {r['page']} 页：✗")
    
    # 生成合并文本
    merged_text_path = os.path.join(OUTPUT_DIR, "sanguang_merged.txt")
    with open(merged_text_path, 'w', encoding='utf-8') as f:
        f.write("# 三光课内容整理（第 292-297 页）\n\n")
        f.write(f"提取时间：2026-03-21\n")
        f.write(f"PDF 文件：{PDF_FILE}\n")
        f.write(f"页码范围：{PAGE_START}-{PAGE_END}\n\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results:
            if r['success']:
                f.write(f"## 第 {r['page']} 页\n\n")
                f.write(r['text'])
                f.write("\n\n" + "=" * 70 + "\n\n")
    
    print(f"\n合并文本已保存：{merged_text_path}")
    
    return results


def main():
    """主函数"""
    # 批量提取页面
    results = extract_pages_batch()
    
    # 生成摘要报告
    generate_summary(results)
    
    print("\n" + "=" * 70)
    print("全部处理完成！")
    print("=" * 70)
    print(f"\n输出目录：{OUTPUT_DIR}")
    print("\n生成的文件：")
    print("  - page_292.png 到 page_297.png（页面图片）")
    print("  - page_292_ocr.txt 到 page_297_ocr.txt（OCR 文本）")
    print("  - sanguang_merged.txt（合并文本）")
    
    print("\n提示：")
    print("  1. OCR 识别可能存在错误，建议人工校对")
    print("  2. 可以查看图片对照校对文本")
    print("  3. 校对后的文本可保存为：sanguang_corrected.txt")


if __name__ == "__main__":
    main()
