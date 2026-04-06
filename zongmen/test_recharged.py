# -*- coding: utf-8 -*-
"""
重新测试 OCR - 账户已充值
"""

import requests
import base64
import json

# 凭证
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = 'aVIqswuOu3BArSpV1A2xsGVu7WyhzCuO'

print("=" * 70)
print("重新测试 OCR API（账户已充值）")
print("=" * 70)

# 获取 token
token_url = "https://aip.baidubce.com/oauth/2.0/token"
token_params = {
    'grant_type': 'client_credentials',
    'client_id': API_KEY,
    'client_secret': SECRET_KEY
}

print("\n1. 获取 access_token...")
response = requests.post(token_url, params=token_params, timeout=15)
token_result = response.json()

if 'access_token' not in token_result:
    print(f"X 获取 token 失败：{token_result}")
    exit(1)

access_token = token_result['access_token']
print(f"OK Token 获取成功")

# 测试图片
test_image = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

with open(test_image, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"OK 图片已加载")

# 测试高精度版 API
print(f"\n2. 调用高精度版 OCR API...")
ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = {'image': image_data, 'type': 'BASE64'}

response = requests.post(ocr_url, headers=headers, data=data, timeout=30)
result = response.json()

# 检查结果
if 'error_code' in result:
    print(f"\nX OCR 失败！")
    print(f"错误代码：{result['error_code']}")
    print(f"错误信息：{result['error_msg']}")
    
    # 保存错误详情
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\ocr_error.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n错误详情已保存到：ocr_error.json")
    exit(1)
else:
    print(f"\nOK OCR 识别成功！")
    print(f"识别结果行数：{len(result.get('words_result', []))}")
    
    if result.get('words_result'):
        print(f"\n前 5 行内容：")
        for i, item in enumerate(result['words_result'][:5]):
            print(f"  {i+1}. {item.get('words', 'N/A')}")
    
    # 保存结果
    with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\ocr_success.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n识别结果已保存到：ocr_success.json")

print("\n" + "=" * 70)
print("OK 凭证验证通过！可以开始批量提取")
print("=" * 70)
