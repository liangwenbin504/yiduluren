# -*- coding: utf-8 -*-
"""
百度 OCR 批量提取 64 课内容（高精度版 - 已充值）
页码范围：207-610（共 404 页）
"""

import requests
import base64
import os
import json
import time
import fitz  # PyMuPDF

# ========== 配置区域 ==========
# OCR 凭证
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = 'aVIqswuOu3BArSpV1A2xsGVu7WyhzCuO'

# PDF 文件路径
PDF_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren'
PDF_FILE = None

# 查找 PDF 文件
for f in os.listdir(PDF_DIR):
    if '图解六壬大全' in f and f.endswith('.pdf'):
        PDF_FILE = os.path.join(PDF_DIR, f)
        print(f"OK 找到 PDF 文件：{f}")
        break

if not PDF_FILE or not os.path.exists(PDF_FILE):
    print("X 未找到 PDF 文件！")
    exit(1)

# 页码范围
PAGE_START = 207
PAGE_END = 610

# 输出目录
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full'
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'images')
OCR_DIR = os.path.join(OUTPUT_DIR, 'ocr_result')

# ===========================================


def get_access_token():
    """获取 access_token（使用 API_KEY 作为 client_id）"""
    token_url = "https://aip.baidubce.com/oauth/2.0/token"
    token_params = {
        'grant_type': 'client_credentials',
        'client_id': API_KEY,  # 关键：使用 API_KEY，不是 APP_ID
        'client_secret': SECRET_KEY
    }
    
    response = requests.post(token_url, params=token_params, timeout=15)
    result = response.json()
    
    if 'access_token' not in result:
        raise Exception(f"获取 token 失败：{result.get('error_description')}")
    
    return result['access_token']


def create_output_dirs():
    """创建输出目录"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(OCR_DIR, exist_ok=True)
    print(f"OK 输出目录已创建")


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
            print(f"  第 {page_num} 页：OK (已存在)")
            continue
        
        try:
            page = doc[page_num - 1]  # 页码从 0 开始
            
            # 转换为图片（300 DPI）
            mat = fitz.Matrix(2, 2)  # 2 倍缩放
            pix = page.get_pixmap(matrix=mat)
            pix.save(img_path)
            
            print(f"  第 {page_num} 页：OK 转换成功")
            
        except Exception as e:
            print(f"  第 {page_num} 页：X 失败 ({e})")
    
    doc.close()
    print(f"\n图片转换完成！")


def ocr_single_page(img_path, access_token):
    """对单张图片进行 OCR 识别（高精度版）"""
    with open(img_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # 使用高精度版 API
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'image': image_data, 'type': 'BASE64'}
    
    response = requests.post(ocr_url, headers=headers, data=data, timeout=60)
    result = response.json()
    
    # 检查错误
    if 'error_code' in result:
        return None, f"错误 {result['error_code']}: {result['error_msg']}"
    
    return result, None


def batch_ocr():
    """批量 OCR 识别"""
    print("\n" + "=" * 70)
    print("步骤 2: 批量 OCR 识别（高精度版）")
    print("=" * 70)
    
    # 获取 access_token
    print("正在获取 access_token...")
    try:
        access_token = get_access_token()
        print("OK access_token 获取成功")
    except Exception as e:
        print(f"X 获取 token 失败：{e}")
        return
    
    results = []
    success_count = 0
    error_count = 0
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        img_path = os.path.join(IMAGES_DIR, f'page_{page_num}.png')
        
        if not os.path.exists(img_path):
            print(f"  第 {page_num} 页：X 图片不存在")
            error_count += 1
            continue
        
        # OCR 识别
        result, error = ocr_single_page(img_path, access_token)
        
        if error:
            print(f"  第 {page_num} 页：X {error}")
            error_count += 1
            # 保存错误信息
            page_result = {
                'page': page_num,
                'error': error,
                'words_result': []
            }
        else:
            print(f"  第 {page_num} 页：OK 识别成功 ({len(result.get('words_result', []))} 行)")
            success_count += 1
            page_result = {
                'page': page_num,
                'words_result': result.get('words_result', [])
            }
        
        results.append(page_result)
        
        # 保存单页结果
        json_path = os.path.join(OCR_DIR, f'page_{page_num}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(page_result, f, ensure_ascii=False, indent=2)
        
        # 同时保存为 TXT
        txt_path = os.path.join(OCR_DIR, f'page_{page_num}.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== 第 {page_num} 页 ===\n\n")
            if page_result.get('words_result'):
                for item in page_result['words_result']:
                    f.write(f"{item.get('words', '')}\n")
            else:
                f.write("无识别内容\n")
        
        # 短暂延迟，避免请求过快
        time.sleep(0.2)
    
    # 保存汇总报告
    summary_path = os.path.join(OUTPUT_DIR, 'summary.json')
    summary = {
        'total_pages': PAGE_END - PAGE_START + 1,
        'success_count': success_count,
        'error_count': error_count,
        'success_rate': f"{success_count / (PAGE_END - PAGE_START + 1) * 100:.1f}%",
        'results': results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n" + "=" * 70)
    print(f"OCR 识别完成！")
    print(f"总页数：{PAGE_END - PAGE_START + 1}")
    print(f"成功：{success_count} 页")
    print(f"失败：{error_count} 页")
    print(f"成功率：{summary['success_rate']}")
    print(f"结果保存在：{OUTPUT_DIR}")
    print("=" * 70)


def merge_results():
    """合并所有识别结果"""
    print("\n" + "=" * 70)
    print("步骤 3: 合并识别结果")
    print("=" * 70)
    
    merged_text = []
    
    for page_num in range(PAGE_START, PAGE_END + 1):
        txt_path = os.path.join(OCR_DIR, f'page_{page_num}.txt')
        
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                merged_text.append(content)
    
    # 保存合并文件
    merged_path = os.path.join(OUTPUT_DIR, 'merged_64ke.txt')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(merged_text))
    
    print(f"OK 合并完成：{merged_path}")
    print("=" * 70)


if __name__ == '__main__':
    print("=" * 70)
    print("百度 OCR 批量提取 64 课内容（高精度版）")
    print("页码范围：207-610（共 404 页）")
    print("=" * 70)
    print(f"\nOCR 凭证:")
    print(f"  API Key: {API_KEY[:20]}...")
    print(f"  Secret Key: {SECRET_KEY[:20]}...")
    print(f"\nPDF 文件：{PDF_FILE}")
    
    # 创建输出目录
    create_output_dirs()
    
    # 步骤 1: PDF 转图片
    pdf_to_images()
    
    # 步骤 2: 批量 OCR
    batch_ocr()
    
    # 步骤 3: 合并结果
    merge_results()
    
    print("\nOK 全部任务完成！")
