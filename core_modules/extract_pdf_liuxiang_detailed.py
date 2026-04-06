#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从《仪度六壬选日要诀》注解中提取六相六替内容
重点关注斗首法与大六壬相结合的特定规则
"""

import fitz  # PyMuPDF
import os

pdf_files = [
    r'd:\新建文件夹\仪度六壬择日\yiduluren\1《仪度六壬选日要诀》注解 1.pdf',
    r'd:\新建文件夹\仪度六壬择日\yiduluren\2《仪度六壬选日要诀》注解 2.pdf'
]

# 关键词列表（按优先级排序）
keywords = [
    '六相', '六替', '化气六相', '化气六替',
    '斗首', '大六壬', '相结合', '番化',
    '三元', '决断', '生死辩', '课体'
]

print('=' * 80)
print('提取《仪度六壬选日要诀》中的六相六替理论')
print('重点关注：斗首法与大六壬相结合的特定规则')
print('=' * 80)

all_extracted_content = []

for pdf_path in pdf_files:
    if not os.path.exists(pdf_path):
        print(f"\n❌ 文件不存在：{pdf_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"正在处理：{os.path.basename(pdf_path)}")
    print('='*80)
    
    try:
        doc = fitz.open(pdf_path)
        print(f"✓ PDF 文件打开成功，共{len(doc)}页")
        
        file_content = []
        
        # 遍历所有页面
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # 检查是否包含关键词
            found_keywords = [kw for kw in keywords if kw in text]
            
            if found_keywords:
                print(f"\n【第{page_num + 1}页】找到关键词：{', '.join(found_keywords)}")
                print('-' * 80)
                
                # 提取整页内容
                file_content.append({
                    'page': page_num + 1,
                    'keywords': found_keywords,
                    'content': text
                })
                
                # 显示内容摘要
                lines = text.split('\n')
                # 打印前 30 行作为摘要
                for i, line in enumerate(lines[:30]):
                    if line.strip():
                        print(f"  {line}")
                
                if len(lines) > 30:
                    print(f"  ... (还有{len(lines) - 30}行)")
        
        doc.close()
        
        if file_content:
            print(f"\n✓ 从该文件提取到 {len(file_content)} 个相关页面")
            all_extracted_content.append({
                'file': os.path.basename(pdf_path),
                'content': file_content
            })
        else:
            print("\n⚠ 未找到六相六替相关内容")
    
    except Exception as e:
        print(f"\n❌ 读取失败：{e}")
        import traceback
        traceback.print_exc()

# 保存提取结果
print('\n' + '=' * 80)
print('提取完成，保存结果...')
print('=' * 80)

if all_extracted_content:
    # 保存为 TXT 文件
    output_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\core_modules\extracted_liuxiang_liuti_content.txt'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('《仪度六壬选日要诀》六相六替内容提取\n')
        f.write('斗首法与大六壬相结合特定规则\n')
        f.write('=' * 80 + '\n\n')
        
        for file_data in all_extracted_content:
            f.write('=' * 80 + '\n')
            f.write(f"文件：{file_data['file']}\n")
            f.write('=' * 80 + '\n\n')
            
            for page_data in file_data['content']:
                f.write(f"[第{page_data['page']}页] 关键词：{', '.join(page_data['keywords'])}\n")
                f.write('-' * 80 + '\n')
                f.write(page_data['content'])
                f.write('\n\n')
    
    print(f"\n✓ 提取结果已保存到：{output_path}")
    print(f"✓ 共从 {len(all_extracted_content)} 个文件中提取到内容")
    total_pages = sum(len(fc['content']) for fc in all_extracted_content)
    print(f"✓ 总计 {total_pages} 个相关页面")
else:
    print("\n❌ 未提取到任何内容")

print('\n' + '=' * 80)
print('所有处理完成')
print('=' * 80)
