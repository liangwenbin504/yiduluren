"""
《仪度六壬选日要诀》排盘模块
根据传统大六壬规则排出天盘与贵人盘（天将盘）

核心规则：
1. 天盘：月将加时，顺布十二宫
2. 贵人盘：贵人加临天盘地支，根据昼夜、阴阳位决定顺逆
"""

import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from data.斗首择日规则 import (
    TIANGAN, DIZHI, JIGONG, YUEJIANG, JIEQI_YUEJIANG,
    GUIREN, TIANJIANG
)


class YiDuLiuRenPaiPan:
    """
    《仪度六壬选日要诀》排盘引擎
    
    排盘步骤：
    1. 起月将（根据农历月份或节气）
    2. 排天盘（月将加时，顺布十二宫）
    3. 排贵人盘（天将盘）
    """
    
    def __init__(self):
        self.tiangan = TIANGAN
        self.dizhi = DIZHI
        self.tianjiang = TIANJIANG
        self.jigong = JIGONG
        self.yuejiang = YUEJIANG
        self.jieqi_yuejiang = JIEQI_YUEJIANG
        self.guiren = GUIREN
    
    def get_yuejiang_by_month(self, lunar_month: int) -> str:
        """
        根据农历月份获取月将
        
        :param lunar_month: 农历月份（1-12）
        :return: 月将地支
        """
        return self.jieqi_yuejiang.get(lunar_month, '子')
    
    def get_yuejiang_by_jieqi(self, jieqi: str) -> str:
        """
        根据节气获取月将
        
        :param jieqi: 节气名称（如'雨水'、'春分'等）
        :return: 月将地支
        """
        return self.yuejiang.get(jieqi, '子')
    
    def arrange_tian_pan(self, yuejiang: str, shichen: str) -> dict:
        """
        排天盘（月将加时，顺布十二宫）
        
        《仪度六壬选日要诀》规则：
        - 月将永远加在地盘的时支位置上
        - 天盘地支按子丑寅卯...顺序顺时针排布
        
        地盘固定位置：
              巳午未申
              辰   酉
              卯   戌
              寅丑子亥
        
        排法示例（月将亥，占时午）：
        1. 亥将加在地盘午位（位置 1,0）
        2. 天盘顺布：子 (未)、丑 (申)、寅 (酉)、卯 (戌)、辰 (亥)、巳 (子)...
        
        :param yuejiang: 月将（地支）
        :param shichen: 占时（地支）
        :return: 天盘字典（包含天地对应关系）
        """
        # 地盘固定
        di_pan = DIZHI.copy()
        
        # 月将加时：月将加在地盘的时支位置
        shi_index = DIZHI.index(shichen)
        yuejiang_index = DIZHI.index(yuejiang)
        
        # 关键计算：
        # 月将是天盘的起始地支
        # 月将加在时支上，意味着时支位置的地盘上是月将
        # 然后天盘按子丑寅卯...顺序顺时针排布
        
        # 计算天盘子位在地盘的哪个位置
        # 公式：子位 = 时支索引 - 月将索引
        zi_position = (shi_index - yuejiang_index) % 12
        
        # 排天盘：从地盘子宫开始，每个位置上的天盘地支
        tian_pan = []
        for i in range(12):
            # 地盘第 i 宫上的天盘地支
            # 天盘子位在 zi_position，那么第 i 位的天盘 = (i - zi_position) % 12
            tian_index = (i - zi_position) % 12
            tian_pan.append(DIZHI[tian_index])
        
        # 组合天地盘
        result = {
            '地盘': di_pan,
            '天盘': tian_pan,
            '月将': yuejiang,
            '占时': shichen
        }
        
        # 天地对应：地盘地支 → 天盘地支
        result['天地对应'] = {}
        for i in range(12):
            result['天地对应'][di_pan[i]] = tian_pan[i]
        
        return result
    
    def arrange_gui_ren_pan(self, ri_gan: str, tian_pan: dict, is_night: bool = False) -> dict:
        """
        排贵人盘（天将盘）
        
        《仪度六壬选日要诀》规则：
        1. 起贵人：根据日干确定贵人（丑或未）
           - 甲戊庚牛羊：甲日阳贵丑、阴贵未
           - 乙己鼠猴乡：乙日阳贵子、阴贵申
           - 丙丁猪鸡位：丙丁日阳贵亥、阴贵酉
           - 壬癸蛇兔藏：壬癸日阳贵巳、阴贵卯
           - 六辛逢马虎：辛日阳贵午、阴贵寅
        
        2. 判断昼夜：
           - 昼占（卯至申时）：用阳贵
           - 夜占（酉至寅时）：用阴贵
        
        3. 贵人加临：
           - 贵人加在天盘地支上（不是地盘）
           - 看天盘贵人落地盘的哪个位置
        
        4. 判断顺逆：
           - 天盘贵人落地盘阳位（亥子丑寅卯辰）→ 顺行
           - 天盘贵人落地盘阴位（巳午未申酉戌）→ 逆行
        
        5. 布十二天将：
           - 贵人→螣蛇→朱雀→六合→勾陈→青龙→天空→白虎→太常→玄武→太阴→天后
           - 顺行：按顺序布在天盘地支上
           - 逆行：按逆序布在天盘地支上
        
        :param ri_gan: 日干
        :param tian_pan: 天盘（包含天地对应关系）
        :param is_night: 是否夜间（True=夜贵，False=昼贵）
        :return: 贵人盘字典
        """
        # 1. 起贵人（根据日干）
        gui_ren_list = self.guiren.get(ri_gan, ['丑', '未'])
        
        # 2. 确定用阳贵还是阴贵
        if is_night and len(gui_ren_list) > 1:
            gui_ren = gui_ren_list[1]  # 夜贵（阴贵）
        else:
            gui_ren = gui_ren_list[0] if gui_ren_list else '丑'
        
        # 3. 找位置：天盘贵人地支落地盘的哪个位置
        # 例如：天盘丑落地盘申位
        gui_di_position = None
        for di_zhi, tian_zhi in tian_pan['天地对应'].items():
            if tian_zhi == gui_ren:
                gui_di_position = di_zhi
                break
        
        # 4. 判断顺逆：看天盘贵人落地盘的位置是阳位还是阴位
        yang_positions = ['亥', '子', '丑', '寅', '卯', '辰']
        is_shun_xing = gui_di_position in yang_positions
        
        # 5. 排十二天将
        # 天将顺序：贵人→螣蛇→朱雀→六合→勾陈→青龙→天空→白虎→太常→玄武→太阴→天后
        # 天将布在天盘地支上
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
            '天将列表': tian_jiang_list,
            '天将映射': tian_jiang_map
        }
    
    def full_pai_pan(self, lunar_month: int, shichen: str, 
                     ri_gan: str, ri_zhi: str, is_night: bool = None) -> dict:
        """
        完整排盘（天盘 + 贵人盘）
        
        :param lunar_month: 农历月份（1-12）
        :param shichen: 占时（地支）
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param is_night: 是否夜间（None=自动判断）
        :return: 完整排盘结果
        """
        # 1. 起月将
        yuejiang = self.get_yuejiang_by_month(lunar_month)
        
        # 2. 排天盘
        tian_pan = self.arrange_tian_pan(yuejiang, shichen)
        
        # 3. 自动判断昼夜（如果未指定）
        if is_night is None:
            # 卯辰巳午未申为昼，酉戌亥子丑寅为夜
            zhou_shi = ['卯', '辰', '巳', '午', '未', '申']
            is_night = shichen not in zhou_shi
        
        # 4. 排贵人盘（天将盘）
        gui_ren_pan = self.arrange_gui_ren_pan(ri_gan, tian_pan, is_night)
        
        return {
            '月将': yuejiang,
            '占时': shichen,
            '日柱': f"{ri_gan}{ri_zhi}",
            '昼夜': '夜' if is_night else '昼',
            '天盘': tian_pan,
            '贵人盘': gui_ren_pan
        }
    
    def print_pai_pan(self, lunar_month: int, shichen: str, 
                      ri_gan: str, ri_zhi: str, is_night: bool = None):
        """
        打印排盘结果
        
        :param lunar_month: 农历月份
        :param shichen: 占时
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param is_night: 是否夜间
        """
        result = self.full_pai_pan(lunar_month, shichen, ri_gan, ri_zhi, is_night)
        
        print("=" * 60)
        print(f"【基本信息】")
        print(f"  月将：{result['月将']}")
        print(f"  占时：{result['占时']}")
        print(f"  日柱：{result['日柱']}")
        print(f"  昼夜：{result['昼夜']}")
        
        print(f"\n【天盘】（月将加时）")
        print(f"  地盘：{' '.join(result['天盘']['地盘'])}")
        print(f"  天盘：{' '.join(result['天盘']['天盘'])}")
        
        print(f"\n  天地对应：")
        for i, di in enumerate(result['天盘']['地盘']):
            tian = result['天盘']['天盘'][i]
            print(f"    地盘{di} → 天盘{tian}")
        
        print(f"\n【贵人盘】（天将盘）")
        print(f"  贵人：{result['贵人盘']['贵人']}")
        print(f"  贵人落地盘位置：{result['贵人盘']['贵人落地盘位置']}")
        print(f"  顺逆：{result['贵人盘']['顺逆']}行")
        
        print(f"\n  十二天将：")
        for tj in result['贵人盘']['天将列表']:
            print(f"    {tj['天将']:4} → 天盘{tj['地支']:2} ({tj['顺逆']})")
        
        print("=" * 60)


def test_pai_pan():
    """测试排盘功能"""
    paipan = YiDuLiuRenPaiPan()
    
    print("测试案例 1：正月（雨水后），甲子日，午时（昼占）")
    print("月将亥，占时午")
    paipan.print_pai_pan(1, '午', '甲', '子', is_night=False)
    
    print("\n\n测试案例 2：正月（雨水后），甲子日，子时（夜占）")
    print("月将亥，占时子")
    paipan.print_pai_pan(1, '子', '甲', '子', is_night=True)
    
    print("\n\n测试案例 3：三月（谷雨后），丙寅日，酉时（夜占）")
    print("月将酉，占时酉")
    paipan.print_pai_pan(3, '酉', '丙', '寅', is_night=True)


if __name__ == '__main__':
    test_pai_pan()
