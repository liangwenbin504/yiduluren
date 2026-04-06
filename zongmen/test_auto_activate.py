"""
尝试直接调用 API，看是否能自动开通服务
"""

import requests
import base64
import os

# 凭证
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

print("=" * 70)
print("尝试自动开通 OCR 服务")
print("=" * 70)

# 步骤 1: 获取 token
print("\n[1] 获取 access_token...")
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
    print(f"\n✗ 获取 token 失败")
    print(f"错误：{token_result.get('error')}")
    print(f"描述：{token_result.get('error_description')}")
    
    print("\n建议操作：")
    print("1. 点击左侧菜单【概览】（在【应用列表】上方）")
    print("2. 在概览页面找到【开通服务】或【立即使用】按钮")
    print("3. 或者检查账户是否已完成实名认证")
    exit(1)

access_token = token_result['access_token']
print(f"✓ access_token 获取成功")

# 步骤 2: 尝试调用 OCR（可能会自动开通）
print("\n[2] 尝试调用 OCR 接口（可能自动开通服务）...")

# 创建一个简单的测试图片（1x1 像素的白色图片）
test_image_data = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82').decode('utf-8')

ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = {'image': test_image_data, 'type': 'BASE64'}

try:
    ocr_response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
    ocr_result = ocr_response.json()
    
    print(f"HTTP 状态码：{ocr_response.status_code}")
    print(f"返回结果：{ocr_result}")
    
    if 'error_code' in ocr_result:
        error_code = ocr_result['error_code']
        error_msg = ocr_result['error_msg']
        
        print(f"\n错误代码：{error_code}")
        print(f"错误信息：{error_msg}")
        
        if error_code == 17:
            print("\n可能原因：服务未开通或余额不足")
            print("\n解决方案：")
            print("1. 检查百度账户是否已实名认证")
            print("2. 可能需要绑定支付方式（即使有免费额度）")
            print("3. 联系百度客服：400-877-7788")
        elif error_code == 18:
            print("\n余额不足，请充值")
        elif error_code == 14:
            print("\n认证失败，请检查密钥")
    else:
        print("\n✓✓✓ 服务已开通！OCR 识别成功！")
        
except requests.exceptions.Timeout:
    print("\n请求超时")
except Exception as e:
    print(f"\n发生错误：{e}")
