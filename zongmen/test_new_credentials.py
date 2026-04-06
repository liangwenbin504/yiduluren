"""
测试新的百度 OCR 凭证是否有效
"""

from aip import AipOcr
import os

# 新的凭证（从百度云控制台获取）
APP_ID = 'ALTAK-Y982KRZJddAl58RRUe3Zk'
API_KEY = '***REMOVED***'
SECRET_KEY = '***REMOVED***'

# 测试图片（使用之前提取的三光课页面）
TEST_IMAGE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print("=" * 70)
print("测试新的百度 OCR 凭证")
print("=" * 70)
print(f"\nAPP_ID: {APP_ID}")
print(f"API_KEY: {API_KEY[:20]}...")
print(f"SECRET_KEY: {SECRET_KEY[:20]}...")

# 检查测试图片是否存在
if not os.path.exists(TEST_IMAGE):
    print(f"\n✗ 测试图片不存在：{TEST_IMAGE}")
    print("\n请先运行页面提取脚本")
    exit(1)

print(f"\n✓ 测试图片存在：{TEST_IMAGE}")

# 初始化客户端
print("\n正在初始化百度 OCR 客户端...")
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取测试图片
with open(TEST_IMAGE, 'rb') as f:
    image = f.read()

print(f"图片大小：{len(image)} bytes")

# 调用 OCR 识别
print("\n正在调用 OCR 识别接口...")
try:
    result = client.basicAccurate(image, {
        'recognize_granularity': 'big',
        'probability': 'true',
    })
    
    # 检查结果
    if 'error_code' in result:
        print(f"\n✗ 识别失败！")
        print(f"错误代码：{result['error_code']}")
        print(f"错误信息：{result['error_msg']}")
        
        if result['error_code'] == 14:
            print("\n可能原因：IAM 认证失败")
            print("解决方案：")
            print("1. 检查 APP_ID 是否正确（应该是 AccessKey ID）")
            print("2. 检查 API_KEY 和 SECRET_KEY 是否正确")
            print("3. 确认子用户是否有 OCR 服务权限")
        elif result['error_code'] == 17:
            print("\n可能原因：QPS 超限")
        elif result['error_code'] == 18:
            print("\n可能原因：余额不足")
    else:
        print("\n✓ 识别成功！")
        print(f"识别结果行数：{len(result.get('words_result', []))}")
        print("\n前 5 行内容：")
        for i, word in enumerate(result['words_result'][:5]):
            print(f"  {i+1}. {word['words']}")
        
        print("\n" + "=" * 70)
        print("✓ 凭证有效！可以开始批量识别")
        print("=" * 70)
        
except Exception as e:
    print(f"\n✗ 调用失败：{e}")
    print("\n请检查：")
    print("1. 网络连接是否正常")
    print("2. 凭证格式是否正确")
    print("3. 百度 OCR 服务是否可用")
