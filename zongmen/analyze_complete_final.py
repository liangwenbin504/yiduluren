# -*- coding: utf-8 -*-
"""
64 课完整分析报告（最终版）
包含：
1. 提取 64 课课名
2. 统计特征
3. 生成完整报告
"""

import json
import os
import re

INPUT_FILE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\merged_64ke.txt'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\analysis'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("=" * 70)
    print("64 课完整分析报告")
    print("=" * 70)
    
    # 加载文本
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"✓ 总行数：{len(lines)}")
    
    # 查找所有课
    lesson_starts = []
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        match = re.match(r'^第.+课$', line_stripped)
        if match and len(line_stripped) <= 6:
            lesson_starts.append((i, line_stripped))
    
    print(f"✓ 找到 {len(lesson_starts)} 个课")
    
    # 提取每课详细信息
    lessons = []
    for idx, (line_num, lesson_line) in enumerate(lesson_starts[:64]):
        next_line_num = lesson_starts[idx + 1][0] if idx + 1 < len(lesson_starts) else len(lines)
        
        lesson_number = lesson_line
        
        # 课名（下一行包含冒号的）
        title = "未知"
        for j in range(line_num + 1, min(line_num + 5, len(lines))):
            next_line = lines[j].strip()
            if ':' in next_line:
                title = next_line.split(':')[0].strip()
                # 清理课名
                if title == lesson_line:
                    continue
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
        
        # 提取课内容
        content = ''.join(lines[line_num:next_line_num])
        
        # 分析特征
        has_original = '【原文】' in content or '原文' in content
        has_translation = '【白话提要】' in content or '白话' in content
        has_diagram = '图' in content or '图解' in content
        has_xiang = '象曰' in content
        
        # 判断吉凶
        if any(word in content for word in ['大吉', '元吉', '福祐', '顺利', '亨通']):
            fortune = '吉'
        elif any(word in content for word in ['凶', '祸', '灾', '难', '咎']):
            fortune = '凶'
        else:
            fortune = '平'
        
        lessons.append({
            'number': lesson_number,
            'title': title,
            'page': page,
            'length': content_length,
            'fortune': fortune,
            'has_original': has_original,
            'has_translation': has_translation,
            'has_diagram': has_diagram,
            'has_xiang': has_xiang
        })
        
        if idx < 15 or idx % 10 == 0:
            print(f"  {lesson_number:6s} {title:15s} 第{page}页 {fortune} 原文:{'✓' if has_original else '✗'} 白话:{'✓' if has_translation else '✗'}")
    
    # 统计
    print("\n" + "=" * 70)
    print("统计信息")
    print("=" * 70)
    
    stats = {
        'total': len(lessons),
        'with_original': sum(1 for l in lessons if l['has_original']),
        'with_translation': sum(1 for l in lessons if l['has_translation']),
        'with_diagram': sum(1 for l in lessons if l['has_diagram']),
        'with_xiang': sum(1 for l in lessons if l['has_xiang']),
        'fortune': {
            '吉': sum(1 for l in lessons if l['fortune'] == '吉'),
            '凶': sum(1 for l in lessons if l['fortune'] == '凶'),
            '平': sum(1 for l in lessons if l['fortune'] == '平')
        }
    }
    
    print(f"总课数：{stats['total']}")
    print(f"有原文：{stats['with_original']} 课")
    print(f"有白话：{stats['with_translation']} 课")
    print(f"有图解：{stats['with_diagram']} 课")
    print(f"有象曰：{stats['with_xiang']} 课")
    print(f"吉凶分布：吉{stats['fortune']['吉']} / 凶{stats['fortune']['凶']} / 平{stats['fortune']['平']}")
    
    # 保存结果
    result = {
        'statistics': stats,
        'lessons': lessons
    }
    
    json_path = os.path.join(OUTPUT_DIR, '64_lessons_complete_analysis.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ JSON 已保存：{json_path}")
    
    # 生成 Markdown 报告
    md_path = os.path.join(OUTPUT_DIR, '64_lessons_full_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 64 课完整分析报告\n\n")
        f.write("## 统计摘要\n\n")
        f.write(f"- 总课数：{stats['total']}\n")
        f.write(f"- 有原文：{stats['with_original']} 课 ({stats['with_original']/stats['total']*100:.1f}%)\n")
        f.write(f"- 有白话：{stats['with_translation']} 课 ({stats['with_translation']/stats['total']*100:.1f}%)\n")
        f.write(f"- 有图解：{stats['with_diagram']} 课\n")
        f.write(f"- 有象曰：{stats['with_xiang']} 课\n")
        f.write(f"- 吉凶分布：吉{stats['fortune']['吉']} / 凶{stats['fortune']['凶']} / 平{stats['fortune']['平']}\n\n")
        
        f.write("## 64 课详细列表\n\n")
        f.write("| 序号 | 课号 | 课名 | 页码 | 吉凶 | 原文 | 白话 | 象曰 |\n")
        f.write("|------|------|------|------|------|------|------|------|\n")
        
        for i, lesson in enumerate(lessons, 1):
            f.write(f"| {i:2d} | {lesson['number']:6s} | {lesson['title']:15s} | {lesson['page']:3s} | {lesson['fortune']:1s} | {'✓' if lesson['has_original'] else '✗':1s} | {'✓' if lesson['has_translation'] else '✗':1s} | {'✓' if lesson['has_xiang'] else '✗':1s} |\n")
    
    print(f"✓ Markdown 报告已保存：{md_path}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ 分析完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
