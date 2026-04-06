# -*- coding: utf-8 -*-
"""
使用 Qwen Max API 深度分析 64 课内容
任务：
1. 对比 OCR 内容与《六壬大全》原著
2. 建立知识点对照表
3. 识别特殊课式和从格
4. 生成综合分析报告
"""

import json
import os
from dashscope import Generation

# Qwen API Key
API_KEY = '***REMOVED***'

# 输入输出文件
INPUT_JSON = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\analysis\64_lessons_complete_analysis.json'
MERGED_TEXT = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\merged_64ke.txt'
OUTPUT_DIR = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\qwen_analysis'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_lessons():
    """加载 64 课分析数据"""
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_sample_text(lesson_num):
    """加载指定课的样本内容"""
    with open(MERGED_TEXT, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找课的开始位置
    import re
    lesson_starts = []
    for i, line in enumerate(lines):
        if re.match(r'^第.+课$', line.strip()) and len(line.strip()) <= 6:
            lesson_starts.append(i)
    
    if lesson_num <= len(lesson_starts):
        start = lesson_starts[lesson_num - 1]
        end = lesson_starts[lesson_num] if lesson_num < len(lesson_starts) else len(lines)
        return ''.join(lines[start:min(start+50, end)])
    return ""


def analyze_with_qwen(text, task):
    """使用 Qwen Max API 分析文本"""
    try:
        prompt = f"""你是一位精通大六壬的专家。请完成以下任务：

{task}

待分析内容：
{text}

请用 JSON 格式返回分析结果。"""

        response = Generation.call(
            model='qwen-max',
            api_key=API_KEY,
            messages=[
                {'role': 'system', 'content': '你是一位精通大六壬的专家，擅长分析和整理六壬课式内容。'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=2000
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"API 调用失败：{response.code} - {response.message}"
    
    except Exception as e:
        return f"分析出错：{str(e)}"


def analyze_first_lesson():
    """分析第一课（元首课）作为样本"""
    print("=" * 70)
    print("使用 Qwen Max API 分析第一课（元首课）")
    print("=" * 70)
    
    text = load_sample_text(1)
    
    if not text:
        print("✗ 无法加载课文内容")
        return
    
    print(f"\n加载内容长度：{len(text)} 字符")
    print("\n分析任务：")
    print("  1. 提取核心知识点")
    print("  2. 整理占断规则")
    print("  3. 识别特殊课式")
    print("  4. 与原著对比差异")
    
    task = """
请对这段六壬课内容进行全面分析，包括：
1. 课名和基本信息
2. 核心定义（用现代语言概括）
3. 占断规则（列出关键判断要点）
4. 吉凶特征
5. 特殊课式或从格
6. 重要术语解释
7. 与《六壬大全》原著的可能差异（如果有）

请按以下 JSON 格式返回：
{
    "lesson_name": "课名",
    "subtitle": "副标题",
    "core_definition": "核心定义",
    "divination_rules": ["规则 1", "规则 2"],
    "fortune": "吉凶",
    "special_patterns": ["特殊课式"],
    "key_terms": {"术语": "解释"},
    "notes": "备注说明"
}
"""
    
    print("\n正在调用 Qwen Max API...")
    result = analyze_with_qwen(text, task)
    
    # 保存结果
    output_path = os.path.join(OUTPUT_DIR, 'lesson_01_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n✓ 分析结果已保存：{output_path}")
    print(f"\n分析结果预览：")
    print("-" * 70)
    print(result[:500])
    print("...")


def create_knowledge_comparison():
    """创建知识点对照表框架"""
    print("\n" + "=" * 70)
    print("创建知识点对照表框架")
    print("=" * 70)
    
    comparison_table = {
        "title": "64 课知识点对照表",
        "source": "《图解六壬大全》vs《六壬大全》原著",
        "categories": [
            {
                "category": "术语对比",
                "items": []
            },
            {
                "category": "占断规则对比",
                "items": []
            },
            {
                "category": "案例分析对比",
                "items": []
            },
            {
                "category": "特殊课式对比",
                "items": []
            }
        ]
    }
    
    output_path = os.path.join(OUTPUT_DIR, 'knowledge_comparison_template.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_table, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 对照表模板已保存：{output_path}")


def generate_analysis_plan():
    """生成完整分析计划"""
    print("\n" + "=" * 70)
    print("生成 64 课完整分析计划")
    print("=" * 70)
    
    plan = """# 64 课深度分析实施计划

## 第一阶段：单课分析（已完成样本）
- ✓ 第一课：元首课 - 样本分析完成
- [ ] 第二课：重审课
- [ ] 第三课：知一课
- [ ] ... (共 64 课)

## 第二阶段：知识点整理
### 1. 术语对照
- 古术语 vs 现代解释
- 不同版本的术语差异
- 术语演变历史

### 2. 占断规则
- 九宗门规则
- 特殊课式规则
- 从格判断规则

### 3. 课式特征
- 吉凶分类
- 课体特征
- 课象描述

## 第三阶段：对比分析
### 1. 与原著对比
- 《六壬大全》原著
- 《六壬指南》
- 其他古籍

### 2. 版本差异
- 文字差异
- 解释差异
- 课例差异

## 第四阶段：数据库建立
### 1. 结构化数据
- 64 课标准数据库
- 知识点关联
- 课例索引

### 2. 与 720 课例匹配
- 课式匹配
- 验证准确性
- 补充案例

## 技术实现
### API 使用
- Qwen Max API 调用
- 批量处理策略
- 结果验证机制

### 数据格式
- JSON 结构化存储
- Markdown 报告生成
- Excel 导出格式

## 预期成果
1. 64 课完整分析报告
2. 知识点对照表
3. 特殊课式识别指南
4. 与原著差异说明
5. 标准化数据库

## 进度安排
- 第一阶段：1-2 天
- 第二阶段：2-3 天
- 第三阶段：1-2 天
- 第四阶段：1 天
总计：5-8 天
"""
    
    output_path = os.path.join(OUTPUT_DIR, 'analysis_plan.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(plan)
    
    print(f"✓ 分析计划已保存：{output_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("64 课深度分析 - Qwen Max API")
    print("=" * 70)
    
    # 1. 分析第一课作为样本
    analyze_first_lesson()
    
    # 2. 创建对照表框架
    create_knowledge_comparison()
    
    # 3. 生成分析计划
    generate_analysis_plan()
    
    print("\n" + "=" * 70)
    print("✓✓✓ 第一阶段分析完成！")
    print("=" * 70)
    print(f"\n输出文件：")
    print(f"  1. 课例分析：{os.path.join(OUTPUT_DIR, 'lesson_01_analysis.json')}")
    print(f"  2. 对照表模板：{os.path.join(OUTPUT_DIR, 'knowledge_comparison_template.json')}")
    print(f"  3. 分析计划：{os.path.join(OUTPUT_DIR, 'analysis_plan.md')}")
    
    print("\n下一步：")
    print("  - 查看第一课分析结果")
    print("  - 确认分析框架")
    print("  - 批量处理其余 63 课")


if __name__ == '__main__':
    main()
