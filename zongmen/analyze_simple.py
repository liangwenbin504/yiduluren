# -*- coding: utf-8 -*-
"""
64 课内容分析（最终版）
"""

import json
import os
import re

# 输入文件
INPUT_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\merged_64ke.txt'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\analysis'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_text():
    """加载 OCR 提取的文本"""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def split_by_lesson(text):
    """按课分割文本"""
    print("\n分析文本结构...")
    
    # 使用更简单的模式：第 X 课
    lesson_pattern = r'(第 [一二三四五六七八九十百千 0-9]+课)'
    matches = list(re.finditer(lesson_pattern, text))
    
    print(f"找到 {len(matches)} 个课的开始位置")
    
    lessons = []
    
    for i, match in enumerate(matches[:64]):  # 最多 64 课
        lesson_start = match.start()
        lesson_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        lesson_content = text[lesson_start:lesson_end]
        lesson_number = match.group(1)
        
        # 提取课名标题（第 X 课后面的内容）
        lines = lesson_content.split('\n')
        title = '未知'
        for line in lines[:5]:  # 在前 5 行找
            if lesson_number in line and ':' in line:
                title = line.split(':')[0].replace(lesson_number, '').strip()
                break
            elif lesson_number == line.strip():
                # 下一行可能是标题
                if i + 1 < len(lines) and ':' in lines[i + 1]:
                    title = lines[i + 1].split(':')[0].strip()
                break
        
        # 找到对应的页码
        page_search = text[max(0, lesson_start-500):lesson_start]
        page_match = re.search(r'=== 第 (\d+) 页 ===', page_search)
        page_num = page_match.group(1) if page_match else '未知'
        
        lessons.append({
            'lesson_number': lesson_number,
            'title': title,
            'page': page_num,
            'content': lesson_content[:500],
            'full_length': lesson_end - lesson_start
        })
        
        print(f"  {lesson_number}: {title} (第{page_num}页)")
    
    return lessons


def analyze_lessons(lessons):
    """分析每课的特征"""
    print("\n" + "=" * 70)
    print("分析每课特征")
    print("=" * 70)
    
    lessons_info = []
    
    for i, lesson in enumerate(lessons, 1):
        content = lesson['content']
        
        info = {
            'lesson_number': lesson['lesson_number'],
            'title': lesson['title'],
            'page': lesson['page'],
            'content_length': lesson['full_length'],
            'has_original': '【原文】' in content or '原文' in content,
            'has_translation': '【白话提要】' in content or '白话' in content,
            'has_diagram': '图' in content or '图解' in content,
        }
        
        # 判断吉凶
        if any(word in content for word in ['大吉', '元吉', '福祐', '顺利']):
            info['fortune'] = '吉'
        elif any(word in content for word in ['凶', '祸', '灾', '难']):
            info['fortune'] = '凶'
        else:
            info['fortune'] = '平'
        
        lessons_info.append(info)
        
        if i <= 10 or i % 10 == 0:
            print(f"  [{i:2d}] {lesson['lesson_number']:5s} {lesson['title']:15s} {info['fortune']} 原文:{'✓' if info['has_original'] else '✗'} 白话:{'✓' if info['has_translation'] else '✗'}")
    
    return lessons_info


def create_statistics(lessons_info):
    """创建统计信息"""
    print("\n" + "=" * 70)
    print("创建统计信息")
    print("=" * 70)
    
    stats = {
        'total': len(lessons_info),
        'with_original': sum(1 for l in lessons_info if l['has_original']),
        'with_translation': sum(1 for l in lessons_info if l['has_translation']),
        'with_diagram': sum(1 for l in lessons_info if l['has_diagram']),
        'fortune': {
            '吉': sum(1 for l in lessons_info if l.get('fortune') == '吉'),
            '凶': sum(1 for l in lessons_info if l.get('fortune') == '凶'),
            '平': sum(1 for l in lessons_info if l.get('fortune') == '平')
        }
    }
    
    print(f"\n总课数：{stats['total']}")
    print(f"有原文：{stats['with_original']} 课")
    print(f"有白话：{stats['with_translation']} 课")
    print(f"有图解：{stats['with_diagram']} 课")
    print(f"吉凶分布：吉{stats['fortune']['吉']} / 凶{stats['fortune']['凶']} / 平{stats['fortune']['平']}")
    
    return stats


def save_results(lessons_info, stats):
    """保存结果"""
    print("\n" + "=" * 70)
    print("保存结果")
    print("=" * 70)
    
    # 保存 JSON
    result = {
        'statistics': stats,
        'lessons': lessons_info
    }
    
    json_path = os.path.join(OUTPUT_DIR, '64_lessons_analysis.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON 已保存：{json_path}")
    
    # 保存 Markdown 报告
    md_path = os.path.join(OUTPUT_DIR, '64_lessons_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 64 课 OCR 内容分析报告\n\n")
        f.write(f"## 统计摘要\n\n")
        f.write(f"- 总课数：{stats['total']}\n")
        f.write(f"- 有原文：{stats['with_original']} 课\n")
        f.write(f"- 有白话：{stats['with_translation']} 课\n")
        f.write(f"- 有图解：{stats['with_diagram']} 课\n")
        f.write(f"- 吉凶分布：吉{stats['fortune']['吉']} / 凶{stats['fortune']['凶']} / 平{stats['fortune']['平']}\n\n")
        
        f.write("## 64 课列表\n\n")
        f.write("| 序号 | 课号 | 课名 | 页码 | 吉凶 | 原文 | 白话 |\n")
        f.write("|------|------|------|------|------|------|------|\n")
        
        for i, lesson in enumerate(lessons_info, 1):
            f.write(f"| {i:2d} | {lesson['lesson_number']:5s} | {lesson['title']:15s} | {lesson['page']:3s} | {lesson.get('fortune', '?'):1s} | {'✓' if lesson['has_original'] else '✗':1s} | {'✓' if lesson['has_translation'] else '✗':1s} |\n")
    
    print(f"✓ Markdown 报告已保存：{md_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("64 课 OCR 内容分析")
    print("=" * 70)
    
    # 加载文本
    print("\n加载文本...")
    text = load_text()
    print(f"✓ 文本长度：{len(text):,} 字符")
    
    # 分割课
    lessons = split_by_lesson(text)
    
    if not lessons:
        print("\n✗ 未能识别出课！")
        return
    
    # 分析
    lessons_info = analyze_lessons(lessons)
    
    # 统计
    stats = create_statistics(lessons_info)
    
    # 保存
    save_results(lessons_info, stats)
    
    print("\n" + "=" * 70)
    print("✓✓✓ 分析完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
