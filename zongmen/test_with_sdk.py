"""
使用百度官方 SDK 测试
"""

from aip import AipOcr
import os

# 新凭证
APP_ID = '122486851'
API_KEY = 'fehPZapCubu65Z7i9cxLGlPu'
SECRET_KEY = 'tozzQgSmihrcYx92VwAkctE8fSyuVmq3'

print("=" * 70)
print("使用百度官方 SDK 测试")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 初始化客户端
print("\n初始化 OCR 客户端...")
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
print("✓ 客户端初始化完成")

# 测试图片
test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

if not os.path.exists(test_image_path):
    print(f"\n✗ 测试图片不存在")
    exit(1)

# 读取图片
with open(test_image_path, 'rb') as f:
    image = f.read()

print(f"✓ 图片已加载：{len(image)} bytes")

# 调用 OCR（使用标准接口）
print("\n正在调用 OCR 识别（标准版）...")
result = client.basicGeneral(image)

print(f"\n返回结果：{result}")

if 'error_code' in result:
    print(f"\n✗ OCR 失败！")
    print(f"错误代码：{result['error_code']}")
    print(f"错误信息：{result['error_msg']}")
    
    print("\n建议：")
    print("1. 新应用可能需要 5-10 分钟激活")
    print("2. 请在 OCR 控制台确认服务状态为'已开通'")
    print("3. 等待 10 分钟后再试")
else:
    print(f"\n✓✓✓ OCR 识别成功！")
    print(f"识别结果行数：{len(result.get('words_result', []))}")
    if result.get('words_result'):
        print("\n前 5 行内容：")
        for i, item in enumerate(result['words_result'][:5]):
            print(f"  {i+1}. {item.get('words', 'N/A')}")
