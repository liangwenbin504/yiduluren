"""
百度 OCR 问题诊断工具
"""

import requests
import json

# 凭证
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

print("=" * 70)
print("百度 OCR 问题诊断")
print("=" * 70)

# 诊断 1: 检查网络连接
print("\n[诊断 1] 检查网络连接...")
try:
    response = requests.get("https://aip.baidubce.com", timeout=5)
    print(f"✓ 网络连接正常 (HTTP {response.status_code})")
except Exception as e:
    print(f"✗ 网络连接失败：{e}")
    exit(1)

# 诊断 2: 尝试获取 access_token
print("\n[诊断 2] 尝试获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

print(f"AppID: {APP_ID}")
print(f"Secret Key: {SECRET_KEY[:20]}...")

token_response = requests.post(token_url, params=token_params, timeout=15)
print(f"HTTP 状态码：{token_response.status_code}")
print(f"返回内容：{token_response.text}")

token_result = token_response.json()

if 'access_token' in token_result:
    print(f"\n✓✓✓ 认证成功！Token 已获取")
    exit(0)

# 失败分析
print(f"\n✗ 认证失败")
print(f"错误类型：{token_result.get('error')}")
print(f"错误描述：{token_result.get('error_description')}")

print("\n" + "=" * 70)
print("问题分析和解决方案")
print("=" * 70)

if token_result.get('error') == 'invalid_client':
    print("\n【问题】客户端认证失败")
    print("\n可能原因：")
    print("1. AppID 不存在或未激活")
    print("2. Secret Key 不正确")
    print("3. 应用可能被禁用或删除")
    print("4. 账户未实名认证")
    
    print("\n建议操作：")
    print("步骤 1: 在百度 OCR 控制台确认应用状态是否正常")
    print("步骤 2: 点击'更新 Secret Key'重新生成密钥")
    print("步骤 3: 检查账户实名认证状态")
    print("步骤 4: 尝试删除应用后重新创建")
    
    print("\n快速修复：")
    print("1. 返回应用列表页面")
    print("2. 找到'六壬'应用")
    print("3. 点击右侧'更新 Secret Key'")
    print("4. 复制新的 Secret Key")
    print("5. 告诉我新的密钥")

elif token_result.get('error') == 'invalid_grant':
    print("\n【问题】授权类型错误")
    print("请检查 grant_type 是否为 'client_credentials'")

else:
    print(f"\n【未知错误】{token_result}")

print("\n" + "=" * 70)
