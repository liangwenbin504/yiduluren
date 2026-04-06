"""
最终测试：使用最简单的方式验证 OCR
"""

import requests
import json
import time

# 凭证
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

print("=" * 70)
print("百度 OCR 最终验证测试")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY}")

# 步骤 1: 获取 access_token
print("\n[步骤 1] 获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

try:
    token_response = requests.post(token_url, params=token_params, timeout=10)
    token_result = token_response.json()
    
    print(f"HTTP 状态码：{token_response.status_code}")
    print(f"返回结果：{token_result}")
    
    if 'access_token' not in token_result:
        print("\n✗ 获取 access_token 失败！")
        print(f"错误：{token_result.get('error', 'unknown')}")
        print(f"描述：{token_result.get('error_description', 'unknown')}")
        
        if token_result.get('error') == 'invalid_client':
            print("\n可能原因：")
            print("1. AppID 或 Secret Key 不正确")
            print("2. 应用可能还未激活（新应用需要等待几分钟）")
            print("3. 应用未启用 OCR 服务")
        exit(1)
    
    access_token = token_result['access_token']
    print(f"\n✓ access_token 获取成功！")
    print(f"Token: {access_token[:50]}...")
    
    # 步骤 2: 测试 OCR（使用小图片）
    print("\n[步骤 2] 测试 OCR 识别...")
    
    # 先检查是否有测试图片
    import os
    test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'
    
    if not os.path.exists(test_image_path):
        print(f"✗ 测试图片不存在：{test_image_path}")
        print("请先提取页面图片")
        exit(1)
    
    # 读取并转换为 base64
    with open(test_image_path, 'rb') as f:
        import base64
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"✓ 图片已加载：{len(image_data)} bytes (base64)")
    
    # 调用 OCR
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'image': image_data, 'type': 'BASE64'}
    
    print(f"正在请求 OCR 接口...")
    ocr_response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
    ocr_result = ocr_response.json()
    
    print(f"HTTP 状态码：{ocr_response.status_code}")
    
    if 'error_code' in ocr_result:
        print(f"\n✗ OCR 识别失败！")
        print(f"错误代码：{ocr_result['error_code']}")
        print(f"错误信息：{ocr_result['error_msg']}")
        exit(1)
    
    print(f"\n✓ OCR 识别成功！")
    print(f"识别结果数：{len(ocr_result.get('words_result', []))}")
    
    if ocr_result.get('words_result'):
        print("\n前 5 行内容：")
        for i, item in enumerate(ocr_result['words_result'][:5]):
            print(f"  {i+1}. {item.get('words', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✓✓✓ 凭证验证通过！可以开始批量提取 ✓✓✓")
    print("=" * 70)
    
except requests.exceptions.Timeout:
    print("\n✗ 请求超时！请检查网络连接")
except requests.exceptions.RequestException as e:
    print(f"\n✗ 网络错误：{e}")
except Exception as e:
    print(f"\n✗ 发生错误：{e}")
