"""
测试百度 OCR 通用接口
"""

from aip import AipOcr
import os

# 配置
APP_ID = '122484585'
API_KEY = 'fHvvwcgIFlKucSeAtcx53DlK'
SECRET_KEY = 'WxKzp9GaOBfdAACPm5sLdckYWG6cjQ1'

# 测试图片
img_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\temp_images\page_207.png'

print("测试百度 OCR 接口...")
print(f"图片：{os.path.basename(img_path)}")

# 初始化
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取图片
with open(img_path, 'rb') as f:
    image = f.read()

# 通用文字识别（更快）
print("\n使用通用接口识别...")
try:
    result = client.basicGeneral(image)
    
    if 'words_result' in result:
        print(f"✓ 识别成功！")
        print(f"识别行数：{len(result['words_result'])} 行")
        print("\n前 10 行内容：")
        for i, word in enumerate(result['words_result'][:10], 1):
            print(f"  {i}. {word['words']}")
    else:
        print(f"✗ 识别失败：{result}")
        
except Exception as e:
    print(f"✗ 错误：{e}")
