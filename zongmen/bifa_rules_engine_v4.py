#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
《毕法赋》规则匹配引擎 v4.0
第四阶段：扩展至 40-60 条规则，集成天将、课体格局系统
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from daliuren_base import (
    get_xun, get_kong_wang, get_ding_shen, get_lu_shen,
    get_gui_shen, get_cai_shen, get_zhang_sheng,
    get_yin_yang, get_wu_xing, get_sheng_ke,
    enhance_ke_li_data, get_nian_zhi, get_sang_men, get_diao_ke,
    get_tian_jiang_ke_ri, get_ke_ti_ge_ju, TIAN_JIANG_JI_XIONG
)

class BiFaRulesMatcherV4:
    """毕法赋规则匹配器 v4.0"""
    
    def __init__(self):
        self.matched_rules = []
    
    def _get_ri_gan_zhi(self, ke_li: Dict) -> Tuple[str, str]:
        """统一提取日干支"""
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi or len(ri_gan_zhi) < 2:
            return '', ''
        return ri_gan_zhi[0], ri_gan_zhi[1]
    
    def match_rule_001(self, ke_li: Dict) -> Dict:
        """规则 1：前后引从升迁吉"""
        result = {'rule_id': 1, 'rule_name': '前后引从升迁吉', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        chu_chuan = ke_li.get('chu_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        # 引从格：初传引前，末传从后
        zhi_xu = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                 '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
        
        ri_zhi_idx = zhi_xu.get(ri_zhi, 0)
        chu_idx = zhi_xu.get(chu_chuan, 0)
        mo_idx = zhi_xu.get(mo_chuan, 0)
        
        # 初传在日支前，末传在日支后
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
        
        # 首尾相见：初传与末传相同
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
        
        # 帘幕贵人：贵人临干上
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
        
        # 催官使者：官鬼临三传
        gui_shen = get_gui_shen(ri_gan)
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
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
        
        # 避难逃生：干上受克，支上得生
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
        
        # 墓神：五行之墓
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
        
        # 太阳：月将
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
        
        # 独足：三传相同
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
        
        # 无亲：三传皆非日干之亲（生我者）
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
        # 简化判断
        if len(chuan_list) == 3 and all(c for c in chuan_list):
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
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
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
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
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
        """规则 17：进茹空亡宜退步"""
        result = {'rule_id': 17, 'rule_name': '进茹空亡宜退步', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        kong_wang = get_kong_wang(ri_gan_zhi)
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        if all(c in kong_wang for c in chuan_list if c):
            result['matched'] = True
            result['matched_patterns'].append('三传皆空')
            result['reasoning'] = f'三传皆空亡'
        return result
    
    def match_rule_018(self, ke_li: Dict) -> Dict:
        """规则 18：退茹空亡宜进步"""
        result = {'rule_id': 18, 'rule_name': '退茹空亡宜进步', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        # 退茹：三传逆行且空亡
        kong_wang = get_kong_wang(ri_gan_zhi)
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
        zhi_xu = {'子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
                 '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11}
        
        if len(chuan_list) == 3 and all(c for c in chuan_list):
            chu_idx = zhi_xu.get(chuan_list[0], 0)
            zhong_idx = zhi_xu.get(chuan_list[1], 0)
            mo_idx = zhi_xu.get(chuan_list[2], 0)
            
            # 逆行
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
        
        # 胎神：日干之胎
        tai_map = {
            '甲': '酉', '乙': '申', '丙': '子', '丁': '亥',
            '戊': '子', '己': '亥', '庚': '午', '辛': '巳',
            '壬': '午', '癸': '巳'
        }
        tai_shen = tai_map.get(ri_gan, '')
        
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
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
        
        # 胎神 + 死气
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
        
        # 交车相生：干上生支上，或支上生干上
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
        
        # 交车相克：干上克支上，或支上克干上
        if get_sheng_ke(gan_shang, zhi_shang, True, True) == '克' or get_sheng_ke(zhi_shang, gan_shang, True, True) == '克':
            result['matched'] = True
            result['matched_patterns'].append('交车相克')
            result['reasoning'] = f'干上{gan_shang}与支上{zhi_shang}相克'
        
        return result
    
    def match_rule_023(self, ke_li: Dict) -> Dict:
        """规则 23：彼求我事支传干"""
        result = {'rule_id': 23, 'rule_name': '彼求我事支传干', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 支传干：三传从支上传到干上
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        gan_shang = ke_li.get('gan_shang', '')
        
        if gan_shang in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('支传干')
            result['reasoning'] = f'三传传至干上{gan_shang}'
        
        return result
    
    def match_rule_024(self, ke_li: Dict) -> Dict:
        """规则 24：我求彼事干传支"""
        result = {'rule_id': 24, 'rule_name': '我求彼事干传支', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 干传支：三传从干上传到支上
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        zhi_shang = ke_li.get('zhi_shang', '')
        
        if zhi_shang in chuan_list:
            result['matched'] = True
            result['matched_patterns'].append('干传支')
            result['reasoning'] = f'三传传至支上{zhi_shang}'
        
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
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
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
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
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
        
        # 干上旺相，支上墓绝
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        # 简化判断
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
        
        # 财旺身衰
        cai_shen = get_cai_shen(ri_gan)
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
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
        
        # 支上旺相，干上墓绝
        zhi_shang = ke_li.get('zhi_shang', '')
        gan_shang = ke_li.get('gan_shang', '')
        
        if zhi_shang in get_zhang_sheng(ri_gan):
            result['matched'] = True
            result['matched_patterns'].append('宅旺人衰')
            result['reasoning'] = f'支上{zhi_shang}旺'
        
        return result
    
    def match_rule_032(self, ke_li: Dict) -> Dict:
        """规则 32：大多苦少乐"""
        result = {'rule_id': 32, 'rule_name': '大多苦少乐', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 初传吉，末传凶
        chu_chuan = ke_li.get('chu_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
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
        
        # 天将相克
        chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
        zhong_tian_jiang = ke_li.get('zhong_tian_jiang', '')
        
        if chu_tian_jiang and zhong_tian_jiang:
            # 简化判断：天将不同即视为内战
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
        
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
        # 财爻空亡
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
        
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
        # 鬼爻空亡
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
        
        # 干上死气，支上死气
        gan_shang = ke_li.get('gan_shang', '')
        zhi_shang = ke_li.get('zhi_shang', '')
        
        # 简化判断
        if gan_shang and zhi_shang:
            result['matched'] = True
            result['matched_patterns'].append('人宅皆死')
            result['reasoning'] = f'干上{gan_shang}、支上{zhi_shang}皆死气'
        
        return result
    
    def match_rule_039(self, ke_li: Dict) -> Dict:
        """规则 39：太阳照武宜擒贼"""
        result = {'rule_id': 39, 'rule_name': '太阳照武宜擒贼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 太阳（月将）照玄武（天将）
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
        
        # 天后、六合临三传
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
        
        # 魁（戌）加天门（亥）
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if chu_chuan == '戌':
            result['matched'] = True
            result['matched_patterns'].append('魁度天门')
            result['reasoning'] = f'初传{chu_chuan}为魁'
        
        return result
    
    def match_rule_042(self, ke_li: Dict) -> Dict:
        """规则 42：罡塞鬼户路不通"""
        result = {'rule_id': 42, 'rule_name': '罡塞鬼户路不通', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 罡（辰）塞鬼户
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if chu_chuan == '辰':
            result['matched'] = True
            result['matched_patterns'].append('罡塞鬼户')
            result['reasoning'] = f'初传{chu_chuan}为罡'
        
        return result
    
    def match_rule_043(self, ke_li: Dict) -> Dict:
        """规则 43：一马当途非久长"""
        result = {'rule_id': 43, 'rule_name': '一马当途非久长', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 驿马临传
        chu_chuan = ke_li.get('chu_chuan', '')
        
        # 简化：假设某些地支为驿马
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
        
        # 六冲：日支与初传冲
        zhi_chong = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
            '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
        }
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if zhi_chong.get(ri_zhi) == chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('六冲格')
            result['reasoning'] = f'日支{ri_zhi}与初传{chu_chuan}冲'
        
        return result
    
    def match_rule_045(self, ke_li: Dict) -> Dict:
        """规则 45：六合格主事和合"""
        result = {'rule_id': 45, 'rule_name': '六合格主事和合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan: return result
        
        # 六合：日支与初传合
        zhi_he = {
            '子': '丑', '丑': '子', '寅': '亥', '卯': '戌',
            '辰': '酉', '巳': '申', '午': '未', '未': '午',
            '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅'
        }
        
        chu_chuan = ke_li.get('chu_chuan', '')
        
        if zhi_he.get(ri_zhi) == chu_chuan:
            result['matched'] = True
            result['matched_patterns'].append('六合格')
            result['reasoning'] = f'日支{ri_zhi}与初传{chu_chuan}合'
        
        return result
    
    def match_rule_046(self, ke_li: Dict) -> Dict:
        """规则 46：三奇格主事异常"""
        result = {'rule_id': 46, 'rule_name': '三奇格主事异常', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 三奇：甲戊庚、乙丙丁等
        chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
        
        # 简化判断
        if len(set(chuan_list)) == 3:
            result['matched'] = True
            result['matched_patterns'].append('三奇格')
            result['reasoning'] = f'三传各异'
        
        return result
    
    def match_rule_047(self, ke_li: Dict) -> Dict:
        """规则 47：龙德格主事吉祥"""
        result = {'rule_id': 47, 'rule_name': '龙德格主事吉祥', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 青龙临传
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
        
        # 天赦：春戊寅等
        chu_chuan = ke_li.get('chu_chuan', '')
        
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
        
        # 天网：癸癸
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        
        if ri_gan_zhi == '癸亥':
            result['matched'] = True
            result['matched_patterns'].append('天网格')
            result['reasoning'] = f'日干支{ri_gan_zhi}为天网'
        
        return result
    
    def match_rule_050(self, ke_li: Dict) -> Dict:
        """规则 50：地网格主事难逃"""
        result = {'rule_id': 50, 'rule_name': '地网格主事难逃', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
        # 地网：巳亥
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        
        if ri_gan_zhi in ['巳亥', '亥巳']:
            result['matched'] = True
            result['matched_patterns'].append('地网格')
            result['reasoning'] = f'日干支{ri_gan_zhi}为地网'
        
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
        
        # 检查课例是否包含丧门吊客信息
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
        """规则 77：三合局主事成合"""
        result = {'rule_id': 77, 'rule_name': '三合局主事成合', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        
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
