"""
测试百度 OCR 是否正常
"""

from aip import AipOcr
import os

# 配置
APP_ID = '122484585'
API_KEY = 'fHvvwcgIFlKucSeAtcx53DlK'
SECRET_KEY = 'WxKzp9GaOBfdAACPm5sLdckYWG6cjQ1'

# 测试图片
img_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\pdf_extract\64_ke_full\temp_images\page_207.png'

print(f"测试图片：{img_path}")
print(f"图片存在：{os.path.exists(img_path)}")

# 初始化
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 读取图片
with open(img_path, 'rb') as f:
    image = f.read()

print(f"图片大小：{len(image)} 字节")

# 识别
print("\n正在识别...")
try:
    result = client.basicAccurate(image)
    
    if 'words_result' in result:
        print(f"✓ 识别成功！")
        print(f"识别行数：{len(result['words_result'])} 行")
        print("\n前 5 行内容：")
        for i, word in enumerate(result['words_result'][:5], 1):
            print(f"  {i}. {word['words']}")
    else:
        print(f"✗ 识别失败")
        print(f"返回结果：{result}")
        
except Exception as e:
    print(f"✗ 错误：{e}")
    import traceback
    traceback.print_exc()
