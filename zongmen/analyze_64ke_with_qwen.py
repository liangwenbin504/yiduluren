# -*- coding: utf-8 -*-
"""
使用 Qwen Max API 分析 64 课 OCR 提取内容
任务：
1. 提取 64 课的完整内容
2. 整理每课的核心知识点
3. 识别特殊课式和从格
4. 建立结构化数据库
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
    """按课分割文本"""
    # 使用正则表达式匹配课的开始
    pattern = r'=== 第 (\d+) 页 ==='
    pages = re.split(pattern, text)
    
    lessons = []
    current_lesson = None
    
    for i in range(1, len(pages), 2):
        page_num = pages[i]
        content = pages[i + 1] if i + 1 < len(pages) else ''
        
        # 提取课名
        lesson_match = re.search(r'第 ([一二三四五六七八九十百千\d]+) 课', content)
        if lesson_match:
            lesson_name_match = re.search(r'第 [一二三四五六七八九十百千\d]+ 课\s*\n*(.+?)(?:：|·)', content)
            if lesson_name_match:
                lesson_title = lesson_name_match.group(1).strip()
                lessons.append({
                    'page': page_num,
                    'lesson_number': lesson_match.group(1),
                    'title': lesson_title,
                    'content': content[:500]  # 只取前 500 字用于初步分析
                })
    
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


def extract_64_lessons_info(lessons):
    """提取 64 课的基本信息"""
    print("\n" + "=" * 70)
    print("步骤 1: 提取 64 课基本信息")
    print("=" * 70)
    
    lessons_info = []
    
    for i, lesson in enumerate(lessons, 1):
        print(f"\n处理第 {i} 课：{lesson['title']}")
        
        # 提取关键信息
        info = {
            'lesson_number': lesson['lesson_number'],
            'title': lesson['title'],
            'page': lesson['page'],
            'keywords': [],
            'divination_rules': '',
            'interpretation': ''
        }
        
        # 简单的关键词提取
        content = lesson['content']
        if '原文' in content:
            info['divination_rules'] = '有原文'
        if '白话提要' in content:
            info['interpretation'] = '有白话解释'
        
        # 提取关键词
        keywords_pattern = r'【?([A-Z 口一二三四五六七八九十百千\d 事占课象吉凶]{{2,8}})】?'
        keywords = re.findall(keywords_pattern, content)
        info['keywords'] = list(set(keywords))[:10]
        
        lessons_info.append(info)
        print(f"  ✓ 提取完成：{len(info['keywords'])} 个关键词")
    
    return lessons_info


def create_knowledge_base(lessons_info):
    """创建 64 课知识库"""
    print("\n" + "=" * 70)
    print("步骤 2: 创建 64 课知识库")
    print("=" * 70)
    
    knowledge_base = {
        'total_lessons': len(lessons_info),
        'lessons': lessons_info,
        'statistics': {
            'with_original_text': sum(1 for l in lessons_info if l['divination_rules'] == '有原文'),
            'with_modern_interpretation': sum(1 for l in lessons_info if l['interpretation'] == '有白话解释')
        }
    }
    
    # 保存知识库
    output_path = os.path.join(OUTPUT_DIR, '64_lessons_knowledge_base.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 知识库已保存：{output_path}")
    print(f"  总课数：{knowledge_base['total_lessons']}")
    print(f"  有原文：{knowledge_base['statistics']['with_original_text']} 课")
    print(f"  有白话解释：{knowledge_base['statistics']['with_modern_interpretation']} 课")
    
    return knowledge_base


def generate_comparison_table(lessons_info):
    """生成知识点对照表"""
    print("\n" + "=" * 70)
    print("步骤 3: 生成知识点对照表")
    print("=" * 70)
    
    comparison_data = []
    
    for lesson in lessons_info:
        comparison_data.append({
            '课号': lesson['lesson_number'],
            '课名': lesson['title'],
            '页码': lesson['page'],
            '关键词数量': len(lesson['keywords']),
            '关键词': '、'.join(lesson['keywords'][:5]),
            '原文': '✓' if lesson['divination_rules'] == '有原文' else '✗',
            '白话': '✓' if lesson['interpretation'] == '有白话解释' else '✗'
        })
    
    # 保存为 JSON
    output_path = os.path.join(OUTPUT_DIR, 'comparison_table.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 对照表已保存：{output_path}")
    print(f"  共 {len(comparison_data)} 条记录")
    
    return comparison_data


def main():
    """主函数"""
    print("=" * 70)
    print("64 课 OCR 内容分析与整理")
    print("=" * 70)
    
    # 加载文本
    print("\n加载 OCR 提取的文本...")
    text = load_text()
    print(f"✓ 文本已加载，总长度：{len(text)} 字符")
    
    # 分割课
    print("\n按课分割文本...")
    lessons = split_by_lesson(text)
    print(f"✓ 共识别出 {len(lessons)} 课")
    
    # 提取基本信息
    lessons_info = extract_64_lessons_info(lessons)
    
    # 创建知识库
    knowledge_base = create_knowledge_base(lessons_info)
    
    # 生成对照表
    comparison_table = generate_comparison_table(lessons_info)
    
    # 生成分析报告
    print("\n" + "=" * 70)
    print("步骤 4: 生成分析报告")
    print("=" * 70)
    
    report = f"""# 64 课 OCR 内容分析报告

## 基本信息
- 总课数：{len(lessons_info)}
- 有原文：{knowledge_base['statistics']['with_original_text']} 课
- 有白话解释：{knowledge_base['statistics']['with_modern_interpretation']} 课

## 64 课列表
"""
    
    for lesson in lessons_info:
        report += f"\n### {lesson['lesson_number']}. {lesson['title']}\n"
        report += f"- 页码：{lesson['page']}\n"
        report += f"- 关键词：{', '.join(lesson['keywords'][:5])}\n"
    
    # 保存报告
    report_path = os.path.join(OUTPUT_DIR, 'analysis_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ 分析报告已保存：{report_path}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ 分析完成！")
    print("=" * 70)
    print(f"\n输出文件：")
    print(f"  1. 知识库：{os.path.join(OUTPUT_DIR, '64_lessons_knowledge_base.json')}")
    print(f"  2. 对照表：{os.path.join(OUTPUT_DIR, 'comparison_table.json')}")
    print(f"  3. 分析报告：{os.path.join(OUTPUT_DIR, 'analysis_report.md')}")


if __name__ == '__main__':
    main()
