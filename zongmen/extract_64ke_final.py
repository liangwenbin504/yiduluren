"""
百度 OCR 批量提取 64 课内容
页码范围：207-610（共 404 页）
"""

from aip import AipOcr
import os
import json
import time
from PIL import Image
import fitz  # PyMuPDF

# ========== 配置区域 ==========
# OCR 凭证（从调试成功页面获取）
APP_ID = '7542631'
API_KEY = 'OdZmhXw9AqtxP16uZMCbk76q'
SECRET_KEY = '1jDJjCL6rSlcsvsfg2bHBwTSIUEM4bc'

# PDF 文件路径
PDF_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren'
PDF_FILE = None

# 查找 PDF 文件
for f in os.listdir(PDF_DIR):
    if '图解六壬大全' in f and f.endswith('.pdf'):
        PDF_FILE = os.path.join(PDF_DIR, f)
        print(f"✓ 找到 PDF 文件：{f}")
        break

if not PDF_FILE or not os.path.exists(PDF_FILE):
    print("✗ 未找到 PDF 文件！")
    exit(1)

# 页码范围
PAGE_START = 207
PAGE_END = 610

# 输出目录
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full'
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')
OCR_DIR = os.path.join(OUTPUT_DIR, 'ocr_result')

# ===========================================


def create_output_dirs():
    """创建输出目录"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(OCR_DIR, exist_ok=True)
    print(f"✓ 输出目录已创建")


def pdf_to_images():
    """将 PDF 页面转换为图片"""
    print("\n" + "=" * 70)
    print("步骤 1: 将 PDF 转换为图片")
    print("=" * 70)
    
    doc = fitz.open(PDF_FILE)
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        img_path = os.path.join(IMAGES_DIR, f'page_{page_num}.png')
        
        # 如果图片已存在，跳过
        if os.path.exists(img_path):
            print(f"  第 {page_num} 页：✓ (已存在)")
            continue
        
        try:
            page = doc[page_num - 1]  # 页码从 0 开始
            
            # 转换为图片（300 DPI）
            mat = fitz.Matrix(2, 2)  # 2 倍缩放
            pix = page.get_pixmap(matrix=mat)
            pix.save(img_path)
            
            print(f"  第 {page_num} 页：✓ 转换成功")
            
        except Exception as e:
            print(f"  第 {page_num} 页：✗ 失败 ({e})")
    
    doc.close()
    print(f"\n图片转换完成！")


def batch_ocr():
    """批量 OCR 识别"""
    print("\n" + "=" * 70)
    print("步骤 2: 批量 OCR 识别")
    print("=" * 70)
    
    # 初始化客户端
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    
    results = []
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        img_path = os.path.join(IMAGES_DIR, f'page_{page_num}.png')
        
        if not os.path.exists(img_path):
            print(f"  第 {page_num} 页：✗ 图片不存在")
            results.append({
                'page': page_num,
                'success': False,
                'error': '图片不存在'
            })
            continue
        
        # 检查是否已有 OCR 结果
        ocr_path = os.path.join(OCR_DIR, f'page_{page_num}.json')
        if os.path.exists(ocr_path):
            print(f"  第 {page_num} 页：✓ (已识别)")
            with open(ocr_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            results.append({
                'page': page_num,
                'success': True,
                'word_count': len(result.get('words_result', []))
            })
            continue
        
        print(f"  正在识别第 {page_num} 页...")
        
        try:
            # 读取图片
            with open(img_path, 'rb') as f:
                image = f.read()
            
            # 调用 OCR（使用高精度版）
            result = client.basicAccurate(image, {
                'recognize_granularity': 'big',
                'probability': 'true',
            })
            
            # 保存结果
            with open(ocr_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 同时保存 TXT 格式
            txt_path = os.path.join(OCR_DIR, f'page_{page_num}.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                if 'words_result' in result:
                    for word in result['words_result']:
                        f.write(word['words'] + '\n')
            
            word_count = len(result.get('words_result', []))
            
            print(f"    ✓ 识别成功 ({word_count} 行)")
            
            results.append({
                'page': page_num,
                'success': True,
                'word_count': word_count
            })
            
            # 避免频率限制，每 10 次请求暂停 1 秒
            if (page_num - PAGE_START) % 10 == 0:
                time.sleep(1)
            
        except Exception as e:
            print(f"    ✗ 识别失败：{e}")
            results.append({
                'page': page_num,
                'success': False,
                'error': str(e)
            })
    
    return results


def generate_report(results):
    """生成摘要报告"""
    print("\n" + "=" * 70)
    print("识别完成摘要")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    total_words = sum(r.get('word_count', 0) for r in results if r['success'])
    
    print(f"总页数：{total}")
    print(f"成功：{successful} 页")
    print(f"失败：{failed} 页")
    print(f"总文字行数：{total_words} 行")
    
    if failed > 0:
        print(f"\n失败的页码：{[r['page'] for r in results if not r['success']]}")
    
    # 生成合并文件
    merged_path = os.path.join(OUTPUT_DIR, '64_ke_merged.txt')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write("# 六壬大全 64 课内容（OCR 识别）\n\n")
        f.write(f"识别时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"页码范围：{PAGE_START}-{PAGE_END}\n")
        f.write(f"总页数：{successful} 页\n")
        f.write(f"总文字行数：{total_words} 行\n")
        f.write(f"识别引擎：百度 OCR 高精度版\n\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results:
            if r['success']:
                page_num = r['page']
                f.write(f"## 第 {page_num} 页\n\n")
                
                txt_path = os.path.join(OCR_DIR, f'page_{page_num}.txt')
                with open(txt_path, 'r', encoding='utf-8') as tf:
                    f.write(tf.read())
                
                f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"\n合并文件已保存：{merged_path}")
    print(f"\n各页识别情况：")
    
    # 每 50 页显示一次摘要
    for i in range(0, len(results), 50):
        chunk = results[i:i+50]
        success_count = sum(1 for r in chunk if r['success'])
        print(f"  第 {PAGE_START+i}-{PAGE_START+i+len(chunk)-1} 页：{success_count}/{len(chunk)} 成功")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("六壬大全 64 课批量提取工具")
    print("=" * 70)
    print(f"\nPDF 文件：{PDF_FILE}")
    print(f"页码范围：{PAGE_START}-{PAGE_END}（共 {PAGE_END-PAGE_START+1} 页）")
    print(f"输出目录：{OUTPUT_DIR}")
    
    # 创建目录
    create_output_dirs()
    
    # 转换 PDF 为图片
    pdf_to_images()
    
    # 批量 OCR
    results = batch_ocr()
    
    # 生成报告
    generate_report(results)
    
    print("\n" + "=" * 70)
    print("批量提取完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
