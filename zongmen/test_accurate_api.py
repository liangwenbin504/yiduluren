"""
测试高精度版 OCR API
"""

import requests
import base64
import os

# 凭证
APP_ID = '122488765'
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = 'aVIqswuOu3BArSpV1A2xsGVu7WyhzCuO'

print("=" * 70)
print("测试高精度版 OCR API")
print("=" * 70)

# 获取 token
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': API_KEY,
    'client_secret': SECRET_KEY
}

response = requests.post(token_url, params=token_params, timeout=15)
token_result = response.json()

if 'access_token' not in token_result:
    print(f"✗ 获取 token 失败：{token_result}")
    exit(1)

access_token = token_result['access_token']
print(f"✓ access_token 获取成功")

# 测试图片
test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

with open(test_image_path, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"✓ 图片已加载")

# 测试不同的 API 端点
endpoints = [
    ('标准版', 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'),
    ('高精度版', 'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic'),
    ('高精度含位置', 'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate'),
]

for name, base_url in endpoints:
    print(f"\n测试【{name}】...")
    ocr_url = f"{base_url}?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'image': image_data, 'type': 'BASE64'}
    
    response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
    result = response.json()
    
    if 'error_code' in result:
        print(f"  ✗ 错误 {result['error_code']}: {result['error_msg']}")
    else:
        print(f"  ✓ 成功！识别行数：{len(result.get('words_result', []))}")
        if result.get('words_result'):
            print(f"     前 3 行：{result['words_result'][0].get('words', '')[:30]}...")

print("\n" + "=" * 70)
