"""
使用百度 OCR 批量提取 PDF 中 64 课完整内容
页码范围：292-355 页（覆盖全部 64 课）
高精度识别，支持古籍文字

配置说明：
已配置百度 OCR API 密钥，直接运行即可
"""

from aip import AipOcr
import os
import json
import time

# ========== 配置区域 ==========
# 百度 OCR API 密钥
APP_ID = '122484585'
API_KEY = 'fHvvwcgIFlKucSeAtcx53DlK'
SECRET_KEY = 'WxKzp9GaOBfdAACPm5sLdckYWG6cjQ1'

# PDF 文件路径
PDF_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf'

# 64 课页码范围（根据实际 PDF）
PAGE_START = 292  # 第 1 课开始
PAGE_END = 355    # 第 64 课结束

# 输出目录
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_baidu'
# ===========================================


def create_output_dir():
    """创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✓ 输出目录：{OUTPUT_DIR}")


def initialize_client():
    """初始化百度 OCR 客户端"""
    print("\n正在初始化百度 OCR 客户端...")
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    
    # 测试连接
    try:
        # 先检查是否有测试图片
        test_img = os.path.join(OUTPUT_DIR, '../sanguang/page_292.png')
        if os.path.exists(test_img):
            with open(test_img, 'rb') as f:
                image = f.read()
            client.basicAccurate(image, {'recognize_granularity': 'big'})
            print("✓ 连接百度 OCR 成功！")
        else:
            print("✓ 百度 OCR 客户端已初始化")
    except Exception as e:
        print(f"✗ 连接失败：{e}")
        return None
    
    return client


def recognize_pdf_page(client, pdf_path, page_num):
    """
    识别 PDF 指定页面
    
    参数：
        client: AipOcr 客户端
        pdf_path: PDF 文件路径
        page_num: 页码
    
    返回：
        识别结果
    """
    # 注意：百度 OCR 不支持直接识别 PDF，需要先转为图片
    # 这里我们使用已有的图片
    img_path = os.path.join(OUTPUT_DIR, f'page_{page_num}.png')
    
    if not os.path.exists(img_path):
        print(f"  ✗ 图片不存在：{img_path}")
        return None
    
    with open(img_path, 'rb') as f:
        image = f.read()
    
    # 调用高精度识别
    result = client.basicAccurate(image, {
        'recognize_granularity': 'big',
        'probability': 'true'
    })
    
    return result


def batch_recognite_pages(client):
    """批量识别所有页面"""
    print("\n" + "=" * 70)
    print("开始批量识别 64 课内容")
    print("=" * 70)
    print(f"页码范围：{PAGE_START} - {PAGE_END}")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 70)
    
    results = []
    total_pages = PAGE_END - PAGE_START + 1
    
    for i, page_num in enumerate(range(PAGE_START, PAGE_END + 1), 1):
        print(f"\n[{i}/{total_pages}] 正在识别第 {page_num} 页...")
        
        try:
            result = recognize_pdf_page(client, PDF_FILE, page_num)
            
            if result and 'words_result' in result:
                # 保存文本
                txt_path = os.path.join(OUTPUT_DIR, f'page_{page_num}.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    for word in result['words_result']:
                        f.write(word['words'] + '\n')
                
                # 保存 JSON
                json_path = os.path.join(OUTPUT_DIR, f'page_{page_num}.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                word_count = len(result['words_result'])
                print(f"  ✓ 识别成功（{word_count} 行）")
                
                results.append({
                    'page': page_num,
                    'success': True,
                    'word_count': word_count,
                    'txt': txt_path,
                    'json': json_path
                })
                
                # 避免频率限制
                if i % 10 == 0:
                    print("  等待 1 秒...")
                    time.sleep(1)
            else:
                print(f"  ✗ 识别失败")
                results.append({
                    'page': page_num,
                    'success': False,
                    'error': '无识别结果'
                })
                
        except Exception as e:
            print(f"  ✗ 错误：{e}")
            results.append({
                'page': page_num,
                'success': False,
                'error': str(e)
            })
    
    return results


def generate_summary(results):
    """生成摘要报告"""
    print("\n" + "=" * 70)
    print("识别完成摘要")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"总页数：{total}")
    print(f"成功：{successful} 页")
    print(f"失败：{failed} 页")
    
    if failed > 0:
        print(f"\n失败的页码：{[r['page'] for r in results if not r['success']]}")
    
    # 生成合并文件
    merged_path = os.path.join(OUTPUT_DIR, '64_ke_complete.txt')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write("# 64 课完整内容（百度 OCR 高精度识别）\n\n")
        f.write(f"识别时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"页码范围：{PAGE_START}-{PAGE_END}\n")
        f.write(f"识别引擎：百度 OCR 高精度版\n")
        f.write(f"PDF 文件：{PDF_FILE}\n\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results:
            if r['success']:
                f.write(f"## 第 {r['page']} 页\n\n")
                with open(r['txt'], 'r', encoding='utf-8') as tf:
                    f.write(tf.read())
                f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"\n合并文件已保存：{merged_path}")
    
    # 生成统计报告
    report_path = os.path.join(OUTPUT_DIR, '识别统计报告.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_pages': total,
            'successful': successful,
            'failed': failed,
            'results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, ensure_ascii=False, indent=2)
    
    print(f"统计报告已保存：{report_path}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("64 课内容批量提取工具")
    print("=" * 70)
    
    # 创建输出目录
    create_output_dir()
    
    # 初始化客户端
    client = initialize_client()
    if not client:
        return
    
    # 批量识别
    results = batch_recognite_pages(client)
    
    # 生成摘要
    generate_summary(results)
    
    print("\n" + "=" * 70)
    print("批量提取完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
