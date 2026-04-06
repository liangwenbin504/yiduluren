"""
批量提取《图解六壬大全 2》第 207-610 页内容
使用 PyMuPDF 直接提取文本（如果可能）或 Tesseract OCR
"""

import fitz  # PyMuPDF
import os
import json
import time

# ========== 配置区域 ==========
# PDF 文件路径（动态检测）
PDF_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren'
PDF_FILE = None

# 查找目标 PDF
for f in os.listdir(PDF_DIR):
    if '图解六壬大全' in f and f.endswith('.pdf'):
        PDF_FILE = os.path.join(PDF_DIR, f)
        print(f"✓ 找到 PDF 文件：{f}")
        break

if not PDF_FILE:
    print("✗ 未找到 PDF 文件")
    exit(1)

# 页码范围
PAGE_START = 207  # 起始页码
PAGE_END = 610    # 结束页码

# 输出目录
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full'
# ===========================================


def create_output_dir():
    """创建输出目录"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"✓ 输出目录：{OUTPUT_DIR}")


def extract_page_text(pdf_path, page_num):
    """
    提取 PDF 页面文本
    
    参数：
        pdf_path: PDF 路径
        page_num: 页码（从 1 开始）
    
    返回：
        文本内容
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        text = page.get_text()
        doc.close()
        return text
    except Exception as e:
        return None


def batch_extract():
    """批量提取主流程"""
    print("\n" + "=" * 70)
    print("批量提取《图解六壬大全 2》")
    print("=" * 70)
    print(f"PDF 文件：{os.path.basename(PDF_FILE)}")
    print(f"页码范围：{PAGE_START} - {PAGE_END}（共 {PAGE_END - PAGE_START + 1} 页）")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 70)
    
    # 创建输出目录
    create_output_dir()
    
    results = []
    total_pages = PAGE_END - PAGE_START + 1
    
    print("\n开始批量提取...\n")
    
    # 打开 PDF
    doc = fitz.open(PDF_FILE)
    
    for i, page_num in enumerate(range(PAGE_START, PAGE_END + 1), 1):
        print(f"[{i}/{total_pages}] 第 {page_num} 页", end=" ")
        
        try:
            page = doc[page_num - 1]
            text = page.get_text()
            
            if text and len(text.strip()) > 0:
                # 保存文本
                txt_path = os.path.join(OUTPUT_DIR, f'page_{page_num}.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                line_count = len(text.split('\n'))
                print(f"✓ ({line_count} 行)")
                
                results.append({
                    'page': page_num,
                    'success': True,
                    'line_count': line_count,
                    'txt': txt_path
                })
            else:
                print("✗ 无文本内容（扫描版）")
                results.append({
                    'page': page_num,
                    'success': False,
                    'error': '扫描版，无文本层'
                })
                
        except Exception as e:
            print(f"✗ 错误：{e}")
            results.append({
                'page': page_num,
                'success': False,
                'error': str(e)
            })
    
    doc.close()
    
    return results


def generate_summary(results):
    """生成摘要报告"""
    print("\n" + "=" * 70)
    print("提取完成摘要")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"总页数：{total}")
    print(f"成功：{successful} 页")
    print(f"失败：{failed} 页")
    
    if failed > 0:
        print(f"\n失败的页码：{[r['page'] for r in results if not r['success']]}")
    
    # 统计字数
    total_lines = sum(r.get('line_count', 0) for r in results if r['success'])
    print(f"\n总识别行数：约 {total_lines:,} 行")
    
    # 生成合并文件
    merged_path = os.path.join(OUTPUT_DIR, 'complete_merged.txt')
    print(f"\n正在生成合并文件：{merged_path}")
    
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write("# 图解六壬大全 2 完整内容（第 207-610 页）\n\n")
        f.write(f"提取时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"页码范围：{PAGE_START}-{PAGE_END}\n")
        f.write(f"PDF 文件：{os.path.basename(PDF_FILE)}\n")
        f.write(f"提取方式：PyMuPDF 文本层提取\n")
        f.write(f"总页数：{total} 页\n")
        f.write(f"成功：{successful} 页\n")
        f.write(f"总行数：约 {total_lines:,} 行\n\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results:
            if r['success']:
                f.write(f"## 第 {r['page']} 页\n\n")
                with open(r['txt'], 'r', encoding='utf-8') as tf:
                    f.write(tf.read())
                f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"✓ 合并文件已生成")
    
    # 生成统计报告
    report_path = os.path.join(OUTPUT_DIR, '提取统计报告.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf_file': os.path.basename(PDF_FILE),
            'page_range': f'{PAGE_START}-{PAGE_END}',
            'total_pages': total,
            'successful': successful,
            'failed': failed,
            'total_lines': total_lines,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 统计报告已生成：{report_path}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("64 课全文批量提取工具（PyMuPDF 版）")
    print("=" * 70)
    
    # 执行批量提取
    results = batch_extract()
    
    # 生成摘要
    generate_summary(results)
    
    print("\n" + "=" * 70)
    print("批量提取完成！")
    print("=" * 70)
    print(f"\n输出目录：{OUTPUT_DIR}")
    print("\n生成的文件：")
    print("  - page_207.txt ~ page_610.txt（单页文本）")
    print("  - complete_merged.txt（合并文本）")
    print("  - 提取统计报告.json（统计信息）")


if __name__ == "__main__":
    main()
