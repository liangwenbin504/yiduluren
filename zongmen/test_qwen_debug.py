# -*- coding: utf-8 -*-
"""
测试 Qwen API - 详细调试版
"""

import dashscope
from dashscope import Generation
import json

API_KEY = '***REMOVED***'

print("=" * 70)
print("测试 Qwen Max API - 详细调试")
print("=" * 70)

dashscope.api_key = API_KEY

test_prompt = "你好，请用一句话介绍大六壬。"

print(f"\n发送请求...")

try:
    response = Generation.call(
        model='qwen-max',
        messages=[{'role': 'user', 'content': test_prompt}],
        timeout=30,
        stream=False
    )
    
    # 打印完整响应
    print(f"\n完整响应对象:")
    print(f"类型：{type(response)}")
    print(f"属性：{dir(response)}")
    
    print(f"\n响应状态码：{response.status_code}")
    print(f"响应代码：{response.code}")
    print(f"响应消息：{response.message}")
    
    # 检查 output
    print(f"\nOutput 属性：{response.output}")
    if response.output:
        print(f"Output 类型：{type(response.output)}")
        print(f"Output 内容：{response.output}")
        
        # 尝试访问 choices
        if hasattr(response.output, 'choices'):
            print(f"Choices: {response.output.choices}")
            if response.output.choices:
                result = response.output.choices[0].message.content
                print(f"\n✓ 结果：{result}")
        else:
            print("Output 没有 choices 属性")
            # 尝试直接访问
            if hasattr(response.output, 'text'):
                print(f"Text: {response.output.text}")
    else:
        print("Output 为 None")
    
    # 尝试使用 response.json()
    print(f"\n尝试 JSON 序列化:")
    try:
        response_dict = json.loads(str(response))
        print(f"JSON: {json.dumps(response_dict, indent=2, ensure_ascii=False)}")
    except:
        print("无法序列化为 JSON")
    
except Exception as e:
    print(f"\n✗ 异常：{str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
