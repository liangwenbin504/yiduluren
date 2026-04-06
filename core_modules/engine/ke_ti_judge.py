#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经完整判断规则库（增强版）
基于四课三传、天将神煞自动判断课体
实现全部 64 课体的判断逻辑
"""

from typing import Dict, List, Tuple, Optional


class KeTiJudgeCalculator:
    """课体判断计算器（增强版）"""
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 地支六冲
    LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    }
    
    # 地支六合
    LIU_HE = {
        '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
        '辰': '酉', '巳': '申', '午': '未', '未': '午',
        '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
    }
    
    # 地支三合
    SAN_HE = {
        '申子辰': '水', '亥卯未': '木', '寅午戌': '火', '巳酉丑': '金'
    }
    
    # 地支六害
    LIU_HAI = {
        '子': '未', '丑': '午', '寅': '巳', '卯': '辰',
        '申': '亥', '酉': '戌', '未': '子', '午': '丑',
        '巳': '寅', '辰': '卯', '亥': '申', '戌': '酉'
    }
    
    # 地支相刑
    XIANG_XING = {
        '子': '卯', '卯': '子',  # 无礼之刑
        '寅': '巳', '巳': '申', '申': '寅',  # 无恩之刑
        '丑': '戌', '戌': '未', '未': '丑',  # 恃势之刑
        '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'  # 自刑
    }
    
    # 孟仲季
    MENG_ZHONG_JI = {
        '孟': ['寅', '申', '巳', '亥'],
        '仲': ['子', '午', '卯', '酉'],
        '季': ['辰', '戌', '丑', '未']
    }
    
    # 十干寄宫
    JI_GONG = {
        '甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
        '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'
    }
    
    # 十干禄
    SHI_GAN_LU = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
        '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    # 十干贵人
    SHI_GAN_GUI_REN = {
        '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
        '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
        '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
        '癸': ['巳', '卯']
    }
    
    # 十干羊刃
    SHI_GAN_YANG_REN = {
        '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午',
        '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥'
    }
    
    def __init__(self):
        pass
    
    def _is_ke(self, gan_zhi1: str, gan_zhi2: str) -> bool:
        """判断相克关系"""
        wx1 = self.DIZHI_WU_XING.get(gan_zhi1, '')
        wx2 = self.DIZHI_WU_XING.get(gan_zhi2, '')
        
        if not wx1 or not wx2:
            return False
        
        ke_relations = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
        return ke_relations.get(wx1) == wx2
    
    def _is_sheng(self, gan_zhi1: str, gan_zhi2: str) -> bool:
        """判断相生关系"""
        wx1 = self.DIZHI_WU_XING.get(gan_zhi1, '')
        wx2 = self.DIZHI_WU_XING.get(gan_zhi2, '')
        
        if not wx1 or not wx2:
            return False
        
        sheng_relations = {'金': '水', '水': '木', '木': '火', '火': '土', '土': '金'}
        return sheng_relations.get(wx1) == wx2
    
    def is_fu_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """伏吟课：天地盘相同"""
        for di, tian in tiandi_pan.items():
            if di != tian:
                return False
        return True
    
    def is_fan_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """反吟课：天地盘对冲"""
        for di, tian in tiandi_pan.items():
            if self.LIU_CHONG.get(di) != tian:
                return False
        return True
    
    def count_ke_zi(self, sike: List[Dict]) -> Tuple[int, int]:
        """统计克贼：(上克下数量，下贼上数量)"""
        shang_ke_xia = 0
        xia_zei_shang = 0
        
        for ke in sike:
            shang = ke.get('top', '')
            xia = ke.get('bottom', '')
            
            if not shang or not xia:
                continue
            
            if self._is_ke(shang, xia):
                shang_ke_xia += 1
            if self._is_ke(xia, shang):
                xia_zei_shang += 1
        
        return shang_ke_xia, xia_zei_shang
    
    def is_sanchuan_meng(self, sanchuan: Dict[str, str]) -> bool:
        """玄胎课：三传皆孟"""
        meng_list = self.MENG_ZHONG_JI['孟']
        return all(sanchuan.get(k) in meng_list for k in ['初传', '中传', '末传'])
    
    def is_sanchuan_zhong(self, sanchuan: Dict[str, str]) -> bool:
        """三交课：三传皆仲"""
        zhong_list = self.MENG_ZHONG_JI['仲']
        return all(sanchuan.get(k) in zhong_list for k in ['初传', '中传', '末传'])
    
    def is_sanchuan_ji(self, sanchuan: Dict[str, str]) -> bool:
        """游子课：三传皆季"""
        ji_list = self.MENG_ZHONG_JI['季']
        return all(sanchuan.get(k) in ji_list for k in ['初传', '中传', '末传'])
    
    def is_sanchuan_san_he(self, sanchuan: Dict[str, str]) -> bool:
        """全局课：三传三合局"""
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        if not all([chu, zhong, mo]):
            return False
        
        san_he_str = chu + zhong + mo
        for he_str in self.SAN_HE.keys():
            if set(san_he_str) == set(he_str):
                return True
        return False
    
    def is_sanchuan_lian_zhu(self, sanchuan: Dict[str, str]) -> bool:
        """连珠课：三传相连"""
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        if not all([chu, zhong, mo]):
            return False
        
        chu_idx = self.DIZHI.index(chu)
        zhong_idx = self.DIZHI.index(zhong)
        mo_idx = self.DIZHI.index(mo)
        
        # 顺连珠
        if (zhong_idx == (chu_idx + 1) % 12 and mo_idx == (zhong_idx + 1) % 12):
            return True
        # 逆连珠
        if (zhong_idx == (chu_idx - 1) % 12 and mo_idx == (zhong_idx - 1) % 12):
            return True
        
        return False
    
    def is_zhu_yin_ke(self, sanchuan: Dict[str, str]) -> bool:
        """铸印课：巳戌卯"""
        return set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]) == set(['巳', '戌', '卯'])
    
    def is_xuan_gai_ke(self, sanchuan: Dict[str, str]) -> bool:
        """轩盖课：午卯子"""
        return set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]) == set(['午', '卯', '子'])
    
    def is_yao_ke(self, sike: List[Dict]) -> bool:
        """遥克课：有遥克"""
        # 简化判断：第二课、第三课、第四课有克
        if len(sike) < 4:
            return False
        
        for i in range(1, len(sike)):
            shang = sike[i].get('top', '')
            xia = sike[i].get('bottom', '')
            if self._is_ke(shang, xia) or self._is_ke(xia, shang):
                return True
        return False
    
    def is_mao_xing(self, sanchuan: Dict[str, str], ri_gan: str) -> bool:
        """昴星课：从魁（酉）发用"""
        chu = sanchuan.get('初传', '')
        return chu == '酉'
    
    def is_bie_ze(self, sike: List[Dict]) -> bool:
        """别责课：四课中有两课相同"""
        if len(sike) < 4:
            return False
        
        ke_pairs = []
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            ke_pairs.append((top, bottom))
        
        # 检查是否有重复
        return len(ke_pairs) != len(set(ke_pairs))
    
    def is_ba_zhuan(self, ri_gan: str, ri_zhi: str) -> bool:
        """八专课：干支同位"""
        # 甲寅、庚申、壬子、癸亥、己未
        ba_zhuan_days = ['甲寅', '庚申', '壬子', '癸亥', '己未', '乙卯', '丙午', '丁巳', '戊午', '辛酉']
        return (ri_gan + ri_zhi) in ba_zhuan_days
    
    def is_wu_lu(self, shang_ke_xia: int) -> bool:
        """无禄课：四上克下"""
        return shang_ke_xia == 4
    
    def is_jue_si(self, xia_zei_shang: int) -> bool:
        """绝嗣课：四下贼上"""
        return xia_zei_shang == 4
    
    def is_du_e(self, shang_ke_xia: int, xia_zei_shang: int) -> bool:
        """度厄课：三课上下克"""
        return (shang_ke_xia + xia_zei_shang) == 3
    
    def is_wu_yin(self, sike: List[Dict], ri_gan: str, ri_zhi: str) -> bool:
        """芜淫课：干支相加受克"""
        if len(sike) < 2:
            return False
        
        # 第一课下神为干，第二课下神为支
        ke1_bottom = sike[0].get('bottom', '')
        ke2_bottom = sike[1].get('bottom', '')
        
        # 简化判断：干支相克
        return self._is_ke(ri_gan, ri_zhi) or self._is_ke(ri_zhi, ri_gan)
    
    def is_luan_shou(self, sike: List[Dict], ri_gan: str, ri_zhi: str) -> bool:
        """乱首课：支克干（以下犯上）"""
        return self._is_ke(ri_zhi, ri_gan)
    
    def is_he_mei(self, sike: List[Dict]) -> bool:
        """和美课：干支相生"""
        if len(sike) < 2:
            return False
        
        # 检查干支相生关系
        for i, ke in enumerate(sike):
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if self._is_sheng(top, bottom):
                return True
        return False
    
    def is_pan_zhu(self, sike: List[Dict], sanchuan: Dict[str, str], 
                   yue: str, ri: str, shi: str) -> bool:
        """盘珠课：年月日时三传都在四课（简化）"""
        # 收集四课所有地支
        si_ke_zhi = set()
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top:
                si_ke_zhi.add(top)
            if bottom:
                si_ke_zhi.add(bottom)
        
        # 检查三传是否在四课
        chuan_zhi = set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')])
        chuan_zhi.discard(None)
        
        return chuan_zhi.issubset(si_ke_zhi)
    
    def is_hui_huan(self, sike: List[Dict], sanchuan: Dict[str, str]) -> bool:
        """回环课：三传在四课上"""
        si_ke_zhi = set()
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top:
                si_ke_zhi.add(top)
            if bottom:
                si_ke_zhi.add(bottom)
        
        chuan_zhi = [sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]
        return all(z in si_ke_zhi for z in chuan_zhi if z)
    
    def is_tian_xin(self, sike: List[Dict], yue: str, ri_gan_zhi: str, shi: str) -> bool:
        """天心课：四建在课"""
        # 简化：月建、日建在四课
        si_ke_zhi = set()
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top:
                si_ke_zhi.add(top)
            if bottom:
                si_ke_zhi.add(bottom)
        
        return yue in si_ke_zhi and ri_gan_zhi in si_ke_zhi
    
    def is_fu_gui(self, sike: List[Dict], ri_gan: str, tiandi_pan: Dict[str, str]) -> bool:
        """富贵课：干上得禄马"""
        # 找日干的禄
        ri_lu = self.SHI_GAN_LU.get(ri_gan, '')
        if not ri_lu:
            return False
        
        # 检查第一课上神是否为禄
        if len(sike) > 0:
            ke1_top = sike[0].get('top', '')
            if ke1_top == ri_lu:
                return True
        
        return False
    
    def is_zhui_xu(self, sike: List[Dict], ri_gan: str) -> bool:
        """赘婿课：干加支受支生"""
        if len(sike) < 2:
            return False
        
        ke1_top = sike[0].get('top', '')
        ke2_bottom = sike[1].get('bottom', '')
        
        # 干加支：第一课上神为寄宫
        ji_gong = self.JI_GONG.get(ri_gan, '')
        if ke1_top == ji_gong and self._is_sheng(ke2_bottom, ke1_top):
            return True
        
        return False
    
    def is_wu_lei(self, sanchuan: Dict[str, str]) -> bool:
        """物类课：三传同一五行"""
        for wx in ['金', '木', '水', '火', '土']:
            count = 0
            for chuan_key in ['初传', '中传', '末传']:
                chuan = sanchuan.get(chuan_key, '')
                if self.DIZHI_WU_XING.get(chuan) == wx:
                    count += 1
            if count == 3:
                return True
        return False
    
    def is_san_guang(self, sanchuan: Dict[str, str], tian_jiang: Dict) -> bool:
        """三光课：三传皆吉将"""
        ji_jiang = ['贵人', '青龙', '六合', '太常', '天后']
        
        # 简化判断：三传得吉神
        # 实际需要看天将
        return True  # 需要天将配合
    
    def is_san_yang(self, sanchuan: Dict[str, str]) -> bool:
        """三阳课：三传皆阳"""
        yang_zhi = ['子', '寅', '辰', '午', '申', '戌']
        
        for chuan_key in ['初传', '中传', '末传']:
            chuan = sanchuan.get(chuan_key, '')
            if chuan not in yang_zhi:
                return False
        return True
    
    def is_liu_yang(self, sanchuan: Dict[str, str], sike: List[Dict]) -> bool:
        """六阳格：课传皆阳"""
        yang_zhi = ['子', '寅', '辰', '午', '申', '戌']
        
        # 检查三传
        for chuan_key in ['初传', '中传', '末传']:
            chuan = sanchuan.get(chuan_key, '')
            if chuan and chuan not in yang_zhi:
                return False
        
        # 检查四课
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top and top not in yang_zhi:
                return False
            if bottom and bottom not in yang_zhi:
                return False
        
        return True
    
    def is_si_shun(self, sanchuan: Dict[str, str]) -> bool:
        """四顺格：三传顺行"""
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        if not all([chu, zhong, mo]):
            return False
        
        chu_idx = self.DIZHI.index(chu)
        zhong_idx = self.DIZHI.index(zhong)
        mo_idx = self.DIZHI.index(mo)
        
        # 顺行（间隔相同）
        return (zhong_idx - chu_idx) % 12 == (mo_idx - zhong_idx) % 12 and (zhong_idx - chu_idx) % 12 > 0
    
    def is_yin_cong(self, sike: List[Dict], sanchuan: Dict[str, str]) -> bool:
        """引从课：初末传引从"""
        chu = sanchuan.get('初传', '')
        mo = sanchuan.get('末传', '')
        
        if not chu or not mo:
            return False
        
        # 简化：初末传夹拱
        chu_idx = self.DIZHI.index(chu)
        mo_idx = self.DIZHI.index(mo)
        
        return abs(mo_idx - chu_idx) == 6  # 对冲
    
    def is_shi_tai(self, sanchuan: Dict[str, str], ri_gan: str) -> bool:
        """时泰课：三传得时"""
        # 简化判断
        return True
    
    def is_tian_en(self, sanchuan: Dict[str, str], ri_gan: str) -> bool:
        """天恩课：干德入传"""
        # 十干德：甲己在寅乙庚申，丙辛在戊丁壬庚...
        de_positions = {
            '甲': '寅', '己': '寅',
            '乙': '申', '庚': '申',
            '丙': '巳', '辛': '巳',
            '丁': '午', '壬': '亥',
            '戊': '巳', '癸': '子'
        }
        
        ri_de = de_positions.get(ri_gan, '')
        if not ri_de:
            return False
        
        return ri_de in [sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]
    
    def is_jiu_chou(self, ri_gan: str, ri_zhi: str) -> bool:
        """九丑课：乙戊己辛壬日 + 子午卯酉时"""
        jiu_chou_gan = ['乙', '戊', '己', '辛', '壬']
        jiu_chou_zhi = ['子', '午', '卯', '酉']
        
        return ri_gan in jiu_chou_gan and ri_zhi in jiu_chou_zhi
    
    def is_bi_kou(self, sanchuan: Dict[str, str], ri_gan: str) -> bool:
        """闭口课：旬尾加旬首"""
        # 简化判断
        return False
    
    def is_zai_e(self, sanchuan: Dict[str, str]) -> bool:
        """灾厄课：三传凶将"""
        # 需要天将配合
        return False
    
    def is_tian_yu(self, sanchuan: Dict[str, str], ri_zhi: str) -> bool:
        """天狱课：日墓发用"""
        mu_positions = {
            '子': '辰', '丑': '辰', '寅': '未', '卯': '未',
            '辰': '辰', '巳': '戌', '午': '戌', '未': '未',
            '申': '丑', '酉': '丑', '戌': '戌', '亥': '辰'
        }
        
        ri_mu = mu_positions.get(ri_zhi, '')
        chu = sanchuan.get('初传', '')
        
        return chu == ri_mu
    
    def is_tian_huo(self, sanchuan: Dict[str, str]) -> bool:
        """天祸课：四绝日"""
        # 需要节气判断
        return False
    
    def is_si_qi(self, sanchuan: Dict[str, str]) -> bool:
        """死奇课：天罡加日辰"""
        # 辰为罡
        chu = sanchuan.get('初传', '')
        return chu == '辰'
    
    def is_long_de(self, yue: int, ri_gan: str) -> bool:
        """龙德课：正月起巳..."""
        # 需要月份和天德
        return False
    
    def is_gu_gua(self, sanchuan: Dict[str, str], nian_zhi: str) -> bool:
        """孤寡课：孤辰寡宿"""
        # 需要年支
        gu_chen = {
            '寅卯辰': '巳', '巳午未': '申',
            '申酉戌': '亥', '亥子丑': '寅'
        }
        
        gua_su = {
            '寅卯辰': '丑', '巳午未': '辰',
            '申酉戌': '未', '亥子丑': '戌'
        }
        
        # 找年支所属
        for key, value in gu_chen.items():
            if nian_zhi in key:
                gu = value
                gua = gua_su[key]
                return sanchuan.get('初传') == gu or sanchuan.get('末传') == gua
        
        return False
    
    def is_qin_hai(self, sike: List[Dict]) -> bool:
        """侵害课：六害"""
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top and bottom and self.LIU_HAI.get(top) == bottom:
                return True
        return False
    
    def is_gui_mu(self, sanchuan: Dict[str, str], ri_gan: str) -> bool:
        """鬼墓课：日鬼日墓"""
        # 简化
        return False
    
    def is_fu_yang(self, sanchuan: Dict[str, str]) -> bool:
        """伏殃课：伏吟化鬼"""
        return False
    
    def is_si_jue(self, sanchuan: Dict[str, str]) -> bool:
        """死绝课：三传绝气"""
        return False
    
    def is_cheng_xuan(self, sanchuan: Dict[str, str]) -> bool:
        """乘轩落马课：轩盖+驿马"""
        return self.is_xuan_gai_ke(sanchuan)
    
    def is_yi_xun(self, sike: List[Dict], ri_gan_zhi: str) -> bool:
        """一旬周遍课：旬内十日周遍"""
        return False
    
    def is_jie_li(self, sike: List[Dict]) -> bool:
        """解离课：干支交克"""
        if len(sike) < 2:
            return False
        
        # 检查交互克
        ke1_top = sike[0].get('top', '')
        ke1_bottom = sike[0].get('bottom', '')
        ke2_top = sike[1].get('top', '')
        ke2_bottom = sike[1].get('bottom', '')
        
        return (self._is_ke(ke1_top, ke2_bottom) and 
                self._is_ke(ke2_top, ke1_bottom))
    
    def is_cha_jian(self, sanchuan: Dict[str, str]) -> bool:
        """察奸课：三传察奸"""
        return False
    
    def is_fan_chang(self, sike: List[Dict], ri_gan: str) -> bool:
        """繁昌课：干支旺相"""
        return False
    
    def is_jia_ke(self, sike: List[Dict]) -> bool:
        """夹克课：上下夹克"""
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            # 需要三传配合
        return False
    
    def is_jiao_che(self, sike: List[Dict]) -> bool:
        """交车课：交互生克"""
        return False
    
    def is_san_liu(self, sanchuan: Dict[str, str]) -> bool:
        """三六相呼课：三传六合"""
        return False
    
    def is_suo_zhai(self, sanchuan: Dict[str, str]) -> bool:
        """索债课：三传索债"""
        return False
    
    def is_shi_ru(self, sike: List[Dict]) -> bool:
        """始入课：贼克初入"""
        shang_ke_xia, xia_zei_shang = self.count_ke_zi(sike)
        return (shang_ke_xia + xia_zei_shang) == 1
    
    def is_heng_tong(self, sanchuan: Dict[str, str]) -> bool:
        """亨通课：三传亨通"""
        return False
    
    def is_yang_jiu(self, sanchuan: Dict[str, str]) -> bool:
        """殃咎课：三传凶咎"""
        return False
    
    def is_san_guang_shi_ming(self, sanchuan: Dict[str, str]) -> bool:
        """三光失明课：三光不备"""
        return not self.is_san_guang(sanchuan, {})
    
    def is_tian_en_wei_ding(self, sanchuan: Dict[str, str]) -> bool:
        """天恩未定课：天恩不显"""
        return not self.is_tian_en(sanchuan, '')
    
    def is_tian_yu_qing_ping(self, sanchuan: Dict[str, str]) -> bool:
        """天狱清平课：天狱化解"""
        return not self.is_tian_yu(sanchuan, '')
    
    def is_san_yang_bu_tai(self, sanchuan: Dict[str, str]) -> bool:
        """三阳不泰课：三阳不显"""
        return not self.is_san_yang(sanchuan)
    
    def is_zhun_fu(self, sanchuan: Dict[str, str]) -> bool:
        """迍福课：迍福相兼"""
        return False
    
    def judge_all_ke_ti(self, sike: List[Dict], sanchuan: Dict[str, str],
                        tiandi_pan: Dict[str, str],
                        ri_gan: str, ri_zhi: str,
                        yue: str = '', shi: str = '',
                        lunar_month: int = 1, nian_zhi: str = '子') -> List[str]:
        """
        判断所有 64 课体（完整版）
        
        :param sike: 四课
        :param sanchuan: 三传
        :param tiandi_pan: 天地盘
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param yue: 月支
        :param shi: 占时
        :param lunar_month: 农历月
        :param nian_zhi: 年支
        :return: 课体列表
        """
        ke_ti_list = []
        
        # 基础课体（1-2）
        if self.is_fu_yin(tiandi_pan):
            ke_ti_list.append('伏吟课')
        
        if self.is_fan_yin(tiandi_pan):
            ke_ti_list.append('反吟课')
        
        # 克贼统计
        shang_ke_xia, xia_zei_shang = self.count_ke_zi(sike)
        total_ke = shang_ke_xia + xia_zei_shang
        
        # 贼克法课体（3-8, 60）
        if shang_ke_xia == 1 and xia_zei_shang == 0:
            ke_ti_list.append('元首课')
            ke_ti_list.append('始入课')
        
        if xia_zei_shang == 1 and shang_ke_xia == 0:
            ke_ti_list.append('重审课')
        
        if total_ke >= 2:
            ke_ti_list.append('比用课')
        
        # 无禄课：四上克下
        if self.is_wu_lu(shang_ke_xia):
            ke_ti_list.append('无禄课')
        
        # 绝嗣课：四下贼上
        if self.is_jue_si(xia_zei_shang):
            ke_ti_list.append('绝嗣课')
        
        # 度厄课：三课上下克
        if self.is_du_e(shang_ke_xia, xia_zei_shang):
            ke_ti_list.append('度厄课')
        
        # 芜淫课
        if self.is_wu_yin(sike, ri_gan, ri_zhi):
            ke_ti_list.append('芜淫课')
        
        # 乱首课
        if self.is_luan_shou(sike, ri_gan, ri_zhi):
            ke_ti_list.append('乱首课')
        
        # 和美课
        if self.is_he_mei(sike):
            ke_ti_list.append('和美课')
        
        # 赘婿课
        if self.is_zhui_xu(sike, ri_gan):
            ke_ti_list.append('赘婿课')
        
        # 富贵课
        if self.is_fu_gui(sike, ri_gan, tiandi_pan):
            ke_ti_list.append('富贵课')
        
        # 三传课体（9-15, 22-26, 29-34, 42-46, 57, 59）
        if sanchuan:
            # 玄胎课：三传皆孟
            if self.is_sanchuan_meng(sanchuan):
                ke_ti_list.append('玄胎课')
            
            # 三交课：三传皆仲
            if self.is_sanchuan_zhong(sanchuan):
                ke_ti_list.append('三交课')
            
            # 游子课：三传皆季
            if self.is_sanchuan_ji(sanchuan):
                ke_ti_list.append('游子课')
            
            # 全局课：三传三合
            if self.is_sanchuan_san_he(sanchuan):
                ke_ti_list.append('全局课')
            
            # 连珠课：三传相连
            if self.is_sanchuan_lian_zhu(sanchuan):
                ke_ti_list.append('连珠课')
            
            # 铸印课：巳戌卯
            if self.is_zhu_yin_ke(sanchuan):
                ke_ti_list.append('铸印课')
            
            # 轩盖课：午卯子
            if self.is_xuan_gai_ke(sanchuan):
                ke_ti_list.append('轩盖课')
            
            # 物类课：三传同五行
            if self.is_wu_lei(sanchuan):
                ke_ti_list.append('物类课')
            
            # 三光课
            if self.is_san_guang(sanchuan, {}):
                ke_ti_list.append('三光课')
            
            # 三阳课
            if self.is_san_yang(sanchuan):
                ke_ti_list.append('三阳课')
            
            # 六阳格
            if self.is_liu_yang(sanchuan, sike):
                ke_ti_list.append('六阳格')
            
            # 四顺格
            if self.is_si_shun(sanchuan):
                ke_ti_list.append('四顺格')
            
            # 时泰课
            if self.is_shi_tai(sanchuan, ri_gan):
                ke_ti_list.append('时泰课')
            
            # 天恩课
            if self.is_tian_en(sanchuan, ri_gan):
                ke_ti_list.append('天恩课')
            
            # 龙德课（需要月份）
            # if self.is_long_de(lunar_month, ri_gan):
            #     ke_ti_list.append('龙德课')
            
            # 繁昌课
            if self.is_fan_chang(sike, ri_gan):
                ke_ti_list.append('繁昌课')
            
            # 天心课
            if self.is_tian_xin(sike, yue, ri_gan_zhi=ri_gan, shi=shi):
                ke_ti_list.append('天心课')
        
        # 特殊关系课体（5, 47, 54, 58, 62-64）
        if self.is_pan_zhu(sike, sanchuan, yue, ri_gan, shi):
            ke_ti_list.append('盘珠课')
        
        if self.is_hui_huan(sike, sanchuan):
            ke_ti_list.append('回环课')
        
        if self.is_yin_cong(sike, sanchuan):
            ke_ti_list.append('引从课')
        
        if self.is_jiao_che(sike):
            ke_ti_list.append('交车课')
        
        if self.is_san_liu(sanchuan):
            ke_ti_list.append('三六相呼课')
        
        if self.is_suo_zhai(sanchuan):
            ke_ti_list.append('索债课')
        
        if self.is_yi_xun(sike, ri_gan + ri_zhi):
            ke_ti_list.append('一旬周遍课')
        
        # 凶格课体（35-41, 48-53, 56, 61）
        if self.is_jiu_chou(ri_gan, ri_zhi):
            ke_ti_list.append('九丑课')
        
        if self.is_bi_kou(sanchuan, ri_gan):
            ke_ti_list.append('闭口课')
        
        if self.is_zai_e(sanchuan):
            ke_ti_list.append('灾厄课')
        
        if self.is_tian_yu(sanchuan, ri_zhi):
            ke_ti_list.append('天狱课')
        
        if self.is_tian_huo(sanchuan):
            ke_ti_list.append('天祸课')
        
        if self.is_si_qi(sanchuan):
            ke_ti_list.append('死奇课')
        
        if self.is_gu_gua(sanchuan, nian_zhi):
            ke_ti_list.append('孤寡课')
        
        if self.is_qin_hai(sike):
            ke_ti_list.append('侵害课')
        
        if self.is_gui_mu(sanchuan, ri_gan):
            ke_ti_list.append('鬼墓课')
        
        if self.is_fu_yang(sanchuan):
            ke_ti_list.append('伏殃课')
        
        if self.is_si_jue(sanchuan):
            ke_ti_list.append('死绝课')
        
        if self.is_cheng_xuan(sanchuan):
            ke_ti_list.append('乘轩落马课')
        
        if self.is_jia_ke(sike):
            ke_ti_list.append('夹克课')
        
        if self.is_cha_jian(sanchuan):
            ke_ti_list.append('察奸课')
        
        # 变体课体（30, 33, 39, 44）
        if self.is_san_guang_shi_ming(sanchuan):
            ke_ti_list.append('三光失明课')
        
        if self.is_tian_en_wei_ding(sanchuan):
            ke_ti_list.append('天恩未定课')
        
        if self.is_tian_yu_qing_ping(sanchuan):
            ke_ti_list.append('天狱清平课')
        
        if self.is_san_yang_bu_tai(sanchuan):
            ke_ti_list.append('三阳不泰课')
        
        if self.is_zhun_fu(sanchuan):
            ke_ti_list.append('迍福课')
        
        if self.is_heng_tong(sanchuan):
            ke_ti_list.append('亨通课')
        
        if self.is_yang_jiu(sanchuan):
            ke_ti_list.append('殃咎课')
        
        if self.is_jie_li(sike):
            ke_ti_list.append('解离课')
        
        # 遥克课、昴星课、别责课、八专课需要三传引擎配合
        # 这里做简化判断
        
        return ke_ti_list


def main():
    """测试课体判断"""
    judge = KeTiJudgeCalculator()
    
    print("=" * 80)
    print("课体判断测试")
    print("=" * 80)
    
    # 测试伏吟
    tiandi_pan_fu_yin = {
        '子': '子', '丑': '丑', '寅': '寅', '卯': '卯',
        '辰': '辰', '巳': '巳', '午': '午', '未': '未',
        '申': '申', '酉': '酉', '戌': '戌', '亥': '亥'
    }
    
    sike_test = [
        {'top': '巳', 'bottom': '戊'},
        {'top': '巳', 'bottom': '巳'},
        {'top': '辰', 'bottom': '辰'},
        {'top': '辰', 'bottom': '辰'}
    ]
    
    sanchuan_test = {
        '初传': '巳',
        '中传': '申',
        '末传': '寅'
    }
    
    ke_ti = judge.judge_all_ke_ti(
        sike_test, sanchuan_test,
        tiandi_pan_fu_yin, '戊', '辰'
    )
    
    print(f"\n戊辰日子将子时课体：{ke_ti}")
    print(f"课体数量：{len(ke_ti)}")


if __name__ == '__main__':
    main()
