# -*- coding: utf-8 -*-
import requests
import base64
import json

API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = 'aVIqswuOu3BArSpV1A2xsGVu7WyhzCuO'

# 获取 token
token_result = requests.post('https://aip.baidubce.com/oauth/2.0/token', 
    params={'grant_type':'client_credentials','client_id':API_KEY,'client_secret':SECRET_KEY}
).json()
access_token = token_result['access_token']
print("Token OK")

# 读取图片
with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png', 'rb') as f:
    img = base64.b64encode(f.read()).decode()

# 测试高精度版
r = requests.post('https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token=' + access_token,
    headers={'Content-Type':'application/x-www-form-urlencoded'},
    data={'image': img, 'type': 'BASE64'}
)
result = r.json()

# 保存结果
with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\test_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

if 'error_code' in result:
    print(f"Error: {result['error_code']} - {result['error_msg']}")
else:
    print(f"Success! Rows: {len(result.get('words_result', []))}")
    if result.get('words_result'):
        print(f"First line: {result['words_result'][0].get('words', '')[:50]}")
