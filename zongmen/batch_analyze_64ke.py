# -*- coding: utf-8 -*-
"""
批量分析 64 课（使用修复后的 API）
"""

import dashscope
from dashscope import Generation
import json
import re
import os
import time

API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

MERGED_TEXT = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\merged_64ke.txt'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_lessons():
    """从合并文本中提取 64 课"""
    with open(MERGED_TEXT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lesson_starts = []
    for i, line in enumerate(lines):
        if re.match(r'^第.+课$', line.strip()) and len(line.strip()) <= 6:
            lesson_starts.append(i)
    
    lessons = []
    for idx in range(min(64, len(lesson_starts))):
        start = lesson_starts[idx]
        end = lesson_starts[idx + 1] if idx + 1 < len(lesson_starts) else len(lines)
        
        lesson_text = ''.join(lines[start:end])
        lesson_name = lines[start].strip()
        
        # 找课名
        title = "未知"
        for j in range(start + 1, min(start + 5, len(lines))):
            if ':' in lines[j]:
                title = lines[j].split(':')[0].strip()
                break
        
        # 找页码
        page = "未知"
        for j in range(max(0, start - 20), start):
            page_match = re.search(r'=== 第 (\d+) 页 ===', lines[j])
            if page_match:
                page = page_match.group(1)
                break
        
        lessons.append({
            'index': idx + 1,
            'name': lesson_name,
            'title': title,
            'page': page,
            'text': lesson_text[:2000]  # 限制长度
        })
    
    return lessons


def analyze_lesson(lesson):
    """分析单课"""
    task = f"""请对这段六壬课内容进行分析，提取以下信息并以 JSON 格式返回：

1. 课名和副标题
2. 核心定义（用一句话概括）
3. 占断规则（列出 3-5 个关键点）
4. 吉凶属性
5. 象曰内容
6. 重要术语（3-5 个）

JSON 格式：
{{
    "lesson_name": "课名",
    "subtitle": "副标题",
    "core_definition": "核心定义",
    "divination_rules": ["规则 1", "规则 2", "规则 3"],
    "fortune": "吉凶",
    "xiang_yue": "象曰内容",
    "key_terms": {{"术语 1": "解释 1", "术语 2": "解释 2"}}
}}

待分析内容：
{lesson['text']}
"""
    
    try:
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '你是一位精通大六壬的专家。'},
                {'role': 'user', 'content': task}
            ],
            timeout=90,
            stream=False
        )
        
        if response.status_code == 200:
            result = response.output.get('text', '')
            
            # 提取 JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                try:
                    parsed = json.loads(json_str)
                    return parsed, None
                except:
                    return None, f"JSON 解析失败"
            return None, "未找到 JSON"
        else:
            return None, f"API 错误：{response.code}"
    
    except Exception as e:
        return None, f"异常：{str(e)}"


def batch_analyze():
    """批量分析"""
    print("=" * 70)
    print("批量分析 64 课")
    print("=" * 70)
    
    # 提取课程
    print("\n提取课程...")
    lessons = extract_lessons()
    print(f"✓ 提取到 {len(lessons)} 课")
    
    # 批量分析
    results = []
    
    for i, lesson in enumerate(lessons, 1):
        print(f"\n[{i:2d}/{len(lessons)}] 分析 {lesson['name']}: {lesson['title']}")
        
        # 跳过已分析的
        output_file = os.path.join(OUTPUT_DIR, f"lesson_{i:02d}_analyzed.json")
        if os.path.exists(output_file):
            print(f"  ✓ 已存在，跳过")
            with open(output_file, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
            continue
        
        # 分析
        result, error = analyze_lesson(lesson)
        
        if result:
            print(f"  ✓ 分析成功")
            
            # 添加元数据
            result['metadata'] = {
                'lesson_index': i,
                'lesson_name': lesson['name'],
                'lesson_title': lesson['title'],
                'page': lesson['page']
            }
            
            results.append(result)
            
            # 保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            print(f"  ✗ 分析失败：{error}")
            results.append({
                'error': error,
                'metadata': {
                    'lesson_index': i,
                    'lesson_name': lesson['name'],
                    'lesson_title': lesson['title'],
                    'page': lesson['page']
                }
            })
        
        # 延迟，避免请求过快
        time.sleep(1)
    
    # 保存汇总
    summary_path = os.path.join(OUTPUT_DIR, '64_lessons_batch_analysis.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(results),
            'success': sum(1 for r in results if 'error' not in r),
            'failed': sum(1 for r in results if 'error' in r),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"批量分析完成！")
    print(f"成功：{sum(1 for r in results if 'error' not in r)}/{len(results)}")
    print(f"失败：{sum(1 for r in results if 'error' in r)}/{len(results)}")
    print(f"结果保存在：{OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    batch_analyze()
