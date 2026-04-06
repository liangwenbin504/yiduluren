"""
大六壬贵人排盘模块
包含：贵人起例、顺逆判断、十二天将排布
"""

import sys
import os

# 添加路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from data.斗首择日规则 import DIZHI, GUIREN, TIANJIANG


class GuiRenCalculator:
    """贵人计算器"""
    
    def __init__(self):
        self.dizhi = DIZHI
        self.guiren = GUIREN
        self.tianjiang = TIANJIANG
    
    def get_gui_ren_by_ri_gan(self, ri_gan: str, is_night: bool = False) -> str:
        """
        根据日干获取贵人（天乙贵人）
        
        贵人起例口诀：
        - 甲戊庚牛羊（丑未）
        - 乙己鼠猴乡（子申）
        - 丙丁猪鸡位（亥酉）
        - 壬癸蛇兔藏（巳卯）
        - 六辛逢马虎（午寅）
        
        :param ri_gan: 日干
        :param is_night: 是否夜间（True=阴贵，False=阳贵）
        :return: 贵人地支
        """
        gui_ren_list = self.guiren.get(ri_gan, ['丑', '未'])
        
        if is_night and len(gui_ren_list) > 1:
            return gui_ren_list[1]  # 阴贵（夜贵）
        else:
            return gui_ren_list[0]  # 阳贵（昼贵）
    
    def is_night_time(self, shichen: str) -> bool:
        """
        判断是否为夜间
        
        昼时：卯、辰、巳、午、未、申
        夜时：酉、戌、亥、子、丑、寅
        
        :param shichen: 占时（地支）
        :return: True=夜间，False=昼间
        """
        zhou_shi = ['卯', '辰', '巳', '午', '未', '申']
        return shichen not in zhou_shi
    
    def is_yang_position(self, dizhi: str) -> bool:
        """
        判断地支是否为阳位
        
        阳位：亥、子、丑、寅、卯、辰
        阴位：巳、午、未、申、酉、戌
        
        :param dizhi: 地支
        :return: True=阳位，False=阴位
        """
        yang_positions = ['亥', '子', '丑', '寅', '卯', '辰']
        return dizhi in yang_positions
    
    def arrange_gui_ren_pan(self, ri_gan: str, tian_pan: dict, 
                           shichen: str = None, is_night: bool = None) -> dict:
        """
        排贵人盘（十二天将）
        
        排法步骤：
        1. 起贵人：根据日干确定贵人（丑或未）
        2. 分昼夜：昼占用阳贵，夜占用阴贵
        3. 贵人加临：贵人加在天盘地支上
        4. 判顺逆：天盘贵人落地盘阳位则顺行，落地盘阴位则逆行
        5. 布天将：贵人→螣蛇→朱雀→六合→勾陈→青龙→天空→白虎→太常→玄武→太阴→天后
        
        :param ri_gan: 日干
        :param tian_pan: 天盘（包含天地对应关系）
        :param shichen: 占时（可选，用于自动判断昼夜）
        :param is_night: 是否夜间（可选，不填则根据 shichen 自动判断）
        :return: 贵人盘字典
        """
        # 1. 自动判断昼夜
        if is_night is None and shichen:
            is_night = self.is_night_time(shichen)
        elif is_night is None:
            is_night = False  # 默认昼占
        
        # 2. 起贵人
        gui_ren = self.get_gui_ren_by_ri_gan(ri_gan, is_night)
        
        # 3. 找位置：天盘贵人地支落地盘的哪个位置
        gui_di_position = None
        for di_zhi, tian_zhi in tian_pan['天地对应'].items():
            if tian_zhi == gui_ren:
                gui_di_position = di_zhi
                break
        
        # 4. 判断顺逆：看天盘贵人落地盘的位置是阳位还是阴位
        # 处理gui_di_position为None的情况
        if gui_di_position:
            is_shun_xing = self.is_yang_position(gui_di_position)
        else:
            # 默认顺行
            is_shun_xing = True
        
        # 5. 排十二天将
        # 天将顺序：贵人→螣蛇→朱雀→六合→勾陈→青龙→天空→白虎→太常→玄武→太阴→天后
        tian_jiang_list = []
        gui_index = DIZHI.index(gui_ren)
        
        for i in range(12):
            # 天将所在地支（天盘地支）
            if is_shun_xing:
                # 顺行：从贵人地支开始，按十二支顺序
                tian_index = (gui_index + i) % 12
            else:
                # 逆行：从贵人地支开始，逆序
                tian_index = (gui_index - i) % 12
            
            tian_jiang_name = self.tianjiang[i]
            tian_jiang_list.append({
                '天将': tian_jiang_name,
                '地支': DIZHI[tian_index],  # 天盘地支
                '位置': i,
                '顺逆': '顺' if is_shun_xing else '逆'
            })
        
        # 创建天将映射：天盘地支 → 天将名
        tian_jiang_map = {}
        for tj in tian_jiang_list:
            tian_jiang_map[tj['地支']] = tj['天将']
        
        return {
            '贵人': gui_ren,
            '贵人落地盘位置': gui_di_position,
            '顺逆': '顺' if is_shun_xing else '逆',
            '昼夜': '夜' if is_night else '昼',
            '天将列表': tian_jiang_list,
            '天将映射': tian_jiang_map
        }
    
    def print_gui_ren_pan(self, ri_gan: str, tian_pan: dict, shichen: str = None):
        """
        打印贵人盘
        
        :param ri_gan: 日干
        :param tian_pan: 天盘
        :param shichen: 占时
        """
        result = self.arrange_gui_ren_pan(ri_gan, tian_pan, shichen)
        
        print("=" * 70)
        print(f"【贵人盘】日干：{ri_gan}")
        print("=" * 70)
        print(f"贵人：{result['贵人']}")
        print(f"昼夜：{result['昼夜']}")
        print(f"贵人落地盘位置：{result['贵人落地盘位置']}")
        print(f"顺逆：{result['顺逆']}行")
        print()
        print("【十二天将】")
        for tj in result['天将列表']:
            print(f"  {tj['天将']:4} → 天盘{tj['地支']:2} ({tj['顺逆']})")
        print("=" * 70)


def test_gui_ren():
    """测试贵人排盘"""
    calc = GuiRenCalculator()
    
    # 测试案例 1：甲日，午时（昼占）
    print("测试 1：甲日，午时（昼占）")
    tian_pan = {
        '天地对应': {
            '子': '巳', '丑': '午', '寅': '未', '卯': '申',
            '辰': '酉', '巳': '戌', '午': '亥', '未': '子',
            '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'
        }
    }
    calc.print_gui_ren_pan('甲', tian_pan, '午')
    
    print("\n\n")
    
    # 测试案例 2：甲日，子时（夜占）
    print("测试 2：甲日，子时（夜占）")
    calc.print_gui_ren_pan('甲', tian_pan, '子')
    
    print("\n\n")
    
    # 测试案例 3：丙日，酉时（夜占）
    print("测试 3：丙日，酉时（夜占）")
    calc.print_gui_ren_pan('丙', tian_pan, '酉')


if __name__ == '__main__':
    test_gui_ren()
