"""
测试百度 OCR 连通性（带超时）
"""

from aip import AipOcr
import socket

# 设置超时
socket.setdefaulttimeout(30)

# 凭证
APP_ID = '122486396'
API_KEY = '***REMOVED***'
SECRET_KEY = 'wdrSqpnJOtkzVrRpZobYybqidSBdUPNM'

# 测试图片（使用较小的图片）
TEST_IMAGE = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\sanguang\page_292.png'

print("=" * 70)
print("百度 OCR 连通性测试（带超时）")
print("=" * 70)

try:
    # 初始化客户端
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    print("✓ 客户端初始化成功")
    
    # 读取图片
    with open(TEST_IMAGE, 'rb') as f:
        image = f.read()
    print(f"✓ 图片已读取：{len(image)} bytes")
    
    # 调用识别（使用标准版，更快）
    print("\n正在调用 OCR 识别（标准版）...")
    result = client.basicGeneral(image)
    
    if 'error_code' in result:
        print(f"\n✗ 识别失败！")
        print(f"错误代码：{result['error_code']}")
        print(f"错误信息：{result['error_msg']}")
    else:
        print(f"\n✓ 识别成功！")
        print(f"识别结果行数：{len(result.get('words_result', []))}")
        if result.get('words_result'):
            print(f"前 3 行：{result['words_result'][:3]}")
            
except socket.timeout:
    print("\n✗ 请求超时！请检查网络连接")
except Exception as e:
    print(f"\n✗ 发生错误：{e}")
