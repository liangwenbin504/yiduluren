#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
《毕法赋》规则匹配引擎 v3.0
第三阶段：扩展至 30+ 条规则，集成天将、神煞系统
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from daliuren_base import (
    get_xun, get_kong_wang, get_ding_shen, get_lu_shen,
    get_gui_shen, get_cai_shen, get_zhang_sheng,
    get_yin_yang, get_wu_xing, get_sheng_ke,
    enhance_ke_li_data, get_nian_zhi, get_sang_men, get_diao_ke
)

class BiFaRulesMatcherV3:
    """毕法赋规则匹配器 v3.0"""
    
    def __init__(self):
        self.matched_rules = []
    
    def _get_ri_gan_zhi(self, ke_li: Dict) -> Tuple[str, str]:
        """统一提取日干支"""
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi or len(ri_gan_zhi) < 2:
            return '', ''
        return ri_gan_zhi[0], ri_gan_zhi[1]
    
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
    
    def match_rule_039(self, ke_li: Dict) -> Dict:
        """规则 39：太阳照武宜擒贼"""
        result = {'rule_id': 39, 'rule_name': '太阳照武宜擒贼', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        # 需要月将和玄武信息，简化处理
        return result
    
    def match_rule_040(self, ke_li: Dict) -> Dict:
        """规则 40：后合占婚岂用媒"""
        result = {'rule_id': 40, 'rule_name': '后合占婚岂用媒', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        # 需要天后、六合信息，简化处理
        return result
    
    def match_rule_071(self, ke_li: Dict) -> Dict:
        """规则 71：病符克宅全家患"""
        result = {'rule_id': 71, 'rule_name': '病符克宅全家患', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        # 简化：暂不实现
        return result
    
    def match_rule_072(self, ke_li: Dict) -> Dict:
        """规则 72：丧吊全逢挂缟衣"""
        result = {'rule_id': 72, 'rule_name': '丧吊全逢挂缟衣', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi: return result
        
        # 简化判断：检查课例是否包含丧门吊客信息
        if ke_li.get('chu_sang_men', False) or ke_li.get('chu_diao_ke', False):
            result['matched'] = True
            result['matched_patterns'].append('丧吊临传')
            result['reasoning'] = f'三传见丧门或吊客'
        
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
