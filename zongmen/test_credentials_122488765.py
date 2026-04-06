"""
测试新 OCR 凭证 (122488765)
"""

import requests
import base64
import os

# 新凭证
APP_ID = '122488765'
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = '1PTGbm2FJsGVMaSq3XTs6WZg7VwBXtO5'

print("=" * 70)
print("测试 OCR 凭证")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 获取 token
print("\n正在获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

token_response = requests.post(token_url, params=token_params, timeout=15)
token_result = token_response.json()

print(f"HTTP 状态码：{token_response.status_code}")

if 'access_token' not in token_result:
    print(f"\n✗ 获取 token 失败！")
    print(f"错误：{token_result.get('error')}")
    print(f"描述：{token_result.get('error_description')}")
    exit(1)

access_token = token_result['access_token']
print(f"\n✓✓✓ access_token 获取成功！")

# 测试 OCR
test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

if not os.path.exists(test_image_path):
    print(f"\n✗ 测试图片不存在")
    exit(1)

with open(test_image_path, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"✓ 图片已加载")

ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = {'image': image_data, 'type': 'BASE64'}

print(f"\n正在调用 OCR 识别...")
ocr_response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
ocr_result = ocr_response.json()

if 'error_code' in ocr_result:
    print(f"\n✗ OCR 失败！")
    print(f"错误代码：{ocr_result['error_code']}")
    print(f"错误信息：{ocr_result['error_msg']}")
    exit(1)

print(f"\n✓✓✓ OCR 识别成功！")
print(f"识别结果行数：{len(ocr_result.get('words_result', []))}")
if ocr_result.get('words_result'):
    print("\n前 5 行内容：")
    for i, item in enumerate(ocr_result['words_result'][:5]):
        print(f"  {i+1}. {item.get('words', 'N/A')}")

print("\n" + "=" * 70)
print("✓✓✓ 凭证验证通过！可以开始批量提取 ✓✓✓")
print("=" * 70)
