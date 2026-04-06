"""
大六壬排盘引擎
实现天地盘、四课、三传等核心功能
"""

from data.斗首择日规则 import (
    TIANGAN, DIZHI, JIGONG, YUEJIANG, JIEQI_YUEJIANG,
    DIZHI_CHONG, LU, YIMA, GUIREN, TIANJIANG
)


class DaLiuRenEngine:
    """大六壬排盘引擎"""
    
    def __init__(self):
        self.tiangan = TIANGAN
        self.dizhi = DIZHI
    
    def get_yuejiang(self, lunar_month: int) -> str:
        """
        根据农历月份获取月将
        :param lunar_month: 农历月份（1-12）
        :return: 月将地支
        """
        return JIEQI_YUEJIANG.get(lunar_month, '子')
    
    def get_jieqi_yuejiang(self, jieqi: str) -> str:
        """
        根据节气获取月将
        :param jieqi: 节气名称
        :return: 月将地支
        """
        return YUEJIANG.get(jieqi, '子')
    
    def arrange_tiandi_pan(self, yuejiang: str, shichen: str) -> dict:
        """
        排天地盘
        月将加时，顺布天盘
        :param yuejiang: 月将
        :param shichen: 占时（时辰）
        :return: 天地盘字典
        """
        # 地盘固定
        di_pan = DIZHI.copy()
        
        # 天盘：月将加在时支上，顺布
        shi_index = DIZHI.index(shichen)
        yuejiang_index = DIZHI.index(yuejiang)
        
        # 计算偏移量
        offset = shi_index - yuejiang_index
        
        # 排天盘
        tian_pan = []
        for i in range(12):
            tian_index = (i + offset) % 12
            tian_pan.append(DIZHI[tian_index])
        
        # 组合天地盘
        result = {
            '地盘': di_pan,
            '天盘': tian_pan,
            '月将': yuejiang,
            '占时': shichen
        }
        
        # 添加对应关系
        result['天地对应'] = {}
        for i in range(12):
            result['天地对应'][di_pan[i]] = tian_pan[i]
        
        return result
    
    def get_jigong(self, tiangan: str) -> str:
        """
        获取十干寄宫
        :param tiangan: 天干
        :return: 寄宫地支
        """
        return JIGONG.get(tiangan, '')
    
    def arrange_si_ke(self, ri_gan: str, ri_zhi: str, tian_pan: dict) -> list:
        """
        起四课
        从日干起二课，从日支起二课
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param tian_pan: 天盘信息（包含天地对应）
        :return: 四课列表
        """
        si_ke = []
        
        # 第一课：日干寄宫的天盘
        ji_gong = self.get_jigong(ri_gan)
        if ji_gong:
            ke1_top = tian_pan['天地对应'].get(ji_gong, '')
            si_ke.append({'top': ke1_top, 'bottom': ri_gan, 'name': '第一课'})
            
            # 第二课：第一课上神的天盘
            if ke1_top in DIZHI:
                ke2_top = tian_pan['天地对应'].get(ke1_top, '')
                si_ke.append({'top': ke2_top, 'bottom': ke1_top, 'name': '第二课'})
        
        # 第三课：日支的天盘
        if ri_zhi in DIZHI:
            ke3_top = tian_pan['天地对应'].get(ri_zhi, '')
            si_ke.append({'top': ke3_top, 'bottom': ri_zhi, 'name': '第三课'})
            
            # 第四课：第三课上神的天盘
            if ke3_top in DIZHI:
                ke4_top = tian_pan['天地对应'].get(ke3_top, '')
                si_ke.append({'top': ke4_top, 'bottom': ke3_top, 'name': '第四课'})
        
        return si_ke
    
    def check_ke(self, top: str, bottom: str) -> str:
        """
        检查课体上下克关系
        :param top: 上神
        :param bottom: 下神
        :return: '克上', '克下', '无克'
        """
        # 五行属性（简化版，实际需要更完整的五行配置）
        wuxing_map = {
            '寅': '木', '卯': '木',
            '巳': '火', '午': '火',
            '申': '金', '酉': '金',
            '亥': '水', '子': '水',
            '辰': '土', '戌': '土', '丑': '土', '未': '土'
        }
        
        # 五行相克：木克土，土克水，水克火，火克金，金克木
        ke_relations = {
            '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
        }
        
        top_wx = wuxing_map.get(top, '')
        bottom_wx = wuxing_map.get(bottom, '')
        
        if not top_wx or not bottom_wx:
            return '无克'
        
        if ke_relations.get(top_wx) == bottom_wx:
            return '克下'  # 上克下
        elif ke_relations.get(bottom_wx) == top_wx:
            return '克上'  # 下克上
        
        return '无克'
    
    def fa_san_chuan(self, si_ke: list, ri_gan: str) -> dict:
        """
        发三传（九宗门）
        1. 贼克法 2. 比用法 3. 涉害法 4. 遥克法 5. 昴星法
        6. 别责法 7. 八专法 8. 伏吟法 9. 反吟法
        :param si_ke: 四课
        :param ri_gan: 日干
        :return: 三传信息
        """
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
                ke_list.append({
                    '课': ke,
                    '类型': ke_type
                })
        
        if not ke_list:
            # 无克，用遥克法或昴星法
            return self._yao_ke_or_ao_xing(si_ke, ri_gan, result)
        
        # 有克，优先用贼克法
        if len(ke_list) == 1:
            # 只有一课有克
            ke_info = ke_list[0]
            result['课体'] = '重审课' if ke_info['类型'] == '克上' else '元首课'
            result['三传'] = self._get_chuan_from_ke(ke_info['课'], si_ke)
            result['起法'] = '贼克法'
        else:
            # 多课有克，用比用法或涉害法
            return self._bi_yong_or_she_hai(ke_list, ri_gan, si_ke, result)
        
        return result
    
    def _yao_ke_or_ao_xing(self, si_ke: list, ri_gan: str, result: dict) -> dict:
        """遥克法或昴星法"""
        # 检查遥克（课上之神遥克日干，或日干遥克课上之神）
        # 简化实现，实际需完整逻辑
        
        # 无遥克用昴星法
        result['课体'] = '昴星课'
        result['起法'] = '昴星法'
        
        # 阳日取地盘酉上之神，阴日取天盘酉下之神
        ri_gan_yin_yang = '阳' if TIANGAN.index(ri_gan) % 2 == 0 else '阴'
        
        if ri_gan_yin_yang == '阳':
            # 阳日，简化处理
            result['三传'] = [si_ke[0]['top']] if si_ke else []
        else:
            result['三传'] = [si_ke[-1]['top']] if si_ke else []
        
        return result
    
    def _bi_yong_or_she_hai(self, ke_list: list, ri_gan: str, si_ke: list, result: dict) -> dict:
        """比用法或涉害法"""
        # 简化实现
        result['课体'] = '比用课'
        result['起法'] = '比用法'
        result['三传'] = [ke_list[0]['课']['top']]
        return result
    
    def _get_chuan_from_ke(self, ke: dict, si_ke: list) -> list:
        """从课获取三传"""
        # 初传
        chu_chuan = ke['top']
        
        # 中传、末传简化处理
        zhong_chuan = ''
        mo_chuan = ''
        
        # 查找中传（初传的天盘）
        for s_ke in si_ke:
            if s_ke['bottom'] == chu_chuan:
                zhong_chuan = s_ke['top']
                break
        
        # 查找末传（中传的天盘）
        if zhong_chuan:
            for s_ke in si_ke:
                if s_ke['bottom'] == zhong_chuan:
                    mo_chuan = s_ke['top']
                    break
        
        return [chu_chuan, zhong_chuan, mo_chuan]
    
    def get_lu_ma_gui(self, ri_gan: str, ri_zhi: str) -> dict:
        """
        获取禄马贵
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 禄马贵信息
        """
        lu = LU.get(ri_gan, '')
        
        # 驿马（以日支查）
        yima = ''
        for key, value in YIMA.items():
            if ri_zhi in key:
                yima = value
                break
        
        # 贵人
        guiren_list = GUIREN.get(ri_gan, [])
        
        return {
            '禄': lu,
            '驿马': yima,
            '贵人': guiren_list
        }
    
    def full_pai_pan(self, lunar_month: int, shichen: str, 
                     ri_gan: str, ri_zhi: str) -> dict:
        """
        完整排盘
        :param lunar_month: 农历月份
        :param shichen: 占时
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :return: 完整排盘结果
        """
        # 1. 起月将
        yuejiang = self.get_yuejiang(lunar_month)
        
        # 2. 排天地盘
        tiandi_pan = self.arrange_tiandi_pan(yuejiang, shichen)
        
        # 3. 起四课
        si_ke = self.arrange_si_ke(ri_gan, ri_zhi, tiandi_pan)
        
        # 4. 发三传
        san_chuan = self.fa_san_chuan(si_ke, ri_gan)
        
        # 5. 起禄马贵
        lu_ma_gui = self.get_lu_ma_gui(ri_gan, ri_zhi)
        
        return {
            '月将': yuejiang,
            '占时': shichen,
            '日柱': f"{ri_gan}{ri_zhi}",
            '天地盘': tiandi_pan,
            '四课': si_ke,
            '三传': san_chuan,
            '禄马贵': lu_ma_gui
        }


# 测试函数
def test_da_liu_ren():
    """测试大六壬引擎"""
    engine = DaLiuRenEngine()
    
    print("=== 月将测试 ===")
    for month in range(1, 13):
        print(f"农历{month}月：{engine.get_yuejiang(month)}将")
    
    print("\n=== 天地盘测试 ===")
    result = engine.arrange_tiandi_pan('亥', '寅')
    print(f"亥将加寅时：{result}")
    
    print("\n=== 四课测试 ===")
    # 雨水后，甲子日，寅时
    tiandi_pan = engine.arrange_tiandi_pan('亥', '寅')
    si_ke = engine.arrange_si_ke('甲', '子', tiandi_pan)
    for ke in si_ke:
        print(f"{ke['name']}: {ke['top']} {ke['bottom']}")
    
    print("\n=== 完整排盘测试 ===")
    result = engine.full_pai_pan(1, '寅', '甲', '子')
    print(f"排盘结果：{result}")


if __name__ == '__main__':
    test_da_liu_ren()
