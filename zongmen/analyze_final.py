# -*- coding: utf-8 -*-
"""
64 课内容分析（正确版）
"""

import json
import os
import re

INPUT_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\merged_64ke.txt'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\analysis'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 70)
    print("64 课 OCR 内容分析")
    print("=" * 70)
    
    # 加载文本
    print("\n加载文本...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f"✓ 文本长度：{len(text):,} 字符")
    
    # 按行分割
    lines = text.split('\n')
    print(f"✓ 总行数：{len(lines)}")
    
    # 查找所有"第 X 课"的行
    print("\n查找课的开始位置...")
    lesson_starts = []
    
    for i, line in enumerate(lines):
        # 匹配"第一课"、"第二课"等
        if re.match(r'^第 [一二三四五六七八九十百千\d]+课$', line.strip()):
            lesson_starts.append((i, line.strip()))
    
    print(f"找到 {len(lesson_starts)} 个课的开始位置")
    
    # 提取每课信息
    lessons = []
    for idx, (line_num, lesson_line) in enumerate(lesson_starts[:64]):
        # 找下一课的位置
        next_line_num = lesson_starts[idx + 1][0] if idx + 1 < len(lesson_starts) else len(lines)
        
        # 提取课号
        lesson_number = lesson_line
        
        # 找课名（下一行包含":"的）
        title = "未知"
        for j in range(line_num + 1, min(line_num + 5, len(lines))):
            if ':' in lines[j]:
                title = lines[j].split(':')[0].strip()
                break
        
        # 找页码
        page = "未知"
        for j in range(max(0, line_num - 20), line_num):
            page_match = re.search(r'=== 第 (\d+) 页 ===', lines[j])
            if page_match:
                page = page_match.group(1)
                break
        
        # 内容长度
        content_length = next_line_num - line_num
        
        lessons.append({
            'number': lesson_number,
            'title': title,
            'page': page,
            'length': content_length
        })
        
        if idx < 10 or idx % 10 == 0:
            print(f"  {lesson_number:6s} {title:20s} 第{page}页 {content_length:4d}行")
    
    # 统计
    print("\n" + "=" * 70)
    print("统计信息")
    print("=" * 70)
    print(f"总课数：{len(lessons)}")
    
    # 保存结果
    result = {
        'total': len(lessons),
        'lessons': lessons
    }
    
    json_path = os.path.join(OUTPUT_DIR, '64_lessons_simple.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 结果已保存：{json_path}")
    
    # 生成 Markdown 表格
    md_path = os.path.join(OUTPUT_DIR, '64_lessons_table.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 64 课列表\n\n")
        f.write("| 序号 | 课号 | 课名 | 页码 | 行数 |\n")
        f.write("|------|------|------|------|------|\n")
        
        for i, lesson in enumerate(lessons, 1):
            f.write(f"| {i:2d} | {lesson['number']:6s} | {lesson['title']:20s} | {lesson['page']:3s} | {lesson['length']:4d} |\n")
    
    print(f"✓ Markdown 表格已保存：{md_path}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ 分析完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
