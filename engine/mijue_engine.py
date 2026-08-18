#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬断案秘诀 - 规则引擎
========================
从《六壬断案秘诀》提取的核心规则，集成到择日评分和股票预测中。

内容：
  1. 求财规则（财爻/财神/传财化鬼/还魂债/破碎煞）
  2. 煞曜系统（破碎煞/刑煞）
  3. 高级课格（魁度天门/罡塞鬼户/蛇化龙/二贵引从）
  4. 旺相休囚判断
  5. 官星十二长生宫
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 基础数据结构 ──

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
TIANJIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
             '天空', '白虎', '太常', '玄武', '太阴', '天后']

# 五行
WUXING_TG = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
WUXING_DZ = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}


# ── 1. 求财规则 ──

# 财爻：日干所克之五行对应的地支
# 甲乙日 → 土(辰戌丑未), 丙丁日 → 金(申酉), 戊己日 → 水(亥子), 庚辛日 → 木(寅卯), 壬癸日 → 火(巳午)
CAI_YAO = {
    '甲': ['辰','戌','丑','未'], '乙': ['辰','戌','丑','未'],
    '丙': ['申','酉'], '丁': ['申','酉'],
    '戊': ['亥','子'], '己': ['亥','子'],
    '庚': ['寅','卯'], '辛': ['寅','卯'],
    '壬': ['巳','午'], '癸': ['巳','午'],
}

# 财神：青龙/六合为财神
CAI_SHEN = ['青龙', '六合']


def check_cai_yao(ri_gan: str, sanchuan: list, sike: list = None) -> dict:
    """检查财爻是否入课传"""
    cai = CAI_YAO.get(ri_gan, [])
    hits = [z for z in sanchuan if z in cai] if sanchuan else []
    return {
        'has_cai': len(hits) > 0,
        'cai_zhi': hits,
        'cai_count': len(hits),
        'level': '旺' if len(hits) >= 2 else ('有' if len(hits) == 1 else '无'),
    }


def check_cai_shen(tianjiang_map: dict) -> dict:
    """检查财神(青龙/六合)是否入传"""
    hits = [tj for tj in tianjiang_map.values() if tj in CAI_SHEN] if tianjiang_map else []
    return {
        'has_shen': len(hits) > 0,
        'shen_list': hits,
    }


def check_zhuan_cai_hua_gui(sanchuan: list, ri_gan: str, tianjiang_map: dict,
                            gan_shang_shen: str = '') -> dict:
    """
    传财化鬼检测：三传皆作日之财而生其干上日鬼伤其日干
    秘诀原文："三传皆作日之财而生其干上日鬼伤其日干者，必因财而致祸"
    【BUG-FIX 2026-08-18】原判据在三传中找鬼爻——财爻(日干所克)与鬼爻(克日干)
    五行互斥，三传既皆财又含鬼恒不可能 → 该规则永不触发。
    正解：三传皆财爻，且干上神为日鬼(克日干)，且财爻五行生鬼爻五行（财生鬼，鬼伤干）。
    """
    cai = CAI_YAO.get(ri_gan, [])
    if not sanchuan or len(sanchuan) < 3:
        return {'is_danger': False, 'warning': ''}

    # 三传是否都是财爻
    all_cai = all(z in cai for z in sanchuan)
    if not all_cai:
        return {'is_danger': False, 'warning': ''}

    # 干上神是否为日鬼（克日干五行）
    if not gan_shang_shen:
        return {'is_danger': False, 'warning': ''}
    today_wx = WUXING_TG.get(ri_gan, '')
    gui_wx = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}.get(today_wx, '')
    shang_wx = WUXING_DZ.get(gan_shang_shen, '')
    if shang_wx != gui_wx:
        return {'is_danger': False, 'warning': ''}

    # 三传财爻五行 生 干上鬼爻五行（财生鬼→鬼伤干→因财致祸）
    cai_wx = WUXING_DZ.get(cai[0], '')
    sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    if not cai_wx or sheng.get(cai_wx) != shang_wx:
        return {'is_danger': False, 'warning': ''}

    return {'is_danger': True,
            'warning': '⚠️ 传财化鬼：因财致祸，慎防亏损',
            'level': '大凶',
            'deduction': 25}  # 扣25分


def check_huan_hun_zhai(sanchuan: list, ri_gan: str, gan_shang_shen: str) -> dict:
    """
    还魂债检测：三传泄干气而干上得财爻
    秘诀原文："三传泄干气，而干或支上得财爻，乃三传却来生之，此去而复来，名曰还魂债"
    """
    if not sanchuan or not gan_shang_shen:
        return {'is_rebound': False, 'signal': ''}

    cai = CAI_YAO.get(ri_gan, [])
    today_wx = WUXING_TG.get(ri_gan, '')

    # 三传是否泄干气（三传五行生干五行 → 干被泄）
    # 实际：泄 = 干生出的五行在主
    xie_wx = {'木':'火','火':'土','土':'金','金':'水','水':'木'}.get(today_wx, '')
    xie_count = sum(1 for z in sanchuan if WUXING_DZ.get(z,'') == xie_wx)
    is_xie = xie_count >= 2

    # 干上神是否财爻
    gan_has_cai = gan_shang_shen in cai

    if is_xie and gan_has_cai:
        return {'is_rebound': True,
                'signal': '🔄 还魂债：去而复来，适合抄底/短线反弹',
                'level': '吉'}
    return {'is_rebound': False, 'signal': ''}


# ── 2. 煞曜系统 ──

def get_posui_sha(ri_zhi: str) -> Optional[str]:
    """
    破碎煞：寅申巳亥在酉，子午卯酉在巳，辰戌丑未在丑
    秘诀："干支上乘破碎煞者主求财不利"
    """
    if ri_zhi in '寅申巳亥': return '酉'
    if ri_zhi in '子午卯酉': return '巳'
    if ri_zhi in '辰戌丑未': return '丑'
    return None


def check_shas(ri_zhi: str, ri_gan: str, tiandi_pan: dict, tianjiang_map: dict) -> dict:
    """综合煞曜检查"""
    shas = {}
    posui = get_posui_sha(ri_zhi)
    if posui:
        shas['破碎煞'] = posui

    # 雨煞（用于择日天气预测）
    # 风煞
    # TODO: 扩展到更多煞

    # 检查破碎煞是否入课
    warnings = []
    if posui and posui in tiandi_pan.values():
        warnings.append(f'破碎煞入课({posui})，求财不利')

    return {
        'shas': shas,
        'warnings': warnings,
        'has_posui': posui is not None and posui in tiandi_pan.values(),
    }


# ── 3. 高级课格 ──

def check_kuidu_tianmen(tiandi_pan: dict, sanchuan: list) -> dict:
    """魁度天门：戌加亥为用"""
    if not sanchuan: return {'match': False}
    # 戌(天魁)在亥(天门)上
    for di, tian in (tiandi_pan or {}).items():
        if di == '亥' and tian == '戌':
            if '戌' in sanchuan[:1]:  # 戌为初传
                return {'match': True, 'name': '魁度天门', 'level': '凶',
                        'desc': '阻隔不通,安问功名', 'deduction': 20}
    return {'match': False}


def check_gangsai_guihu(tiandi_pan: dict) -> dict:
    """罡塞鬼户：辰加寅"""
    if not tiandi_pan: return {'match': False}
    tian = tiandi_pan.get('寅', '')
    if tian == '辰':
        return {'match': True, 'name': '罡塞鬼户', 'level': '大吉',
                'desc': '谋为必利,功名得意', 'bonus': 15}
    return {'match': False}


def check_she_hua_long(sanchuan_tianjiang: list) -> dict:
    """蛇化龙：初传螣蛇，末传青龙"""
    if not sanchuan_tianjiang or len(sanchuan_tianjiang) < 3:
        return {'match': False}
    if sanchuan_tianjiang[0] == '螣蛇' and sanchuan_tianjiang[-1] == '青龙':
        return {'match': True, 'name': '蛇化龙', 'level': '吉',
                'desc': '小变大,从吉之象,先凶后吉', 'bonus': 10}
    return {'match': False}


def check_long_hua_she(sanchuan_tianjiang: list) -> dict:
    """龙化蛇：初传青龙，末传螣蛇"""
    if not sanchuan_tianjiang or len(sanchuan_tianjiang) < 3:
        return {'match': False}
    if sanchuan_tianjiang[0] == '青龙' and sanchuan_tianjiang[-1] == '螣蛇':
        return {'match': True, 'name': '龙化蛇', 'level': '凶',
                'desc': '大变小,始吉终凶,不利远图', 'deduction': 15}
    return {'match': False}


# ── 4. 旺相休囚判断 ──

def get_season_from_month(yue_zhi: str) -> str:
    """月支 → 季节（四季末月辰未戌丑为土旺）"""
    if yue_zhi in ('辰', '未', '戌', '丑'):
        return '土旺'
    return {'寅':'春','卯':'春',
            '巳':'夏','午':'夏',
            '申':'秋','酉':'秋',
            '亥':'冬','子':'冬'}.get(yue_zhi, '春')

WX_SEASON_WANG = {
    '春': {'木':'旺','火':'相','土':'死','金':'囚','水':'休'},
    '夏': {'火':'旺','土':'相','金':'死','水':'囚','木':'休'},
    '秋': {'金':'旺','水':'相','木':'死','火':'囚','土':'休'},
    '冬': {'水':'旺','木':'相','火':'死','土':'囚','金':'休'},
    # 四季末月：辰未戌丑
    '土旺': {'土':'旺','金':'相','水':'死','木':'囚','火':'休'},
}

def check_wang_xiang(dizhi: str, season: str) -> str:
    """检查某地支在当季的旺衰状态"""
    wx = WUXING_DZ.get(dizhi, '')
    return WX_SEASON_WANG.get(season, {}).get(wx, '休')


# ── 5. 综合分析 ──

def analyze_with_mijue(ri_gan: str, ri_zhi: str, yue_zhi: str,
                        sanchuan: list, sike: list,
                        tiandi_pan: dict, tianjiang_map: dict,
                        sanchuan_tj: list = None,
                        gan_shang_shen: str = None) -> dict:
    """
    综合六壬断案秘诀分析
    返回: 各项规则检查结果 + 总分调整建议
    """
    result = {
        '求财': {},
        '煞曜': {},
        '课格': {},
        '旺衰': {},
        'score_adjustment': 0,
        'warnings': [],
        'signals': [],
    }

    season = get_season_from_month(yue_zhi)

    # 1. 求财规则
    cai_yao = check_cai_yao(ri_gan, sanchuan)
    cai_shen = check_cai_shen(tianjiang_map)
    zhuan_gui = check_zhuan_cai_hua_gui(sanchuan, ri_gan, tianjiang_map, gan_shang_shen)
    huan_hun = check_huan_hun_zhai(sanchuan, ri_gan, gan_shang_shen)
    result['求财'] = {
        '财爻': cai_yao,
        '财神': cai_shen,
        '传财化鬼': zhuan_gui,
        '还魂债': huan_hun,
    }

    if cai_yao['level'] == '旺':
        result['signals'].append(f"财爻旺({','.join(cai_yao['cai_zhi'])})→利求财")
        result['score_adjustment'] += 5
    elif cai_yao['level'] == '无':
        result['warnings'].append('财爻不入课传→不利求财')
        result['score_adjustment'] -= 5

    if zhuan_gui['is_danger']:
        result['warnings'].append(zhuan_gui['warning'])
        result['score_adjustment'] -= zhuan_gui.get('deduction', 25)

    if huan_hun['is_rebound']:
        result['signals'].append(huan_hun['signal'])
        result['score_adjustment'] += 10

    # 2. 煞曜
    shas = check_shas(ri_zhi, ri_gan, tiandi_pan, tianjiang_map)
    result['煞曜'] = shas
    if shas['has_posui']:
        result['warnings'].append('破碎煞入课→求财不利')
        result['score_adjustment'] -= 10

    # 3. 高级课格
    kuidu = check_kuidu_tianmen(tiandi_pan, sanchuan)
    gangsai = check_gangsai_guihu(tiandi_pan)
    shl = check_she_hua_long(sanchuan_tj)
    lhs = check_long_hua_she(sanchuan_tj)
    result['课格'] = {'魁度天门': kuidu, '罡塞鬼户': gangsai,
                      '蛇化龙': shl, '龙化蛇': lhs}

    if kuidu['match']:
        result['warnings'].append(kuidu['desc'])
        result['score_adjustment'] -= kuidu.get('deduction', 20)
    if gangsai['match']:
        result['signals'].append(gangsai['desc'])
        result['score_adjustment'] += gangsai.get('bonus', 15)
    if shl['match']:
        result['signals'].append(shl['desc'])
        result['score_adjustment'] += shl.get('bonus', 10)
    if lhs['match']:
        result['warnings'].append(lhs['desc'])
        result['score_adjustment'] -= lhs.get('deduction', 15)

    # 4. 旺衰
    if sanchuan:
        sc_ws = [(z, check_wang_xiang(z, season)) for z in sanchuan[:3]]
        result['旺衰']['三传旺衰'] = sc_ws
        wang_count = sum(1 for _, s in sc_ws if s in ['旺','相'])
        if wang_count >= 2:
            result['signals'].append('三传旺相→力量充足')
            result['score_adjustment'] += 5
        elif wang_count == 0:
            result['warnings'].append('三传休囚→力量不足')
            result['score_adjustment'] -= 5

    return result


# ── 6. 快捷接入函数（供调度器调用） ──

def apply_to_prediction(prediction_data: dict) -> dict:
    """将秘诀规则应用到一条预测上"""
    ri_gan = prediction_data.get('rizhu', '')[:1]
    ri_zhi = prediction_data.get('rizhu', '')[1:2] if len(prediction_data.get('rizhu','')) > 1 else ''
    yue_zhi = prediction_data.get('yue_zhi', '') or prediction_data.get('shichen', '午')
    sanchuan = prediction_data.get('sanchuan', [])
    sike = prediction_data.get('sike', [])
    tiandi_pan = prediction_data.get('tiandi_pan', {})
    tianjiang_map = prediction_data.get('tianjiang_map', {})
    sanchuan_tj = prediction_data.get('sanchuan_tianjiang', [])
    gan_shang = prediction_data.get('gan_shang_shen', '')

    result = analyze_with_mijue(
        ri_gan, ri_zhi, yue_zhi,
        sanchuan, sike, tiandi_pan, tianjiang_map,
        sanchuan_tj, gan_shang
    )

    # 合并结果
    prediction_data['mijue_analysis'] = result
    prediction_data['mijue_score_adjustment'] = result['score_adjustment']
    return prediction_data
