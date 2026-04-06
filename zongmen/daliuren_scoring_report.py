#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬综合评分报告生成器
基于64课经完整数据 + 禄马贵人到山向评分
"""

import sys
import os
import json

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 添加路径
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))
sys.path.insert(0, os.path.join(current_dir, 'src', 'engine'))
sys.path.insert(0, os.path.join(current_dir, 'src', 'utils'))
sys.path.insert(0, os.path.join(current_dir, 'src', 'data'))

from dizhi_layout_generator import arrange_tiandi_pan
from sike_sanchuan_engine import SiKeSanChuanCalculator
from gui_ren_engine import GuiRenCalculator

# 加载64课经数据
KE_JING_PATH = os.path.join(parent_dir, 'data', '64_ke_jing_accurate.json')
KE_JING_DATA = {}

try:
    with open(KE_JING_PATH, 'r', encoding='utf-8') as f:
        ke_jing = json.load(f)
        for k, v in ke_jing.get('courses', {}).items():
            KE_JING_DATA[v['ke_name']] = {
                'score': v.get('score', 50),
                'level': v.get('level', '中平'),
                'summary': v.get('summary', ''),
                'ke_type': v.get('ke_type', '')
            }
except Exception as e:
    print(f"加载64课经数据失败: {e}")

# 课体等级评分映射（备用）
KE_LEVEL_SCORE = {
    '上吉': 20,
    '中吉': 15,
    '中平': 10,
    '下吉': 5,
    '凶': 0
}

# 禄神
LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# 驿马
YIMA = {'申': '寅', '子': '寅', '辰': '寅', '亥': '巳', '卯': '巳', '未': '巳', '寅': '申', '午': '申', '戌': '申', '巳': '亥', '酉': '亥', '丑': '亥'}

# 山向对应
SHAN_XIANG = {'壬': '丙', '子': '午', '癸': '丁', '丑': '未', '艮': '坤', '寅': '申', '甲': '庚', '卯': '酉', '乙': '辛', '辰': '戌', '巽': '乾', '巳': '亥', '丙': '壬', '午': '子', '丁': '癸', '未': '丑', '坤': '艮', '申': '寅', '庚': '甲', '酉': '卯', '辛': '乙', '戌': '辰', '乾': '巽', '亥': '巳'}

def analyze_daliuren(shan, ri_gan, ri_zhi, yue_jiang, shi_chen):
    """大六壬综合分析"""
    
    print(f"\n{'='*60}")
    print(f"大六壬评分报告")
    print(f"{'='*60}")
    print(f"坐山: {shan} | 日干支: {ri_gan}{ri_zhi} | 月将: {yue_jiang} | 时辰: {shi_chen}")
    
    # 获取天地盘
    tiandi_pan = arrange_tiandi_pan(yue_jiang, shi_chen)
    print(f"\n天地盘: {tiandi_pan}")
    
    # 起四课三传
    calc = SiKeSanChuanCalculator()
    sike = calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
    sanchuan = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
    
    print(f"\n四课:")
    for ke in sike:
        print(f"  {ke[0]}: {ke[1]} / {ke[2]} ({ke[3]})")
    
    print(f"\n三传: 初传={sanchuan.get('初传')} | 中传={sanchuan.get('中传')} | 末传={sanchuan.get('末传')}")
    print(f"课体: {sanchuan.get('课体')} | 起法: {sanchuan.get('起法')}")
    
    # 获取贵人信息
    guiren_calc = GuiRenCalculator()
    guiren_info = guiren_calc.arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shi_chen)
    
    # 获取贵人
    guiren_data = guiren_info.get('贵人', {})
    if isinstance(guiren_data, dict):
        guiren = guiren_data.get('贵人', '')
    else:
        guiren = str(guiren_data)
    print(f"\n贵人: {guiren}")
    
    # 评分项目
    score = 0
    print(f"\n{'='*60}")
    print("评分项目")
    print(f"{'='*60}")
    
    # 1. 课体评分（基于64课经数据）
    keti = sanchuan.get('课体', '')
    ke_info = KE_JING_DATA.get(keti, {})
    ke_score = ke_info.get('score', 50)
    ke_level = ke_info.get('level', '中平')
    ke_summary = ke_info.get('summary', '')
    
    # 将课经评分转换为满分20分的评分
    if ke_score >= 80:
        item_score = 20
    elif ke_score >= 70:
        item_score = 18
    elif ke_score >= 60:
        item_score = 15
    elif ke_score >= 50:
        item_score = 10
    elif ke_score >= 40:
        item_score = 5
    else:
        item_score = 0
    
    score += item_score
    print(f"1. 课体评分: {'✓' if item_score >= 10 else '✗'} | 课体={keti} | 等级={ke_level} | 课经评分={ke_score} | 得分={item_score}")
    if ke_summary:
        print(f"   断语: {ke_summary}")
    
    # 2. 禄神到山向
    lu_zhi = LU.get(ri_gan, '')
    xiang = SHAN_XIANG.get(shan, '')
    lu_daoshan = lu_zhi == shan
    lu_daoxiang = lu_zhi == xiang
    is_lu = lu_daoshan or lu_daoxiang
    item_score = 15 if is_lu else 0
    score += item_score
    print(f"2. 禄神到山向: {'✓ 达标' if is_lu else '✗ 未达标'} | 禄神={lu_zhi} | 山={shan} 向={xiang} | 得分={item_score}")
    
    # 3. 驿马到山向
    ma_zhi = YIMA.get(ri_zhi, '')
    ma_daoshan = ma_zhi == shan
    ma_daoxiang = ma_zhi == xiang
    is_ma = ma_daoshan or ma_daoxiang
    item_score = 15 if is_ma else 0
    score += item_score
    print(f"3. 驿马到山向: {'✓ 达标' if is_ma else '✗ 未达标'} | 驿马={ma_zhi} | 山={shan} 向={xiang} | 得分={item_score}")
    
    # 4. 贵人到山向
    tianjiang_map = guiren_info.get('天将映射', {})
    guiren_pos = None
    for zhi, tj in tianjiang_map.items():
        if tj == '贵人':
            guiren_pos = zhi
            break
    guiren_daoshan = guiren_pos == shan
    guiren_daoxiang = guiren_pos == xiang
    is_guiren = guiren_daoshan or guiren_daoxiang
    item_score = 20 if is_guiren else 0
    score += item_score
    print(f"4. 贵人到山向: {'✓ 达标' if is_guiren else '✗ 未达标'} | 贵人位置={guiren_pos} | 山={shan} 向={xiang} | 得分={item_score}")
    
    # 5. 三传夹贵
    chu = sanchuan.get('初传', '')
    zhong = sanchuan.get('中传', '')
    mo = sanchuan.get('末传', '')
    chu_tj = tianjiang_map.get(chu, '')
    zhong_tj = tianjiang_map.get(zhong, '')
    mo_tj = tianjiang_map.get(mo, '')
    is_jiagui = chu_tj == '贵人' or zhong_tj == '贵人' or mo_tj == '贵人'
    item_score = 15 if is_jiagui else 0
    score += item_score
    print(f"5. 三传夹贵: {'✓ 达标' if is_jiagui else '✗ 未达标'} | 初传天将={chu_tj} 中传天将={zhong_tj} 末传天将={mo_tj} | 得分={item_score}")
    
    # 总分
    print(f"\n{'='*60}")
    print(f"总分: {score}/85")
    if score >= 50:
        print("评估: 优秀")
    elif score >= 30:
        print("评估: 合格")
    elif score >= 15:
        print("评估: 基本合格")
    else:
        print("评估: 不合格")
    print(f"{'='*60}")
    
    return score

if __name__ == '__main__':
    print("大六壬综合评分测试")
    
    test_cases = [
        {'shan': '壬', 'ri_gan': '甲', 'ri_zhi': '寅', 'yue_jiang': '亥', 'shi_chen': '子'},
        {'shan': '壬', 'ri_gan': '丙', 'ri_zhi': '子', 'yue_jiang': '亥', 'shi_chen': '子'},
        {'shan': '艮', 'ri_gan': '甲', 'ri_zhi': '寅', 'yue_jiang': '亥', 'shi_chen': '子'},
    ]
    
    for tc in test_cases:
        analyze_daliuren(tc['shan'], tc['ri_gan'], tc['ri_zhi'], tc['yue_jiang'], tc['shi_chen'])
