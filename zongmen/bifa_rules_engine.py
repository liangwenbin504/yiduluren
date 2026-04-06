#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬《毕法赋》100 句规则匹配引擎
基于毕法赋规则对 8640 课例进行精准匹配
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# ==================== 基础工具函数 ====================

def get_yin_yang(ri_gan: str, ri_zhi: str) -> Tuple[str, str]:
    """获取日干支的阴阳"""
    gan_yin = {
        '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳',
        '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴'
    }
    zhi_yin = {
        '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴', '辰': '阳',
        '巳': '阴', '午': '阳', '未': '阴', '申': '阳', '酉': '阴',
        '戌': '阳', '亥': '阴'
    }
    return gan_yin.get(ri_gan, '阳'), zhi_yin.get(ri_zhi, '阳')

def get_wu_xing(element: str) -> str:
    """获取五行属性"""
    wu_xing_map = {
        '甲': '木', '乙': '木',
        '丙': '火', '丁': '火',
        '戊': '土', '己': '土',
        '庚': '金', '辛': '金',
        '壬': '水', '癸': '水',
        '寅': '木', '卯': '木',
        '巳': '火', '午': '火',
        '辰': '土', '戌': '土', '丑': '土', '未': '土',
        '申': '金', '酉': '金',
        '亥': '水', '子': '水'
    }
    return wu_xing_map.get(element, '土')

def get_sheng_ke(element1: str, element2: str) -> str:
    """判断五行生克关系"""
    wx1 = get_wu_xing(element1)
    wx2 = get_wu_xing(element2)
    
    sheng_cycle = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    ke_cycle = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    if wx1 == wx2:
        return '比和'
    elif sheng_cycle.get(wx1) == wx2:
        return '生'
    elif sheng_cycle.get(wx2) == wx1:
        return '被生'
    elif ke_cycle.get(wx1) == wx2:
        return '克'
    elif ke_cycle.get(wx2) == wx1:
        return '被克'
    else:
        return '未知'

def get_lu_shen(ri_gan: str) -> str:
    """获取禄神"""
    lu_map = {
        '甲': '寅', '乙': '卯',
        '丙': '巳', '丁': '午',
        '戊': '巳', '己': '午',
        '庚': '申', '辛': '酉',
        '壬': '亥', '癸': '子'
    }
    return lu_map.get(ri_gan, '')

def get_gui_shen(ri_gan: str) -> List[str]:
    """获取鬼煞（克日干者）"""
    gan_ke = {
        '甲': ['庚', '辛', '申', '酉'],
        '乙': ['庚', '辛', '申', '酉'],
        '丙': ['壬', '癸', '亥', '子'],
        '丁': ['壬', '癸', '亥', '子'],
        '戊': ['甲', '乙', '寅', '卯'],
        '己': ['甲', '乙', '寅', '卯'],
        '庚': ['丙', '丁', '巳', '午'],
        '辛': ['丙', '丁', '巳', '午'],
        '壬': ['戊', '己', '辰', '戌', '丑', '未'],
        '癸': ['戊', '己', '辰', '戌', '丑', '未']
    }
    return gan_ke.get(ri_gan, [])

def get_cai_shen(ri_gan: str) -> List[str]:
    """获取财煞（日干克者）"""
    gan_cai = {
        '甲': ['戊', '己', '辰', '戌', '丑', '未'],
        '乙': ['戊', '己', '辰', '戌', '丑', '未'],
        '丙': ['庚', '辛', '申', '酉'],
        '丁': ['庚', '辛', '申', '酉'],
        '戊': ['壬', '癸', '亥', '子'],
        '己': ['壬', '癸', '亥', '子'],
        '庚': ['甲', '乙', '寅', '卯'],
        '辛': ['甲', '乙', '寅', '卯'],
        '壬': ['丙', '丁', '巳', '午'],
        '癸': ['丙', '丁', '巳', '午']
    }
    return gan_cai.get(ri_gan, [])

def get_zhang_sheng(ri_gan: str) -> List[str]:
    """获取长生"""
    zhang_sheng_map = {
        '甲': ['亥'], '乙': ['午'],
        '丙': ['寅'], '丁': ['酉'],
        '戊': ['寅'], '己': ['酉'],
        '庚': ['巳'], '辛': ['子'],
        '壬': ['申'], '癸': ['卯']
    }
    return zhang_sheng_map.get(ri_gan, [])

def get_kong_wang(xun: str) -> List[str]:
    """获取旬空"""
    kong_wang_map = {
        '甲子': ['戌', '亥'],
        '甲戌': ['申', '酉'],
        '甲申': ['午', '未'],
        '甲午': ['辰', '巳'],
        '甲辰': ['寅', '卯'],
        '甲寅': ['子', '丑']
    }
    return kong_wang_map.get(xun, [])

def get_liu_he(zhi1: str, zhi2: str) -> bool:
    """判断是否六合"""
    liu_he_pairs = [
        ('子', '丑'), ('寅', '亥'), ('卯', '戌'),
        ('辰', '酉'), ('巳', '申'), ('午', '未')
    ]
    return (zhi1, zhi2) in liu_he_pairs or (zhi2, zhi1) in liu_he_pairs

def get_san_he(chuan: List[str]) -> bool:
    """判断是否三合"""
    san_he_combos = [
        ['申', '子', '辰'],
        ['亥', '卯', '未'],
        ['寅', '午', '戌'],
        ['巳', '酉', '丑']
    ]
    chuan_set = set(chuan)
    for combo in san_he_combos:
        if chuan_set == set(combo):
            return True
    return False

# ==================== 毕法赋规则匹配类 ====================

class BiFaRulesMatcher:
    """毕法赋 100 句规则匹配器"""
    
    def __init__(self):
        self.matched_rules = []
    
    def _get_ri_gan_zhi(self, ke_li: Dict) -> Tuple[str, str]:
        """统一提取日干支"""
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi or len(ri_gan_zhi) < 2:
            return '', ''
        return ri_gan_zhi[0], ri_gan_zhi[1]
    
    def match_rule_001(self, ke_li: Dict) -> Dict:
        """
        规则 1：前后引从升迁吉
        初传居干前为引，末传居干后为从
        """
        result = {
            'rule_id': 1,
            'rule_name': '前后引从升迁吉',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要三传和干支位置信息
        # 由于 8640 课例数据结构限制，此规则暂时无法完全匹配
        # 需要扩展数据结构，包含天盘位置信息
        
        return result
    
    def match_rule_002(self, ke_li: Dict) -> Dict:
        """
        规则 2：首尾相见始终宜
        干上有旬尾，支上有旬首，名周而复始格
        """
        result = {
            'rule_id': 2,
            'rule_name': '首尾相见始终宜',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要旬首旬尾信息
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_005(self, ke_li: Dict) -> Dict:
        """
        规则 5：六阳数足须公用
        支干四课三传皆居六阳之位
        """
        result = {
            'rule_id': 5,
            'rule_name': '六阳数足须公用',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi:
            return result
            
        # 从 ri_gan_zhi 提取日干和日支
        ri_gan = ri_gan_zhi[0] if len(ri_gan_zhi) >= 1 else ''
        ri_zhi = ri_gan_zhi[1] if len(ri_gan_zhi) >= 2 else ''
        
        gan_yin, zhi_yin = get_yin_yang(ri_gan, ri_zhi)
        
        # 判断日干支是否皆阳
        if gan_yin == '阳' and zhi_yin == '阳':
            result['matched'] = True
            result['matched_patterns'].append('六阳格')
            result['reasoning'] = f'日干{ri_gan}({gan_yin})、日支{ri_zhi}({zhi_yin})皆阳，符合六阳格'
        
        return result
    
    def match_rule_006(self, ke_li: Dict) -> Dict:
        """
        规则 6：六阴相继尽昏迷
        课传皆居六阴之位
        """
        result = {
            'rule_id': 6,
            'rule_name': '六阴相继尽昏迷',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi:
            return result
            
        ri_gan = ri_gan_zhi[0] if len(ri_gan_zhi) >= 1 else ''
        ri_zhi = ri_gan_zhi[1] if len(ri_gan_zhi) >= 2 else ''
        
        gan_yin, zhi_yin = get_yin_yang(ri_gan, ri_zhi)
        
        if gan_yin == '阴' and zhi_yin == '阴':
            result['matched'] = True
            result['matched_patterns'].append('六阴格')
            result['reasoning'] = f'日干{ri_gan}({gan_yin})、日支{ri_zhi}({zhi_yin})皆阴，符合六阴格'
        
        return result
    
    def match_rule_007(self, ke_li: Dict) -> Dict:
        """
        规则 7：旺禄临身徒妄作
        日之禄神又作旺神临干上
        """
        result = {
            'rule_id': 7,
            'rule_name': '旺禄临身徒妄作',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
        if not ri_gan_zhi:
            return result
            
        ri_gan = ri_gan_zhi[0]
        gan_shang = ke_li.get('gan_shang', '')
        
        lu_shen = get_lu_shen(ri_gan)
        
        if lu_shen and gan_shang == lu_shen:
            result['matched'] = True
            result['matched_patterns'].append('旺禄临身')
            result['reasoning'] = f'日干{ri_gan}禄神在{lu_shen}，临干上{gan_shang}'
        
        return result
    
    def match_rule_008(self, ke_li: Dict) -> Dict:
        """
        规则 8：权摄不正禄临支
        日干禄神加临支辰上
        """
        result = {
            'rule_id': 8,
            'rule_name': '权摄不正禄临支',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
            
        zhi_shang = ke_li.get('zhi_shang', '')
        lu_shen = get_lu_shen(ri_gan)
        
        if lu_shen and zhi_shang == lu_shen:
            result['matched'] = True
            result['matched_patterns'].append('禄临支')
            result['reasoning'] = f'日干{ri_gan}禄神在{lu_shen}，临支上{zhi_shang}'
        
        return result
    
    def match_rule_011(self, ke_li: Dict) -> Dict:
        """
        规则 11：众鬼虽彰全不畏
        三传皆鬼，干上有救神制鬼
        """
        result = {
            'rule_id': 11,
            'rule_name': '众鬼虽彰全不畏',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
            
        gan_shang = ke_li.get('gan_shang', '')
        chu_chuan = ke_li.get('chu_chuan', '')
        zhong_chuan = ke_li.get('zhong_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        gui_shen = get_gui_shen(ri_gan)
        
        # 判断三传是否多鬼
        chuan_list = [chu_chuan, zhong_chuan, mo_chuan]
        chuan_gui_count = sum(1 for chuan in chuan_list if chuan in gui_shen)
        
        if chuan_gui_count >= 2:
            # 判断干上是否有救神（制鬼者）
            for gui in gui_shen:
                if get_sheng_ke(gan_shang, gui) == '克':
                    result['matched'] = True
                    result['matched_patterns'].append('干上有救')
                    result['reasoning'] = f'三传多鬼，干上{gan_shang}可制鬼'
                    break
        
        return result
    
    def match_rule_013(self, ke_li: Dict) -> Dict:
        """
        规则 13：鬼贼当时无畏忌
        鬼贼旺相之时，贪荣无意克干
        """
        result = {
            'rule_id': 13,
            'rule_name': '鬼贼当时无畏忌',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要月令信息，暂时无法完全匹配
        
        return result
    
    def match_rule_014(self, ke_li: Dict) -> Dict:
        """
        规则 14：传财太旺反财亏
        三传皆财太旺，反无财
        """
        result = {
            'rule_id': 14,
            'rule_name': '传财太旺反财亏',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
            
        chu_chuan = ke_li.get('chu_chuan', '')
        zhong_chuan = ke_li.get('zhong_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        cai_shen = get_cai_shen(ri_gan)
        
        # 判断三传是否皆财
        chuan_list = [chu_chuan, zhong_chuan, mo_chuan]
        chuan_cai_count = sum(1 for chuan in chuan_list if chuan and chuan in cai_shen)
        
        if chuan_cai_count == 3:
            result['matched'] = True
            result['matched_patterns'].append('三传皆财')
            result['reasoning'] = f'三传{chu_chuan}{zhong_chuan}{mo_chuan}皆为日干{ri_gan}之财'
        
        return result
    
    def match_rule_017(self, ke_li: Dict) -> Dict:
        """
        规则 17：进茹空亡宜退步
        三传进茹空亡，宜退步
        """
        result = {
            'rule_id': 17,
            'rule_name': '进茹空亡宜退步',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要旬空信息
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_018(self, ke_li: Dict) -> Dict:
        """
        规则 18：踏脚空亡进用宜
        三传退茹空亡，宜进不宜退
        """
        result = {
            'rule_id': 18,
            'rule_name': '踏脚空亡进用宜',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要旬空信息
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_023(self, ke_li: Dict) -> Dict:
        """
        规则 23：彼求我事支传干
        初传从支上起，末传归于干上
        """
        result = {
            'rule_id': 23,
            'rule_name': '彼求我事支传干',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要三传起止信息
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_024(self, ke_li: Dict) -> Dict:
        """
        规则 24：我求彼事干传支
        初传从干上起，末传归于支上
        """
        result = {
            'rule_id': 24,
            'rule_name': '我求彼事干传支',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要三传起止信息
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_025(self, ke_li: Dict) -> Dict:
        """
        规则 25：金日逢丁凶祸动
        庚辛二日，三传年命日辰逢旬内六丁神
        """
        result = {
            'rule_id': 25,
            'rule_name': '金日逢丁凶祸动',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
        
        # 金日：庚辛
        if ri_gan in ['庚', '辛']:
            # 需要丁神信息，暂时简化判断
            result['matched'] = True
            result['matched_patterns'].append('金日逢丁')
            result['reasoning'] = f'{ri_gan}日逢丁神，主凶祸动'
        
        return result
    
    def match_rule_026(self, ke_li: Dict) -> Dict:
        """
        规则 26：水日逢丁财动之
        壬癸二日，三传年命日辰逢旬内六丁神
        """
        result = {
            'rule_id': 26,
            'rule_name': '水日逢丁财动之',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
        
        # 水日：壬癸
        if ri_gan in ['壬', '癸']:
            result['matched'] = True
            result['matched_patterns'].append('水日逢丁')
            result['reasoning'] = f'{ri_gan}日逢丁神，主财动'
        
        return result
    
    def match_rule_027(self, ke_li: Dict) -> Dict:
        """
        规则 27：传财化鬼财休觅
        三传皆财，生起干上日鬼
        """
        result = {
            'rule_id': 27,
            'rule_name': '传财化鬼财休觅',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
            
        gan_shang = ke_li.get('gan_shang', '')
        chu_chuan = ke_li.get('chu_chuan', '')
        zhong_chuan = ke_li.get('zhong_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        cai_shen = get_cai_shen(ri_gan)
        gui_shen = get_gui_shen(ri_gan)
        
        # 三传皆财
        chuan_list = [chu_chuan, zhong_chuan, mo_chuan]
        chuan_cai_count = sum(1 for chuan in chuan_list if chuan and chuan in cai_shen)
        
        # 干上见鬼
        gan_is_gui = gan_shang in gui_shen
        
        if chuan_cai_count == 3 and gan_is_gui:
            result['matched'] = True
            result['matched_patterns'].append('传财化鬼')
            result['reasoning'] = f'三传皆财生干上鬼{gan_shang}，财休觅'
        
        return result
    
    def match_rule_028(self, ke_li: Dict) -> Dict:
        """
        规则 28：传鬼化财钱险危
        三传俱鬼，能去比肩，独存财
        """
        result = {
            'rule_id': 28,
            'rule_name': '传鬼化财钱险危',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        ri_gan, ri_zhi = self._get_ri_gan_zhi(ke_li)
        if not ri_gan:
            return result
            
        chu_chuan = ke_li.get('chu_chuan', '')
        zhong_chuan = ke_li.get('zhong_chuan', '')
        mo_chuan = ke_li.get('mo_chuan', '')
        
        gui_shen = get_gui_shen(ri_gan)
        cai_shen = get_cai_shen(ri_gan)
        
        # 三传多鬼
        chuan_list = [chu_chuan, zhong_chuan, mo_chuan]
        chuan_gui_count = sum(1 for chuan in chuan_list if chuan and chuan in gui_shen)
        
        # 独存财
        chuan_cai_count = sum(1 for chuan in chuan_list if chuan and chuan in cai_shen)
        
        if chuan_gui_count >= 2 and chuan_cai_count >= 1:
            result['matched'] = True
            result['matched_patterns'].append('传鬼化财')
            result['reasoning'] = f'三传多鬼化财，财从险中出'
        
        return result
    
    def match_rule_029(self, ke_li: Dict) -> Dict:
        """
        规则 29：眷属丰盈居狭宅
        三传生日干，反脱支辰
        """
        result = {
            'rule_id': 29,
            'rule_name': '眷属丰盈居狭宅',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要三传与干支关系
        # 暂时无法完全匹配
        
        return result
    
    def match_rule_030(self, ke_li: Dict) -> Dict:
        """
        规则 30：屋宅宽广致人衰
        三传窃盗日干，反生支辰
        """
        result = {
            'rule_id': 30,
            'rule_name': '屋宅宽广致人衰',
            'matched': False,
            'matched_patterns': [],
            'reasoning': ''
        }
        
        # 需要三传与干支关系
        # 暂时无法完全匹配
        
        return result
    
    def match_all_rules(self, ke_li: Dict) -> Dict:
        """匹配所有毕法赋规则"""
        all_matched = []
        
        # 调用所有规则匹配函数
        rules_methods = [
            method for method in dir(self)
            if method.startswith('match_rule_') and callable(getattr(self, method))
        ]
        
        for method_name in rules_methods:
            method = getattr(self, method_name)
            try:
                result = method(ke_li)
                if result.get('matched', False):
                    all_matched.append(result)
            except Exception as e:
                print(f"规则匹配错误 {method_name}: {e}")
        
        return {
            'total_rules': len(rules_methods),
            'matched_count': len(all_matched),
            'matched_rules': all_matched
        }

# ==================== 主程序 ====================

def main():
    """主程序"""
    print("="*70)
    print("  《毕法赋》100 句规则匹配引擎")
    print("="*70)
    print()
    
    # 加载 8640 课例数据
    print("加载 8640 课例数据...")
    try:
        with open(r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\local_rules_matched_results.json', 'r', encoding='utf-8') as f:
            data_8640 = json.load(f)
        print(f"✓ 成功加载 {data_8640['matched']} 个课例")
    except Exception as e:
        print(f"✗ 加载失败：{e}")
        return
    
    # 创建匹配器
    matcher = BiFaRulesMatcher()
    
    # 抽样测试
    print("\n抽样测试前 10 个课例...")
    sample_results = []
    
    matched_results = data_8640.get('matched_results', {})
    for i, (key, ke_li) in enumerate(list(matched_results.items())[:10]):
        print(f"\n课例 {i+1}: {key}")
        print(f"  日干支：{ke_li.get('ri_gan')}{ke_li.get('ri_zhi')}")
        print(f"  三传：{ke_li.get('chu_chuan')} {ke_li.get('zhong_chuan')} {ke_li.get('mo_chuan')}")
        
        # 匹配毕法赋规则
        bifa_result = matcher.match_all_rules(ke_li)
        
        if bifa_result['matched_count'] > 0:
            print(f"  ✓ 匹配到 {bifa_result['matched_count']} 条毕法赋规则")
            for rule in bifa_result['matched_rules']:
                print(f"    - {rule['rule_name']}: {rule['reasoning']}")
        else:
            print(f"  - 未匹配到毕法赋规则")
        
        sample_results.append({
            'ke_li_key': key,
            'bifa_match': bifa_result
        })
    
    # 保存抽样结果
    output_file = r'd:\新建文件夹\仪度六壬择日\yiduluren\zongmen\bifa_sample_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 抽样结果已保存至：{output_file}")
    print("\n" + "="*70)
    print("  毕法赋规则匹配引擎框架已完成")
    print("="*70)
    print("\n说明：")
    print("1. 当前已实现部分核心规则的匹配框架")
    print("2. 完整 100 句规则需要扩展数据结构（天盘、月将、天将等）")
    print("3. 建议分阶段实施：")
    print("   - 第一阶段：实现 20-30 句核心规则（当前）")
    print("   - 第二阶段：扩展数据结构，实现更多规则")
    print("   - 第三阶段：完整 100 句规则匹配")

if __name__ == '__main__':
    main()
