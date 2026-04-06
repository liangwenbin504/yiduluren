#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从《仪度六壬选日要诀》注解中提取六相六替内容
"""

import fitz
import os
import glob

# 使用 glob 找到正确的文件名
pdf_files = glob.glob('*注解*.pdf')

keywords = [
    '六相', '六替', '化气六相', '化气六替',
    '斗首', '大六壬', '相结合', '番化',
    '三元', '决断', '生死辩', '课体'
]

print('=' * 80)
print('提取《仪度六壬选日要诀》中的六相六替理论')
print('=' * 80)
print(f"\n找到的PDF文件：{pdf_files}")

all_extracted = []

for pdf_path in pdf_files:
    print(f"\n{'='*80}")
    print(f"处理：{pdf_path}")
    print('='*80)
    
    try:
        doc = fitz.open(pdf_path)
        print(f"✓ 打开成功，共{len(doc)}页")
        
        file_results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            found = [kw for kw in keywords if kw in text]
            
            if found:
                print(f"\n【第{page_num+1}页】关键词：{', '.join(found)}")
                
                file_results.append({
                    'page': page_num + 1,
                    'keywords': found,
                    'content': text
                })
                
                # 显示前 20 行
                lines = [l for l in text.split('\n') if l.strip()]
                for line in lines[:20]:
                    print(f"  {line}")
                if len(lines) > 20:
                    print(f"  ... 还有{len(lines)-20}行")
        
        doc.close()
        
        if file_results:
            print(f"\n✓ 提取到{len(file_results)}个相关页面")
            all_extracted.append({
                'file': pdf_path,
                'pages': file_results
            })
    
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

# 保存结果
if all_extracted:
    output_file = 'extracted_liuxiang_content.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('《仪度六壬选日要诀》六相六替内容提取\n')
        f.write('斗首法与大六壬相结合特定规则\n')
        f.write('=' * 80 + '\n\n')
        
        for file_data in all_extracted:
            f.write('=' * 80 + '\n')
            f.write(f"文件：{file_data['file']}\n")
            f.write(f"相关页面数：{len(file_data['pages'])}\n")
            f.write('=' * 80 + '\n\n')
            
            for page_data in file_data['pages']:
                f.write(f"[第{page_data['page']}页] 关键词：{', '.join(page_data['keywords'])}\n")
                f.write('-' * 80 + '\n')
                f.write(page_data['content'])
                f.write('\n\n')
    
    print(f"\n✓ 结果已保存到：{output_file}")
    print(f"✓ 共{len(all_extracted)}个文件，{sum(len(fd['pages']) for fd in all_extracted)}个页面")
else:
    print("\n❌ 未提取到内容")

print('\n完成')
