#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
8640 课例精准匹配 - 带调试的版本
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

print("="*70)
print("  8640 课例精准匹配 - 调试版")
print("="*70)
print()

# 加载数据
print("1. 加载数据...")
try:
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\batch_analysis\64_lessons_batch_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        ke_jing_data = {item['lesson_name']: item for item in data['results']}
        print(f"   ✓ 64 课数据：{len(ke_jing_data)} 条")
except Exception as e:
    print(f"   ✗ 加载 64 课数据失败：{e}")
    input("按回车键退出...")
    exit(1)

try:
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\data\720_ke_li_matched.json', 'r', encoding='utf-8') as f:
        ke_li_data = json.load(f)
        print(f"   ✓ 课例数据：{len(ke_li_data)} 个")
except Exception as e:
    print(f"   ✗ 加载课例数据失败：{e}")
    input("按回车键退出...")
    exit(1)

print()
print("2. 测试第一个课例...")
first_key = list(ke_li_data.keys())[0]
first_ke_li = ke_li_data[first_key]

print(f"   课例：{first_key}")
print(f"   日干支：{first_ke_li['ri_gan_zhi']}")
print(f"   月：{first_ke_li['yue']}")
print(f"   时：{first_ke_li['shi']}")
print()

prompt = f"""大六壬课例：
日干支：{first_ke_li['ri_gan_zhi']}
月：{first_ke_li['yue']}
时：{first_ke_li['shi']}
月将：{first_ke_li['yue_jiang']}

从 64 课经中选 1 个最匹配的，返回 JSON：
{{"matched_ke_jing":["课经名"],"confidence_scores":[90],"primary_ke_jing":"课经名","reasoning":"理由"}}

64 课经：元首课、重审课、知一课、涉害课、遥克课、昴星课、别责课、八专课、伏吟课、返吟课、三光课、三阳课、三奇课、六仪课、时泰课、龙德课、官爵课、富贵课、轩盖课、铸印课、斫轮课、引从课、亨通课、繁昌课、荣华课、德庆课、合欢课、和美课、斩关课、闭口课、游子课、三交课、赘婿课、冲破课、淫泆课、芜淫课、解离课、度厄课、无禄课、绝嗣课、迍福课、侵害课、刑伤课、二烦课、天祸课、天狱课、天寇课、天网课、魄化课、三阴课、龙战课、死奇课、灾厄课、殃咎课、九丑课、鬼墓课、励德课、盘珠课、全局课、元胎课、连珠课、间传课、六纯课、杂状课、物类课
"""

print("3. 调用 API（超时 120 秒）...")
print(f"   提示词长度：{len(prompt)}")
print()

try:
    response = Generation.call(
        model='qwen-max',
        messages=[
            {'role': 'system', 'content': '大六壬专家。'},
            {'role': 'user', 'content': prompt}
        ],
        timeout=120,
        stream=False
    )
    
    print(f"   状态码：{response.status_code}")
    
    if response.status_code == 200:
        result_text = response.output.get('text', '')
        print(f"   返回长度：{len(result_text)}")
        print(f"   返回内容：{result_text[:200]}...")
        
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            print()
            print("   ✓ JSON 解析成功！")
            print(f"   主课经：{result.get('primary_ke_jing', '')}")
        else:
            print("   ✗ 无法解析 JSON")
    else:
        print(f"   ✗ API 错误：{response.status_code}")
        if hasattr(response, 'message'):
            print(f"   错误信息：{response.message}")
    
except Exception as e:
    print(f"   ✗ 异常：{str(e)}")
    import traceback
    traceback.print_exc()

print()
print("4. 准备开始批量匹配...")
print(f"   总课例数：{len(ke_li_data)}")
print()

response = input("是否继续？(输入 y 继续，其他键取消): ")
if response.lower() != 'y':
    print("已取消")
    input("按回车键退出...")
    exit(0)

# 开始批量匹配
print()
print("="*70)
print("  开始批量匹配")
print("="*70)
print()

matched_results = {}
error_log = []
start_time = time.time()

for i, (ke_li_key, ke_li) in enumerate(ke_li_data.items()):
    elapsed = time.time() - start_time
    avg_time = elapsed / (i + 1) if i > 0 else 0
    remaining = (len(ke_li_data) - i) * avg_time
    
    print(f"[{i+1}/{len(ke_li_data)}] {ke_li_key} | 预计剩余:{int(remaining/60)}分", end=" ")
    
    # 构建提示词
    prompt = f"""课例：{ke_li['ri_gan_zhi']} {ke_li['yue']} {ke_li['shi']} {ke_li['yue_jiang']}
匹配课经，返回 JSON: {{"matched_ke_jing":["课经"],"confidence_scores":[90],"primary_ke_jing":"课经","reasoning":"理由"}}
64 课经：元首课、重审课、知一课、涉害课、遥克课、昴星课、别责课、八专课、伏吟课、返吟课、三光课、三阳课、三奇课、六仪课、时泰课、龙德课、官爵课、富贵课、轩盖课、铸印课、斫轮课、引从课、亨通课、繁昌课、荣华课、德庆课、合欢课、和美课、斩关课、闭口课、游子课、三交课、赘婿课、冲破课、淫泆课、芜淫课、解离课、度厄课、无禄课、绝嗣课、迍福课、侵害课、刑伤课、二烦课、天祸课、天狱课、天寇课、天网课、魄化课、三阴课、龙战课、死奇课、灾厄课、殃咎课、九丑课、鬼墓课、励德课、盘珠课、全局课、元胎课、连珠课、间传课、六纯课、杂状课、物类课
"""
    
    try:
        response = Generation.call(
            model='qwen-max',
            messages=[
                {'role': 'system', 'content': '大六壬专家。'},
                {'role': 'user', 'content': prompt}
            ],
            timeout=120,
            stream=False
        )
        
        if response.status_code == 200:
            result_text = response.output.get('text', '')
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                matched = result.get('matched_ke_jing', [])
                
                if matched and matched[0] in ke_jing_data:
                    matched_results[ke_li_key] = {
                        **ke_li,
                        'qwen_matched': result,
                        'match_time': datetime.now().isoformat()
                    }
                    print(f"✓ {result.get('primary_ke_jing', 'N/A')}")
                else:
                    print(f"✗ 课经无效")
                    error_log.append({'ke_li_key': ke_li_key, 'error': '课经无效'})
            else:
                print(f"✗ 无法解析")
                error_log.append({'ke_li_key': ke_li_key, 'error': '无法解析 JSON'})
        else:
            print(f"✗ API:{response.status_code}")
            error_log.append({'ke_li_key': ke_li_key, 'error': f'API 错误:{response.status_code}'})
    
    except Exception as e:
        print(f"✗ 异常:{str(e)[:30]}")
        error_log.append({'ke_li_key': ke_li_key, 'error': str(e)})
    
    # 每 10 个保存一次
    if (i + 1) % 10 == 0:
        progress = {
            'timestamp': datetime.now().isoformat(),
            'completed': i + 1,
            'total': len(ke_li_data),
            'matched_results': matched_results,
            'error_log': error_log
        }
        with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\match_progress_debug.json', 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        print(f"  [已保存进度]")
    
    time.sleep(1)

# 最终保存
print()
print("="*70)
print("  匹配完成！")
print("="*70)
print(f"成功：{len(matched_results)}/{len(ke_li_data)}")
print(f"失败：{len(error_log)}/{len(ke_li_data)}")

final_result = {
    'timestamp': datetime.now().isoformat(),
    'total': len(ke_li_data),
    'matched': len(matched_results),
    'errors': len(error_log),
    'matched_results': matched_results
}

with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\qwen_max_matched_results_debug.json', 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存")
print()
input("按回车键退出...")
