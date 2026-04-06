# -*- coding: utf-8 -*-
"""
修复并测试 Qwen Max API 连接
"""

import dashscope
from dashscope import Generation

# API Key
API_KEY = '***REMOVED***'

print("=" * 70)
print("测试 Qwen Max API 连接")
print("=" * 70)

# 检查 API Key
print(f"\nAPI Key: {API_KEY[:15]}...{API_KEY[-10:]}")
print(f"API Key 长度：{len(API_KEY)}")

# 简单测试
test_prompt = "你好，请用一句话介绍大六壬。"

print(f"\n发送测试请求...")
print(f"提示词：{test_prompt}")

try:
    # 设置 API Key
    dashscope.api_key = API_KEY
    
    # 调用 API
    response = Generation.call(
        model='qwen-max',
        messages=[
            {'role': 'user', 'content': test_prompt}
        ],
        timeout=30
    )
    
    # 检查结果
    print(f"\n响应状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.output.choices[0].message.content
        print("✓ API 调用成功！")
        print(f"\n回复内容：{result}")
    else:
        print(f"✗ API 调用失败")
        print(f"错误代码：{response.code}")
        print(f"错误信息：{response.message}")
        
except Exception as e:
    print(f"✗ 发生异常：{str(e)}")
    print(f"异常类型：{type(e).__name__}")

print("\n" + "=" * 70)
