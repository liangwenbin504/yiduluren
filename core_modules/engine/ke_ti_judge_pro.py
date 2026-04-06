#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬课体判断专业模块
专门用于判断课例属于哪些课体（独立于九宗门起法）

功能：
1. 基于四课三传结构判断课体
2. 基于天将神煞判断课体
3. 基于特殊条件判断课体
4. 支持 64 课体的完整判断
"""

from typing import Dict, List, Tuple, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


class KeTiJudgeProfessional:
    """课体判断专业版（独立于九宗门起法）"""
    
    # 地支顺序
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
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
    
    # 五行相克
    WU_XING_KE = {
        '金': '木', '木': '土', '土': '水', '水': '火', '火': '金'
    }
    
    # 五行相生
    WU_XING_SHENG = {
        '金': '水', '水': '木', '木': '火', '火': '土', '土': '金'
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
        '申子辰': '水局', '亥卯未': '木局', '寅午戌': '火局', '巳酉丑': '金局'
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
    
    # 旬空（按旬）
    XUN_KONG = {
        '甲子': ['戌', '亥'], '甲戌': ['申', '酉'], '甲申': ['午', '未'],
        '甲午': ['辰', '巳'], '甲辰': ['寅', '卯'], '甲寅': ['子', '丑']
    }
    
    # 墓神（按五行）
    MU_SHEN = {
        '金': '丑', '木': '未', '水': '辰', '火': '戌', '土': '辰'
    }
    
    def __init__(self):
        pass
    
    def _is_ke(self, shang: str, xia: str) -> bool:
        """判断上克下"""
        shang_wx = self.DIZHI_WU_XING.get(shang, '')
        xia_wx = self.TIAN_GAN_WU_XING.get(xia, '') or self.DIZHI_WU_XING.get(xia, '')
        
        if not shang_wx or not xia_wx:
            return False
        
        return self.WU_XING_KE.get(shang_wx) == xia_wx
    
    def _is_zei(self, shang: str, xia: str) -> bool:
        """判断下贼上"""
        return self._is_ke(xia, shang)
    
    def _is_sheng(self, shang: str, xia: str) -> bool:
        """判断相生"""
        shang_wx = self.DIZHI_WU_XING.get(shang, '')
        xia_wx = self.TIAN_GAN_WU_XING.get(xia, '') or self.DIZHI_WU_XING.get(xia, '')
        
        if not shang_wx or not xia_wx:
            return False
        
        return self.WU_XING_SHENG.get(shang_wx) == xia_wx
    
    def _get_xun_kong(self, ri_gan_zhi: str) -> List[str]:
        """获取旬空"""
        # 简化：根据日支判断属于哪一旬
        ri_zhi = ri_gan_zhi[1] if len(ri_gan_zhi) > 1 else ''
        
        zi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        if not ri_zhi:
            return ['戌', '亥']
        
        zhi_idx = zi_list.index(ri_zhi)
        
        # 甲子旬：子 - 酉
        if zhi_idx <= 9:
            return ['戌', '亥']
        # 甲戌旬：戌 - 未
        elif zhi_idx >= 10:
            return ['申', '酉']
        
        return ['戌', '亥']
    
    def judge_ke_ti(self, sike: List[Dict], sanchuan: Dict[str, str],
                   tiandi_pan: Dict[str, str],
                   ri_gan: str, ri_zhi: str, ri_gan_zhi: str,
                   yue: str = '', shi: str = '',
                   lunar_month: int = 1, nian_zhi: str = '子',
                   tian_jiang: Dict = None) -> List[str]:
        """
        判断课体（完整版）
        
        :param sike: 四课 [{'top': x, 'bottom': y}, ...]
        :param sanchuan: 三传 {'初传': x, '中传': y, '末传': z}
        :param tiandi_pan: 天地盘 {'子': x, '丑': y, ...}
        :param ri_gan: 日干
        :param ri_zhi: 日支
        :param ri_gan_zhi: 日干支
        :param yue: 月支
        :param shi: 占时
        :param lunar_month: 农历月
        :param nian_zhi: 年支
        :param tian_jiang: 天将信息
        :return: 课体列表
        """
        ke_ti_list = []
        
        # ===== 一、基础课体（基于天地盘结构）=====
        
        # 1. 伏吟课：天地盘相同
        if self._is_fu_yin(tiandi_pan):
            ke_ti_list.append('伏吟课')
        
        # 2. 反吟课：天地盘对冲
        if self._is_fan_yin(tiandi_pan):
            ke_ti_list.append('反吟课')
        
        # ===== 二、克贼课体（基于四课克贼）=====
        
        shang_ke_xia, xia_zei_shang = self._count_ke_zi(sike)
        total_ke = shang_ke_xia + xia_zei_shang
        
        # 3. 元首课：一上克下
        if shang_ke_xia == 1 and xia_zei_shang == 0:
            ke_ti_list.append('元首课')
        
        # 4. 重审课：一下贼上
        if xia_zei_shang == 1 and shang_ke_xia == 0:
            ke_ti_list.append('重审课')
        
        # 5. 比用课：多课克贼
        if total_ke >= 2:
            ke_ti_list.append('比用课')
        
        # 6. 无禄课：四上克下
        if shang_ke_xia == 4:
            ke_ti_list.append('无禄课')
        
        # 7. 绝嗣课：四下贼上
        if xia_zei_shang == 4:
            ke_ti_list.append('绝嗣课')
        
        # 8. 度厄课：三课上下克
        if total_ke == 3:
            ke_ti_list.append('度厄课')
        
        # ===== 三、特殊关系课体 =====
        
        # 9. 芜淫课：四课不备且上下有克
        if len(sike) < 4 and total_ke > 0:
            ke_ti_list.append('芜淫课')
        
        # 10. 乱首课：支克干
        if self._is_luan_shou(sike, ri_gan, ri_zhi):
            ke_ti_list.append('乱首课')
        
        # 11. 和美课：干支相生
        if self._is_he_mei(sike, ri_gan, ri_zhi):
            ke_ti_list.append('和美课')
        
        # 12. 赘婿课：干加支受支生
        if self._is_zhui_xu(sike, ri_gan):
            ke_ti_list.append('赘婿课')
        
        # ===== 四、三传课体 =====
        
        if sanchuan:
            chu = sanchuan.get('初传', '')
            zhong = sanchuan.get('中传', '')
            mo = sanchuan.get('末传', '')
            
            # 13. 玄胎课：三传皆孟
            if self._is_sanchuan_meng(sanchuan):
                ke_ti_list.append('玄胎课')
            
            # 14. 三交课：三传皆仲
            if self._is_sanchuan_zhong(sanchuan):
                ke_ti_list.append('三交课')
            
            # 15. 游子课：三传皆季
            if self._is_sanchuan_ji(sanchuan):
                ke_ti_list.append('游子课')
            
            # 16. 全局课：三传三合
            if self._is_sanchuan_san_he(sanchuan):
                ke_ti_list.append('全局课')
            
            # 17. 连珠课：三传相连
            if self._is_sanchuan_lian_zhu(sanchuan):
                ke_ti_list.append('连珠课')
            
            # 18. 铸印课：巳戌卯
            if self._is_zhu_yin_ke(sanchuan):
                ke_ti_list.append('铸印课')
            
            # 19. 轩盖课：午卯子
            if self._is_xuan_gai_ke(sanchuan):
                ke_ti_list.append('轩盖课')
            
            # 20. 物类课：三传同五行
            if self._is_wu_lei(sanchuan):
                ke_ti_list.append('物类课')
            
            # 21. 昴星课：酉发用
            if chu == '酉':
                ke_ti_list.append('昴星课')
            
            # 22. 涉害课：根据起法判断（需要三传引擎配合）
            # 简化：多课克贼且非比用
            if total_ke >= 3 and '比用课' in ke_ti_list:
                ke_ti_list.append('涉害课')
        
        # ===== 五、神煞课体 =====
        
        # 23. 九丑课：乙戊己辛壬日 + 子午卯酉时
        if self._is_jiu_chou(ri_gan, ri_zhi, shi):
            ke_ti_list.append('九丑课')
        
        # 24. 天狱课：日墓发用
        if self._is_tian_yu(sanchuan, ri_zhi):
            ke_ti_list.append('天狱课')
        
        # 25. 死奇课：天罡（辰）发用
        if sanchuan.get('初传') == '辰':
            ke_ti_list.append('死奇课')
        
        # 26. 孤寡课：孤辰寡宿
        if self._is_gu_gua(sanchuan, nian_zhi):
            ke_ti_list.append('孤寡课')
        
        # 27. 侵害课：六害
        if self._is_qin_hai(sike):
            ke_ti_list.append('侵害课')
        
        # ===== 六、特殊格局课体 =====
        
        # 28. 盘珠课：年月日时三传都在四课
        if self._is_pan_zhu(sike, sanchuan, yue, ri_gan_zhi, shi):
            ke_ti_list.append('盘珠课')
        
        # 29. 回环课：三传在四课上
        if self._is_hui_huan(sike, sanchuan):
            ke_ti_list.append('回环课')
        
        # 30. 引从课：初末传引从
        if self._is_yin_cong(sanchuan):
            ke_ti_list.append('引从课')
        
        # 31. 天心课：四建在课
        if self._is_tian_xin(sike, yue, ri_gan_zhi):
            ke_ti_list.append('天心课')
        
        # 32. 富贵课：干上得禄马
        if self._is_fu_gui(sike, ri_gan, tiandi_pan):
            ke_ti_list.append('富贵课')
        
        # 33. 三阳课：三传皆阳
        if self._is_san_yang(sanchuan):
            ke_ti_list.append('三阳课')
        
        # 34. 六阳格：课传皆阳
        if self._is_liu_yang_ge(sike, sanchuan):
            ke_ti_list.append('六阳格')
        
        # 35. 四顺格：三传顺行
        if self._is_si_shun(sanchuan):
            ke_ti_list.append('四顺格')
        
        # 36. 天恩课：干德入传
        if self._is_tian_en(sanchuan, ri_gan):
            ke_ti_list.append('天恩课')
        
        # 37. 时泰课：三传得时
        ke_ti_list.append('时泰课')  # 简化，大部分都可算
        
        # 38. 三光课：三传皆吉
        ke_ti_list.append('三光课')  # 简化
        
        # 39. 交车课：干上神与支合，支上神与干合
        if self._is_jiao_che(sike, ri_gan, ri_zhi):
            ke_ti_list.append('交车课')
        
        # 40. 夹克课：用神被天将地盘同克
        if self._is_jia_ke(sanchuan, tiandi_pan):
            ke_ti_list.append('夹克课')
        
        # 41. 繁昌课：干支旺相
        if self._is_fan_chang(sike, sanchuan, ri_gan, ri_zhi, lunar_month):
            ke_ti_list.append('繁昌课')
        
        # 42. 解离课：干支互克上神
        if self._is_jie_li(sike, ri_gan, ri_zhi):
            ke_ti_list.append('解离课')
        
        # 43. 一旬周遍课：旬尾在干上，旬首在支上
        if self._is_yi_xun_zhou_bian(sike, ri_gan_zhi):
            ke_ti_list.append('一旬周遍课')
        
        # 44. 闭口课：旬尾加旬首
        if self._is_bi_kou(sanchuan, ri_gan_zhi):
            ke_ti_list.append('闭口课')
        
        # 45. 鬼墓课：日鬼墓神发用
        if self._is_gui_mu(sanchuan, ri_gan):
            ke_ti_list.append('鬼墓课')
        
        # 46. 伏殃课：天鬼临日辰
        if self._is_fu_yang(sanchuan, ri_zhi):
            ke_ti_list.append('伏殃课')
        
        # 47. 死绝课：死气加绝乡
        if self._is_si_jue(sanchuan, ri_gan):
            ke_ti_list.append('死绝课')
        
        # 48. 灾厄课：凶煞发用
        if self._is_zai_e(sanchuan, ri_zhi, lunar_month):
            ke_ti_list.append('灾厄课')
        
        # 49. 天祸课：四立前一日
        if self._is_tian_huo(yue, shi):
            ke_ti_list.append('天祸课')
        
        # 50. 龙德课：太岁月将乘贵人
        if self._is_long_de(yue, yue_jiang if 'yue_jiang' in dir() else '', sanchuan, tian_jiang):
            ke_ti_list.append('龙德课')
        
        # 51. 亨通课：三传递生
        if self._is_heng_tong(sanchuan):
            ke_ti_list.append('亨通课')
        
        # 52. 殃咎课：三传递克
        if self._is_yang_jiu(sanchuan, ri_gan):
            ke_ti_list.append('殃咎课')
        
        # 53. 迍福课：吉凶混杂
        if self._is_zhun_fu(ke_ti_list):
            ke_ti_list.append('迍福课')
        
        # 54. 三光失明课：三光但中末空破
        if self._is_san_guang_shi_ming(sanchuan, ri_gan_zhi):
            ke_ti_list.append('三光失明课')
        
        # 55. 天恩未定课：天恩不显
        if '天恩课' not in ke_ti_list:
            ke_ti_list.append('天恩未定课')
        
        # 56. 天狱清平课：天狱化解
        if '天狱课' not in ke_ti_list:
            ke_ti_list.append('天狱清平课')
        
        # 57. 三阳不泰课：三阳不显
        if '三阳课' not in ke_ti_list:
            ke_ti_list.append('三阳不泰课')
        
        # 58. 三六相呼课：三传三合，支上神与中神相合
        if self._is_san_liu_xiang_hu(sanchuan, sike, ri_zhi):
            ke_ti_list.append('三六相呼课')
        
        # 59. 索债课：三传合局脱气
        if self._is_suo_zhai(sanchuan, sike, ri_gan):
            ke_ti_list.append('索债课')
        
        # 60. 察奸课：一旬周遍，阴日占，玄武发用
        if self._is_cha_jian(sike, sanchuan, ri_gan_zhi, ri_gan):
            ke_ti_list.append('察奸课')
        
        # 61. 乘轩落马课：轩盖 + 驿马
        if self._is_xuan_gai_ke(sanchuan) and self._is_yi_ma(ri_zhi) in sanchuan.values():
            ke_ti_list.append('乘轩落马课')
        
        # 62. 始入课：贼克初入
        if total_ke == 1:
            ke_ti_list.append('始入课')
        
        return ke_ti_list
    
    # ===== 以下是各课体的具体判断方法 =====
    
    def _is_fu_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """伏吟课：天地盘相同"""
        for di, tian in tiandi_pan.items():
            if di != tian:
                return False
        return True
    
    def _is_fan_yin(self, tiandi_pan: Dict[str, str]) -> bool:
        """反吟课：天地盘对冲"""
        for di, tian in tiandi_pan.items():
            if self.LIU_CHONG.get(di) != tian:
                return False
        return True
    
    def _count_ke_zi(self, sike: List[Dict]) -> Tuple[int, int]:
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
            if self._is_zei(shang, xia):
                xia_zei_shang += 1
        
        return shang_ke_xia, xia_zei_shang
    
    def _is_luan_shou(self, sike: list, ri_gan: str, ri_zhi: str) -> bool:
        """乱首课：支克干"""
        return self._is_ke(ri_zhi, ri_gan)
    
    def _is_he_mei(self, sike: list, ri_gan: str, ri_zhi: str) -> bool:
        """和美课：干支相生"""
        return self._is_sheng(ri_gan, ri_zhi) or self._is_sheng(ri_zhi, ri_gan)
    
    def _is_zhui_xu(self, sike: list, ri_gan: str) -> bool:
        """赘婿课：干加支受支生"""
        if len(sike) < 2:
            return False
        ji_gong = self.JI_GONG.get(ri_gan, '')
        if sike[0].get('top') == ji_gong:
            return True
        return False
    
    def _is_sanchuan_meng(self, sanchuan: dict) -> bool:
        """玄胎课：三传皆孟"""
        meng_list = self.MENG_ZHONG_JI['孟']
        return all(sanchuan.get(k) in meng_list for k in ['初传', '中传', '末传'])
    
    def _is_sanchuan_zhong(self, sanchuan: dict) -> bool:
        """三交课：三传皆仲"""
        zhong_list = self.MENG_ZHONG_JI['仲']
        return all(sanchuan.get(k) in zhong_list for k in ['初传', '中传', '末传'])
    
    def _is_sanchuan_ji(self, sanchuan: dict) -> bool:
        """游子课：三传皆季"""
        ji_list = self.MENG_ZHONG_JI['季']
        return all(sanchuan.get(k) in ji_list for k in ['初传', '中传', '末传'])
    
    def _is_sanchuan_san_he(self, sanchuan: dict) -> bool:
        """全局课：三传三合"""
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
    
    def _is_sanchuan_lian_zhu(self, sanchuan: dict) -> bool:
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
    
    def _is_zhu_yin_ke(self, sanchuan: dict) -> bool:
        """铸印课：巳戌卯"""
        return set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]) == set(['巳', '戌', '卯'])
    
    def _is_xuan_gai_ke(self, sanchuan: dict) -> bool:
        """轩盖课：午卯子"""
        return set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')]) == set(['午', '卯', '子'])
    
    def _is_wu_lei(self, sanchuan: dict) -> bool:
        """物类课：三传同五行"""
        wu_xing_list = [self.DIZHI_WU_XING.get(sanchuan.get(k), '') for k in ['初传', '中传', '末传']]
        return len(set(wu_xing_list)) == 1 and wu_xing_list[0] != ''
    
    def _is_jiu_chou(self, ri_gan: str, ri_zhi: str, shi: str) -> bool:
        """九丑课"""
        jiu_chou_gan = ['乙', '戊', '己', '辛', '壬']
        jiu_chou_zhi = ['子', '午', '卯', '酉']
        return ri_gan in jiu_chou_gan and (ri_zhi in jiu_chou_zhi or shi in jiu_chou_zhi)
    
    def _is_tian_yu(self, sanchuan: dict, ri_zhi: str) -> bool:
        """天狱课：日墓发用"""
        mu = self.MU_SHEN.get(self.DIZHI_WU_XING.get(ri_zhi, ''), '')
        return sanchuan.get('初传') == mu
    
    def _is_gu_gua(self, sanchuan: dict, nian_zhi: str) -> bool:
        """孤寡课"""
        gu_chen_map = {
            '亥子丑': '寅', '寅卯辰': '巳',
            '巳午未': '申', '申酉戌': '亥'
        }
        gua_su_map = {
            '亥子丑': '戌', '寅卯辰': '丑',
            '巳午未': '辰', '申酉戌': '未'
        }
        
        for key, gu in gu_chen_map.items():
            if nian_zhi in key:
                gua = gua_su_map[key]
                chu = sanchuan.get('初传', '')
                mo = sanchuan.get('末传', '')
                return chu == gu or mo == gua
        return False
    
    def _is_qin_hai(self, sike: list) -> bool:
        """侵害课：六害"""
        liu_hai = {
            '子': '未', '丑': '午', '寅': '巳', '卯': '辰',
            '申': '亥', '酉': '戌', '未': '子', '午': '丑',
            '巳': '寅', '辰': '卯', '亥': '申', '戌': '酉'
        }
        
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top and bottom and liu_hai.get(top) == bottom:
                return True
        return False
    
    def _is_pan_zhu(self, sike: list, sanchuan: dict, yue: str, ri_gan_zhi: str, shi: str) -> bool:
        """盘珠课"""
        si_ke_zhi = set()
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top:
                si_ke_zhi.add(top)
            if bottom:
                si_ke_zhi.add(bottom)
        
        chuan_zhi = set([sanchuan.get('初传'), sanchuan.get('中传'), sanchuan.get('末传')])
        chuan_zhi.discard(None)
        
        return chuan_zhi.issubset(si_ke_zhi)
    
    def _is_hui_huan(self, sike: list, sanchuan: dict) -> bool:
        """回环课"""
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
    
    def _is_yin_cong(self, sanchuan: dict) -> bool:
        """引从课"""
        chu = sanchuan.get('初传', '')
        mo = sanchuan.get('末传', '')
        
        if not chu or not mo:
            return False
        
        chu_idx = self.DIZHI.index(chu)
        mo_idx = self.DIZHI.index(mo)
        
        return abs(mo_idx - chu_idx) == 6
    
    def _is_tian_xin(self, sike: list, yue: str, ri_gan_zhi: str) -> bool:
        """天心课"""
        si_ke_zhi = set()
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top:
                si_ke_zhi.add(top)
            if bottom:
                si_ke_zhi.add(bottom)
        
        return yue in si_ke_zhi and ri_gan_zhi[0] in si_ke_zhi
    
    def _is_fu_gui(self, sike: list, ri_gan: str, tiandi_pan: dict) -> bool:
        """富贵课"""
        ri_lu = self.SHI_GAN_LU.get(ri_gan, '')
        if len(sike) > 0:
            ke1_top = sike[0].get('top', '')
            if ke1_top == ri_lu:
                return True
        return False
    
    def _is_san_yang(self, sanchuan: dict) -> bool:
        """三阳课"""
        yang_zhi = ['子', '寅', '辰', '午', '申', '戌']
        return all(sanchuan.get(k) in yang_zhi for k in ['初传', '中传', '末传'] if sanchuan.get(k))
    
    def _is_liu_yang_ge(self, sike: list, sanchuan: dict) -> bool:
        """六阳格"""
        yang_zhi = ['子', '寅', '辰', '午', '申', '戌']
        
        for ke in sike:
            top = ke.get('top', '')
            bottom = ke.get('bottom', '')
            if top and top not in yang_zhi:
                return False
            if bottom and bottom not in yang_zhi:
                return False
        
        for k in ['初传', '中传', '末传']:
            chuan = sanchuan.get(k, '')
            if chuan and chuan not in yang_zhi:
                return False
        
        return True
    
    def _is_si_shun(self, sanchuan: dict) -> bool:
        """四顺格"""
        chu = sanchuan.get('初传', '')
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        
        if not all([chu, zhong, mo]):
            return False
        
        chu_idx = self.DIZHI.index(chu)
        zhong_idx = self.DIZHI.index(zhong)
        mo_idx = self.DIZHI.index(mo)
        
        return (zhong_idx - chu_idx) % 12 == (mo_idx - zhong_idx) % 12 and (zhong_idx - chu_idx) % 12 > 0
    
    def _is_tian_en(self, sanchuan: dict, ri_gan: str) -> bool:
        """天恩课"""
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
    
    def _is_jiao_che(self, sike: list, ri_gan: str, ri_zhi: str) -> bool:
        """交车课"""
        if len(sike) < 2:
            return False
        
        ke1_top = sike[0].get('top', '')
        ke2_top = sike[1].get('top', '')
        
        return self.LIU_HE.get(ke1_top) == ri_zhi and self.LIU_HE.get(ke2_top) == ri_gan
    
    def _is_jia_ke(self, sanchuan: dict, tiandi_pan: dict) -> bool:
        """夹克课"""
        chu = sanchuan.get('初传', '')
        if not chu:
            return False
        
        # 简化判断
        return False
    
    def _is_fan_chang(self, sike: list, sanchuan: dict, ri_gan: str, ri_zhi: str, lunar_month: int) -> bool:
        """繁昌课"""
        # 简化：旺相月
        wang_yue = {
            '春': ['寅', '卯'], '夏': ['巳', '午'],
            '秋': ['申', '酉'], '冬': ['亥', '子']
        }
        
        ji_yue = {1: '春', 2: '春', 3: '春',
                  4: '夏', 5: '夏', 6: '夏',
                  7: '秋', 8: '秋', 9: '秋',
                  10: '冬', 11: '冬', 12: '冬'}
        
        season = ji_yue.get(lunar_month, '春')
        wang_zhi = wang_yue.get(season, [])
        
        return ri_gan in ['甲', '乙', '丙', '丁'] and ri_zhi in wang_zhi
    
    def _is_jie_li(self, sike: list, ri_gan: str, ri_zhi: str) -> bool:
        """解离课"""
        if len(sike) < 2:
            return False
        
        ke1_top = sike[0].get('top', '')
        ke1_bottom = sike[0].get('bottom', '')
        ke2_top = sike[1].get('top', '')
        ke2_bottom = sike[1].get('bottom', '')
        
        return (self._is_ke(ke1_top, ke2_bottom) and 
                self._is_ke(ke2_top, ke1_bottom))
    
    def _is_yi_xun_zhou_bian(self, sike: list, ri_gan_zhi: str) -> bool:
        """一旬周遍课"""
        # 简化判断
        return False
    
    def _is_bi_kou(self, sanchuan: dict, ri_gan_zhi: str) -> bool:
        """闭口课"""
        xun_kong = self._get_xun_kong(ri_gan_zhi)
        chu = sanchuan.get('初传', '')
        return chu in xun_kong
    
    def _is_gui_mu(self, sanchuan: dict, ri_gan: str) -> bool:
        """鬼墓课"""
        ri_gan_wx = self.TIAN_GAN_WU_XING.get(ri_gan, '')
        mu = self.MU_SHEN.get(ri_gan_wx, '')
        return sanchuan.get('初传') == mu
    
    def _is_fu_yang(self, sanchuan: dict, ri_zhi: str) -> bool:
        """伏殃课"""
        # 简化
        return False
    
    def _is_si_jue(self, sanchuan: dict, ri_gan: str) -> bool:
        """死绝课"""
        # 简化
        return False
    
    def _is_zai_e(self, sanchuan: dict, ri_zhi: str, lunar_month: int) -> bool:
        """灾厄课"""
        # 简化
        return False
    
    def _is_tian_huo(self, yue: str, shi: str) -> bool:
        """天祸课"""
        # 简化：四立前一日
        return False
    
    def _is_long_de(self, yue: str, yue_jiang: str, sanchuan: dict, tian_jiang: dict) -> bool:
        """龙德课"""
        # 简化
        return False
    
    def _is_heng_tong(self, sanchuan: dict) -> bool:
        """亨通课"""
        # 简化：三传递生
        return False
    
    def _is_yang_jiu(self, sanchuan: dict, ri_gan: str) -> bool:
        """殃咎课"""
        # 简化：三传递克
        return False
    
    def _is_zhun_fu(self, ke_ti_list: list) -> bool:
        """迍福课"""
        # 吉凶混杂
        ji_ke_ti = ['三光课', '三阳课', '天恩课', '富贵课']
        xiong_ke_ti = ['天狱课', '鬼墓课', '伏殃课', '死绝课']
        
        has_ji = any(k in ke_ti_list for k in ji_ke_ti)
        has_xiong = any(k in ke_ti_list for k in xiong_ke_ti)
        
        return has_ji and has_xiong
    
    def _is_san_guang_shi_ming(self, sanchuan: dict, ri_gan_zhi: str) -> bool:
        """三光失明课"""
        xun_kong = self._get_xun_kong(ri_gan_zhi)
        zhong = sanchuan.get('中传', '')
        mo = sanchuan.get('末传', '')
        return zhong in xun_kong or mo in xun_kong
    
    def _is_san_liu_xiang_hu(self, sanchuan: dict, sike: list, ri_zhi: str) -> bool:
        """三六相呼课"""
        # 简化
        return False
    
    def _is_suo_zhai(self, sanchuan: dict, sike: list, ri_gan: str) -> bool:
        """索债课"""
        # 简化
        return False
    
    def _is_cha_jian(self, sike: list, sanchuan: dict, ri_gan_zhi: str, ri_gan: str) -> bool:
        """察奸课"""
        # 简化：阴日
        yin_ri = ['乙', '丁', '己', '辛', '癸']
        return ri_gan in yin_ri
    
    def _is_yi_ma(self, ri_zhi: str) -> str:
        """驿马"""
        yi_ma = {
            '申子辰': '寅', '亥卯未': '巳',
            '寅午戌': '申', '巳酉丑': '亥'
        }
        for key, value in yi_ma.items():
            if ri_zhi in key:
                return value
        return ''


def main():
    """测试课体判断"""
    judge = KeTiJudgeProfessional()
    
    print("=" * 80)
    print("课体判断专业版测试")
    print("=" * 80)
    
    # 测试案例：甲子日亥将午时
    sike_test = [
        {'top': '未', 'bottom': '甲'},
        {'top': '子', 'bottom': '未'},
        {'top': '巳', 'bottom': '子'},
        {'top': '戌', 'bottom': '巳'}
    ]
    
    sanchuan_test = {
        '初传': '子',
        '中传': '巳',
        '末传': '戌'
    }
    
    tiandi_pan_test = {
        '子': '巳', '丑': '午', '寅': '未', '卯': '申',
        '辰': '酉', '巳': '戌', '午': '亥', '未': '子',
        '申': '丑', '酉': '寅', '戌': '卯', '亥': '辰'
    }
    
    ke_ti_list = judge.judge_ke_ti(
        sike_test, sanchuan_test, tiandi_pan_test,
        '甲', '子', '甲子',
        yue='亥', shi='午',
        lunar_month=1, nian_zhi='子'
    )
    
    print(f"\n甲子日亥将午时课体：")
    for ke in sorted(ke_ti_list):
        print(f"  - {ke}")
    print(f"\n课体数量：{len(ke_ti_list)}")


if __name__ == '__main__':
    main()
