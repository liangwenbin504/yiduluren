#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成六壬相关内容的图片
将四柱、天盘、四课、三传转换为图片格式
"""

import os
from PIL import Image, ImageDraw, ImageFont
from remove_white_background import remove_white_background


def generate_sizhu_image(sizhu_data):
    """
    生成四柱图片
    """
    try:
        # 创建图片，尺寸为 500x300 像素
        img = Image.new('RGB', (500, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            font = ImageFont.truetype('simhei.ttf', 16)
            title_font = ImageFont.truetype('simhei.ttf', 20)
            ganzhi_font = ImageFont.truetype('simhei.ttf', 24)
            label_font = ImageFont.truetype('simhei.ttf', 12)
        except:
            font = ImageFont.load_default()
            title_font = font
            ganzhi_font = font
            label_font = font
        
        # 绘制标题
        draw.text((250, 30), '四柱区域', fill='black', font=title_font, anchor='mm')
        
        # 绘制分隔线
        draw.line([(50, 50), (450, 50)], fill='blue', width=2)
        
        # 四柱顺序：年柱、月柱、日柱、时柱（从右到左）
        items = ['年', '月', '日', '时']
        positions = [125, 200, 275, 350]  # 从右到左的位置
        
        for i, item in enumerate(items):
            value = sizhu_data.get(item, '')
            x = positions[i]
            
            # 绘制柱子背景
            draw.rectangle([x-40, 70, x+40, 270], fill='#FFF3E0', outline='#FFB74D', width=2)
            
            # 绘制柱子标签
            if item == '年':
                label = '年柱'
            elif item == '月':
                label = '月柱'
            elif item == '日':
                label = '日柱'
            else:
                label = '时柱'
            draw.text((x, 85), label, fill='#E65100', font=font, anchor='mm')
            
            # 绘制干支
            draw.text((x, 130), value, fill='#BF360C', font=ganzhi_font, anchor='mm')
            
            # 绘制元辰标签
            draw.rectangle([x-25, 170, x+25, 190], fill='#F48FB1', outline='#EC407A', width=1)
            draw.text((x, 180), '元辰', fill='#C2185B', font=label_font, anchor='mm')
            
            # 绘制演禽信息
            draw.rectangle([x-35, 200, x+35, 260], fill='#C8E6C9', outline='#81C784', width=1)
            
            # 模拟演禽信息
            yanqin_info = {
                '年': '鼠(虚日鼠)',
                '月': '鸟(毕月乌)',
                '日': '狗(娄金狗)',
                '时': '狗(时禽随日)'
            }
            info = yanqin_info.get(item, '')
            draw.text((x, 230), info, fill='#2E7D32', font=label_font, anchor='mm')
        
        # 保存图片
        temp_path = os.path.join(os.path.dirname(__file__), 'sizhu_temp.png')
        img.save(temp_path)
        
        # 去除白色背景，转换为透明背景
        transparent_path = os.path.join(os.path.dirname(__file__), 'sizhu_temp_transparent.png')
        remove_white_background(temp_path, transparent_path, tolerance=30)
        
        # 删除原始图片，返回透明版本
        try:
            os.remove(temp_path)
        except:
            pass
        
        return transparent_path
    except Exception as e:
        print(f"⚠️ 生成四柱图片失败: {e}")
        return None


def generate_tiandi_image(tian_pan):
    """
    生成天地盘图片（包含贵人盘）
    """
    try:
        # 计算扩大后的尺寸（扩大10%）
        base_size = 800
        new_size = int(base_size * 1.1)
        padding = (new_size - base_size) // 2
        
        # 计算1cm对应的像素数（假设300DPI）
        # 1cm ≈ 118.11像素
        extra_space = 118
        
        # 创建图片，在底部增加1cm空间
        img = Image.new('RGB', (new_size, new_size + extra_space), color='white')
        draw = ImageDraw.Draw(img)
        
        # 定义地盘顺序
        di_pan_order = [
            ['巳', '午', '未', '申'],
            ['辰', '', '', '酉'],
            ['卯', '', '', '戌'],
            ['寅', '丑', '子', '亥']
        ]
        
        # 单元格大小（保持原始尺寸）
        cell_size = 200
        
        # 绘制标题（放大字体50%）
        try:
            title_font = ImageFont.truetype('simhei.ttf', 36)  # 放大50%
            font = ImageFont.truetype('simhei.ttf', 36)        # 放大50%
            small_font = ImageFont.truetype('simhei.ttf', 24)   # 放大50%
        except:
            title_font = ImageFont.load_default()
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 调整标题位置，使整体内容更靠下
        draw.text((new_size//2, 60 + padding), '天地盘', fill='black', font=title_font, anchor='mm')
        
        # 绘制网格（调整位置，使整体内容更靠下，并考虑底部增加的空间）
        for i in range(5):
            # 横线
            draw.line([(padding, 120 + padding + i*cell_size), (new_size - padding, 120 + padding + i*cell_size)], fill='gray', width=2)
            # 竖线
            draw.line([(padding + i*cell_size, 120 + padding), (padding + i*cell_size, 920 + padding + extra_space)], fill='gray', width=2)
        
        # 贵人盘配置（示例）
        gui_ren_pan = {
            '子': '贵人',
            '丑': '腾蛇',
            '寅': '朱雀',
            '卯': '六合',
            '辰': '勾陈',
            '巳': '青龙',
            '午': '贵人',
            '未': '天后',
            '申': '太阴',
            '酉': '玄武',
            '戌': '太常',
            '亥': '白虎'
        }
        
        for row_idx, row_data in enumerate(di_pan_order):
            for col_idx, zhi in enumerate(row_data):
                if zhi:
                    # 获取天盘地支
                    tian_zhi = tian_pan.get(zhi, zhi)
                    # 获取贵人盘信息
                    gui_ren = gui_ren_pan.get(zhi, '')
                    
                    # 计算文字位置（调整为更靠下的位置）
                    x = padding + col_idx * cell_size + cell_size // 2
                    y = padding + 120 + row_idx * cell_size + cell_size // 2
                    
                    # 绘制单元格背景（保持原始大小）
                    draw.rectangle([x-90, y-90, x+90, y+90], fill='#E3F2FD', outline='#90CAF9', width=2)
                    
                    # 绘制天盘（只显示天盘和贵人盘，不显示地盘）
                    draw.text((x, y-30), tian_zhi, fill='red', font=font, anchor='mm')
                    # 绘制贵人盘
                    if gui_ren:
                        draw.text((x, y+30), gui_ren, fill='purple', font=small_font, anchor='mm')
        
        # 保存图片（确保完整尺寸和范围）
        temp_path = os.path.join(os.path.dirname(__file__), 'tiandi_temp.png')
        # 确保保存完整图片，不进行任何裁剪
        img.save(temp_path, dpi=(300, 300), quality=100)
        
        # 去除白色背景，转换为透明背景
        transparent_path = os.path.join(os.path.dirname(__file__), 'tiandi_temp_transparent.png')
        remove_white_background(temp_path, transparent_path, tolerance=30)
        
        # 删除原始图片，返回透明版本
        try:
            os.remove(temp_path)
        except:
            pass
        
        return transparent_path
    except Exception as e:
        print(f"⚠️ 生成天地盘图片失败: {e}")
        return None


def generate_sike_image(sike_data):
    """
    生成四课图片（包含天将标识）
    """
    try:
        # 创建图片，尺寸为 600x300 像素（增大尺寸）
        img = Image.new('RGB', (600, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            title_font = ImageFont.truetype('simhei.ttf', 20)
            font = ImageFont.truetype('simhei.ttf', 16)
            ganzhi_font = ImageFont.truetype('simhei.ttf', 20)
            small_font = ImageFont.truetype('simhei.ttf', 12)
        except:
            title_font = ImageFont.load_default()
            font = ImageFont.load_default()
            ganzhi_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 绘制标题
        draw.text((300, 30), '四课', fill='black', font=title_font, anchor='mm')
        
        # 四课从右到左排列
        if sike_data:
            for i, ke in enumerate(sike_data):
                # 计算位置（从右到左）
                x = 500 - i * 120
                y = 180
                
                # 绘制课体背景
                draw.rectangle([x-50, y-80, x+50, y+80], fill='#FFF9C4', outline='#FDD835', width=2)
                
                # 绘制课号
                draw.text((x, y-70), f'课{i+1}', fill='#F57F17', font=font, anchor='mm')
                
                # 绘制上神
                top = ke.get('top', '--')
                draw.text((x, y-30), top, fill='#C62828', font=ganzhi_font, anchor='mm')
                
                # 绘制上神天将（示例）
                tian_jiang_map = {
                    '申': '太阴',
                    '酉': '玄武',
                    '子': '贵人',
                    '丑': '腾蛇'
                }
                tian_jiang = tian_jiang_map.get(top, '')
                if tian_jiang:
                    draw.text((x, y-10), tian_jiang, fill='purple', font=small_font, anchor='mm')
                
                # 绘制下神
                bottom = ke.get('bottom', '--')
                draw.text((x, y+30), bottom, fill='#2E7D32', font=ganzhi_font, anchor='mm')
        
        # 保存图片
        temp_path = os.path.join(os.path.dirname(__file__), 'sike_temp.png')
        img.save(temp_path)
        
        # 去除白色背景，转换为透明背景
        transparent_path = os.path.join(os.path.dirname(__file__), 'sike_temp_transparent.png')
        remove_white_background(temp_path, transparent_path, tolerance=30)
        
        # 删除原始图片，返回透明版本
        try:
            os.remove(temp_path)
        except:
            pass
        
        return transparent_path
    except Exception as e:
        print(f"⚠️ 生成四课图片失败: {e}")
        return None


def generate_sanchuan_image(sanchuan_data):
    """
    生成三传图片（包含天将标识）
    """
    try:
        # 创建图片，尺寸为 600x400 像素（增大尺寸）
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试使用系统字体
        try:
            title_font = ImageFont.truetype('simhei.ttf', 20)
            font = ImageFont.truetype('simhei.ttf', 16)
            ganzhi_font = ImageFont.truetype('simhei.ttf', 20)
            small_font = ImageFont.truetype('simhei.ttf', 12)
        except:
            title_font = ImageFont.load_default()
            font = ImageFont.load_default()
            ganzhi_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # 绘制标题
        draw.text((300, 30), '三传', fill='black', font=title_font, anchor='mm')
        
        # 绘制三传内容
        y_offset = 100
        chuan_names = ['初传', '中传', '末传']
        # 三传天将映射（示例）
        chuan_tianjiang = {
            '初传': '腾蛇',
            '中传': '朱雀',
            '末传': '六合'
        }
        
        for i, name in enumerate(chuan_names):
            chuan = sanchuan_data.get(name, {})
            if chuan:
                x = 300
                y = y_offset + i * 90
                
                # 绘制传体背景
                draw.rectangle([x-200, y-35, x+200, y+35], fill='#C8E6C9', outline='#81C784', width=2)
                
                # 绘制传名
                draw.text((x-150, y), name, fill='#33691E', font=font, anchor='mm')
                
                # 绘制干支
                ganzhi = f'{chuan.get("tiangan", "")}{chuan.get("dizhi", "")}'
                draw.text((x-50, y), ganzhi, fill='#1B5E20', font=ganzhi_font, anchor='mm')
                
                # 绘制天将
                tianjiang = chuan_tianjiang.get(name, '')
                if tianjiang:
                    draw.text((x+50, y-10), '天将:', fill='#33691E', font=small_font, anchor='mm')
                    draw.text((x+100, y-10), tianjiang, fill='purple', font=small_font, anchor='mm')
                
                # 绘制六亲
                if chuan.get('liuqin'):
                    draw.text((x+50, y+10), '六亲:', fill='#33691E', font=small_font, anchor='mm')
                    draw.text((x+100, y+10), chuan.get('liuqin'), fill='#1B5E20', font=small_font, anchor='mm')
        
        # 保存图片
        temp_path = os.path.join(os.path.dirname(__file__), 'sanchuan_temp.png')
        img.save(temp_path)
        
        # 去除白色背景，转换为透明背景
        transparent_path = os.path.join(os.path.dirname(__file__), 'sanchuan_temp_transparent.png')
        remove_white_background(temp_path, transparent_path, tolerance=30)
        
        # 删除原始图片，返回透明版本
        try:
            os.remove(temp_path)
        except:
            pass
        
        return transparent_path
    except Exception as e:
        print(f"⚠️ 生成三传图片失败: {e}")
        return None


def generate_all_images(data):
    """
    生成所有图片
    """
    images = {}
    
    # 生成四柱图片
    sizhu_data = data.get('four_pillars', {})
    if sizhu_data:
        images['sizhu'] = generate_sizhu_image(sizhu_data)
    
    # 生成天地盘图片
    daliuren_data = data.get('daliuren_data', {})
    if daliuren_data:
        tian_pan = daliuren_data.get('tianPan', {})
        if tian_pan:
            images['tiandi'] = generate_tiandi_image(tian_pan)
        
        # 生成四课图片
        sike = daliuren_data.get('sike', [])
        if sike:
            images['sike'] = generate_sike_image(sike)
        
        # 生成三传图片
        sanchuan = daliuren_data.get('sanchuan', {})
        if sanchuan:
            images['sanchuan'] = generate_sanchuan_image(sanchuan)
    
    return images


if __name__ == '__main__':
    # 测试数据
    test_data = {
        'four_pillars': {'年': '丙午', '月': '辛卯', '日': '己亥', '时': '甲戌'},
        'daliuren_data': {
            'tianPan': {'子': '丑', '丑': '寅', '寅': '卯', '卯': '辰', '辰': '巳', '巳': '午', '午': '未', '未': '申', '申': '酉', '酉': '戌', '戌': '亥', '亥': '子'},
            'sike': [
                {'top': '申', 'bottom': '己'},
                {'top': '酉', 'bottom': '申'},
                {'top': '子', 'bottom': '亥'},
                {'top': '丑', 'bottom': '子'}
            ],
            'sanchuan': {
                '初传': {'tiangan': '辛', 'dizhi': '丑', 'liuqin': '兄弟'},
                '中传': {'tiangan': '壬', 'dizhi': '寅', 'liuqin': '官鬼'},
                '末传': {'tiangan': '癸', 'dizhi': '卯', 'liuqin': '官鬼'}
            }
        }
    }
    
    # 生成所有图片
    images = generate_all_images(test_data)
    
    # 打印结果
    for name, path in images.items():
        if path:
            print(f"✅ 生成{name}图片成功：{path}")
        else:
            print(f"❌ 生成{name}图片失败")
