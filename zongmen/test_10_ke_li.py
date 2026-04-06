#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例精准匹配系统 - 简化测试版

先测试前 10 个课例，验证系统正常工作
"""

import json
import os
import re
import time
from datetime import datetime
import dashscope
from dashscope import Generation

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

print("="*60)
print("  8640 课例精准匹配系统 - 测试模式")
print("="*60)
print()

# 加载数据
print("1. 加载数据...")
analysis_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json'
with open(analysis_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
    ke_jing_data = {item['lesson_name']: item for item in data['results']}
    print(f"   ✓ 已加载 {len(ke_jing_data)} 条 64 课数据")

ke_li_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json'
with open(ke_li_file, 'r', encoding='utf-8') as f:
    ke_li_data = json.load(f)
    print(f"   ✓ 已加载 {len(ke_li_data)} 个课例")
print()

# 测试前 10 个课例
print("2. 测试前 10 个课例匹配...")
print()

test_count = 0
success_count = 0

for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
    if i >= 10:  # 只测试前 10 个
        break
    
    test_count += 1
    print(f"[{test_count}/10] 处理：{ke_li_key}")
    
    # 构建提示词
    prompt = f"""你是一位精通大六壬的专家。请根据以下课例信息分析课体特征并匹配课经。

课例信息：
- 日干支：{ke_li['ri_gan_zhi']}
- 月份：{ke_li['yue']}
- 时辰：{ke_li['shi']}
- 月将：{ke_li['yue_jiang']}

请从 64 课经中选择最匹配的 1-2 个课经，并给出置信度评分。

64 课经列表：元首课、重审课、知一课、涉害课、遥克课、昴星课、别责课、八专课、伏吟课、返吟课、三光课、三阳课、三奇课、六仪课、时泰课、龙德课、官爵课、富贵课、轩盖课、铸印课、斫轮课、引从课、亨通课、繁昌课、荣华课、德庆课、合欢课、和美课、斩关课、闭口课、游子课、三交课、赘婿课、冲破课、淫泆课、芜淫课、解离课、度厄课、无禄绝嗣课、迍福课、侵害课、刑伤课、二烦课、天祸课、天狱课、天寇课、天网课、魄化课、三阴课、龙战课、死奇课、灾厄课、殃咎课、九丑课、鬼墓课、励德课、盘珠课、全局课、元胎课、连珠课、间传课、六纯课、杂状课、物类课

请以 JSON 格式返回：
{{
    "matched_ke_jing": ["课经 1", "课经 2"],
    "confidence_scores": [95, 85],
    "primary_ke_jing": "课经 1",
    "reasoning": "匹配理由"
}}
"""
    
    # 调用 API
    try:
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '你是一位精通大六壬的专家。'},
                {'role': 'user', 'content': prompt}
            ],
            timeout=60,
            stream=False
        )
        
        if response.status_code == 200:
            result_text = response.output.get('text', '')
            # 提取 JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                print(f"   ✓ 成功 - 主课经：{result.get('primary_ke_jing', 'N/A')}")
                success_count += 1
            else:
                print(f"   ✗ 失败 - 无法解析 JSON")
        else:
            print(f"   ✗ 失败 - API 错误：{response.status_code}")
            
    except Exception as e:
        print(f"   ✗ 失败 - 异常：{str(e)[:50]}")
    
    # 等待一下，避免限流
    time.sleep(1)

print()
print("="*60)
print("  测试结果")
print("="*60)
print(f"总测试数：{test_count}")
print(f"成功数：{success_count}")
print(f"成功率：{success_count/test_count*100:.1f}%")
print()

if success_count >= 8:
    print("✅ 测试通过！系统可以正常运行。")
    print()
    print("下一步：可以开始完整的 8640 课例匹配")
else:
    print("⚠️ 测试未完全通过，请检查问题。")
