"""
《仪度六壬选日要诀》可视化排盘模块
以传统环形布局显示天盘与贵人盘
"""

import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from utils.yiduluren_paipan import YiDuLiuRenPaiPan


def visualize_tiandi_pan(paipan_result: dict):
    """
    可视化显示天地盘（环形布局）
    
    地盘固定布局：
            巳午未申
          辰       酉
          卯       戌
            寅丑子亥
    
    :param paipan_result: 排盘结果字典
    """
    tian_pan = paipan_result['天盘']
    tiandi_dying = tian_pan['天地对应']
    
    print("\n【天地盘环形布局】")
    print("        (天盘→地盘)")
    print()
    
    # 上排（4 个）
    row1 = "            "
    for dizhi in ['巳', '午', '未', '申']:
        tian = tiandi_dying[dizhi]
        row1 += f"{tian}→{dizhi}  "
    print(row1)
    
    # 左列 + 右列
    row2_left = f"      {tiandi_dying['辰']}→辰"
    row2_right = f"          {tiandi_dying['酉']}→酉"
    print(row2_left + row2_right)
    
    row3_left = f"      {tiandi_dying['卯']}→卯"
    row3_right = f"          {tiandi_dying['戌']}→戌"
    print(row3_left + row3_right)
    
    # 下排（4 个，从右到左）
    row4 = "            "
    for dizhi in ['寅', '丑', '子', '亥']:
        tian = tiandi_dying[dizhi]
        row4 += f"{tian}→{dizhi}  "
    print(row4)


def visualize_gui_ren_pan(paipan_result: dict):
    """
    可视化显示贵人盘（天将盘）
    
    :param paipan_result: 排盘结果字典
    """
    gui_ren_pan = paipan_result['贵人盘']
    tian_jiang_list = gui_ren_pan['天将列表']
    
    # 创建天将映射：天盘地支 → 天将
    tian_jiang_map = gui_ren_pan['天将映射']
    
    # 获取天地对应
    tian_pan = paipan_result['天盘']
    tiandi_dying = tian_pan['天地对应']
    
    print("\n【贵人盘环形布局】")
    print("        (天将→天盘→地盘)")
    print()
    
    # 上排（4 个）
    row1 = "                  "
    for dizhi in ['巳', '午', '未', '申']:
        tian = tiandi_dying[dizhi]
        tianjiang = tian_jiang_map.get(tian, '')
        if tianjiang:
            row1 += f"{tianjiang}→{tian}→{dizhi}  "
        else:
            row1 += f"    {tian}→{dizhi}  "
    print(row1)
    
    # 左列 + 右列
    row2_left = f"      {tian_jiang_map.get(tiandi_dying['辰'], '')}→{tiandi_dying['辰']}→辰"
    row2_right = f"              {tian_jiang_map.get(tiandi_dying['酉'], '')}→{tiandi_dying['酉']}→酉"
    print(row2_left + "  " + row2_right)
    
    row3_left = f"      {tian_jiang_map.get(tiandi_dying['卯'], '')}→{tiandi_dying['卯']}→卯"
    row3_right = f"              {tian_jiang_map.get(tiandi_dying['戌'], '')}→{tiandi_dying['戌']}→戌"
    print(row3_left + "  " + row3_right)
    
    # 下排（4 个，从右到左）
    row4 = "                  "
    for dizhi in ['寅', '丑', '子', '亥']:
        tian = tiandi_dying[dizhi]
        tianjiang = tian_jiang_map.get(tian, '')
        if tianjiang:
            row4 += f"{tianjiang}→{tian}→{dizhi}  "
        else:
            row4 += f"    {tian}→{dizhi}  "
    print(row4)


def visualize_full_pai_pan(lunar_month: int, shichen: str, ri_gan: str, ri_zhi: str, is_night: bool = None):
    """
    完整可视化排盘
    
    :param lunar_month: 农历月份
    :param shichen: 占时
    :param ri_gan: 日干
    :param ri_zhi: 日支
    :param is_night: 是否夜间
    """
    paipan = YiDuLiuRenPaiPan()
    result = paipan.full_pai_pan(lunar_month, shichen, ri_gan, ri_zhi, is_night)
    
    print("\n" + "=" * 80)
    print(f"【基本信息】")
    print(f"  月将：{result['月将']}  占时：{result['占时']}  日柱：{result['日柱']}  昼夜：{result['昼夜']}")
    print(f"  贵人：{result['贵人盘']['贵人']}  落地盘：{result['贵人盘']['贵人落地盘位置']}  {result['贵人盘']['顺逆']}行")
    print("=" * 80)
    
    # 显示天地盘
    visualize_tiandi_pan(result)
    
    # 显示贵人盘
    visualize_gui_ren_pan(result)
    
    print("\n" + "=" * 80)


def test_visualization():
    """测试可视化排盘"""
    print("=" * 80)
    print("测试案例 1：正月（雨水后），甲子日，午时（昼占）")
    print("=" * 80)
    visualize_full_pai_pan(1, '午', '甲', '子', is_night=False)
    
    print("\n\n")
    print("=" * 80)
    print("测试案例 2：正月（雨水后），甲子日，子时（夜占）")
    print("=" * 80)
    visualize_full_pai_pan(1, '子', '甲', '子', is_night=True)
    
    print("\n\n")
    print("=" * 80)
    print("测试案例 3：三月（谷雨后），丙寅日，酉时（夜占）")
    print("=" * 80)
    visualize_full_pai_pan(3, '酉', '丙', '寅', is_night=True)


if __name__ == '__main__':
    test_visualization()
