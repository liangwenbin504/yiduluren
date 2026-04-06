#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试第一个课例的匹配
"""

import json
import re
import dashscope
from dashscope import Generation

# API 配置
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

print("="*60)
print("  测试第一个课例匹配")
print("="*60)
print()

# 加载数据
print("加载数据...")
with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    ke_jing_data = {item['lesson_name']: item for item in data['results']}
    print(f"✓ 64 课数据：{len(ke_jing_data)} 条")

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json', 'r', encoding='utf-8') as f:
    ke_li_data = json.load(f)
    print(f"✓ 课例数据：{len(ke_li_data)} 个")

# 获取第一个课例
first_key = list(ke_li_data.keys())[0]
first_ke_li = ke_li_data[first_key]

print(f"\n第一个课例：{first_key}")
print(f"  日干支：{first_ke_li['ri_gan_zhi']}")
print(f"  月：{first_ke_li['yue']}")
print(f"  时：{first_ke_li['shi']}")
print(f"  月将：{first_ke_li['yue_jiang']}")
print()

# 构建提示词
prompt = f"""大六壬课例分析：
日干支：{first_ke_li['ri_gan_zhi']}
月：{first_ke_li['yue']}
时：{first_ke_li['shi']}
月将：{first_ke_li['yue_jiang']}

请从 64 课经中选择最匹配的 1 个课经。
64 课经：元首课、重审课、知一课、涉害课、遥克课、昴星课、别责课、八专课、伏吟课、返吟课、三光课、三阳课、三奇课、六仪课、时泰课、龙德课、官爵课、富贵课、轩盖课、铸印课、斫轮课、引从课、亨通课、繁昌课、荣华课、德庆课、合欢课、和美课、斩关课、闭口课、游子课、三交课、赘婿课、冲破课、淫泆课、芜淫课、解离课、度厄课、无禄课、绝嗣课、迍福课、侵害课、刑伤课、二烦课、天祸课、天狱课、天寇课、天网课、魄化课、三阴课、龙战课、死奇课、灾厄课、殃咎课、九丑课、鬼墓课、励德课、盘珠课、全局课、元胎课、连珠课、间传课、六纯课、杂状课、物类课

返回 JSON 格式：
{{"matched_ke_jing":["课经名"],"confidence_scores":[90],"primary_ke_jing":"课经名","reasoning":"简要理由"}}
"""

print("正在调用 Qwen Max API...")
print("提示词长度:", len(prompt))
print()

try:
    response = Generation.call(
        model='qwen-max',
        messages=[
            {'role': 'system', 'content': '你是一位大六壬专家。'},
            {'role': 'user', 'content': prompt}
        ],
        timeout=120,  # 2 分钟超时
        stream=False
    )
    
    print(f"API 响应状态码：{response.status_code}")
    
    if response.status_code == 200:
        result_text = response.output.get('text', '')
        print(f"返回内容长度：{len(result_text)}")
        print(f"\n返回内容:\n{result_text}")
        
        # 尝试解析 JSON
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            print(f"\n✓ JSON 解析成功!")
            print(f"匹配的课经：{result.get('matched_ke_jing', [])}")
            print(f"主课经：{result.get('primary_ke_jing', '')}")
            print(f"置信度：{result.get('confidence_scores', [])}")
        else:
            print(f"\n✗ 无法解析 JSON")
    else:
        print(f"✗ API 错误：{response.status_code}")
        
except Exception as e:
    print(f"✗ 异常：{str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("  测试完成")
print("="*60)
