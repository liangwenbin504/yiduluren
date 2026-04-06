"""
简单测试百度 OCR 连接
"""

import requests
import base64

# 新的凭证
ACCESS_KEY_ID = 'ALTAK-Y982KRZJddAl58RRUe3Zk'
SECRET_ACCESS_KEY = '***REMOVED***'

# 测试图片
TEST_IMAGE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print("=" * 70)
print("百度 OCR 简单连接测试")
print("=" * 70)

# 读取图片
with open(TEST_IMAGE, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"✓ 图片已读取：{len(image_data)} bytes (base64)")

# 获取 access_token
print("\n步骤 1: 获取 access_token...")
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': ACCESS_KEY_ID,
    'client_secret': SECRET_ACCESS_KEY
}

try:
    response = requests.post(token_url, params=token_params)
    token_result = response.json()
    
    if 'access_token' in token_result:
        print(f"✓ 获取 access_token 成功")
        access_token = token_result['access_token']
        print(f"  Token: {access_token[:50]}...")
        
        # 调用 OCR 接口
        print("\n步骤 2: 调用 OCR 识别接口...")
        ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'image': image_data,
            'type': 'BASE64'
        }
        
        ocr_response = requests.post(ocr_url, headers=headers, data=data)
        ocr_result = ocr_response.json()
        
        if 'error_code' in ocr_result:
            print(f"\n✗ OCR 识别失败！")
            print(f"错误代码：{ocr_result['error_code']}")
            print(f"错误信息：{ocr_result['error_msg']}")
        else:
            print(f"\n✓ OCR 识别成功！")
            print(f"识别结果行数：{len(ocr_result.get('words_result', []))}")
            print("\n前 3 行内容：")
            for i, word in enumerate(ocr_result['words_result'][:3]):
                print(f"  {i+1}. {word['words']}")
            
            print("\n" + "=" * 70)
            print("✓ 凭证有效！可以开始批量识别")
            print("=" * 70)
    else:
        print(f"\n✗ 获取 access_token 失败！")
        print(f"错误信息：{token_result}")
        
        if 'error_description' in token_result:
            print(f"详细描述：{token_result['error_description']}")
        
        print("\n可能原因：")
        print("1. AccessKey ID 或 Secret Access Key 不正确")
        print("2. 子用户没有 OCR 服务权限")
        print("3. 需要使用主账号创建应用获取 API Key")
        
except Exception as e:
    print(f"\n✗ 请求失败：{e}")
    print("\n请检查网络连接")
