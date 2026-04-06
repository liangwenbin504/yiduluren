"""
重新验证百度 OCR 凭证
"""

import requests
import base64
import os

# 当前使用的凭证
APP_ID = '7542631'
API_KEY = 'OdZmhXw9AqtxP16uZMCbk76q'
SECRET_KEY = '1jDJjCL6rSlcsvsfg2bHBwTSIUEM4bc'

print("=" * 70)
print("百度 OCR 凭证重新验证")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY[:20]}...")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 步骤 1: 获取 access_token
print("\n[步骤 1] 获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': APP_ID,
    'client_secret': SECRET_KEY
}

try:
    token_response = requests.post(token_url, params=token_params, timeout=15)
    token_result = token_response.json()
    
    print(f"HTTP 状态码：{token_response.status_code}")
    
    if 'access_token' not in token_result:
        print(f"\n✗ 获取 access_token 失败！")
        print(f"错误：{token_result.get('error')}")
        print(f"描述：{token_result.get('error_description')}")
        
        print("\n【解决方案】")
        print("1. 返回百度 OCR 控制台")
        print("2. 检查应用是否已被禁用")
        print("3. 或者重新创建新的 OCR 应用")
        exit(1)
    
    access_token = token_result['access_token']
    print(f"\n✓ access_token 获取成功！")
    print(f"Token: {access_token[:50]}...")
    
    # 步骤 2: 测试 OCR 识别
    print("\n[步骤 2] 测试 OCR 识别...")
    
    # 使用之前已有的测试图片
    test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'
    
    if not os.path.exists(test_image_path):
        print(f"\n✗ 测试图片不存在")
        exit(1)
    
    with open(test_image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"✓ 测试图片已加载")
    
    # 调用 OCR
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'image': image_data, 'type': 'BASE64'}
    
    print(f"正在调用 OCR 接口...")
    ocr_response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
    ocr_result = ocr_response.json()
    
    print(f"HTTP 状态码：{ocr_response.status_code}")
    
    if 'error_code' in ocr_result:
        print(f"\n✗ OCR 识别失败！")
        print(f"错误代码：{ocr_result['error_code']}")
        print(f"错误信息：{ocr_result['error_msg']}")
        
        if ocr_result['error_code'] == 14:
            print("\n【问题】IAM 认证失败")
            print("\n可能原因：")
            print("1. 应用被禁用或删除")
            print("2. 服务未开通或已过期")
            print("3. 账户欠费")
            
            print("\n【解决方案】")
            print("1. 登录百度 OCR 控制台")
            print("2. 检查应用状态是否正常")
            print("3. 确认服务已开通")
            print("4. 如有必要，重新创建应用")
    else:
        print(f"\n✓✓✓ OCR 识别成功！")
        print(f"识别结果行数：{len(ocr_result.get('words_result', []))}")
        if ocr_result.get('words_result'):
            print("\n前 3 行内容：")
            for i, item in enumerate(ocr_result['words_result'][:3]):
                print(f"  {i+1}. {item.get('words', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("✓✓✓ 凭证有效！可以重新执行批量提取 ✓✓✓")
        print("=" * 70)
        
except requests.exceptions.Timeout:
    print("\n✗ 请求超时！请检查网络连接")
except Exception as e:
    print(f"\n✗ 发生错误：{e}")
