#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""设置图片红色部分的透明度"""

from PIL import Image
import os

def set_red_transparency(input_path, output_path, red_transparency=128):
    """
    设置图片红色部分的透明度
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        red_transparency: 红色部分的透明度 (0-255, 0为完全透明，255为完全不透明)
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        
        datas = img.getdata()
        
        new_data = []
        for item in datas:
            r, g, b, a = item
            # 检查是否是红色区域（红色值较高，绿色和蓝色值较低）
            if r > 100 and g < 100 and b < 100:
                # 保持红色不变，设置透明度为指定值
                new_data.append((r, g, b, red_transparency))
            else:
                # 其他区域保持不变
                new_data.append(item)
        
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"处理完成！图片已保存至: {output_path}")
        print(f"红色部分透明度已设置为: {red_transparency}")
        return True
        
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_image = os.path.join(base_dir, "图片1_transparent.png")
    output_image = os.path.join(base_dir, "图片1_transparent_30.png")
    
    if os.path.exists(input_image):
        print(f"正在处理图片: {input_image}")
        set_red_transparency(input_image, output_image, red_transparency=30)
    else:
        print(f"找不到输入图片: {input_image}")
