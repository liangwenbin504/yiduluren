"""
地支布局生成器 - 大六壬环形地盘布局
基于 skill: dizhi-layout-generator

地盘永远不动，天盘根据月将加时转动
"""

import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from data.斗首择日规则 import DIZHI

# 地盘位置（永远不动）
# 使用网格坐标 (col, row) 定位
DIZHI_POSITIONS = {
    # 上排（4 个，从左到右）
    '巳': (0, 0), '午': (1, 0), '未': (2, 0), '申': (3, 0),
    # 左列（2 个，从上到下）
    '辰': (0, 1), '卯': (0, 2),
    # 右列（2 个，从上到下，左移一格）
    '酉': (3, 1), '戌': (3, 2),
    # 下排（4 个，从右到左）
    '亥': (3, 3), '子': (2, 3), '丑': (1, 3), '寅': (0, 3),
}


def arrange_tiandi_pan(yuejiang: str, shichen: str) -> dict:
    """
    排天地盘（月将加时，天盘顺排）
    
    :param yuejiang: 月将（地支）
    :param shichen: 占时（地支）
    :return: 天地盘对应关系 {地盘地支：天盘地支}
    """
    shi_index = DIZHI.index(shichen)
    yuejiang_index = DIZHI.index(yuejiang)
    
    # 计算天盘子位在地盘的哪个位置
    zi_position = (shi_index - yuejiang_index) % 12
    
    # 天盘：从地盘子宫开始，每个位置上的天盘地支
    tian_pan = []
    for i in range(12):
        tian_index = (i - zi_position) % 12
        tian_pan.append(DIZHI[tian_index])
    
    # 天地对应：地盘地支 -> 天盘地支
    result = {}
    for i in range(12):
        result[DIZHI[i]] = tian_pan[i]
    
    return result


def get_tiandi_pan_visual(yuejiang: str, shichen: str) -> list:
    """
    获取天地盘可视化布局（用于文本显示）
    
    :param yuejiang: 月将
    :param shichen: 占时
    :return: 格式化布局字符串列表
    """
    tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)
    
    layout = []
    
    # 上排
    row1 = "        "
    for dizhi in ['巳', '午', '未', '申']:
        tian = tiandi_pan[dizhi]
        row1 += f"{tian}{dizhi}  "
    layout.append(row1)
    
    # 左列 + 右列（辰卯右移一格，酉戌左移一格）
    row2 = f"        辰      酉  "
    layout.append(row2)
    
    row3 = f"        卯      戌  "
    layout.append(row3)
    
    # 下排
    row4 = "        "
    for dizhi in ['寅', '丑', '子', '亥']:
        tian = tiandi_pan[dizhi]
        row4 += f"{tian}{dizhi}  "
    layout.append(row4)
    
    return layout


def print_tiandi_pan(yuejiang: str, shichen: str):
    """
    打印天地盘布局
    
    :param yuejiang: 月将
    :param shichen: 占时
    """
    print(f"月将：{yuejiang}，占时：{shichen}")
    print("=" * 40)
    
    layout = get_tiandi_pan_visual(yuejiang, shichen)
    for line in layout:
        print(line)
    
    print("=" * 40)


# 使用示例
if __name__ == '__main__':
    # 示例：月将亥，占时午
    print("示例：亥将午时")
    print_tiandi_pan('亥', '午')
    
    # 获取天地盘对应关系
    result = arrange_tiandi_pan('亥', '午')
    print("\n天地盘对应关系：")
    for dizhi in DIZHI:
        print(f"地盘{dizhi} → 天盘{result[dizhi]}")
