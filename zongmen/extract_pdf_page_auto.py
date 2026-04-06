"""
从扫描版 PDF 中提取指定页面内容
支持 OCR 识别，适用于《图解六壬大全》等扫描版书籍

使用方法：
python extract_pdf_page_auto.py
"""

import os
import sys
from pathlib import Path

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
    print(f"在目录 {PDF_DIR} 中搜索包含以下关键词的 PDF 文件：")
    print("  - 图解六壬大全")
    print("  - 吉凶占断")
    print("  - 许颐平")
    print("\n找到的 PDF 文件：")
    for file in os.listdir(PDF_DIR):
        if file.endswith('.pdf'):
            print(f"  - {file}")
    sys.exit(1)

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def check_dependencies():
    """检查必需的依赖包"""
    print("=" * 70)
    print("检查依赖包...")
    print("=" * 70)
    
    required_packages = {
        'pdf2image': '用于将 PDF 转为图片',
        'pytesseract': 'OCR 识别引擎',
        'PIL': '图像处理',
        'pdfplumber': 'PDF 文本提取（可选）',
    }
    
    missing = []
    for package, desc in required_packages.items():
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'pytesseract':
                __import__('pytesseract')
            else:
                __import__(package)
            print(f"✓ {package:15} - {desc}")
        except ImportError:
            print(f"✗ {package:15} - {desc} - 未安装")
            missing.append(package)
    
    if missing:
        print("\n" + "=" * 70)
        print("需要安装以下包：")
        print("=" * 70)
        print("pip install " + " ".join(missing))
        print("\n另外，还需要安装 Tesseract-OCR 引擎：")
        print("下载地址：https://github.com/UB-Mannheim/tesseract/wiki")
        print("安装后需要将 tesseract.exe 添加到 PATH 或指定路径")
        return False
    
    return True


def extract_page_as_image(pdf_path, page_num, output_path, dpi=300):
    """
    将 PDF 指定页面提取为图片
    
    参数：
        pdf_path: PDF 文件路径
        page_num: 页码（从 1 开始）
        output_path: 输出图片路径
        dpi: 分辨率（默认 300）
    """
    from pdf2image import convert_from_path
    
    print(f"\n正在提取第 {page_num} 页...")
    print(f"DPI: {dpi}")
    
    try:
        # 转换指定页面为图片
        images = convert_from_path(
            pdf_path,
            first_page=page_num,
            last_page=page_num,
            dpi=dpi,
            fmt='png'
        )
        
        # 保存图片
        images[0].save(output_path, 'PNG')
        print(f"✓ 图片已保存：{output_path}")
        return output_path
        
    except Exception as e:
        print(f"✗ 提取失败：{e}")
        return None


def perform_ocr(image_path, output_txt, lang='chi_sim+eng'):
    """
    对图片进行 OCR 识别
    
    参数：
        image_path: 图片路径
        output_txt: 输出文本文件路径
        lang: 识别语言（默认简体中文 + 英文）
    """
    import pytesseract
    from PIL import Image
    
    print(f"\n正在进行 OCR 识别...")
    print(f"语言：{lang}")
    
    try:
        # 打开图片
        image = Image.open(image_path)
        
        # OCR 识别
        print("识别中，请稍候...")
        text = pytesseract.image_to_string(image, lang=lang)
        
        # 保存文本
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✓ OCR 完成，文本已保存：{output_txt}")
        return text
        
    except Exception as e:
        print(f"✗ OCR 失败：{e}")
        print("\n可能的原因：")
        print("1. Tesseract-OCR 未安装或未添加到 PATH")
        print("2. 语言包未安装（需要安装中文语言包）")
        print("\n解决方法：")
        print("1. 下载 Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. 安装中文语言包：chi_sim.traineddata")
        print("3. 将 tesseract.exe 路径添加到系统 PATH")
        return None


def enhance_image(image_path, enhanced_path):
    """
    增强图片质量（可选，用于提高 OCR 准确率）
    
    参数：
        image_path: 原图片路径
        enhanced_path: 增强后图片路径
    """
    from PIL import Image, ImageFilter, ImageEnhance
    
    print(f"\n正在增强图片质量...")
    
    try:
        # 打开图片
        image = Image.open(image_path)
        
        # 转换为灰度图
        image = image.convert('L')
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # 增强亮度
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
        
        # 锐化
        image = image.filter(ImageFilter.SHARPEN)
        
        # 二值化（可选，适用于文字清晰的扫描版）
        # threshold = 128
        # image = image.point(lambda p: 255 if p > threshold else 0)
        
        # 保存增强后的图片
        image.save(enhanced_path, 'PNG')
        print(f"✓ 图片已增强：{enhanced_path}")
        return enhanced_path
        
    except Exception as e:
        print(f"✗ 图片增强失败：{e}")
        return None


def extract_with_pdfplumber(pdf_path, page_num):
    """
    尝试使用 pdfplumber 直接提取文本（适用于部分扫描版）
    
    参数：
        pdf_path: PDF 文件路径
        page_num: 页码
    """
    import pdfplumber
    
    print(f"\n尝试直接提取文本（可能不适用于纯扫描版）...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]  # 页码从 0 开始
            text = page.extract_text()
            
            if text:
                output_path = os.path.join(OUTPUT_DIR, f"page_{page_num}_direct.txt")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"✓ 直接提取成功：{output_path}")
                return text
            else:
                print("✗ 无法直接提取文本，需要使用 OCR")
                return None
                
    except Exception as e:
        print(f"✗ 直接提取失败：{e}")
        return None


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("扫描版 PDF 内容提取工具")
    print("=" * 70)
    print(f"PDF 文件：{PDF_FILE}")
    print(f"目标页码：第 {TARGET_PAGE} 页")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 70)
    
    # 检查文件是否存在（已经在上一步确认）
    if not os.path.exists(PDF_FILE):
        print(f"\n✗ 错误：PDF 文件不存在")
        print(f"请检查路径：{PDF_FILE}")
        return
    
    # 检查依赖
    if not check_dependencies():
        print("\n请先安装必需的依赖包")
        return
    
    # 尝试直接提取文本（快速但可能失败）
    print("\n" + "=" * 70)
    print("方法 1：尝试直接提取文本")
    print("=" * 70)
    direct_text = extract_with_pdfplumber(PDF_FILE, TARGET_PAGE)
    
    if direct_text and len(direct_text.strip()) > 50:
        print("\n✓ 直接提取成功，无需 OCR")
        print(f"提取到 {len(direct_text)} 字符")
        return
    
    # 提取为图片
    print("\n" + "=" * 70)
    print("方法 2：提取为图片 + OCR 识别")
    print("=" * 70)
    
    image_path = os.path.join(OUTPUT_DIR, f"page_{TARGET_PAGE}.png")
    image_path = extract_page_as_image(PDF_FILE, TARGET_PAGE, image_path, dpi=300)
    
    if not image_path:
        print("\n✗ 图片提取失败")
        return
    
    # 可选：增强图片
    print("\n是否需要增强图片质量？")
    print("1. 是（推荐，可提高 OCR 准确率）")
    print("2. 否（直接识别）")
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == '1':
        enhanced_path = os.path.join(OUTPUT_DIR, f"page_{TARGET_PAGE}_enhanced.png")
        image_path = enhance_image(image_path, enhanced_path)
        if not image_path:
            image_path = enhanced_path
    
    # OCR 识别
    output_txt = os.path.join(OUTPUT_DIR, f"page_{TARGET_PAGE}_ocr.txt")
    ocr_text = perform_ocr(image_path, output_txt, lang='chi_sim+eng')
    
    if ocr_text:
        print("\n" + "=" * 70)
        print("提取完成！")
        print("=" * 70)
        print(f"图片文件：{image_path}")
        print(f"文本文件：{output_txt}")
        print("\n预览（前 500 字符）：")
        print("-" * 70)
        print(ocr_text[:500])
        print("-" * 70)
        
        # 询问是否需要手动校对
        print("\n提示：OCR 识别可能存在错误，建议人工校对")
        print("校对后的文本可保存为：page_290_corrected.txt")
    else:
        print("\n✗ OCR 识别失败")
        print("请检查：")
        print("1. Tesseract-OCR 是否安装")
        print("2. 中文语言包是否安装")
        print("3. tesseract.exe 是否在 PATH 中")


if __name__ == "__main__":
    main()
