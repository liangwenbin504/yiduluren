#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试禄马贵人到山到向评分系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen', 'src', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zongmen', 'src', 'data'))

from datetime import datetime, timedelta
import json

def test_luma_guiren_scoring():
    """测试禄马贵人到山到向评分系统"""
    
    from sizhu_engine import get_sizhu
    from dizhi_layout_generator import arrange_tiandi_pan
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    from gui_ren_engine import GuiRenCalculator
    
    LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
    YIMA = {'申': '寅', '子': '寅', '辰': '寅', '亥': '巳', '卯': '巳', '未': '巳', '寅': '申', '午': '申', '戌': '申', '巳': '亥', '酉': '亥', '丑': '亥'}
    
    SHAN_JIA_MAP = {
        '壬': '子', '子': '子',
        '癸': '子', '丑': '子',
        '艮': '丑', '寅': '丑',
        '甲': '卯', '卯': '卯',
        '乙': '卯', '辰': '卯',
        '巽': '辰', '巳': '辰',
        '丙': '午', '午': '午',
        '丁': '午', '未': '午',
        '坤': '未', '申': '未',
        '庚': '酉', '酉': '酉',
        '辛': '酉', '戌': '酉',
        '乾': '戌', '亥': '戌'
    }
    
    XIANG_SHOU_MAP = {
        '壬': '午', '子': '午',
        '癸': '午', '丑': '午',
        '艮': '未', '寅': '未',
        '甲': '酉', '卯': '酉',
        '乙': '酉', '辰': '酉',
        '巽': '戌', '巳': '戌',
        '丙': '子', '午': '子',
        '丁': '子', '未': '子',
        '坤': '丑', '申': '丑',
        '庚': '卯', '酉': '卯',
        '辛': '卯', '戌': '卯',
        '乾': '辰', '亥': '辰'
    }
    
    ke_jing_path = os.path.join(os.path.dirname(__file__), 'data', '64_ke_jing_accurate.json')
    ke_jing_data = {}
    with open(ke_jing_path, 'r', encoding='utf-8') as f:
        ke_jing = json.load(f)
        for k, v in ke_jing.get('courses', {}).items():
            ke_jing_data[v['ke_name']] = v
    
    mountain = '壬'
    shan_jia = SHAN_JIA_MAP.get(mountain, '子')
    xiang_shou = XIANG_SHOU_MAP.get(mountain, '午')
    
    print("=" * 80)
    print(f"测试禄马贵人到山到向评分系统")
    print(f"山: {mountain} | 山家: {shan_jia} | 向首: {xiang_shou}")
    print("=" * 80)
    
    test_dates = [
        (2025, 1, 15),
        (2025, 2, 8),
        (2025, 3, 21),
        (2025, 4, 5),
        (2025, 5, 12),
    ]
    
    def get_guiren_pos(tian_gan, tiandi_pan, shichen):
        try:
            gui_ren_calc = GuiRenCalculator()
            guiren_info = gui_ren_calc.arrange_gui_ren_pan(tian_gan, {'天地对应': tiandi_pan}, shichen)
            tianjiang_map = guiren_info.get('天将映射', {})
            for zhi, tj in tianjiang_map.items():
                if tj == '贵人':
                    return zhi
        except:
            pass
        return None
    
    def check_luma_guiren(tian_gan, di_zhi, tiandi_pan, shichen, shan_jia, xiang_shou):
        lu_zhi = LU.get(tian_gan, '')
        ma_zhi = YIMA.get(di_zhi, '')
        guiren_zhi = get_guiren_pos(tian_gan, tiandi_pan, shichen)
        
        lu_to_shan = (lu_zhi == shan_jia)
        lu_to_xiang = (lu_zhi == xiang_shou)
        ma_to_shan = (ma_zhi == shan_jia)
        ma_to_xiang = (ma_zhi == xiang_shou)
        guiren_to_shan = (guiren_zhi == shan_jia)
        guiren_to_xiang = (guiren_zhi == xiang_shou)
        
        shan_count = sum([lu_to_shan, ma_to_shan, guiren_to_shan])
        xiang_count = sum([lu_to_xiang, ma_to_xiang, guiren_to_xiang])
        
        return {
            'lu_zhi': lu_zhi,
            'ma_zhi': ma_zhi,
            'guiren_zhi': guiren_zhi,
            'lu_to_shan': lu_to_shan,
            'lu_to_xiang': lu_to_xiang,
            'ma_to_shan': ma_to_shan,
            'ma_to_xiang': ma_to_xiang,
            'guiren_to_shan': guiren_to_shan,
            'guiren_to_xiang': guiren_to_xiang,
            'shan_count': shan_count,
            'xiang_count': xiang_count,
        }
    
    def calc_qualification_coeff(count):
        if count >= 3:
            return 2.0
        elif count >= 2:
            return 1.5
        elif count >= 1:
            return 1.0
        else:
            return 0.0
    
    results = []
    
    for year, month, day in test_dates:
        for shichen_idx in range(12):
            shichen = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][shichen_idx]
            
            sizhu_result = get_sizhu(year, month, day, shichen)
            if not sizhu_result:
                continue
            
            sizhu = {
                '年柱': sizhu_result['年柱'],
                '月柱': sizhu_result['月柱'],
                '日柱': sizhu_result['日柱'],
                '时柱': sizhu_result['时柱']
            }
            
            ri_gan = sizhu['日柱'][0]
            ri_zhi = sizhu['日柱'][1]
            nian_gan = sizhu['年柱'][0]
            nian_zhi = sizhu['年柱'][1]
            yue_gan = sizhu['月柱'][0]
            yue_zhi = sizhu['月柱'][1]
            
            tiandi_pan = arrange_tiandi_pan('亥', shichen)
            calc = SiKeSanChuanCalculator()
            sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            sanchuan = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            
            keti = sanchuan.get('课体', '')
            ke_info = ke_jing_data.get(keti, {})
            base_ke_score = ke_info.get('score', 50)
            
            ri_result = check_luma_guiren(ri_gan, ri_zhi, tiandi_pan, shichen, shan_jia, xiang_shou)
            nian_result = check_luma_guiren(nian_gan, nian_zhi, tiandi_pan, shichen, shan_jia, xiang_shou)
            yue_result = check_luma_guiren(yue_gan, yue_zhi, tiandi_pan, shichen, shan_jia, xiang_shou)
            
            ri_shan_coeff = calc_qualification_coeff(ri_result['shan_count'])
            ri_xiang_coeff = calc_qualification_coeff(ri_result['xiang_count'])
            ri_coeff = max(ri_shan_coeff, ri_xiang_coeff)
            
            nian_shan_coeff = calc_qualification_coeff(nian_result['shan_count'])
            nian_xiang_coeff = calc_qualification_coeff(nian_result['xiang_count'])
            nian_coeff = max(nian_shan_coeff, nian_xiang_coeff)
            
            yue_shan_coeff = calc_qualification_coeff(yue_result['shan_count'])
            yue_xiang_coeff = calc_qualification_coeff(yue_result['xiang_count'])
            yue_coeff = max(yue_shan_coeff, yue_xiang_coeff)
            
            time_coeff = 1.0
            if nian_coeff > 0:
                time_coeff *= 1.8
            if yue_coeff > 0:
                time_coeff *= 1.5
            if ri_coeff > 0:
                time_coeff *= 1.2
            
            shan_qual_coeff = calc_qualification_coeff(
                (1 if ri_result['lu_to_shan'] else 0) +
                (1 if ri_result['ma_to_shan'] else 0) +
                (1 if ri_result['guiren_to_shan'] else 0)
            )
            xiang_qual_coeff = calc_qualification_coeff(
                (1 if ri_result['lu_to_xiang'] else 0) +
                (1 if ri_result['ma_to_xiang'] else 0) +
                (1 if ri_result['guiren_to_xiang'] else 0)
            )
            
            shan_score = base_ke_score * shan_qual_coeff * time_coeff if shan_qual_coeff > 0 else 0
            xiang_score = base_ke_score * xiang_qual_coeff * time_coeff if xiang_qual_coeff > 0 else 0
            
            if shan_score > 0 and xiang_score > 0:
                daliuren_score = round((shan_score + xiang_score) / 2)
            elif shan_score > 0:
                daliuren_score = round(shan_score)
            elif xiang_score > 0:
                daliuren_score = round(xiang_score)
            else:
                daliuren_score = round(base_ke_score * 0.5)
            
            daliuren_score = min(100, daliuren_score)
            
            results.append({
                'date': f"{year}-{month:02d}-{day:02d} {shichen}时",
                'sizhu': sizhu,
                'keti': keti,
                'base_ke_score': base_ke_score,
                'ri_lu': ri_result['lu_zhi'],
                'ri_ma': ri_result['ma_zhi'],
                'ri_guiren': ri_result['guiren_zhi'] or '无',
                'ri_shan_count': ri_result['shan_count'],
                'ri_xiang_count': ri_result['xiang_count'],
                'nian_count': max(nian_result['shan_count'], nian_result['xiang_count']),
                'yue_count': max(yue_result['shan_count'], yue_result['xiang_count']),
                'shan_score': round(shan_score, 1),
                'xiang_score': round(xiang_score, 1),
                'time_coeff': round(time_coeff, 2),
                'final_score': daliuren_score
            })
    
    results.sort(key=lambda x: x['final_score'], reverse=True)
    
    print("\n【评分结果（按分数排序）】\n")
    print(f"{'日期':<18} {'四柱':<22} {'课体':<10} {'基础分':<6} {'日禄':<4} {'日马':<4} {'日贵':<4} {'到山':<4} {'到向':<4} {'年':<3} {'月':<3} {'时间系数':<6} {'最终分':<6}")
    print("-" * 120)
    
    for r in results[:20]:
        sizhu_str = f"{r['sizhu']['年柱']}{r['sizhu']['月柱']}{r['sizhu']['日柱']}{r['sizhu']['时柱']}"
        print(f"{r['date']:<18} {sizhu_str:<22} {r['keti']:<10} {r['base_ke_score']:<6} {r['ri_lu']:<4} {r['ri_ma']:<4} {r['ri_guiren']:<4} {r['ri_shan_count']:<4} {r['ri_xiang_count']:<4} {r['nian_count']:<3} {r['yue_count']:<3} {r['time_coeff']:<6} {r['final_score']:<6}")
    
    print("\n" + "=" * 80)
    print("【评分公式说明】")
    print("=" * 80)
    print("1. 基础定义：壬山丙向，壬子为山家一组，丙午为向首一组")
    print("2. 合格标准：日贵人/日禄/日马至少一项落到子山或午向")
    print("3. 评分梯度：单项=1x, 两项=1.5x, 三项=2x")
    print("4. 时间维度：年柱×1.8（太岁力量最大），月柱×1.5（月令力量大），日柱×1.2，连乘计算")
    print("5. 最终分值 = 基础分值 × 合格项系数 × 时间维度系数")
    print("6. 山向两组分别计算后取平均值")
    print("=" * 80)
    
    high_score_count = sum(1 for r in results if r['final_score'] >= 70)
    print(f"\n统计: 共测试 {len(results)} 个时辰，其中 {high_score_count} 个达到70分以上")

if __name__ == '__main__':
    test_luma_guiren_scoring()
