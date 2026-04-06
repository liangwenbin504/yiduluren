#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 API 密钥是否有效
"""

import dashscope
from dashscope import Generation
import sys

# API 密钥
API_KEY = '***REMOVED***'
dashscope.api_key = API_KEY

print("="*60)
print("  API 密钥测试工具")
print("="*60)
print()
print(f"API 密钥：{API_KEY[:20]}...{API_KEY[-10:]}")
print()

print("测试 1: 简单对话测试...")
print("-"*60)

try:
    response = Generation.call(
        model='qwen-max',
        messages=[
            {'role': 'system', 'content': '你是一位助手。'},
            {'role': 'user', 'content': '你好，请只回复"测试成功"四个字'}
        ],
        timeout=30,
        stream=False
    )
    
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        result = response.output.get('text', '')
        print(f"✅ 测试成功！")
        print(f"返回内容：{result}")
        print()
        print("API 密钥有效，可以正常使用！")
        sys.exit(0)
    else:
        print(f"❌ API 调用失败")
        print(f"错误代码：{response.status_code}")
        print(f"错误信息：{response.message if hasattr(response, 'message') else '未知'}")
        
except Exception as e:
    print(f"❌ 发生异常：{str(e)}")
    print()
    print("可能的原因：")
    print("1. 网络连接问题 - 请检查网络")
    print("2. API 密钥无效 - 请检查密钥是否正确")
    print("3. 服务未开通 - 请访问 DashScope 控制台开通服务")
    print("4. 额度不足 - 请检查账户余额")
    print()
    print("建议操作：")
    print("1. 访问 https://dashscope.console.aliyun.com/")
    print("2. 检查 API-KEY 管理")
    print("3. 查看用量查询")
    print("4. 确认 Qwen-Max 服务已开通")

print()
print("="*60)
