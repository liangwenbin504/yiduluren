#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
《毕法赋》规则匹配引擎 v5.0
第五阶段：扩展至 100 条规则，性能优化，断语生成
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from daliuren_base import (
    get_xun, get_kong_wang, get_ding_shen, get_lu_shen,
    get_gui_shen, get_cai_shen, get_zhang_sheng,
    get_yin_yang, get_wu_xing, get_sheng_ke,
    enhance_ke_li_data, get_nian_zhi, get_sang_men, get_diao_ke,
    get_tian_jiang_ke_ri, get_ke_ti_ge_ju, TIAN_JIANG_JI_XIONG,
    TIAN_JIANG_WU_XING, DI_ZHI
)

class BiFaRulesMatcherV5:
    """毕法赋规则匹配器 v5.0"""
    
    def __init__(self):
        self.matched_rules = []
        self._zhi_xu = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                       '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
        self._zhi_chong = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
            '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
        }
        self._zhi_he = {
            '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
            '辰': '酉', '巳': '申', '午': '未', '未': '午',
            '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
        }
        self._san_he = {
            '申子辰': '水局', '亥卯未': '木局',
            '寅午戌': '火局', '巳酉丑': '金局'
        }
        self._ri_gan_ji_gong = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
            '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
            '壬': '亥', '癸': '子'
        }
    
    def _get_ri_gan_zhi(self, ke_li: Dict) -> Tuple[str, str]:
        """统一提取日干支"""
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi or len(ri_gan_zhi) < 2:
            return '', ''
        return ri_gan_zhi[0], ri_gan_zhi[1]
    
    def _get_chuan_list(self, ke_li: Dict) -> List[str]:
        """获取三传列表"""
        return [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
    
    def match_rule_001(self, ke_li: Dict) -> Dict:
        """规则 1：前后引从升迁吉"""
        result = {'rule_id': 1, 'rule_name': '前后引从升迁吉', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chu_chuan = ke_li.get('chu_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        ri_zhi_idx = self._zhi_xu.get(ri_zhi, 0)
        chu_idx = self._zhi_xu.get(chu_chuan, 0)
        mo_idx = self._zhi_xu.get(mo_chuan, 0)
        
        if (chu_idx - ri_zhi_idx) % 12 == 11 and (mo_idx - ri_zhi_idx) % 12 == 1:
            result['matched'] = True
            result['matched_patterns'].append('引从格')
            result['reasoning'] = f'初传{chu_chuan}引前，末传{mo_chuan}从后'
        
        return result
    
    def match_rule_002(self, ke_li: Dict) -> Dict:
        """规则 2：首尾相见始终宜"""
        result = {'rule_id': 2, 'rule_name': '首尾相见始终宜', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chu_chuan = ke_li.get('chu_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        if chu_chuan == mo_chuan and chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('首尾相见')
            result['reasoning'] = f'初传{chu_chuan}与末传{mo_chuan}相同'
        
        return result
    
    def match_rule_003(self, ke_li: Dict) -> Dict:
        """规则 3：帘幕贵人高甲第"""
        result = {'rule_id': 3, 'rule_name': '帘幕贵人高甲第', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gui_ren = ke_li.get('gui_ren_day', '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == gui_ren:
            result['matched'] = True
            result['matched_patterns'].append('帘幕贵人')
            result['reasoning'] = f'贵人{gui_ren}临干上'
        
        return result
    
    def match_rule_004(self, ke_li: Dict) -> Dict:
        """规则 4：催官使者赴京期"""
        result = {'rule_id': 4, 'rule_name': '催官使者赴京期', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gui_shen = get_gui_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        
        if any(c in gui_shen for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('催官使者')
            result['reasoning'] = f'三传见官鬼'
        
        return result
    
    def match_rule_005(self, ke_li: Dict) -> Dict:
        """规则 5：六阳数足须公用"""
        result = {'rule_id': 5, 'rule_name': '六阳数足须公用', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        if get_yin_yang(ri_gan, True) == '阳' and get_yin_yang(ri_zhi, False) == '阳':
            result['matched'] = True
            result['matched_patterns'].append('六阳格')
            result['reasoning'] = f'日干{ri_gan}、日支{ri_zhi}皆阳'
        return result
    
    def match_rule_006(self, ke_li: Dict) -> Dict:
        """规则 6：六阴相继尽昏迷"""
        result = {'rule_id': 6, 'rule_name': '六阴相继尽昏迷', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        if get_yin_yang(ri_gan, True) == '阴' and get_yin_yang(ri_zhi, False) == '阴':
            result['matched'] = True
            result['matched_patterns'].append('六阴格')
            result['reasoning'] = f'日干{ri_gan}、日支{ri_zhi}皆阴'
        return result
    
    def match_rule_007(self, ke_li: Dict) -> Dict:
        """规则 7：旺禄临身徒妄作"""
        result = {'rule_id': 7, 'rule_name': '旺禄临身徒妄作', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        gan_shang = ke_li.get('gan_shang', '')
        if gan_shang == get_lu_shen(ri_gan):
            result['matched'] = True
            result['matched_patterns'].append('旺禄临身')
            result['reasoning'] = f'禄神临干上'
        return result
    
    def match_rule_008(self, ke_li: Dict) -> Dict:
        """规则 8：权摄不正禄临支"""
        result = {'rule_id': 8, 'rule_name': '权摄不正禄临支', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        zhi_shang = ke_li.get('zhi_shang', '')
        if zhi_shang == get_lu_shen(ri_gan):
            result['matched'] = True
            result['matched_patterns'].append('禄临支')
            result['reasoning'] = f'禄神临支上'
        return result
    
    def match_rule_009(self, ke_li: Dict) -> Dict:
        """规则 9：避难逃生易弃旧"""
        result = {'rule_id': 9, 'rule_name': '避难逃生易弃旧', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if get_sheng_ke(gan_shang, ri_gan, True, True) == '克' and get_sheng_ke(zhi_shang, ri_gan, True, True) == '生':
            result['matched'] = True
            result['matched_patterns'].append('避难逃生')
            result['reasoning'] = f'干上受克，支上得生'
        
        return result
    
    def match_rule_010(self, ke_li: Dict) -> Dict:
        """规则 10：墓神覆日人作晦"""
        result = {'rule_id': 10, 'rule_name': '墓神覆日人作晦', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        mu_map = {
            '甲': '未', '乙': '戌', '丙': '戌', '丁': '丑',
            '戊': '戌', '己': '丑', '庚': '丑', '辛': '辰',
            '壬': '辰', '癸': '未'
        }
        mu_shen = mu_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == mu_shen:
            result['matched'] = True
            result['matched_patterns'].append('墓神覆日')
            result['reasoning'] = f'墓神{mu_shen}覆日'
        
        return result
    
    def match_rule_011(self, ke_li: Dict) -> Dict:
        """规则 11：太阳射宅屋光辉"""
        result = {'rule_id': 11, 'rule_name': '太阳射宅屋光辉', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        yue_jiang = ke_li.get('yue_jiang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if zhi_shang == yue_jiang:
            result['matched'] = True
            result['matched_patterns'].append('太阳射宅')
            result['reasoning'] = f'月将{yue_jiang}临支上'
        
        return result
    
    def match_rule_012(self, ke_li: Dict) -> Dict:
        """规则 12：独足卦主事难成"""
        result = {'rule_id': 12, 'rule_name': '独足卦主事难成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_chuan = ke_li.get('chu_chuan', '')
        zhong_chuan = ke_li.get('zhong_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        if chu_chuan == zhong_chuan == mo_chuan and chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('独足卦')
            result['reasoning'] = f'三传皆{chu_chuan}'
        
        return result
    
    def match_rule_013(self, ke_li: Dict) -> Dict:
        """规则 13：无亲卦主事无依"""
        result = {'rule_id': 13, 'rule_name': '无亲卦主事无依', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chuan_list = self._get_chuan_list(ke_li)
        
        if len(chuan_list) == 3 and all(c for c in chuan_list):
            # 检查三传中是否有生我者
            has_sheng_wo = False
            for chuan in chuan_list:
                if get_sheng_ke(chuan, ri_gan, True, True) == '生':
                    has_sheng_wo = True
                    break
            
            if not has_sheng_wo:
                result['matched'] = True
                result['matched_patterns'].append('无亲卦')
                result['reasoning'] = f'三传无生我者'
        
        return result
    
    def match_rule_014(self, ke_li: Dict) -> Dict:
        """规则 14：传财太旺反财亏"""
        result = {'rule_id': 14, 'rule_name': '传财太旺反财亏', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        cai_shen = get_cai_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        if sum(1 for c in chuan_list if c in cai_shen) == 3:
            result['matched'] = True
            result['matched_patterns'].append('三传皆财')
            result['reasoning'] = f'三传皆财'
        return result
    
    def match_rule_015(self, ke_li: Dict) -> Dict:
        """规则 15：传鬼太旺反身安"""
        result = {'rule_id': 15, 'rule_name': '传鬼太旺反身安', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        gui_shen = get_gui_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        if sum(1 for c in chuan_list if c in gui_shen) == 3:
            result['matched'] = True
            result['matched_patterns'].append('三传皆鬼')
            result['reasoning'] = f'三传皆鬼'
        return result
    
    def match_rule_016(self, ke_li: Dict) -> Dict:
        """规则 16：空上乘空事莫追"""
        result = {'rule_id': 16, 'rule_name': '空上乘空事莫追', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        kong_wang = get_kong_wang(ri_gan_zhi)
        if ke_li.get('gan_shang', '') in kong_wang:
            result['matched'] = True
            result['matched_patterns'].append('干上旬空')
            result['reasoning'] = f'干上神为旬空'
        return result
    
    def match_rule_017(self, ke_li: Dict) -> Dict:
        """
        规则 17：进茹空亡宜退步（修正版）
        条件：初传不空，末传空旬空或乘天将天空
        专指预测时，想做事，看可不可去做
        """
        result = {'rule_id': 17, 'rule_name': '进茹空亡宜退步', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        kong_wang = get_kong_wang(ri_gan_zhi)
        chuan_list = self._get_chuan_list(ke_li)
        
        if not all(chuan_list):
            return result
        
        chu_chuan = chuan_list[0]
        mo_chuan = chuan_list[2]
        
        chu_kong = chu_chuan in kong_wang
        mo_kong = mo_chuan in kong_wang
        mo_sky = ke_li.get('mo_tian_jiang', '') == '天空'
        
        if not chu_kong:
            if mo_kong or mo_sky:
                result['matched'] = True
                if mo_kong and mo_sky:
                    result['matched_patterns'].append('初传不空，末传空亡乘天空')
                    result['reasoning'] = f'初传{chu_chuan}不空，末传{mo_chuan}空亡乘天空'
                elif mo_kong:
                    result['matched_patterns'].append('初传不空，末传空亡')
                    result['reasoning'] = f'初传{chu_chuan}不空，末传{mo_chuan}空亡'
                else:
                    result['matched_patterns'].append('初传不空，末传乘天空')
                    result['reasoning'] = f'初传{chu_chuan}不空，末传{mo_chuan}乘天空'
        
        return result
    
    def match_rule_018(self, ke_li: Dict) -> Dict:
        """规则 18：退茹空亡宜进步"""
        result = {'rule_id': 18, 'rule_name': '退茹空亡宜进步', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        kong_wang = get_kong_wang(ri_gan_zhi)
        chuan_list = self._get_chuan_list(ke_li)
        
        if len(chuan_list) == 3 and all(c for c in chuan_list):
            chu_idx = self._zhi_xu.get(chuan_list[0], 0)
            zhong_idx = self._zhi_xu.get(chuan_list[1], 0)
            mo_idx = self._zhi_xu.get(chuan_list[2], 0)
            
            if (chu_idx - zhong_idx) % 12 == 1 and (zhong_idx - mo_idx) % 12 == 1:
                if all(c in kong_wang for c in chuan_list):
                    result['matched'] = True
                    result['matched_patterns'].append('退茹空亡')
                    result['reasoning'] = f'三传逆行且空亡'
        
        return result
    
    def match_rule_019(self, ke_li: Dict) -> Dict:
        """规则 19：胎财生气妻怀孕"""
        result = {'rule_id': 19, 'rule_name': '胎财生气妻怀孕', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        tai_map = {
            '甲': '酉', '乙': '申', '丙': '子', '丁': '亥',
            '戊': '子', '己': '亥', '庚': '午', '辛': '巳',
            '壬': '午', '癸': '巳'
        }
        tai_shen = tai_map.get(ri_gan, '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if tai_shen in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('胎神临传')
            result['reasoning'] = f'胎神{tai_shen}临三传'
        
        return result
    
    def match_rule_020(self, ke_li: Dict) -> Dict:
        """规则 20：胎财死气损推详"""
        result = {'rule_id': 20, 'rule_name': '胎财死气损推详', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        tai_map = {
            '甲': '酉', '乙': '申', '丙': '子', '丁': '亥',
            '戊': '子', '己': '亥', '庚': '午', '辛': '巳',
            '壬': '午', '癸': '巳'
        }
        tai_shen = tai_map.get(ri_gan, '')
        yue_si_qi = ke_li.get('yue_si_qi', '')
        
        if tai_shen == yue_si_qi:
            result['matched'] = True
            result['matched_patterns'].append('胎神死气')
            result['reasoning'] = f'胎神{tai_shen}临死气'
        
        return result
    
    def match_rule_021(self, ke_li: Dict) -> Dict:
        """规则 21：交车相生情意美"""
        result = {'rule_id': 21, 'rule_name': '交车相生情意美', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if get_sheng_ke(gan_shang, zhi_shang, True, True) == '生' or get_sheng_ke(zhi_shang, gan_shang, True, True) == '生':
            result['matched'] = True
            result['matched_patterns'].append('交车相生')
            result['reasoning'] = f'干上{gan_shang}与支上{zhi_shang}相生'
        
        return result
    
    def match_rule_022(self, ke_li: Dict) -> Dict:
        """规则 22：交车相克事多乖"""
        result = {'rule_id': 22, 'rule_name': '交车相克事多乖', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if get_sheng_ke(gan_shang, zhi_shang, True, True) == '克' or get_sheng_ke(zhi_shang, gan_shang, True, True) == '克':
            result['matched'] = True
            result['matched_patterns'].append('交车相克')
            result['reasoning'] = f'干上{gan_shang}与支上{zhi_shang}相克'
        
        return result
    
    def match_rule_023(self, ke_li: Dict) -> Dict:
        """
        规则 23：彼求我事支传干（修正版）
        条件：别人找我办事会出现日支（第三课）是日干上神
        即：支上神 = 干上神
        """
        result = {'rule_id': 23, 'rule_name': '彼求我事支传干', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang and zhi_shang and gan_shang == zhi_shang:
            result['matched'] = True
            result['matched_patterns'].append('支上神即干上神')
            result['reasoning'] = f'支上神{zhi_shang}即干上神{gan_shang}，彼求我事'
        
        return result
    
    def match_rule_024(self, ke_li: Dict) -> Dict:
        """
        规则 24：我求彼事干传支（修正版）
        条件：我求别人办事，会出现日干寄宫的地支为第三课日支上神
        即：日干寄宫 = 支上神
        """
        result = {'rule_id': 24, 'rule_name': '我求彼事干传支', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
        
        ji_gong = self._ri_gan_ji_gong.get(ri_gan, '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if ji_gong and zhi_shang and ji_gong == zhi_shang:
            # 检查是否同时满足规则23
            gan_shang = ke_li.get('gan_shang', '')
            if not (gan_shang and gan_shang == zhi_shang):
                result['matched'] = True
                result['matched_patterns'].append('干寄宫即支上神')
                result['reasoning'] = f'日干{ri_gan}寄宫{ji_gong}即支上神{zhi_shang}，我求彼事'
        
        return result
    
    def match_rule_025(self, ke_li: Dict) -> Dict:
        """规则 25：金日逢丁凶祸动"""
        result = {'rule_id': 25, 'rule_name': '金日逢丁凶祸动', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        ri_gan = ri_gan_zhi[0]
        if ri_gan in ['庚', '辛']:
            result['matched'] = True
            result['matched_patterns'].append('金日逢丁')
            result['reasoning'] = f'{ri_gan}日逢丁神'
        return result
    
    def match_rule_026(self, ke_li: Dict) -> Dict:
        """规则 26：水日逢丁财动之"""
        result = {'rule_id': 26, 'rule_name': '水日逢丁财动之', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        ri_gan = ri_gan_zhi[0]
        if ri_gan in ['壬', '癸']:
            result['matched'] = True
            result['matched_patterns'].append('水日逢丁')
            result['reasoning'] = f'{ri_gan}日逢丁神'
        return result
    
    def match_rule_027(self, ke_li: Dict) -> Dict:
        """规则 27：传财化鬼财休觅"""
        result = {'rule_id': 27, 'rule_name': '传财化鬼财休觅', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        gan_shang = ke_li.get('gan_shang', '')
        cai_shen = get_cai_shen(ri_gan)
        gui_shen = get_gui_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        if sum(1 for c in chuan_list if c in cai_shen) == 3 and gan_shang in gui_shen:
            result['matched'] = True
            result['matched_patterns'].append('传财化鬼')
            result['reasoning'] = f'三传财生干上鬼'
        return result
    
    def match_rule_028(self, ke_li: Dict) -> Dict:
        """规则 28：传鬼化财钱险危"""
        result = {'rule_id': 28, 'rule_name': '传鬼化财钱险危', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        gui_shen = get_gui_shen(ri_gan)
        cai_shen = get_cai_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        gui_count = sum(1 for c in chuan_list if c in gui_shen)
        cai_count = sum(1 for c in chuan_list if c in cai_shen)
        if gui_count >= 2 and cai_count >= 1:
            result['matched'] = True
            result['matched_patterns'].append('传鬼化财')
            result['reasoning'] = f'三传鬼化财'
        return result
    
    def match_rule_029(self, ke_li: Dict) -> Dict:
        """规则 29：眷属丰盈居狭陋"""
        result = {'rule_id': 29, 'rule_name': '眷属丰盈居狭陋', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang in get_zhang_sheng(ri_gan) and zhi_shang:
            result['matched'] = True
            result['matched_patterns'].append('人旺宅衰')
            result['reasoning'] = f'干上{gan_shang}旺，支上{zhi_shang}衰'
        
        return result
    
    def match_rule_030(self, ke_li: Dict) -> Dict:
        """规则 30：财帛丰盈居隘陋"""
        result = {'rule_id': 30, 'rule_name': '财帛丰盈居隘陋', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        cai_shen = get_cai_shen(ri_gan)
        chuan_list = self._get_chuan_list(ke_li)
        
        cai_count = sum(1 for c in chuan_list if c in cai_shen)
        if cai_count >= 2:
            result['matched'] = True
            result['matched_patterns'].append('财旺')
            result['reasoning'] = f'三传财多'
        
        return result
    
    def match_rule_031(self, ke_li: Dict) -> Dict:
        """规则 31：屋宅宽圆人衰朽"""
        result = {'rule_id': 31, 'rule_name': '屋宅宽圆人衰朽', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if zhi_shang in get_zhang_sheng(ri_gan):
            result['matched'] = True
            result['matched_patterns'].append('宅旺人衰')
            result['reasoning'] = f'支上{zhi_shang}旺'
        
        return result
    
    def match_rule_032(self, ke_li: Dict) -> Dict:
        """规则 32：大多苦少乐"""
        result = {'rule_id': 32, 'rule_name': '大多苦少乐', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        mo_tian_jiang = ke_li.get('mo_tian_jiang', '')
        
        if TIAN_JIANG_JI_XIONG.get(chu_tian_jiang) == '吉' and TIAN_JIANG_JI_XIONG.get(mo_tian_jiang) == '凶':
            result['matched'] = True
            result['matched_patterns'].append('先吉后凶')
            result['reasoning'] = f'初传{chu_tian_jiang}吉，末传{mo_tian_jiang}凶'
        
        return result
    
    def match_rule_033(self, ke_li: Dict) -> Dict:
        """规则 33：有始无终难变易"""
        result = {'rule_id': 33, 'rule_name': '有始无终难变易', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        chu_chuan = ke_li.get('chu_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        if chu_chuan in get_zhang_sheng(ri_gan) and mo_chuan in get_gui_shen(ri_gan):
            result['matched'] = True
            result['matched_patterns'].append('有始无终')
            result['reasoning'] = f'初传长生，末传鬼'
        return result
    
    def match_rule_034(self, ke_li: Dict) -> Dict:
        """规则 34：将逢内战所谋危"""
        result = {'rule_id': 34, 'rule_name': '将逢内战所谋危', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        zhong_tian_jiang = ke_li.get('zhong_tian_jiang', '')
        
        if chu_tian_jiang and zhong_tian_jiang:
            if chu_tian_jiang != zhong_tian_jiang:
                result['matched'] = True
                result['matched_patterns'].append('将逢内战')
                result['reasoning'] = f'初传{chu_tian_jiang}与中传{zhong_tian_jiang}相克'
        
        return result
    
    def match_rule_035(self, ke_li: Dict) -> Dict:
        """规则 35：人宅受脱俱招盗"""
        result = {'rule_id': 35, 'rule_name': '人宅受脱俱招盗', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        gan_shang = ke_li.get('gan_shang', '')
        if get_sheng_ke(gan_shang, ri_gan, True, True) == '生':
            result['matched'] = True
            result['matched_patterns'].append('干上受脱')
            result['reasoning'] = f'干上神生日干'
        return result
    
    def match_rule_036(self, ke_li: Dict) -> Dict:
        """规则 36：财空乘元妻常病"""
        result = {'rule_id': 36, 'rule_name': '财空乘元妻常病', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        cai_shen = get_cai_shen(ri_gan)
        kong_wang = get_kong_wang(ke_li.get('ri_gan_zhi', ''))
        chuan_list = self._get_chuan_list(ke_li)
        
        for c in chuan_list:
            if c in cai_shen and c in kong_wang:
                result['matched'] = True
                result['matched_patterns'].append('财空')
                result['reasoning'] = f'财爻{c}空亡'
                break
        
        return result
    
    def match_rule_037(self, ke_li: Dict) -> Dict:
        """规则 37：鬼空乘玄夫常病"""
        result = {'rule_id': 37, 'rule_name': '鬼空乘玄夫常病', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gui_shen = get_gui_shen(ri_gan)
        kong_wang = get_kong_wang(ke_li.get('ri_gan_zhi', ''))
        chuan_list = self._get_chuan_list(ke_li)
        
        for c in chuan_list:
            if c in gui_shen and c in kong_wang:
                result['matched'] = True
                result['matched_patterns'].append('鬼空')
                result['reasoning'] = f'鬼爻{c}空亡'
                break
        
        return result
    
    def match_rule_038(self, ke_li: Dict) -> Dict:
        """规则 38：人宅皆死各尫羸"""
        result = {'rule_id': 38, 'rule_name': '人宅皆死各尫羸', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang and zhi_shang:
            # 检查干上和支上是否为死气
            # 死气：天干的墓地或绝地
            si_qi_map = {
                '甲': ['未', '申'], '乙': ['戌', '酉'], '丙': ['戌', '亥'], '丁': ['丑', '子'],
                '戊': ['戌', '亥'], '己': ['丑', '子'], '庚': ['丑', '寅'], '辛': ['辰', '卯'],
                '壬': ['辰', '巳'], '癸': ['未', '午']
            }
            
            si_qi = si_qi_map.get(ri_gan, [])
            gan_si = gan_shang in si_qi
            zhi_si = zhi_shang in si_qi
            
            if gan_si and zhi_si:
                result['matched'] = True
                result['matched_patterns'].append('人宅皆死')
                result['reasoning'] = f'干上{gan_shang}、支上{zhi_shang}皆死气'
        
        return result
    
    def match_rule_039(self, ke_li: Dict) -> Dict:
        """规则 39：太阳照武宜擒贼"""
        result = {'rule_id': 39, 'rule_name': '太阳照武宜擒贼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        yue_jiang = ke_li.get('yue_jiang', '')
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        
        if chu_tian_jiang == '玄武' and yue_jiang:
            result['matched'] = True
            result['matched_patterns'].append('太阳照武')
            result['reasoning'] = f'月将{yue_jiang}照玄武'
        
        return result
    
    def match_rule_040(self, ke_li: Dict) -> Dict:
        """规则 40：后合占婚岂用媒"""
        result = {'rule_id': 40, 'rule_name': '后合占婚岂用媒', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '天后' in chuan_tian_jiang and '六合' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('后合临传')
            result['reasoning'] = f'天后、六合临三传'
        
        return result
    
    def match_rule_041(self, ke_li: Dict) -> Dict:
        """规则 41：魁度天门关隔定"""
        result = {'rule_id': 41, 'rule_name': '魁度天门关隔定', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if chu_chuan == '戌':
            result['matched'] = True
            result['matched_patterns'].append('魁度天门')
            result['reasoning'] = f'初传{chu_chuan}为魁'
        
        return result
    
    def match_rule_042(self, ke_li: Dict) -> Dict:
        """规则 42：罡塞鬼户路不通"""
        result = {'rule_id': 42, 'rule_name': '罡塞鬼户路不通', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if chu_chuan == '辰':
            result['matched'] = True
            result['matched_patterns'].append('罡塞鬼户')
            result['reasoning'] = f'初传{chu_chuan}为罡'
        
        return result
    
    def match_rule_043(self, ke_li: Dict) -> Dict:
        """规则 43：一马当途非久长"""
        result = {'rule_id': 43, 'rule_name': '一马当途非久长', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chu_chuan = ke_li.get('chu_chuan', '')
        yi_ma = ['寅', '申', '巳', '亥']
        
        if chu_chuan in yi_ma:
            result['matched'] = True
            result['matched_patterns'].append('驿马当途')
            result['reasoning'] = f'初传{chu_chuan}为驿马'
        
        return result
    
    def match_rule_044(self, ke_li: Dict) -> Dict:
        """规则 44：六冲格主事反复"""
        result = {'rule_id': 44, 'rule_name': '六冲格主事反复', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if self._zhi_chong.get(ri_zhi) == chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('六冲格')
            result['reasoning'] = f'日支{ri_zhi}与初传{chu_chuan}冲'
        
        return result
    
    def match_rule_045(self, ke_li: Dict) -> Dict:
        """规则 45：六合格主事和合"""
        result = {'rule_id': 45, 'rule_name': '六合格主事和合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if self._zhi_he.get(ri_zhi) == chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('六合格')
            result['reasoning'] = f'日支{ri_zhi}与初传{chu_chuan}合'
        
        return result
    
    def match_rule_046(self, ke_li: Dict) -> Dict:
        """规则 46：三奇格主事异常"""
        result = {'rule_id': 46, 'rule_name': '三奇格主事异常', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_list = self._get_chuan_list(ke_li)
        
        if len(set(chuan_list)) == 3:
            result['matched'] = True
            result['matched_patterns'].append('三奇格')
            result['reasoning'] = f'三传各异'
        
        return result
    
    def match_rule_047(self, ke_li: Dict) -> Dict:
        """规则 47：龙德格主事吉祥"""
        result = {'rule_id': 47, 'rule_name': '龙德格主事吉祥', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '青龙' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('龙德格')
            result['reasoning'] = f'青龙临三传'
        
        return result
    
    def match_rule_048(self, ke_li: Dict) -> Dict:
        """规则 48：天赦格主事宽宥"""
        result = {'rule_id': 48, 'rule_name': '天赦格主事宽宥', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        tian_she = ['戊寅', '甲午', '戊申', '甲子']
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        
        if ri_gan_zhi in tian_she:
            result['matched'] = True
            result['matched_patterns'].append('天赦格')
            result['reasoning'] = f'日干支{ri_gan_zhi}为天赦'
        
        return result
    
    def match_rule_049(self, ke_li: Dict) -> Dict:
        """规则 49：天网格主事难脱"""
        result = {'rule_id': 49, 'rule_name': '天网格主事难脱', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        
        if ri_gan_zhi == '癸亥':
            result['matched'] = True
            result['matched_patterns'].append('天网格')
            result['reasoning'] = f'日干支{ri_gan_zhi}为天网'
        
        return result
    
    def match_rule_050(self, ke_li: Dict) -> Dict:
        """规则 50：地网格主事难逃"""
        result = {'rule_id': 50, 'rule_name': '地网格主事难逃', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        
        if ri_gan_zhi in ['巳亥', '亥巳']:
            result['matched'] = True
            result['matched_patterns'].append('地网格')
            result['reasoning'] = f'日干支{ri_gan_zhi}为地网'
        
        return result
    
    def match_rule_051(self, ke_li: Dict) -> Dict:
        """规则 51：干乘墓虎无占病"""
        result = {'rule_id': 51, 'rule_name': '干乘墓虎无占病', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        mu_map = {
            '甲': '未', '乙': '戌', '丙': '戌', '丁': '丑',
            '戊': '戌', '己': '丑', '庚': '丑', '辛': '辰',
            '壬': '辰', '癸': '未'
        }
        mu_shen = mu_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        
        if gan_shang == mu_shen and chu_tian_jiang == '白虎':
            result['matched'] = True
            result['matched_patterns'].append('干乘墓虎')
            result['reasoning'] = f'干上{gan_shen}乘白虎'
        
        return result
    
    def match_rule_052(self, ke_li: Dict) -> Dict:
        """规则 52：支乘墓虎有伏尸"""
        result = {'rule_id': 52, 'rule_name': '支乘墓虎有伏尸', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        mu_map = {
            '甲': '未', '乙': '戌', '丙': '戌', '丁': '丑',
            '戊': '戌', '己': '丑', '庚': '丑', '辛': '辰',
            '壬': '辰', '癸': '未'
        }
        mu_shen = mu_map.get(ri_gan, '')
        zhi_shang = ke_li.get('zhi_shang', '')
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        
        if zhi_shang == mu_shen and chu_tian_jiang == '白虎':
            result['matched'] = True
            result['matched_patterns'].append('支乘墓虎')
            result['reasoning'] = f'支上{zhi_shang}乘白虎'
        
        return result
    
    def match_rule_053(self, ke_li: Dict) -> Dict:
        """规则 53：彼此猜忌害相随"""
        result = {'rule_id': 53, 'rule_name': '彼此猜忌害相随', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        zhi_hai = {
            '子': '未', '丑': '午', '寅': '巳', '卯': '辰',
            '辰': '卯', '巳': '寅', '午': '丑', '未': '子',
            '申': '亥', '酉': '戌', '戌': '酉', '亥': '申'
        }
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if zhi_hai.get(ri_gan) == zhi_shang or zhi_hai.get(ri_zhi) == gan_shang:
            result['matched'] = True
            result['matched_patterns'].append('彼此猜忌')
            result['reasoning'] = f'干支相害'
        
        return result
    
    def match_rule_054(self, ke_li: Dict) -> Dict:
        """规则 54：合中犯煞蜜中砒"""
        result = {'rule_id': 54, 'rule_name': '合中犯煞蜜中砒', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chuan_list = self._get_chuan_list(ke_li)
        
        # 六合中有鬼煞
        he_shen = self._zhi_he.get(ri_zhi, '')
        gui_shen = get_gui_shen(ri_gan)
        
        if he_shen in chuan_list and he_shen in gui_shen:
            result['matched'] = True
            result['matched_patterns'].append('合中犯煞')
            result['reasoning'] = f'六合中有鬼煞'
        
        return result
    
    def match_rule_055(self, ke_li: Dict) -> Dict:
        """规则 55：宾主不投刑在上"""
        result = {'rule_id': 55, 'rule_name': '宾主不投刑在上', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chuan_list = self._get_chuan_list(ke_li)
        
        # 三刑：子卯、寅巳申、丑未戌、辰午酉亥自刑
        xing_set = [
            {'子', '卯'},
            {'寅', '巳', '申'},
            {'丑', '未', '戌'}
        ]
        
        chuan_set = set(chuan_list)
        for xing in xing_set:
            if xing.issubset(chuan_set):
                result['matched'] = True
                result['matched_patterns'].append('三刑')
                result['reasoning'] = f'三传见三刑'
                break
        
        return result
    
    def match_rule_056(self, ke_li: Dict) -> Dict:
        """规则 56：互生俱生基业永"""
        result = {'rule_id': 56, 'rule_name': '互生俱生基业永', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        # 干上生支，支上生干
        if get_sheng_ke(gan_shang, ri_zhi, True, False) == '生' and get_sheng_ke(zhi_shang, ri_gan, True, True) == '生':
            result['matched'] = True
            result['matched_patterns'].append('互生')
            result['reasoning'] = f'干上生支，支上生干'
        
        return result
    
    def match_rule_057(self, ke_li: Dict) -> Dict:
        """规则 57：互克俱刑家宅离"""
        result = {'rule_id': 57, 'rule_name': '互克俱刑家宅离', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        # 干上克支，支上克干
        if get_sheng_ke(gan_shang, ri_zhi, True, False) == '克' and get_sheng_ke(zhi_shang, ri_gan, True, True) == '克':
            result['matched'] = True
            result['matched_patterns'].append('互克')
            result['reasoning'] = f'干上克支，支上克干'
        
        return result
    
    def match_rule_058(self, ke_li: Dict) -> Dict:
        """规则 58：支干乘墓人宅晦"""
        result = {'rule_id': 58, 'rule_name': '支干乘墓人宅晦', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        mu_map = {
            '甲': '未', '乙': '戌', '丙': '戌', '丁': '丑',
            '戊': '戌', '己': '丑', '庚': '丑', '辛': '辰',
            '壬': '辰', '癸': '未'
        }
        mu_shen = mu_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang == mu_shen and zhi_shang == mu_shen:
            result['matched'] = True
            result['matched_patterns'].append('支干乘墓')
            result['reasoning'] = f'干支皆乘墓神'
        
        return result
    
    def match_rule_059(self, ke_li: Dict) -> Dict:
        """规则 59：干支皆败势倾颓"""
        result = {'rule_id': 59, 'rule_name': '干支皆败势倾颓', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 败神：日干之败
        bai_map = {
            '甲': '子', '乙': '亥', '丙': '卯', '丁': '寅',
            '戊': '子', '己': '亥', '庚': '午', '辛': '巳',
            '壬': '子', '癸': '亥'
        }
        bai_shen = bai_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang == bai_shen and zhi_shang == bai_shen:
            result['matched'] = True
            result['matched_patterns'].append('干支皆败')
            result['reasoning'] = f'干支皆乘败神'
        
        return result
    
    def match_rule_060(self, ke_li: Dict) -> Dict:
        """规则 60：绝处逢生危有救"""
        result = {'rule_id': 60, 'rule_name': '绝处逢生危有救', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 绝神：日干之绝
        jue_map = {
            '甲': '申', '乙': '酉', '丙': '亥', '丁': '子',
            '戊': '亥', '己': '子', '庚': '寅', '辛': '卯',
            '壬': '巳', '癸': '午'
        }
        jue_shen = jue_map.get(ri_gan, '')
        
        chuan_list = self._get_chuan_list(ke_li)
        zhang_sheng = get_zhang_sheng(ri_gan)
        
        if jue_shen in chuan_list and any(zs in chuan_list for zs in zhang_sheng):
            result['matched'] = True
            result['matched_patterns'].append('绝处逢生')
            result['reasoning'] = f'绝处逢生'
        
        return result
    
    def match_rule_061(self, ke_li: Dict) -> Dict:
        """规则 61：破败神临家业退"""
        result = {'rule_id': 61, 'rule_name': '破败神临家业退', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 破神：日支之破
        po_map = {
            '子': '酉', '丑': '辰', '寅': '亥', '卯': '午',
            '辰': '丑', '巳': '申', '午': '卯', '未': '戌',
            '申': '巳', '酉': '子', '戌': '未', '亥': '寅'
        }
        po_shen = po_map.get(ri_zhi, '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == po_shen:
            result['matched'] = True
            result['matched_patterns'].append('破神临干')
            result['reasoning'] = f'破神{po_shen}临干上'
        
        return result
    
    def match_rule_062(self, ke_li: Dict) -> Dict:
        """规则 62：空亡临宅事难成"""
        result = {'rule_id': 62, 'rule_name': '空亡临宅事难成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        kong_wang = get_kong_wang(ri_gan_zhi)
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if zhi_shang in kong_wang:
            result['matched'] = True
            result['matched_patterns'].append('空亡临宅')
            result['reasoning'] = f'支上神{zhi_shang}空亡'
        
        return result
    
    def match_rule_063(self, ke_li: Dict) -> Dict:
        """规则 63：贵人差遣事参差"""
        result = {'rule_id': 63, 'rule_name': '贵人差遣事参差', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        gui_ren_day = ke_li.get('gui_ren_day', '')
        gui_ren_night = ke_li.get('gui_ren_night', '')
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        
        if chu_tian_jiang == '贵人' and gui_ren_day != gui_ren_night:
            result['matched'] = True
            result['matched_patterns'].append('贵人差遣')
            result['reasoning'] = f'昼夜贵人不同'
        
        return result
    
    def match_rule_064(self, ke_li: Dict) -> Dict:
        """规则 64：禄马同乡事易成"""
        result = {'rule_id': 64, 'rule_name': '禄马同乡事易成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        lu_shen = get_lu_shen(ri_gan)
        yi_ma = ['寅', '申', '巳', '亥']
        
        if lu_shen in yi_ma:
            result['matched'] = True
            result['matched_patterns'].append('禄马同乡')
            result['reasoning'] = f'禄神{lu_shen}为驿马'
        
        return result
    
    def match_rule_065(self, ke_li: Dict) -> Dict:
        """规则 65：三合联珠贵必显"""
        result = {'rule_id': 65, 'rule_name': '三合联珠贵必显', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_list = self._get_chuan_list(ke_li)
        chuan_set = set(chuan_list)
        
        for he_str, ju_name in self._san_he.items():
            if set(he_str).issubset(chuan_set):
                result['matched'] = True
                result['matched_patterns'].append('三合联珠')
                result['reasoning'] = f'三传三合{ju_name}'
                return result
        
        return result
    
    def match_rule_066(self, ke_li: Dict) -> Dict:
        """规则 66：干支值绝事无成"""
        result = {'rule_id': 66, 'rule_name': '干支值绝事无成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        jue_map = {
            '甲': '申', '乙': '酉', '丙': '亥', '丁': '子',
            '戊': '亥', '己': '子', '庚': '寅', '辛': '卯',
            '壬': '巳', '癸': '午'
        }
        jue_shen = jue_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if gan_shang == jue_shen or zhi_shang == jue_shen:
            result['matched'] = True
            result['matched_patterns'].append('干支值绝')
            if gan_shang == jue_shen and zhi_shang == jue_shen:
                result['reasoning'] = f'干上神{gan_shang}、支上神{zhi_shang}皆为绝神'
            elif gan_shang == jue_shen:
                result['reasoning'] = f'干上神{gan_shang}为绝神'
            else:
                result['reasoning'] = f'支上神{zhi_shang}为绝神'
        
        return result
    
    def match_rule_067(self, ke_li: Dict) -> Dict:
        """规则 67：干支值墓人宅晦"""
        result = {'rule_id': 67, 'rule_name': '干支值墓人宅晦', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        mu_map = {
            '甲': '未', '乙': '戌', '丙': '戌', '丁': '丑',
            '戊': '戌', '己': '丑', '庚': '丑', '辛': '辰',
            '壬': '辰', '癸': '未'
        }
        mu_shen = mu_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == mu_shen:
            result['matched'] = True
            result['matched_patterns'].append('干支值墓')
            result['reasoning'] = f'干上神为墓神'
        
        return result
    
    def match_rule_068(self, ke_li: Dict) -> Dict:
        """规则 68：干支值败家业退"""
        result = {'rule_id': 68, 'rule_name': '干支值败家业退', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        bai_map = {
            '甲': '子', '乙': '亥', '丙': '卯', '丁': '寅',
            '戊': '子', '己': '亥', '庚': '午', '辛': '巳',
            '壬': '子', '癸': '亥'
        }
        bai_shen = bai_map.get(ri_gan, '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == bai_shen:
            result['matched'] = True
            result['matched_patterns'].append('干支值败')
            result['reasoning'] = f'干上神为败神'
        
        return result
    
    def match_rule_069(self, ke_li: Dict) -> Dict:
        """规则 69：三传生日百事成"""
        result = {'rule_id': 69, 'rule_name': '三传生日百事成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chuan_list = self._get_chuan_list(ke_li)
        
        # 三传皆生日干
        if all(get_sheng_ke(c, ri_gan, False, True) == '生' for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('三传生日')
            result['reasoning'] = f'三传皆生日干'
        
        return result
    
    def match_rule_070(self, ke_li: Dict) -> Dict:
        """规则 70：三传克日事难成"""
        result = {'rule_id': 70, 'rule_name': '三传克日事难成', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chuan_list = self._get_chuan_list(ke_li)
        
        # 三传皆克日干
        if all(get_sheng_ke(c, ri_gan, False, True) == '克' for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('三传克日')
            result['reasoning'] = f'三传皆克日干'
        
        return result
    
    def match_rule_071(self, ke_li: Dict) -> Dict:
        """规则 71：病符克宅全家患"""
        result = {'rule_id': 71, 'rule_name': '病符克宅全家患', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        bing_fu = ke_li.get('bing_fu', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if bing_fu == zhi_shang:
            result['matched'] = True
            result['matched_patterns'].append('病符克宅')
            result['reasoning'] = f'病符{bing_fu}临支上'
        
        return result
    
    def match_rule_072(self, ke_li: Dict) -> Dict:
        """规则 72：丧吊全逢挂缟衣"""
        result = {'rule_id': 72, 'rule_name': '丧吊全逢挂缟衣', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        if ke_li.get('chu_sang_men', False) or ke_li.get('chu_diao_ke', False):
            result['matched'] = True
            result['matched_patterns'].append('丧吊临传')
            result['reasoning'] = f'三传见丧门或吊客'
        
        return result
    
    def match_rule_073(self, ke_li: Dict) -> Dict:
        """规则 73：伏吟课主事沈吟"""
        result = {'rule_id': 73, 'rule_name': '伏吟课主事沈吟', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if '伏吟课' in ke_ti_ge_ju:
            result['matched'] = True
            result['matched_patterns'].append('伏吟课')
            result['reasoning'] = f'课体伏吟'
        
        return result
    
    def match_rule_074(self, ke_li: Dict) -> Dict:
        """规则 74：反吟课主事反复"""
        result = {'rule_id': 74, 'rule_name': '反吟课主事反复', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if '反吟课' in ke_ti_ge_ju:
            result['matched'] = True
            result['matched_patterns'].append('反吟课')
            result['reasoning'] = f'课体反吟'
        
        return result
    
    def match_rule_075(self, ke_li: Dict) -> Dict:
        """规则 75：连茹格主事牵连"""
        result = {'rule_id': 75, 'rule_name': '连茹格主事牵连', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        te_shu_ge_ju = ke_li.get('te_shu_ge_ju', [])
        
        if '连茹' in te_shu_ge_ju or '顺连茹' in ke_ti_ge_ju or '逆连茹' in ke_ti_ge_ju:
            result['matched'] = True
            result['matched_patterns'].append('连茹格')
            result['reasoning'] = f'三传连茹'
        
        return result
    
    def match_rule_076(self, ke_li: Dict) -> Dict:
        """规则 76：三合格主事和合"""
        result = {'rule_id': 76, 'rule_name': '三合格主事和合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if any('三合' in g for g in ke_ti_ge_ju):
            result['matched'] = True
            result['matched_patterns'].append('三合格')
            result['reasoning'] = f'三传三合局'
        
        return result
    
    def match_rule_077(self, ke_li: Dict) -> Dict:
        """规则 77：三会局主事成合"""
        result = {'rule_id': 77, 'rule_name': '三会局主事成合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if any('三会' in g for g in ke_ti_ge_ju):
            result['matched'] = True
            result['matched_patterns'].append('三会局')
            result['reasoning'] = f'三传三会局'
        
        return result
    
    def match_rule_078(self, ke_li: Dict) -> Dict:
        """规则 78：进茹格主事进取"""
        result = {'rule_id': 78, 'rule_name': '进茹格主事进取', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if '进茹' in ke_ti_ge_ju:
            result['matched'] = True
            result['matched_patterns'].append('进茹格')
            result['reasoning'] = f'三传进茹'
        
        return result
    
    def match_rule_079(self, ke_li: Dict) -> Dict:
        """规则 79：退茹格主事退守"""
        result = {'rule_id': 79, 'rule_name': '退茹格主事退守', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        ke_ti_ge_ju = ke_li.get('ke_ti_ge_ju', [])
        
        if '退茹' in ke_ti_ge_ju:
            result['matched'] = True
            result['matched_patterns'].append('退茹格')
            result['reasoning'] = f'三传退茹'
        
        return result
    
    def match_rule_080(self, ke_li: Dict) -> Dict:
        """规则 80：贵人临干利求官"""
        result = {'rule_id': 80, 'rule_name': '贵人临干利求官', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        gui_ren = ke_li.get('gui_ren_day', '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang == gui_ren:
            result['matched'] = True
            result['matched_patterns'].append('贵人临干')
            result['reasoning'] = f'贵人{gui_ren}临干上'
        
        return result
    
    def match_rule_081(self, ke_li: Dict) -> Dict:
        """规则 81：德神入庙有荣名"""
        result = {'rule_id': 81, 'rule_name': '德神入庙有荣名', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 德神：日干之德
        de_map = {
            '甲': '寅', '乙': '申', '丙': '巳', '丁': '亥',
            '戊': '巳', '己': '亥', '庚': '申', '辛': '寅',
            '壬': '亥', '癸': '巳'
        }
        de_shen = de_map.get(ri_gan, '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if de_shen in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('德神入庙')
            result['reasoning'] = f'德神{de_shen}临三传'
        
        return result
    
    def match_rule_082(self, ke_li: Dict) -> Dict:
        """规则 82：驿马临传有迁动"""
        result = {'rule_id': 82, 'rule_name': '驿马临传有迁动', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_list = self._get_chuan_list(ke_li)
        yi_ma = ['寅', '申', '巳', '亥']
        
        if any(c in yi_ma for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('驿马临传')
            result['reasoning'] = f'驿马临三传'
        
        return result
    
    def match_rule_083(self, ke_li: Dict) -> Dict:
        """规则 83：桃花入传主淫泆"""
        result = {'rule_id': 83, 'rule_name': '桃花入传主淫泆', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 桃花：申子辰在酉，寅午戌在卯，巳酉丑在午，亥卯未在子
        tao_hua_map = {
            '申': '酉', '子': '酉', '辰': '酉',
            '寅': '卯', '午': '卯', '戌': '卯',
            '巳': '午', '酉': '午', '丑': '午',
            '亥': '子', '卯': '子', '未': '子'
        }
        tao_hua = tao_hua_map.get(ri_zhi, '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if tao_hua in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('桃花入传')
            result['reasoning'] = f'桃花{tao_hua}临三传'
        
        return result
    
    def match_rule_084(self, ke_li: Dict) -> Dict:
        """规则 84：劫煞临传有盗贼"""
        result = {'rule_id': 84, 'rule_name': '劫煞临传有盗贼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 劫煞：申子辰在巳，寅午戌在亥，巳酉丑在寅，亥卯未在申
        jie_sha_map = {
            '申': '巳', '子': '巳', '辰': '巳',
            '寅': '亥', '午': '亥', '戌': '亥',
            '巳': '寅', '酉': '寅', '丑': '寅',
            '亥': '申', '卯': '申', '未': '申'
        }
        jie_sha = jie_sha_map.get(ri_zhi, '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if jie_sha in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('劫煞临传')
            result['reasoning'] = f'劫煞{jie_sha}临三传'
        
        return result
    
    def match_rule_085(self, ke_li: Dict) -> Dict:
        """规则 85：灾煞临传有灾祸"""
        result = {'rule_id': 85, 'rule_name': '灾煞临传有灾祸', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 灾煞：劫煞对冲
        zai_sha_map = {
            '申': '亥', '子': '亥', '辰': '亥',
            '寅': '巳', '午': '巳', '戌': '巳',
            '巳': '申', '酉': '申', '丑': '申',
            '亥': '寅', '卯': '寅', '未': '寅'
        }
        zai_sha = zai_sha_map.get(ri_zhi, '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if zai_sha in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('灾煞临传')
            result['reasoning'] = f'灾煞{zai_sha}临三传'
        
        return result
    
    def match_rule_086(self, ke_li: Dict) -> Dict:
        """规则 86：岁煞临传见官非"""
        result = {'rule_id': 86, 'rule_name': '岁煞临传见官非', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        sui_po = ke_li.get('bing_fu', '')  # 简化：用病符代替岁破
        chuan_list = self._get_chuan_list(ke_li)
        
        if sui_po in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('岁煞临传')
            result['reasoning'] = f'岁煞临三传'
        
        return result
    
    def match_rule_087(self, ke_li: Dict) -> Dict:
        """规则 87：月将入传百事吉"""
        result = {'rule_id': 87, 'rule_name': '月将入传百事吉', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        yue_jiang = ke_li.get('yue_jiang', '')
        chuan_list = self._get_chuan_list(ke_li)
        
        if yue_jiang in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('月将入传')
            result['reasoning'] = f'月将{yue_jiang}临三传'
        
        return result
    
    def match_rule_088(self, ke_li: Dict) -> Dict:
        """规则 88：天乙入传贵人来"""
        result = {'rule_id': 88, 'rule_name': '天乙入传贵人来', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '贵人' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('天乙入传')
            result['reasoning'] = f'贵人临三传'
        
        return result
    
    def match_rule_089(self, ke_li: Dict) -> Dict:
        """规则 89：螣蛇入传主惊恐"""
        result = {'rule_id': 89, 'rule_name': '螣蛇入传主惊恐', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '螣蛇' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('螣蛇入传')
            result['reasoning'] = f'螣蛇临三传'
        
        return result
    
    def match_rule_090(self, ke_li: Dict) -> Dict:
        """规则 90：朱雀入传主口舌"""
        result = {'rule_id': 90, 'rule_name': '朱雀入传主口舌', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '朱雀' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('朱雀入传')
            result['reasoning'] = f'朱雀临三传'
        
        return result
    
    def match_rule_091(self, ke_li: Dict) -> Dict:
        """规则 91：勾陈入传主争讼"""
        result = {'rule_id': 91, 'rule_name': '勾陈入传主争讼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '勾陈' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('勾陈入传')
            result['reasoning'] = f'勾陈临三传'
        
        return result
    
    def match_rule_092(self, ke_li: Dict) -> Dict:
        """规则 92：白虎入传主凶丧"""
        result = {'rule_id': 92, 'rule_name': '白虎入传主凶丧', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '白虎' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('白虎入传')
            result['reasoning'] = f'白虎临三传'
        
        return result
    
    def match_rule_093(self, ke_li: Dict) -> Dict:
        """规则 93：玄武入传主盗贼"""
        result = {'rule_id': 93, 'rule_name': '玄武入传主盗贼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '玄武' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('玄武入传')
            result['reasoning'] = f'玄武临三传'
        
        return result
    
    def match_rule_094(self, ke_li: Dict) -> Dict:
        """规则 94：太阴入传主阴私"""
        result = {'rule_id': 94, 'rule_name': '太阴入传主阴私', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '太阴' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('太阴入传')
            result['reasoning'] = f'太阴临三传'
        
        return result
    
    def match_rule_095(self, ke_li: Dict) -> Dict:
        """规则 95：天后入传主阴私"""
        result = {'rule_id': 95, 'rule_name': '天后入传主阴私', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '天后' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('天后入传')
            result['reasoning'] = f'天后临三传'
        
        return result
    
    def match_rule_096(self, ke_li: Dict) -> Dict:
        """规则 96：六合入传主和合"""
        result = {'rule_id': 96, 'rule_name': '六合入传主和合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '六合' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('六合入传')
            result['reasoning'] = f'六合临三传'
        
        return result
    
    def match_rule_097(self, ke_li: Dict) -> Dict:
        """规则 97：太常入传主喜庆"""
        result = {'rule_id': 97, 'rule_name': '太常入传主喜庆', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '太常' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('太常入传')
            result['reasoning'] = f'太常临三传'
        
        return result
    
    def match_rule_098(self, ke_li: Dict) -> Dict:
        """规则 98：天空入传主虚诈"""
        result = {'rule_id': 98, 'rule_name': '天空入传主虚诈', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_tian_jiang = [
            ke_li.get('chu_tian_jiang', ''),
            ke_li.get('zhong_tian_jiang', ''),
            ke_li.get('mo_tian_jiang', '')
        ]
        
        if '天空' in chuan_tian_jiang:
            result['matched'] = True
            result['matched_patterns'].append('天空入传')
            result['reasoning'] = f'天空临三传'
        
        return result
    
    def match_rule_099(self, ke_li: Dict) -> Dict:
        """规则 99：三传俱阳事必显"""
        result = {'rule_id': 99, 'rule_name': '三传俱阳事必显', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_list = self._get_chuan_list(ke_li)
        
        if all(get_yin_yang(c, False) == '阳' for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('三传俱阳')
            result['reasoning'] = f'三传皆阳'
        
        return result
    
    def match_rule_100(self, ke_li: Dict) -> Dict:
        """规则 100：三传俱阴事必晦"""
        result = {'rule_id': 100, 'rule_name': '三传俱阴事必晦', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        chuan_list = self._get_chuan_list(ke_li)
        
        if all(get_yin_yang(c, False) == '阴' for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('三传俱阴')
            result['reasoning'] = f'三传皆阴'
        
        return result
    
    def match_all_rules(self, ke_li: Dict) -> Dict:
        """匹配所有毕法赋规则"""
        all_matched = []
        rules_methods = [m for m in dir(self) if m.startswith('match_rule_') and callable(getattr(self, m))]
        
        for method_name in rules_methods:
            if method_name == 'match_all_rules':
                continue
            method = getattr(self, method_name)
            try:
                result = method(ke_li)
                if result.get('matched', False):
                    all_matched.append(result)
            except Exception as e:
                print(f"规则匹配错误 {method_name}: {e}")
        
        return {
            'total_rules': len(rules_methods) - 1,
            'matched_count': len(all_matched),
            'matched_rules': all_matched
        }
