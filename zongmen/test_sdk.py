"""
使用百度 SDK 测试 OCR
"""

from aip import AipOcr

# 凭证
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

# 测试图片
TEST_IMAGE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print("=" * 70)
print("使用百度 SDK 测试 OCR")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 初始化客户端
print("\n正在初始化 OCR 客户端...")
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取图片
with open(TEST_IMAGE, 'rb') as f:
    image = f.read()

print(f"✓ 图片已加载：{len(image)} bytes")

# 调用高精度识别
print("\n正在调用 OCR 识别...")
result = client.basicAccurate(image, {
    'recognize_granularity': 'big',
    'probability': 'true',
})

# 检查结果
if 'error_code' in result:
    print(f"\n✗ OCR 识别失败！")
    print(f"错误代码：{result['error_code']}")
    print(f"错误信息：{result['error_msg']}")
    
    if result['error_code'] == 14:
        print("\n可能原因：IAM 认证失败")
        print("请确认：")
        print("1. 是否使用的是 OCR 应用的 API Key（不是 IAM AccessKey）")
        print("2. AppID 是否正确")
        print("3. Secret Key 是否正确")
else:
    print(f"\n✓ OCR 识别成功！")
    print(f"识别结果行数：{len(result.get('words_result', []))}")
    print("\n前 5 行内容：")
    for i, word in enumerate(result['words_result'][:5]):
        print(f"  {i+1}. {word['words']}")
    
    print("\n" + "=" * 70)
    print("✓ 凭证有效！")
    print("=" * 70)
