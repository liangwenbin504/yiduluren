# -*- coding: utf-8 -*-
"""
使用 Qwen Max API 分析 64 课 OCR 提取内容（改进版）
"""

import json
import os
import re
from dashscope import Generation

# Qwen API Key
API_KEY = '***REMOVED***'

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
    """按课分割文本（改进版）"""
    print("\n分析文本结构...")
    
    # 查找所有"第 X 课"的模式
    lesson_pattern = r'(?:^|\n)(第 [一二三四五六七八九十百千\d]+ 课)'
    matches = list(re.finditer(lesson_pattern, text, re.MULTILINE))
    
    print(f"找到 {len(matches)} 个课的开始位置")
    
    lessons = []
    
    for i, match in enumerate(matches):
        lesson_start = match.start()
        lesson_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        
        lesson_content = text[lesson_start:lesson_end]
        lesson_number = match.group(1)
        
        # 提取课名标题
        title_match = re.search(r'第 [一二三四五六七八九十百千\d]+ 课\s*\n*([^\n：·]+)(?:[：·])', lesson_content)
        title = title_match.group(1).strip() if title_match else '未知'
        
        # 找到对应的页码
        page_match = re.search(r'=== 第 (\d+) 页 ===.*?' + re.escape(lesson_number), text[:lesson_start+500], re.DOTALL)
        page_num = page_match.group(1) if page_match else '未知'
        
        lessons.append({
            'lesson_number': lesson_number,
            'title': title,
            'page': page_num,
            'content': lesson_content[:1000],  # 只取前 1000 字用于分析
            'full_length': lesson_end - lesson_start
        })
        
        print(f"  ✓ {lesson_number}: {title} (第{page_num}页，{lesson_end - lesson_start} 字)")
    
    return lessons


def analyze_with_qwen(text_chunk, task_description):
    """使用 Qwen Max API 分析文本"""
    try:
        response = Generation.call(
            model='qwen-max',
            api_key=API_KEY,
            messages=[
                {'role': 'system', 'content': '你是一位精通大六壬的专家，擅长分析和整理六壬课式内容。'},
                {'role': 'user', 'content': f'{task_description}\n\n待分析内容：\n{text_chunk}'}
            ],
            max_tokens=2000
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"API 调用失败：{response.code} - {response.message}"
    
    except Exception as e:
        return f"分析出错：{str(e)}"


def extract_lesson_details(lessons):
    """提取每课的详细信息"""
    print("\n" + "=" * 70)
    print("提取每课详细信息")
    print("=" * 70)
    
    lessons_info = []
    
    for i, lesson in enumerate(lessons, 1):
        print(f"\n[{i}/{len(lessons)}] 分析 {lesson['lesson_number']}: {lesson['title']}")
        
        content = lesson['content']
        
        # 提取关键信息
        info = {
            'lesson_number': lesson['lesson_number'],
            'title': lesson['title'],
            'page': lesson['page'],
            'content_length': lesson['full_length'],
            'has_original_text': '【原文】' in content or '原文' in content,
            'has_modern_translation': '【白话提要】' in content or '白话' in content,
            'has_diagram': '图解' in content or '图解' in content,
            'keywords': []
        }
        
        # 提取关键词
        if '象曰' in content:
            info['keywords'].append('象曰')
        if '凡课' in content:
            info['keywords'].append('占课规则')
        if '解曰' in content:
            info['keywords'].append('解曰')
        
        # 提取吉凶属性
        if '大吉' in content or '元吉' in content:
            info['fortune'] = '大吉'
        elif '凶' in content:
            info['fortune'] = '凶'
        else:
            info['fortune'] = '平'
        
        lessons_info.append(info)
        print(f"  ✓ 属性：{info['fortune']}, 关键词：{len(info['keywords'])} 个")
    
    return lessons_info


def create_knowledge_base(lessons_info):
    """创建 64 课知识库"""
    print("\n" + "=" * 70)
    print("创建 64 课知识库")
    print("=" * 70)
    
    knowledge_base = {
        'total_lessons': len(lessons_info),
        'lessons': lessons_info,
        'statistics': {
            'with_original_text': sum(1 for l in lessons_info if l['has_original_text']),
            'with_modern_translation': sum(1 for l in lessons_info if l['has_modern_translation']),
            'with_diagram': sum(1 for l in lessons_info if l['has_diagram']),
            'fortune_distribution': {
                '大吉': sum(1 for l in lessons_info if l.get('fortune') == '大吉'),
                '凶': sum(1 for l in lessons_info if l.get('fortune') == '凶'),
                '平': sum(1 for l in lessons_info if l.get('fortune') == '平')
            }
        }
    }
    
    # 保存知识库
    output_path = os.path.join(OUTPUT_DIR, '64_lessons_knowledge_base.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 知识库已保存：{output_path}")
    print(f"  总课数：{knowledge_base['total_lessons']}")
    print(f"  有原文：{knowledge_base['statistics']['with_original_text']} 课")
    print(f"  有白话：{knowledge_base['statistics']['with_modern_translation']} 课")
    print(f"  有图解：{knowledge_base['statistics']['with_diagram']} 课")
    print(f"  吉凶分布：大吉{knowledge_base['statistics']['fortune_distribution']['大吉']} / 凶{knowledge_base['statistics']['fortune_distribution']['凶']} / 平{knowledge_base['statistics']['fortune_distribution']['平']}")
    
    return knowledge_base


def generate_analysis_report(lessons_info):
    """生成分析报告"""
    print("\n" + "=" * 70)
    print("生成分析报告")
    print("=" * 70)
    
    report = """# 64 课 OCR 内容分析报告

## 统计摘要
"""
    
    report += f"\n- 总课数：{len(lessons_info)}\n"
    report += f"- 有原文：{sum(1 for l in lessons_info if l['has_original_text'])} 课\n"
    report += f"- 有白话：{sum(1 for l in lessons_info if l['has_modern_translation'])} 课\n"
    report += f"- 有图解：{sum(1 for l in lessons_info if l['has_diagram'])} 课\n\n"
    
    report += "## 64 课详细列表\n\n"
    
    for lesson in lessons_info:
        report += f"### {lesson['lesson_number']}: {lesson['title']}\n"
        report += f"- 页码：{lesson['page']}\n"
        report += f"- 内容长度：{lesson['content_length']} 字\n"
        report += f"- 吉凶：{lesson.get('fortune', '未知')}\n"
        report += f"- 特征：{'原文' if lesson['has_original_text'] else ''} {'白话' if lesson['has_modern_translation'] else ''} {'图解' if lesson['has_diagram'] else ''}\n\n"
    
    # 保存报告
    report_path = os.path.join(OUTPUT_DIR, 'analysis_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ 分析报告已保存：{report_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("64 课 OCR 内容分析与整理（改进版）")
    print("=" * 70)
    
    # 加载文本
    print("\n加载 OCR 提取的文本...")
    text = load_text()
    print(f"✓ 文本已加载，总长度：{len(text):,} 字符")
    
    # 分割课
    lessons = split_by_lesson(text)
    
    if not lessons:
        print("\n✗ 未能识别出任何课！")
        print("可能原因：文本格式与预期不符")
        return
    
    # 提取详细信息
    lessons_info = extract_lesson_details(lessons)
    
    # 创建知识库
    knowledge_base = create_knowledge_base(lessons_info)
    
    # 生成报告
    generate_analysis_report(lessons_info)
    
    print("\n" + "=" * 70)
    print("✓✓✓ 分析完成！")
    print("=" * 70)
    print(f"\n输出文件：")
    print(f"  1. 知识库：{os.path.join(OUTPUT_DIR, '64_lessons_knowledge_base.json')}")
    print(f"  2. 分析报告：{os.path.join(OUTPUT_DIR, 'analysis_report.md')}")


if __name__ == '__main__':
    main()
