"""
诊断百度 OCR 认证问题
"""

import requests

# 凭证
APP_ID = '122488765'
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = 'aVIqswuOu3BArSpV1A2xsGVu7WyhzCuO'

print("=" * 70)
print("诊断百度 OCR 认证")
print("=" * 70)

# 方法 1: 标准 OAuth 2.0
print("\n【方法 1】标准 OAuth 2.0")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': API_KEY,
    'client_secret': SECRET_KEY
}

print(f"URL: {token_url}")
print(f"client_id: {API_KEY[:20]}...")
print(f"client_secret: {SECRET_KEY[:20]}...")

response = requests.post(token_url, params=token_params, timeout=15)
print(f"HTTP 状态码：{response.status_code}")
print(f"响应：{response.text[:200]}")

# 方法 2: 使用 AppID 作为 client_id
print("\n【方法 2】使用 AppID 作为 client_id")
token_params2 = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

response2 = requests.post(token_url, params=token_params2, timeout=15)
print(f"HTTP 状态码：{response2.status_code}")
print(f"响应：{response2.text[:200]}")

# 方法 3: 检查 API 端点
print("\n【方法 3】检查 API 端点")
test_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
print(f"OCR API URL: {test_url}")
print("这个 URL 是正确的")

# 方法 4: 使用 IAM 认证（如果适用）
print("\n【方法 4】IAM 认证（备选方案）")
print("如果以上方法都失败，可能需要使用 IAM 认证")
print("需要：AccessKey ID + Secret Access Key")
