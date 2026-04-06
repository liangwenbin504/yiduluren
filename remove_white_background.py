#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""移除图片白色背景，转换为透明背景"""

from PIL import Image
import os

def remove_white_background(input_path, output_path, tolerance=30):
    """
    移除图片白色背景
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        tolerance: 容差值，用于确定哪些白色需要被移除
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        
        datas = img.getdata()
        
        new_data = []
        for item in datas:
            if item[0] > 255 - tolerance and item[1] > 255 - tolerance and item[2] > 255 - tolerance:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        img.save(output_path, "PNG")
        print(f"处理完成！图片已保存至: {output_path}")
        return True
        
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_image = os.path.join(base_dir, "图片1.png")
    output_image = os.path.join(base_dir, "图片1_transparent.png")
    
    if os.path.exists(input_image):
        print(f"正在处理图片: {input_image}")
        remove_white_background(input_image, output_image, tolerance=40)
    else:
        print(f"找不到输入图片: {input_image}")
