"""
快速测试：验证新的 OCR 凭证是否有效
"""

import requests
import base64

# 新的凭证（2026-03-21）
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

# 测试图片
TEST_IMAGE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print("=" * 70)
print("百度 OCR 凭证验证测试")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 读取图片
with open(TEST_IMAGE, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"\n✓ 测试图片已加载：{len(image_data)} bytes (base64)")

# 获取 access_token
print("\n正在获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

response = requests.post(token_url, params=token_params)
token_result = response.json()

if 'access_token' not in token_result:
    print(f"\n✗ 获取 access_token 失败！")
    print(f"错误：{token_result}")
    exit(1)

access_token = token_result['access_token']
print(f"✓ access_token 获取成功")

# 调用 OCR
print("\n正在调用 OCR 识别...")
ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"

headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = {'image': image_data, 'type': 'BASE64'}

ocr_response = requests.post(ocr_url, headers=headers, data=data)
ocr_result = ocr_response.json()

if 'error_code' in ocr_result:
    print(f"\n✗ OCR 识别失败！")
    print(f"错误代码：{ocr_result['error_code']}")
    print(f"错误信息：{ocr_result['error_msg']}")
    exit(1)

print(f"\n✓ OCR 识别成功！")
print(f"识别结果行数：{len(ocr_result.get('words_result', []))}")
print("\n前 5 行内容：")
for i, word in enumerate(ocr_result['words_result'][:5]):
    print(f"  {i+1}. {word['words']}")

print("\n" + "=" * 70)
print("✓ 凭证验证通过！可以开始批量提取")
print("=" * 70)
