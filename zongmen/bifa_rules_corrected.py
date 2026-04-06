#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毕法赋规则修正版
根据用户解释修正规则17、23、24的判断逻辑
"""

from typing import Dict, List, Any, Optional, Tuple
from daliuren_base import (
    get_xun, get_kong_wang, get_ding_shen, get_lu_shen,
    get_gui_shen, get_cai_shen, get_zhang_sheng,
    get_yin_yang, get_wu_xing, get_sheng_ke,
    enhance_ke_li_data, get_nian_zhi, get_sang_men, get_diao_ke,
    get_tian_jiang_ke_ri, get_ke_ti_ge_ju, TIAN_JIANG_JI_XIONG,
    TIAN_JIANG_WU_XING, DI_ZHI
)

RI_GAN_JI_GONG = {
    '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子'
}

def match_rule_017_corrected(ke_li: Dict) -> Dict:
    """
    规则 17：进茹空亡宜退步（修正版）
    
    用户解释：
    - 初传不空，末传空旬空或乘天将天空
    - 专指预测时，想做事，看可不可去做
    """
    result = {'rule_id': 17, 'rule_name': '进茹空亡宜退步', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
    
    ri_gan_zhi = ke_li.get('ri_gan_zhi', '')
    if not ri_gan_zhi:
        return result
    
    kong_wang = get_kong_wang(ri_gan_zhi)
    chuan_list = [ke_li.get('chu_chuan', ''), ke_li.get('zhong_chuan', ''), ke_li.get('mo_chuan', '')]
    
    if not all(chuan_list):
        return result
    
    chu_chuan = chuan_list[0]
    mo_chuan = chuan_list[2]
    
    chu_tian_jiang = ke_li.get('chu_tian_jiang', '')
    mo_tian_jiang = ke_li.get('mo_tian_jiang', '')
    
    chu_kong = chu_chuan in kong_wang
    mo_kong = mo_chuan in kong_wang
    mo_sky = mo_tian_jiang == '天空'
    
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


def match_rule_023_corrected(ke_li: Dict) -> Dict:
    """
    规则 23：彼求我事支传干（修正版）
    
    用户解释：
    - 别人找我办事会出现日支（第三课）是日干上神
    - 即：支上神 = 干上神
    """
    result = {'rule_id': 23, 'rule_name': '彼求我事支传干', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
    
    ri_gan, ri_zhi = ke_li.get('ri_gan_zhi', '')[:1], ke_li.get('ri_gan_zhi', '')[1:] if ke_li.get('ri_gan_zhi') else ('', '')
    if not ri_gan:
        return result
    
    gan_shang = ke_li.get('gan_shang', '')
    zhi_shang = ke_li.get('zhi_shang', '')
    
    if gan_shang and zhi_shang and gan_shang == zhi_shang:
        result['matched'] = True
        result['matched_patterns'].append('支上神即干上神')
        result['reasoning'] = f'支上神{zhi_shang}即干上神{gan_shang}，彼求我事'
    
    return result


def match_rule_024_corrected(ke_li: Dict) -> Dict:
    """
    规则 24：我求彼事干传支（修正版）
    
    用户解释：
    - 我求别人办事，会出现日干寄宫的地支为第三课日支上神
    - 即：日干寄宫地支 = 支上神
    """
    result = {'rule_id': 24, 'rule_name': '我求彼事干传支', 'matched': False, 'matched_patterns': [], 'reasoning': ''}
    
    ri_gan, ri_zhi = ke_li.get('ri_gan_zhi', '')[:1], ke_li.get('ri_gan_zhi', '')[1:] if ke_li.get('ri_gan_zhi') else ('', '')
    if not ri_gan:
        return result
    
    ji_gong = RI_GAN_JI_GONG.get(ri_gan, '')
    zhi_shang = ke_li.get('zhi_shang', '')
    
    if ji_gong and zhi_shang and ji_gong == zhi_shang:
        result['matched'] = True
        result['matched_patterns'].append('干寄宫即支上神')
        result['reasoning'] = f'日干{ri_gan}寄宫{ji_gong}即支上神{zhi_shang}，我求彼事'
    
    return result


if __name__ == '__main__':
    print("毕法赋规则修正版")
    print("=" * 60)
    print("\n修正的规则:")
    print("  规则17: 进茹空亡宜退步")
    print("    - 修正: 初传不空，末传空旬空或乘天将天空")
    print("  规则23: 彼求我事支传干")
    print("    - 修正: 支上神 = 干上神")
    print("  规则24: 我求彼事干传支")
    print("    - 修正: 日干寄宫地支 = 支上神")
    print("=" * 60)
