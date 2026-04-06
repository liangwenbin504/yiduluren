"""
使用百度官方 SDK 测试 OCR 凭证
"""

from aip import AipOcr

# 凭证
APP_ID = '122488765'
API_KEY = 'YuSVWghkyaklePTTXcJEdpGT'
SECRET_KEY = '1PTGbm2FJsQVMaSq3XTs6WZg7VwBXtO5'

print("=" * 70)
print("使用百度官方 SDK 测试 OCR")
print("=" * 70)
print(f"\nAppID: {APP_ID}")
print(f"API Key: {API_KEY[:20]}...")
print(f"Secret Key: {SECRET_KEY[:20]}...")

# 创建客户端
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取测试图片
test_image_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print(f"\n正在加载图片...")
with open(test_image_path, 'rb') as f:
    image = f.read()

print(f"✓ 图片已加载")
print(f"\n正在调用 OCR 识别...")

# 调用通用文字识别
result = client.generalBasic(image)

print(f"返回结果：{result}")

if 'error_code' in result:
    print(f"\n✗ OCR 失败！")
    print(f"错误代码：{result['error_code']}")
    print(f"错误信息：{result['error_msg']}")
    exit(1)

print(f"\n✓✓✓ OCR 识别成功！")
print(f"识别结果行数：{len(result.get('words_result', []))}")
if result.get('words_result'):
    print("\n前 5 行内容：")
    for i, item in enumerate(result['words_result'][:5]):
        print(f"  {i+1}. {item.get('words', 'N/A')}")

print("\n" + "=" * 70)
print("✓✓✓ 凭证验证通过！可以开始批量提取 ✓✓✓")
print("=" * 70)
