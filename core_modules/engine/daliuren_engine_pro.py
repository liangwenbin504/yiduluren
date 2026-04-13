"""
大六壬排盘引擎 - 增强版
包含：天地盘、四课、三传、天将、课格判断
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core_modules.data.斗首择日规则 import (
    TIANGAN, DIZHI, JIGONG, YUEJIANG, JIEQI_YUEJIANG,
    DIZHI_CHONG, LU, YIMA, GUIREN, TIANJIANG
)


class DaLiuRenEnginePro:
    """大六壬排盘引擎（增强版）"""
    
    def __init__(self):
        self.tiangan = TIANGAN
        self.dizhi = DIZHI
        self.tianjiang = TIANJIANG
    
    def get_yuejiang(self, lunar_month: int) -> str:
        """根据农历月份获取月将"""
        return JIEQI_YUEJIANG.get(lunar_month, '子')
    
    def arrange_tiandi_pan(self, yuejiang: str, shichen: str) -> dict:
        """
        排天地盘（月将加时，天盘顺排）
        正确方法：月将加在地盘时支上，天盘地支顺时针排布（子丑寅卯...）
        
        地盘固定位置（顺时针环形）：
              巳午未申
              辰   酉
              卯   戌
              寅丑子亥
        
        天盘排布（月将加时，顺布十二宫）：
        月将加在时支位上，然后按子丑寅卯...顺序顺时针排布
        
        例如：月将亥，占时午
        1. 亥将加在地盘午位上
        2. 顺布：子 (未)、丑 (申)、寅 (酉)、卯 (戌)...
        """
        di_pan = DIZHI.copy()
        
        # 月将加时：月将加在地盘的时支位置
        shi_index = DIZHI.index(shichen)
        yuejiang_index = DIZHI.index(yuejiang)
        
        # 关键理解：
        # 月将是天盘的起始地支
        # 月将加在时支上，意味着时支位置的地盘上是月将
        # 然后天盘按子丑寅卯...顺序顺时针排布
        
        # 计算天盘子位在地盘的哪个位置
        # 月将在时支位，那么子位 = 时支位 - 月将索引
        zi_position = (shi_index - yuejiang_index) % 12
        
        # 天盘：从地盘子宫开始，每个位置上的天盘地支
        tian_pan = []
        for i in range(12):
            # 地盘第 i 宫上的天盘地支
            # 天盘子位在 zi_position，那么第 i 位的天盘 = (i - zi_position) % 12
            tian_index = (i - zi_position) % 12
            tian_pan.append(DIZHI[tian_index])
        
        result = {
            '地盘': di_pan,
            '天盘': tian_pan,
            '月将': yuejiang,
            '占时': shichen
        }
        
        # 天地对应：地盘地支 -> 天盘地支
        result['天地对应'] = {}
        for i in range(12):
            result['天地对应'][di_pan[i]] = tian_pan[i]
        
        return result
    
    def get_jigong(self, tiangan: str) -> str:
        """获取十干寄宫"""
        return JIGONG.get(tiangan, '')
    
    def arrange_si_ke(self, ri_gan: str, ri_zhi: str, tian_pan: dict) -> list:
        """起四课"""
        si_ke = []
        
        ji_gong = self.get_jigong(ri_gan)
        if ji_gong:
            ke1_top = tian_pan['天地对应'].get(ji_gong, '')
            si_ke.append({'top': ke1_top, 'bottom': ri_gan, 'name': '第一课'})
            
            if ke1_top in DIZHI:
                ke2_top = tian_pan['天地对应'].get(ke1_top, '')
                si_ke.append({'top': ke2_top, 'bottom': ke1_top, 'name': '第二课'})
        
        if ri_zhi in DIZHI:
            ke3_top = tian_pan['天地对应'].get(ri_zhi, '')
            si_ke.append({'top': ke3_top, 'bottom': ri_zhi, 'name': '第三课'})
            
            if ke3_top in DIZHI:
                ke4_top = tian_pan['天地对应'].get(ke3_top, '')
                si_ke.append({'top': ke4_top, 'bottom': ke3_top, 'name': '第四课'})
        
        return si_ke
    
    def arrange_tian_jiang(self, ri_gan: str, ri_zhi: str, tian_pan: dict, is_night: bool = False) -> list:
        """
        排十二天将（贵人顺逆排）
        贵人、螣蛇、朱雀、六合、勾陈、青龙、天空、白虎、太常、玄武、太阴、天后
        
        重要概念：
        - 天将是布在**天盘**地支上的
        - 贵人星必须安放在天盘地支位置上
        
        排法步骤：
        1. 起贵人：根据日干确定贵人（丑或未）- 这是天盘地支
        2. 找位置：找到天盘贵人地支落地盘的哪个位置
        3. 判断顺逆：
           - 天盘贵人落地盘阳位（亥子丑寅卯辰）→ 顺行
           - 天盘贵人落地盘阴位（巳午未申酉戌）→ 逆行
        4. 排天将：从贵人开始，按顺序布在天盘地支上
        
        贵人顺逆规则：
        - 甲戊庚牛羊：甲日贵人丑（阳贵）、未（阴贵）
        - 天盘丑落地盘阳位（亥子丑寅卯辰）→ 顺行
        - 天盘丑落地盘阴位（巳午未申酉戌）→ 逆行
        
        :param ri_gan: 日干
        :param ri_zhi: 日支（占时）
        :param tian_pan: 天盘（包含天地对应关系）
        :param is_night: 是否夜间（夜间用阴贵人）
        """
        # 起贵人（根据日干）
        gui_ren_list = GUIREN.get(ri_gan, ['丑', '未'])
        
        # 确定用阳贵还是阴贵
        if is_night and len(gui_ren_list) > 1:
            gui_ren = gui_ren_list[1]  # 夜贵
        else:
            gui_ren = gui_ren_list[0] if gui_ren_list else '丑'
        
        # 关键：找到天盘贵人地支落地盘的哪个位置
        # 例如：天盘丑落地盘申位 → 申在阴位 → 逆行
        gui_di_position = None
        for di_zhi, tian_zhi in tian_pan['天地对应'].items():
            if tian_zhi == gui_ren:
                gui_di_position = di_zhi
                break
        
        # 判断顺逆：看天盘贵人落地盘的位置是阳位还是阴位
        yang_positions = ['亥', '子', '丑', '寅', '卯', '辰']
        is_shun_xing = gui_di_position in yang_positions
        
        # 排天将
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
                '位置': i
            })
        
        return tian_jiang_list
    
    def fa_san_chuan(self, si_ke: list, ri_gan: str) -> dict:
        """发三传（九宗门）"""
        result = {
            '课体': '',
            '三传': [],
            '起法': ''
        }
        
        # 检查四课是否有克
        ke_list = []
        for ke in si_ke:
            ke_type = self.check_ke(ke['top'], ke['bottom'])
            if ke_type != '无克':
                ke_list.append({'课': ke, '类型': ke_type})
        
        if not ke_list:
            # 无克，用遥克法或昴星法
            return self._yao_ke_or_ao_xing(si_ke, ri_gan, result)
        
        # 有克，用贼克法或比用法
        if len(ke_list) == 1:
            ke_info = ke_list[0]
            result['课体'] = '重审课' if ke_info['类型'] == '克上' else '元首课'
            result['三传'] = self._get_chuan_from_ke(ke_info['课'], si_ke)
            result['起法'] = '贼克法'
        else:
            # 多课有克
            return self._bi_yong_or_she_hai(ke_list, ri_gan, si_ke, result)
        
        return result
    
    def check_ke(self, top: str, bottom: str) -> str:
        """检查课体上下克关系"""
        wuxing_map = {
            '寅': '木', '卯': '木',
            '巳': '火', '午': '火',
            '申': '金', '酉': '金',
            '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土'
        }
        
        ke_relations = {
            '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
        }
        
        top_wx = wuxing_map.get(top, '')
        bottom_wx = wuxing_map.get(bottom, '')
        
        if not top_wx or not bottom_wx:
            return '无克'
        
        if ke_relations.get(top_wx) == bottom_wx:
            return '克下'
        elif ke_relations.get(bottom_wx) == top_wx:
            return '克上'
        
        return '无克'
    
    def _yao_ke_or_ao_xing(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """遥克法或昴星法"""
        result['课体'] = '昴星课'
        result['起法'] = '昴星法'
        
        ri_gan_yin_yang = '阳' if TIANGAN.index(ri_gan) % 2 == 0 else '阴'
        
        if ri_gan_yin_yang == '阳':
            result['三传'] = [si_ke[0]['top']] if si_ke else []
        else:
            result['三传'] = [si_ke[-1]['top']] if si_ke else []
        
        return result
    
    def _bi_yong_or_she_hai(self, ke_list: list, ri_gan: str, si_ke: list, result: dict) -> dict:
        """比用法或涉害法"""
        result['课体'] = '比用课'
        result['起法'] = '比用法'
        result['三传'] = [ke_list[0]['课']['top']]
        return result
    
    def _get_chuan_from_ke(self, ke: dict, si_ke: list) -> list:
        """从课获取三传"""
        chu_chuan = ke['top']
        
        zhong_chuan = ''
        for s_ke in si_ke:
            if s_ke['bottom'] == chu_chuan:
                zhong_chuan = s_ke['top']
                break
        
        mo_chuan = ''
        if zhong_chuan:
            for s_ke in si_ke:
                if s_ke['bottom'] == zhong_chuan:
                    mo_chuan = s_ke['top']
                    break
        
        return [chu_chuan, zhong_chuan, mo_chuan]
    
    def get_ke_ge(self, ri_gan: str, ri_zhi: str, san_chuan: dict, 
                  tian_jiang: list, si_ke: list) -> dict:
        """
        判断课格（龙德、斫轮课等）
        根据三传、天将、四课等综合判断
        """
        ke_ge = {
            '课格名称': '',
            '课格说明': '',
            '吉凶': ''
        }
        
        # 获取三传
        chuan_list = san_chuan.get('三传', [])
        if not chuan_list or len(chuan_list) < 3:
            ke_ge['课格名称'] = '普通课'
            ke_ge['课格说明'] = '无特殊课格'
            ke_ge['吉凶'] = '平'
            return ke_ge
        
        chu_chuan = chuan_list[0]
        zhong_chuan = chuan_list[1]
        mo_chuan = chuan_list[2]
        
        # 判断常见课格
        
        # 1. 龙德课：初传见贵人
        if self._is_gui_ren(chu_chuan, ri_gan):
            ke_ge['课格名称'] = '龙德课'
            ke_ge['课格说明'] = '初传见贵人，主有贵人相助，大吉'
            ke_ge['吉凶'] = '上吉'
            return ke_ge
        
        # 2. 斫轮课：初传卯酉，中传寅申
        if (chu_chuan in ['卯', '酉'] and zhong_chuan in ['寅', '申']):
            ke_ge['课格名称'] = '斫轮课'
            ke_ge['课格说明'] = '斧斤斫轮，主改革更新，先难后易'
            ke_ge['吉凶'] = '中吉'
            return ke_ge
        
        # 3. 铸印课：初传巳，中传戌，末传卯
        if chu_chuan == '巳' and zhong_chuan == '戌' and mo_chuan == '卯':
            ke_ge['课格名称'] = '铸印课'
            ke_ge['课格说明'] = '铸造印信，主升迁得权，大吉'
            ke_ge['吉凶'] = '上吉'
            return ke_ge
        
        # 4. 斫轮课变体：卯酉加寅申
        if chu_chuan == '卯' and zhong_chuan == '申':
            ke_ge['课格名称'] = '斫轮课'
            ke_ge['课格说明'] = '金木相战，主改革变动'
            ke_ge['吉凶'] = '中平'
            return ke_ge
        
        # 5. 三奇课：三传甲戊庚或乙丙丁
        # 简化判断
        
        # 6. 六仪课：三传子午卯酉等
        # 简化判断
        
        # 7. 涉害课：涉害深重
        if san_chuan.get('起法') == '涉害法':
            ke_ge['课格名称'] = '涉害课'
            ke_ge['课格说明'] = '涉害深重，主事多阻隔，需谨慎'
            ke_ge['吉凶'] = '小凶'
            return ke_ge
        
        # 8. 遥克课：蒿矢、弹射
        if san_chuan.get('起法') == '遥克法':
            ke_ge['课格名称'] = '蒿矢课'
            ke_ge['课格说明'] = '如箭在弦，主事有紧迫，速战速决'
            ke_ge['吉凶'] = '中平'
            return ke_ge
        
        # 默认
        ke_ge['课格名称'] = '普通课'
        ke_ge['课格说明'] = '无特殊课格，按三传五行断'
        ke_ge['吉凶'] = '平'
        
        return ke_ge
    
    def _is_gui_ren(self, dizhi: str, ri_gan: str) -> bool:
        """判断是否为贵人"""
        gui_ren_list = GUIREN.get(ri_gan, [])
        return dizhi in gui_ren_list
    
    def get_lu_ma_gui(self, ri_gan: str, ri_zhi: str) -> dict:
        """
        获取禄马贵
        禄：甲禄在寅，乙禄在卯...
        驿马：申子辰马在寅，亥卯未马在巳...
        贵人：天乙贵人
        """
        # 禄神（根据日干）
        lu = LU.get(ri_gan, '')
        
        # 驿马（根据日支查三合局）
        # YIMA 字典的键是三合局的地支组合，需要查找日支属于哪个三合局
        yima = ''
        for key, value in YIMA.items():
            if ri_zhi in key:  # 日支在三合局中
                yima = value
                break
        
        # 贵人（根据日干）
        guiren_list = GUIREN.get(ri_gan, [])
        
        return {
            '禄': lu,
            '驿马': yima,
            '贵人': guiren_list
        }
    
    def full_pai_pan(self, lunar_month: int, shichen: str, 
                     ri_gan: str, ri_zhi: str) -> dict:
        """完整排盘（增强版）"""
        # 1. 起月将
        yuejiang = self.get_yuejiang(lunar_month)
        
        # 2. 排天地盘
        tiandi_pan = self.arrange_tiandi_pan(yuejiang, shichen)
        
        # 3. 起四课
        si_ke = self.arrange_si_ke(ri_gan, ri_zhi, tiandi_pan)
        
        # 4. 排天将
        tian_jiang = self.arrange_tian_jiang(ri_gan, ri_zhi, tiandi_pan)
        
        # 5. 发三传
        san_chuan = self.fa_san_chuan(si_ke, ri_gan)
        
        # 6. 起禄马贵
        lu_ma_gui = self.get_lu_ma_gui(ri_gan, ri_zhi)
        
        # 7. 判课格
        ke_ge = self.get_ke_ge(ri_gan, ri_zhi, san_chuan, tian_jiang, si_ke)
        
        return {
            '月将': yuejiang,
            '占时': shichen,
            '日柱': f"{ri_gan}{ri_zhi}",
            '天地盘': tiandi_pan,
            '四课': si_ke,
            '天将': tian_jiang,
            '三传': san_chuan,
            '禄马贵': lu_ma_gui,
            '课格': ke_ge
        }


# 测试
def test_da_liu_ren_pro():
    engine = DaLiuRenEnginePro()
    
    print("=== 大六壬增强版测试 ===")
    result = engine.full_pai_pan(1, '午', '甲', '子')
    
    print(f"\n月将：{result['月将']}")
    print(f"占时：{result['占时']}")
    print(f"日柱：{result['日柱']}")
    
    print(f"\n【天地盘】")
    print(f"地盘：{' '.join(result['天地盘']['地盘'])}")
    print(f"天盘：{' '.join(result['天地盘']['天盘'])}")
    
    print(f"\n【四课】")
    for ke in result['四课']:
        print(f"  {ke['name']}: {ke['top']} {ke['bottom']}")
    
    print(f"\n【天将】")
    for tj in result['天将'][:6]:  # 显示前 6 个
        print(f"  {tj['天将']:4} - {tj['地支']}")
    
    print(f"\n【三传】")
    print(f"  课体：{result['三传']['课体']}")
    print(f"  起法：{result['三传']['起法']}")
    print(f"  三传：{result['三传']['三传']}")
    
    print(f"\n【课格】")
    print(f"  名称：{result['课格']['课格名称']}")
    print(f"  说明：{result['课格']['课格说明']}")
    print(f"  吉凶：{result['课格']['吉凶']}")
    
    print(f"\n【禄马贵】")
    print(f"  禄：{result['禄马贵']['禄']}")
    print(f"  马：{result['禄马贵']['驿马']}")
    print(f"  贵：{result['禄马贵']['贵人']}")


if __name__ == '__main__':
    test_da_liu_ren_pro()
