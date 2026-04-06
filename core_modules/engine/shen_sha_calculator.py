#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬完整神煞计算模块（增强版）
包含：日辰神煞、月建神煞、年支神煞、季节神煞、旬煞等
实现完整的月煞、日煞系统
"""

from typing import Dict, List, Optional, Tuple


class ShenShaCalculator:
    """神煞计算器（增强版）"""
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 天干顺序
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 天干五行
    TIAN_GAN_WU_XING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
    }
    
    # 地支六合
    LIU_HE = {
        '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
        '辰': '酉', '巳': '申', '午': '未', '未': '午',
        '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
    }
    
    # 地支六冲
    LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    
    # 地支三合
    SAN_HE = {
        '申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金'
    }
    
    # 驿马 (按日支三合)
    YI_MA = {
        '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥'
    }
    
    # 桃花 (按日支三合)
    TAO_HUA = {
        '申子辰': '酉', '亥卯未': '子', '寅午戌': '卯', '巳酉丑': '午'
    }
    
    # 劫煞 (按日支三合)
    JIE_SHA = {
        '申子辰': '巳', '亥卯未': '申', '寅午戌': '亥', '巳酉丑': '寅'
    }
    
    # 灾煞 (按日支三合)
    ZAI_SHA = {
        '申子辰': '午', '亥卯未': '酉', '寅午戌': '子', '巳酉丑': '卯'
    }
    
    # 月煞（按月建）- 完整 12 个月
    YUE_SHA = {
        1: {'月建': '寅', '月破': '申', '月厌': '戌', '天德': '丁', '月德': '丁', '天喜': '戌', '天医': '戌'},
        2: {'月建': '卯', '月破': '酉', '月厌': '酉', '天德': '坤', '月德': '申', '天喜': '亥', '天医': '亥'},
        3: {'月建': '辰', '月破': '戌', '月厌': '申', '天德': '壬', '月德': '壬', '天喜': '子', '天医': '丑'},
        4: {'月建': '巳', '月破': '亥', '月厌': '未', '天德': '辛', '月德': '辛', '天喜': '丑', '天医': '寅'},
        5: {'月建': '午', '月破': '子', '月厌': '午', '天德': '乾', '月德': '亥', '天喜': '寅', '天医': '卯'},
        6: {'月建': '未', '月破': '丑', '月厌': '巳', '天德': '甲', '月德': '甲', '天喜': '卯', '天医': '辰'},
        7: {'月建': '申', '月破': '寅', '月厌': '辰', '天德': '癸', '月德': '癸', '天喜': '辰', '天医': '巳'},
        8: {'月建': '酉', '月破': '卯', '月厌': '卯', '天德': '艮', '月德': '寅', '天喜': '巳', '天医': '午'},
        9: {'月建': '戌', '月破': '辰', '月厌': '寅', '天德': '丙', '月德': '丙', '天喜': '午', '天医': '未'},
        10: {'月建': '亥', '月破': '巳', '月厌': '丑', '天德': '乙', '月德': '乙', '天喜': '未', '天医': '申'},
        11: {'月建': '子', '月破': '午', '月厌': '子', '天德': '巽', '月德': '巳', '天喜': '申', '天医': '酉'},
        12: {'月建': '丑', '月破': '未', '月厌': '亥', '天德': '庚', '月德': '庚', '天喜': '酉', '天医': '戌'}
    }
    
    # 日煞（按日支）- 完整 12 地支
    RI_SHA = {
        '子': {'日禄': '亥', '日德': '巳', '日马': '寅', '日贵': '卯', '日破': '午', '日害': '未'},
        '丑': {'日禄': '子', '日德': '午', '日马': '亥', '日贵': '子', '日破': '未', '日害': '午'},
        '寅': {'日禄': '寅', '日德': '申', '日马': '申', '日贵': '丑', '日破': '申', '日害': '巳'},
        '卯': {'日禄': '卯', '日德': '巳', '日马': '巳', '日贵': '子', '日破': '酉', '日害': '辰'},
        '辰': {'日禄': '巳', '日德': '亥', '日马': '寅', '日贵': '亥', '日破': '戌', '日害': '卯'},
        '巳': {'日禄': '午', '日德': '寅', '日马': '亥', '日贵': '酉', '日破': '亥', '日害': '寅'},
        '午': {'日禄': '巳', '日德': '申', '日马': '申', '日贵': '亥', '日破': '子', '日害': '丑'},
        '未': {'日禄': '午', '日德': '寅', '日马': '巳', '日贵': '子', '日破': '丑', '日害': '子'},
        '申': {'日禄': '申', '日德': '巳', '日马': '寅', '日贵': '丑', '日破': '寅', '日害': '亥'},
        '酉': {'日禄': '酉', '日德': '巳', '日马': '亥', '日贵': '午', '日破': '卯', '日害': '戌'},
        '戌': {'日禄': '亥', '日德': '申', '日马': '申', '日贵': '卯', '日破': '辰', '日害': '酉'},
        '亥': {'日禄': '子', '日德': '巳', '日马': '巳', '日贵': '卯', '日破': '巳', '日害': '申'}
    }
    
    # 十干禄（按日干）
    SHI_GAN_LU = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
        '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    # 十干贵人（按日干）
    SHI_GAN_GUI_REN = {
        '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
        '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
        '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
        '癸': ['巳', '卯']
    }
    
    # 十干羊刃（按日干）
    SHI_GAN_YANG_REN = {
        '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午',
        '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'
    }
    
    # 孤辰寡宿 (按年支三合局)
    GU_GUA = {
        '亥子丑': {'孤': '寅', '寡': '戌'},
        '寅卯辰': {'孤': '巳', '寡': '丑'},
        '巳午未': {'孤': '申', '寡': '辰'},
        '申酉戌': {'孤': '亥', '寡': '未'}
    }
    
    # 丧门吊客 (按年支)
    SANG_DIAO = {
        '子': {'丧门': '寅', '吊客': '戌'},
        '丑': {'丧门': '卯', '吊客': '亥'},
        '寅': {'丧门': '辰', '吊客': '子'},
        '卯': {'丧门': '巳', '吊客': '丑'},
        '辰': {'丧门': '午', '吊客': '寅'},
        '巳': {'丧门': '未', '吊客': '卯'},
        '午': {'丧门': '申', '吊客': '辰'},
        '未': {'丧门': '酉', '吊客': '巳'},
        '申': {'丧门': '戌', '吊客': '午'},
        '酉': {'丧门': '亥', '吊客': '未'},
        '戌': {'丧门': '子', '吊客': '申'},
        '亥': {'丧门': '丑', '吊客': '酉'}
    }
    
    def __init__(self):
        pass
    
    def get_yi_ma(self, ri_zhi: str) -> str:
        """获取驿马"""
        for san_he, ma in self.YI_MA.items():
            if ri_zhi in san_he:
                return ma
        return ''
    
    def get_tao_hua(self, ri_zhi: str) -> str:
        """获取桃花"""
        for san_he, tao in self.TAO_HUA.items():
            if ri_zhi in san_he:
                return tao
        return ''
    
    def get_jie_sha(self, ri_zhi: str) -> str:
        """获取劫煞"""
        for san_he, jie in self.JIE_SHA.items():
            if ri_zhi in san_he:
                return jie
        return ''
    
    def get_zai_sha(self, ri_zhi: str) -> str:
        """获取灾煞"""
        for san_he, zai in self.ZAI_SHA.items():
            if ri_zhi in san_he:
                return zai
        return ''
    
    def get_ri_lu(self, ri_gan: str) -> str:
        """获取日禄"""
        return self.SHI_GAN_LU.get(ri_gan, '')
    
    def get_ri_de(self, ri_gan: str) -> str:
        """获取日德"""
        # 简化版
        de_map = {
            '甲': '寅', '乙': '申', '丙': '巳', '丁': '亥', '戊': '巳',
            '己': '寅', '庚': '申', '辛': '巳', '壬': '亥', '癸': '巳'
        }
        return de_map.get(ri_gan, '')
    
    def get_gui_ren(self, ri_gan: str) -> List[str]:
        """获取天乙贵人"""
        return self.SHI_GAN_GUI_REN.get(ri_gan, [])
    
    def get_yang_ren(self, ri_gan: str) -> str:
        """获取羊刃"""
        return self.SHI_GAN_YANG_REN.get(ri_gan, '')
    
    def get_yue_jian(self, lunar_month: int) -> str:
        """获取月建"""
        return self.YUE_SHA.get(lunar_month, {}).get('月建', '')
    
    def get_yue_po(self, lunar_month: int) -> str:
        """获取月破（月建冲）"""
        yue_jian = self.get_yue_jian(lunar_month)
        return self.LIU_CHONG.get(yue_jian, '')
    
    def get_yue_yan(self, lunar_month: int) -> str:
        """获取月厌"""
        return self.YUE_SHA.get(lunar_month, {}).get('月厌', '')
    
    def get_tian_de(self, lunar_month: int) -> str:
        """获取天德"""
        return self.YUE_SHA.get(lunar_month, {}).get('天德', '')
    
    def get_yue_de(self, lunar_month: int) -> str:
        """获取月德"""
        return self.YUE_SHA.get(lunar_month, {}).get('月德', '')
    
    def get_tian_xi(self, lunar_month: int) -> str:
        """获取天喜"""
        return self.YUE_SHA.get(lunar_month, {}).get('天喜', '')
    
    def get_tian_yi(self, lunar_month: int) -> str:
        """获取天医"""
        return self.YUE_SHA.get(lunar_month, {}).get('天医', '')
    
    def get_ri_sha(self, ri_zhi: str) -> Dict[str, str]:
        """获取日煞（完整）"""
        return self.RI_SHA.get(ri_zhi, {})
    
    def get_yue_sha(self, lunar_month: int) -> Dict[str, str]:
        """获取月煞（完整）"""
        return self.YUE_SHA.get(lunar_month, {})
    
    def get_gu_gua(self, nian_zhi: str) -> Dict[str, str]:
        """获取孤辰寡宿"""
        for san_he, gu_gua in self.GU_GUA.items():
            if nian_zhi in san_he:
                return gu_gua
        return {'孤': '', '寡': ''}
    
    def get_sang_diao(self, nian_zhi: str) -> Dict[str, str]:
        """获取丧门吊客"""
        return self.SANG_DIAO.get(nian_zhi, {'丧门': '', '吊客': ''})
    
    def get_xun_kong(self, ri_gan_zhi: str) -> List[str]:
        """
        获取旬空
        甲子旬戌亥空，甲戌旬申酉空，甲申旬午未空
        甲午旬辰巳空，甲辰旬寅卯空，甲寅旬子丑空
        """
        # 简化处理：根据日支判断
        zi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        ri_zhi = ri_gan_zhi[1] if len(ri_gan_zhi) > 1 else ''
        
        if not ri_zhi:
            return ['戌', '亥']
        
        zhi_idx = zi_list.index(ri_zhi)
        
        # 甲子旬：子丑寅卯辰巳午未申酉
        if zhi_idx <= 9:
            return ['戌', '亥']
        # 甲戌旬：戌亥子丑寅卯辰巳午未
        elif zhi_idx >= 10 or zhi_idx <= 1:
            return ['申', '酉']
        
        return ['戌', '亥']
    
    def calculate_all_shen_sha(self, ri_gan: str, ri_zhi: str, 
                               lunar_month: int = 1, 
                               nian_zhi: str = '子',
                               ri_gan_zhi: str = '') -> Dict[str, str]:
        """
        计算所有神煞（完整版）
        
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param lunar_month: 农历月份
        :param nian_zhi: 年支
        :param ri_gan_zhi: 日干支（用于旬空）
        :return: 神煞字典
        """
        shen_sha = {}
        
        # ===== 日干神煞 =====
        shen_sha['日禄'] = self.get_ri_lu(ri_gan)
        shen_sha['日德'] = self.get_ri_de(ri_gan)
        shen_sha['羊刃'] = self.get_yang_ren(ri_gan)
        
        # 天乙贵人
        gui_ren_list = self.get_gui_ren(ri_gan)
        if gui_ren_list:
            shen_sha['天乙贵人'] = gui_ren_list[0]
            if len(gui_ren_list) > 1:
                shen_sha['天乙贵人 2'] = gui_ren_list[1]
        
        # ===== 日支神煞 =====
        shen_sha['驿马'] = self.get_yi_ma(ri_zhi)
        shen_sha['桃花'] = self.get_tao_hua(ri_zhi)
        shen_sha['劫煞'] = self.get_jie_sha(ri_zhi)
        shen_sha['灾煞'] = self.get_zai_sha(ri_zhi)
        
        # 日煞详情
        ri_sha_detail = self.get_ri_sha(ri_zhi)
        if ri_sha_detail:
            for key, value in ri_sha_detail.items():
                if value and key not in shen_sha:
                    shen_sha[key] = value
        
        # ===== 月建神煞 =====
        shen_sha['月建'] = self.get_yue_jian(lunar_month)
        shen_sha['月破'] = self.get_yue_po(lunar_month)
        shen_sha['月厌'] = self.get_yue_yan(lunar_month)
        shen_sha['天德'] = self.get_tian_de(lunar_month)
        shen_sha['月德'] = self.get_yue_de(lunar_month)
        shen_sha['天喜'] = self.get_tian_xi(lunar_month)
        shen_sha['天医'] = self.get_tian_yi(lunar_month)
        
        # 月煞详情
        yue_sha_detail = self.get_yue_sha(lunar_month)
        for key, value in yue_sha_detail.items():
            if value and key not in shen_sha:
                shen_sha[f'月{key}'] = value
        
        # ===== 年支神煞 =====
        gu_gua = self.get_gu_gua(nian_zhi)
        shen_sha['孤辰'] = gu_gua.get('孤', '')
        shen_sha['寡宿'] = gu_gua.get('寡', '')
        
        sang_diao = self.get_sang_diao(nian_zhi)
        shen_sha['丧门'] = sang_diao.get('丧门', '')
        shen_sha['吊客'] = sang_diao.get('吊客', '')
        
        # ===== 旬空 =====
        if ri_gan_zhi:
            xun_kong = self.get_xun_kong(ri_gan_zhi)
            shen_sha['旬空'] = ','.join(xun_kong)
        
        return shen_sha


def main():
    """测试神煞计算"""
    calculator = ShenShaCalculator()
    
    print("=" * 80)
    print("神煞计算测试")
    print("=" * 80)
    
    # 测试甲子日
    ri_gan = '甲'
    ri_zhi = '子'
    ri_gan_zhi = '甲子'
    lunar_month = 1
    nian_zhi = '子'
    
    print(f"\n测试：{ri_gan_zhi}日 农历{lunar_month}月 年支{nian_zhi}")
    
    shen_sha = calculator.calculate_all_shen_sha(
        ri_gan, ri_zhi, lunar_month, nian_zhi, ri_gan_zhi
    )
    
    print("\n神煞列表:")
    for name, value in sorted(shen_sha.items()):
        if value:
            print(f"  {name:12s}: {value}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
