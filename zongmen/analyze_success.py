# -*- coding: utf-8 -*-
"""
64 课内容分析（真正最终版）
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
        lines = f.readlines()
    print(f"✓ 总行数：{len(lines)}")
    
    # 查找所有"第 X 课"的行
    print("\n查找课的开始位置...")
    lesson_starts = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # 使用更简单的正则：第 + 任意字符 + 课
        match = re.match(r'^第.+课$', line_stripped)
        if match:
            # 确保不是"第一课也"、"第一课为"等
            if len(line_stripped) <= 6:  # 最多"第六十四课"
                lesson_starts.append((i, line_stripped))
                if len(lesson_starts) <= 10:
                    print(f"  行{i+1}: {line_stripped}")
    
    print(f"\n找到 {len(lesson_starts)} 个课的开始位置")
    
    if not lesson_starts:
        print("✗ 未找到任何课！")
        return
    
    # 提取每课信息
    lessons = []
    for idx, (line_num, lesson_line) in enumerate(lesson_starts[:64]):
        # 找下一课的位置
        next_line_num = lesson_starts[idx + 1][0] if idx + 1 < len(lesson_starts) else len(lines)
        
        # 课号
        lesson_number = lesson_line
        
        # 课名（下一行）
        title = "未知"
        if line_num + 1 < len(lines):
            next_line = lines[line_num + 1].strip()
            if ':' in next_line:
                title = next_line.split(':')[0].strip()
        
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
        
        if idx < 15 or idx % 10 == 0:
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
    
    json_path = os.path.join(OUTPUT_DIR, '64_lessons_success.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 结果已保存：{json_path}")
    
    # 生成 Markdown 表格
    md_path = os.path.join(OUTPUT_DIR, '64_lessons_success_table.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 64 课完整列表\n\n")
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
