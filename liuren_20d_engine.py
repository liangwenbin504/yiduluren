#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬20天周期预测引擎 v3.0
==============================
整合统一训练库 + 64课经股市判断
"""

import json, os, re, sys
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
LIUREN_DATA = BASE / "liuren_20d_data"
os.makedirs(MEMORY, exist_ok=True)
os.makedirs(LIUREN_DATA, exist_ok=True)

# ── 股票路径永久关闭「六亲(十神)」信号组 ──
# 依据诚实评估结论：六亲在股票域方向预测贡献≈零(消融Δ≈0)，属死重，清除之。
# 仅作用于股票预测路径（本模块）；古例验证引擎(ancient_backtest)不 import 本模块，
# 且 ancient_backtest 顶部显式 pop 该 env，故古例 90.9% 验证器的六亲保持启用。
# 若某回测脚本需重新开启六亲，可在 import 本模块后 os.environ.pop('DISABLE_LIUQIN')。
os.environ['DISABLE_LIUQIN'] = '1'

# ── 股票路径永久关闭「股票 valence」信号组（2026-07-30 定稿）──
# 实证：股票域开启 valence（设计内 extract_stock_valence + 误置的 _shen_sha_valence）
# 拖 M3 49.34%(p=0.339 近随机, 看跌偏置56%) → 关闭后 52.35%(p=0.001 显著, 看跌偏置20%)。
# 故股票路径禁用全部 valence 注入，方向预测只走课体/毕法/三传/特殊课格等原生信号组。
# 古例验证引擎(ancient_backtest)不 import 本模块，其 valence 不受影响。
os.environ['DISABLE_STOCK_VALENCE'] = '1'

SHICHEN_MAP = {0:'子',1:'丑',2:'寅',3:'卯',4:'辰',5:'巳',6:'午',7:'未',8:'申',9:'酉',10:'戌',11:'亥'}
CYCLE_DAYS = 20

from engine.liuren_scoring_config import (
    get_keti_level_score, get_liuqin_score, get_wangshuai_score,
    get_kongwang_score, get_zhuyin_score,
    get_tianjiang_combo_score, get_tianjiang_xiong_count_score,
    get_changsheng_score, get_changsheng_kong_score,
    get_double_line_score, calculate_confidence, get_trend_prediction,
    DAXIONG_EXTRA_DEDUCTION,
)
from engine.sanchuan_kege import SanChuanKegeDetector, get_sanchuan_kege_summary
from engine.bifa_detector import BiFaDetector, get_bifa_summary
from engine.special_kege import SpecialKegeDetector, get_kege_summary
from engine.liuren_keti_bifa import build_keti_duanyu  # Task #212：股票路径单源化，统一调用 build_keti_duanyu
from engine.multi_angle_analyzer import MultiAngleAnalyzer, multi_angle_score

# 五行映射（用于 reasoning_chain 构建）
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_WX = {'寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土',
          '申': '金', '酉': '金', '戌': '土', '亥': '水', '子': '水', '丑': '土'}

# 加载课格股市规则
def _load_keti_stock_rules():
    f = BASE / "_memory" / "keti_stock_rules.json"
    if f.exists():
        with open(f, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return {}

KETI_STOCK_RULES = _load_keti_stock_rules()


def get_liuren_20d_signal(target_date=None, shichen=None, yuejiang=None):
    tz_beijing = timezone(timedelta(hours=8))
    if target_date is None:
        target_date = datetime.now(tz_beijing)
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=tz_beijing)
    if shichen is None:
        shichen = SHICHEN_MAP[target_date.hour // 2]
    
    year, month, day, hour = target_date.year, target_date.month, target_date.day, target_date.hour
    
    from engine.yuejiang_engine import YueJiangCalculator
    yj_calc = YueJiangCalculator()
    if yuejiang:
        yj_name = yj_calc.YUE_JIANG_NAMES.get(yuejiang, yuejiang)
    else:
        yuejiang, yj_name = yj_calc.get_yuejiang_by_date(year, month, day, hour)
    
    from engine.sizhu_engine import get_day_ganzhi, get_month_ganzhi
    ri_gan, ri_zhi = get_day_ganzhi(year, month, day)
    
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    ssc2 = SiKeSanChuanCalculator2()
    calc_result = ssc2.calculate(ri_gan, ri_zhi, yuejiang, shichen)
    tiandi_pan = calc_result['tiandi_pan']
    si_ke = calc_result['sike']
    san_chuan_result = calc_result['sanchuan']
    
    keti = san_chuan_result.get('课体', '')
    qifa = san_chuan_result.get('起法', '')
    san_chuan_list = [san_chuan_result.get('初传', ''), san_chuan_result.get('中传', ''), san_chuan_result.get('末传', '')]
    
    # 12维度分析
    from engine.liuren_analysis_engine import LiurenAnalysisEngine
    analyzer = LiurenAnalysisEngine()
    sanchuan_dict = {'初传': san_chuan_list[0] if len(san_chuan_list) > 0 else '',
                     '中传': san_chuan_list[1] if len(san_chuan_list) > 1 else '',
                     '末传': san_chuan_list[2] if len(san_chuan_list) > 2 else ''}
    sike_for_analysis = [(sk[2], sk[1]) if len(sk) >= 3 else ('','') for sk in si_ke]
    
    nian_zhi = {'2026':'午','2025':'巳','2027':'未'}.get(str(year), '午')
    # 节气月建（修正：用节气月建而非公历月份判断旺衰；2026-07-30 实为未月→土旺）
    yuejian_zhi = get_month_ganzhi(year, month, day)[1]
    full_analysis = {}
    try:
        full_analysis = analyzer.analyze(ri_gan=ri_gan, ri_zhi=ri_zhi, sanchuan=sanchuan_dict,
            sike=sike_for_analysis, tiandi_pan=tiandi_pan or {}, yue_jiang=yuejiang, shi_chen=shichen,
            lunar_month=month, nian_zhi=nian_zhi, yuejian_zhi=yuejian_zhi, ri_gan_zhi=ri_gan+ri_zhi)
    except: pass
    
    xun_kong = full_analysis.get('旬空', analyzer.get_xun_kong(ri_gan+ri_zhi))
    kong_info = {}
    for i, chuan in enumerate(['初传','中传','末传']):
        if i < len(san_chuan_list): kong_info[chuan] = analyzer.is_kong_wang(san_chuan_list[i], ri_gan+ri_zhi)
    def _base_of(z, tdp):
        for d, t in (tdp or {}).items():
            if t == z:
                return d
        return None
    wangshuai_list = [{'地支':z, '旺衰':analyzer.get_zhi_wang_shuai_by_yuejian(z, yuejian_zhi, _base_of(z, tiandi_pan))} for z in san_chuan_list]
    liuqin_list = full_analysis.get('六亲分析', analyzer.get_liuqin_analysis(ri_gan, san_chuan_list))
    
    relationships = []
    for i in range(len(san_chuan_list)-1):
        a, b = san_chuan_list[i], san_chuan_list[i+1]
        rel = analyzer.analyze_pair_relationship(a, b, f'传{i+1}', f'传{i+2}')
        relationships.append({'from':a,'to':b,'五行关系':rel.get('五行关系',''),'六合':rel.get('六合',''),'六冲':rel.get('六冲',''),'三刑':rel.get('三刑',''),'六害':rel.get('六害','')})
    
    sike_qi_analysis = full_analysis.get('四课加临', {})
    ysa = full_analysis.get('用神分析', {})
    yong_shen_analysis = {'分析':str(ysa.get('分析',''))[:200], '吉凶':ysa.get('吉凶',''), '用神':ysa.get('用神',''), '旺衰':ysa.get('旺衰','')} if ysa else {}
    sanchuan_zhijiu = full_analysis.get('三传制救', {})
    guishen_jixiong = full_analysis.get('贵神吉凶', {})
    ba_sha = full_analysis.get('八杀分析', {})
    cai_analysis = full_analysis.get('十二气财星', {})
    shen_qiang_ruo = full_analysis.get('身强身弱分析', {})
    shen_sha = full_analysis.get('神煞', {})
    
    # 天将计算
    from engine.gui_ren_engine import GuiRenCalculator
    gui_calc = GuiRenCalculator()
    gui_ren_result = gui_calc.arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shichen)
    tian_jiang_map = gui_ren_result.get('天将映射', {})
    tianjiang_list = [tian_jiang_map.get(z, '') for z in san_chuan_list]
    tianjiang_detail = {'初传':tianjiang_list[0] if tianjiang_list else '','中传':tianjiang_list[1] if len(tianjiang_list)>1 else '','末传':tianjiang_list[2] if len(tianjiang_list)>2 else '','贵人':gui_ren_result.get('贵人',''),'昼夜':gui_ren_result.get('昼夜',''),'顺逆':gui_ren_result.get('顺逆','')}
    
    from engine.liuren_stock_rules import StockLiuRenRules
    stock_analysis = StockLiuRenRules.judge_trend(si_ke, san_chuan_list, tianjiang_list)
    
    # 训练库课体
    from engine.liuren_keti_duanyu import LiuRenKetiDuanyu
    from engine.liuren_64ke_v2 import get_keti_info as get_64ke_info, get_keti_level as get_64ke_level
    keti_duanyu_engine = LiuRenKetiDuanyu()
    keti_raw = keti.split('，')[0].strip()
    keti_key = keti_raw.replace('课', '').strip()
    keti_duanyu = keti_duanyu_engine.get_keti_duanyu(keti_raw)
    ke_64_info = get_64ke_info(keti_key) or get_64ke_info(keti_raw)
    ke_64_level_name, ke_64_deduction, ke_64_is_daxiong = (get_64ke_level(keti_key) if keti_key else get_64ke_level(keti_raw))
    
    # 涨跌预测
    trend_score = 0; trend_reasons = []

    # 阳/阴不备：四课有相同两课（本课 课二=课三）→ 明面因素不具体，涨的因素不具备
    def _ke_pair(a, b):
        if not a or not b or len(a) < 3 or len(b) < 3: return False
        return (a[1], a[2]) == (b[1], b[2])
    bubei_pairs = []
    for i in range(len(si_ke)):
        for j in range(i+1, len(si_ke)):
            if _ke_pair(si_ke[i], si_ke[j]):
                bubei_pairs.append((i+1, j+1))
    if bubei_pairs:
        _plabel = '、'.join(f'课{a}=课{b}' for a,b in bubei_pairs)
        _blabel = '阴不备' if (2,3) in bubei_pairs else ('阳不备' if (1,4) in bubei_pairs else '不备')
        trend_score += -4
        trend_reasons.append(f'[{_blabel}] 四课{_plabel}相同，明面因素不具备，涨的因素不具备(-4)')
    keti_level = keti_duanyu.get('等级', '平')
    keti_level_score = get_keti_level_score(keti_level); trend_score += keti_level_score
    if keti_level_score != 0: trend_reasons.append(f'课体{keti_raw}({keti_level})({keti_level_score:+d})')
    if ke_64_is_daxiong: trend_score += DAXIONG_EXTRA_DEDUCTION; trend_reasons.append(f'64大凶({DAXIONG_EXTRA_DEDUCTION:+d})')
    
    keti_detail = {'keti_name':keti_raw,'level':keti_level,'duanyu':keti_duanyu.get('断语',''),'zonglun':keti_duanyu.get('详细断语',{}).get('总论',''),'ke_64_level':ke_64_level_name,'ke_64_xiangyue':ke_64_info.get('象曰','') if ke_64_info else '','ke_64_definition':ke_64_info.get('定义','') if ke_64_info else '','is_daxiong':ke_64_is_daxiong}
    
    # 六亲(十神) 打分 —— 消融开关 DISABLE_LIUQIN（env 置非空则跳过，与融合层一致）
    if not os.environ.get('DISABLE_LIUQIN'):
        for item in liuqin_list: s=get_liuqin_score(item['六亲']); trend_score+=s; trend_reasons.append(f'{item["地支"]}为{item["六亲"]}({s:+d})')
    for item in wangshuai_list: trend_score+=get_wangshuai_score(item['旺衰'])
    if kong_info.get('末传',False): s=get_kongwang_score('末传'); trend_score+=s; trend_reasons.append(f'末传落空亡({s:+d})')
    
    # 通用课格判断
    chu_chuan = san_chuan_list[0] if san_chuan_list else ''
    zhong_chuan = san_chuan_list[1] if len(san_chuan_list)>1 else ''
    mo_chuan = san_chuan_list[2] if len(san_chuan_list)>2 else ''
    # 股市课格规则主用 _memory/keti_stock_rules.json（KETI_STOCK_RULES）。
    # P4（2026-08-15）：删除 knowledge fallback 死代码（liuren_64ke_knowledge 无"股市判断"字段，永不生效）。
    stock_rules = KETI_STOCK_RULES.get(keti_key, {})
    
    if stock_rules:
        nd = stock_rules.get('正常',''); m=re.search(r'\(([+-]?\d+)\)', nd)
        if m: ns=int(m.group(1)); trend_score+=ns; trend_reasons.append(f'课格{keti_key}({ns:+d})')
        mk=mo_k=kong_info.get('末传',False); zk=zhong_k=kong_info.get('中传',False); ck=chu_k=kong_info.get('初传',False); hk=mk or zk or ck
        for rk, rd in stock_rules.items():
            if rk=='正常': continue
            rm=re.search(r'\(([+-]?\d+)\)', rd)
            if not rm: continue
            rs=int(rm.group(1)); ap=False
            if '铸印' in rk or '破模' in rk or '破印' in rk:
                iz=(chu_chuan in ('卯','巳') and zhong_chuan=='戌' and mo_chuan in ('巳','卯'))
                if iz and ((mk and '末' in rk) or (zk and '中' in rk) or (ck and '初' in rk)): ap=True
            elif '空' in rk and hk: ap=True
            elif '失明' in rk or '不泰' in rk:
                if hk: ap=True
            elif '见机' in rk and chu_chuan in ('寅','申','巳','亥'): ap=True
            elif '察微' in rk and chu_chuan in ('子','午','卯','酉'): ap=True
            if ap: trend_score+=rs; keti=keti+'，'+rk; trend_reasons.append(f'子课格{rk}({rs:+d})')
    
    # 天将判断
    tianjiang_xiong_count=0; tianjiang_xiong_list=[]
    if chu_chuan=='卯' and zhong_chuan=='戌' and mo_chuan=='巳':
        tianjiang_xiong_count=3; tianjiang_xiong_list=['天后','勾陈','玄武']
        s=get_tianjiang_combo_score('后勾玄'); trend_score+=s; trend_reasons.append(f'后勾玄({s:+d})')
    trend_score+=get_tianjiang_xiong_count_score(tianjiang_xiong_count)

    # 三传天将吉凶计入（天将亦为判断吉凶标准之一）
    TIANJIANG_SCORE = {'贵人':1,'青龙':1,'六合':1,'太常':1,'天后':1,'太阴':1,'朱雀':0,'勾陈':-1,'螣蛇':-1,'白虎':-2,'玄武':-1,'天空':-1}
    for _i, _tj in enumerate(tianjiang_list):
        _s = TIANJIANG_SCORE.get(_tj, 0)
        if _s != 0:
            trend_score += _s
            trend_reasons.append(f'三传{["初传","中传","末传"][_i]}天将{_tj}({_s:+d})')
    
    # 十二长生
    gw={'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    rw=gw.get(ri_gan,'金'); wcs={'金':'巳','木':'亥','火':'寅','水':'申','土':'申'}; wdw={'金':'酉','木':'卯','火':'午','水':'子','土':'子'}
    cs=wcs.get(rw,'巳'); dw=wdw.get(rw,'酉')
    if cs in san_chuan_list:
        pos=san_chuan_list.index(cs); ik=kong_info.get(['初传','中传','末传'][pos],False)
        if ik: s=get_changsheng_kong_score('长生'); trend_score+=s; trend_reasons.append(f'长生空亡({s:+d})')
        else: s=get_changsheng_score('长生'); trend_score+=s; trend_reasons.append(f'长生入传({s:+d})')
    if dw in san_chuan_list:
        pos=san_chuan_list.index(dw); ik=kong_info.get(['初传','中传','末传'][pos],False)
        if not ik: s=get_changsheng_score('帝旺'); trend_score+=s; trend_reasons.append(f'帝旺入传({s:+d})')
    
    # 双线
    l1x=('铸印破模' in keti or '铸印破印' in keti or tianjiang_xiong_count>=2)
    l1j=('铸印' in keti and '破' not in keti and tianjiang_xiong_count==0)
    l2x=cs in san_chuan_list and kong_info.get(['初传','中传','末传'][san_chuan_list.index(cs)],False)
    l2j=cs in san_chuan_list and not kong_info.get(['初传','中传','末传'][san_chuan_list.index(cs)],False)
    if l1x and l2x: s=get_double_line_score('双线凶煞'); trend_score+=s; trend_reasons.append(f'双线凶煞({s:+d})')
    elif l1j and l2j: s=get_double_line_score('双线吉庆'); trend_score+=s; trend_reasons.append(f'双线吉庆({s:+d})')
    
    # 统一训练库
    from unified_trainer import get_trainer
    trainer=get_trainer(); evo_boost=0; sc_match_count=0; sc_key=' '.join(san_chuan_list[:3])
    if trainer.case_kb:
        sm=trainer.case_kb.get('by_sanchuan',{}).get(sc_key,0)
        sc_match_count=len(sm) if isinstance(sm,list) else (sm if isinstance(sm,int) else 0)
        if sc_match_count>=5: evo_boost+=3; trend_reasons.append(f'古案例({sc_match_count}案)(+3)')
        elif sc_match_count>=2: evo_boost+=1; trend_reasons.append(f'古案例({sc_match_count}案)(+1)')
    tn='看涨' if trend_score>0 else ('看跌' if trend_score<0 else '震荡')
    fs,_=trainer.get_factor_impacts(san_chuan_list,tianjiang_list,'',tn); evo_boost+=fs
    cs2,cr2=trainer.apply_corrections(keti,san_chuan_list,tianjiang_list,ri_gan+ri_zhi); evo_boost+=cs2; trend_reasons.extend(cr2)
    trend_score+=evo_boost; trainer_summary=trainer.get_summary()
    evo_data={'case_kb_matched':sc_match_count,'evo_boost':evo_boost,'sc_key':sc_key,'factor_impacts':fs,'corrections_applied':len(cr2),'trainer_summary':trainer_summary}
    
    # ── 课体格·统一单源抽取（Task #212：删三处重复 rich 调用，改由 build_keti_duanyu 单一真相源）──
    # 与古例路径共用同一组 SanChuanKegeDetector/BiFaDetector/SpecialKegeDetector（rich）。
    # 通过 _partial 注入与内联完全一致的输入（transform 后的 si_ke / 分支式 tianjiang_detail / 地支→天将 tianjiang_map），
    # 保证 kb['bifa'|'sanchuan_kege'|'special_kege'] 与删除前逐字节一致 → M3 零回归。
    # 股票域 use_calibrated=False：走检测器自带的"股票域"股市信号（与内联原行为一致），不经占卜域校准表。
    _yj_char = str(yuejiang).replace('将', '').strip() if yuejiang else ''
    _season_map = {'寅':'春','卯':'春','辰':'春','巳':'夏','午':'夏','未':'夏',
                   '申':'秋','酉':'秋','戌':'秋','亥':'冬','子':'冬','丑':'冬'}
    _season = _season_map.get(_yj_char, '')

    _partial = {
        'basic_info': {'ri_gan': ri_gan, 'ri_zhi': ri_zhi},
        'si_ke': si_ke,                         # 原始 4-元组：供 derive_jiuzongmen（九宗门推导）与干支上神推导
        'san_chuan': san_chuan_list,
        'tiandi_pan': tiandi_pan,
        'keti': keti,
        'tianjiang_detail': tianjiang_detail,   # branch-keyed，供 BiFaDetector（与内联一致）
        'tianjiang_map': tian_jiang_map,         # 地支→天将，供 SpecialKegeDetector（与内联一致）
        'analysis': {'xun_kong': list(xun_kong) if xun_kong else [], 'kong_info': kong_info},
    }
    # si_ke_info 显式传 transform 后的 2-元组，与内联毕法检测输入逐字节一致（rules 70/10/23 读 si_ke_info）
    kb = build_keti_duanyu(_partial, "", "求财",
                           yuejiang=yuejiang, season=_season,
                           use_calibrated=False, level_override=keti_level,
                           si_ke_info=sike_for_analysis)

    # 三传课格信号纳入评分（源：kb['sanchuan_kege']，与内联 sanchuan_kege_result 同构）
    sk_signals = kb.get('sanchuan_kege', {}).get('股市信号', {})
    sk_tendency = sk_signals.get('综合倾向', '平')
    sk_strength = sk_signals.get('信号强度', 0)
    if sk_tendency in ('涨',) and sk_strength > 0.5:
        boost = int(sk_strength * 4)
        trend_score += boost
        trend_reasons.append(f'三传课格偏涨({boost:+d})')
    elif sk_tendency in ('跌',) and sk_strength > 0.5:
        boost = -int(sk_strength * 4)
        trend_score += boost
        trend_reasons.append(f'三传课格偏跌({boost:+d})')
    
    # 毕法赋信号纳入评分（源：kb['bifa']，与内联 bifa_result 同构；检测器调用已在 build_keti_duanyu 内统一）
    bf_signals = kb.get('bifa', {}).get('股市信号', {})
    bf_tendency = bf_signals.get('综合倾向', '平')
    bf_strength = bf_signals.get('信号强度', 0)
    bf_weights = bf_signals.get('各信号权重', {})
    bf_stats = kb.get('bifa', {}).get('检测统计', {})
    bf_bull_count = bf_stats.get('涨法条数', 0)
    bf_bear_count = bf_stats.get('跌法条数', 0)
    # 按原始加权信号分计算boost，最大±12（3条高置信看跌=3+2+3=8, 8*1.5=12）
    MAX_BIFA_BOOST = 12
    if bf_tendency in ('涨',) and bf_strength > 0.3:
        raw_score = bf_weights.get('涨', 0)
        boost = min(int(raw_score * 1.5), MAX_BIFA_BOOST)
        trend_score += boost
        trend_reasons.append(f'毕法赋偏涨({boost:+d}, {bf_bull_count}条法条)')
    elif bf_tendency in ('跌',) and bf_strength > 0.3:
        raw_score = bf_weights.get('跌', 0)
        boost = -min(int(raw_score * 1.5), MAX_BIFA_BOOST)
        trend_score += boost
        trend_reasons.append(f'毕法赋偏跌({boost:+d}, {bf_bear_count}条法条)')

    # 特殊课格信号纳入评分（源：kb['special_kege']，与内联 kege_result 同构；检测器调用已在 build_keti_duanyu 内统一）
    kg_signal = kb.get('special_kege', {}).get('信号汇总', {})
    kg_tendency = kg_signal.get('倾向', '平')
    kg_strength = kg_signal.get('强度', 0)
    if kg_tendency == '涨' and kg_strength > 0.3:
        boost = int(kg_strength * 2)
        trend_score += boost
        trend_reasons.append(f'特殊课格偏涨({boost:+d})')
    elif kg_tendency == '跌' and kg_strength > 0.3:
        boost = -int(kg_strength * 2)
        trend_score += boost
        trend_reasons.append(f'特殊课格偏跌({boost:+d})')
    
    trend_prediction=get_trend_prediction(trend_score)
    sf={'zhu_yin_po_mo':'铸印破模' in keti,'tianjiang_3xiong':tianjiang_xiong_count>=3,'double_line_xiong':l1x and l2x}
    confidence=calculate_confidence(trend_score,sf)
    cycle_end=target_date+timedelta(days=CYCLE_DAYS)
    
    result={
        'cycle_start':target_date.strftime('%Y-%m-%d'),'cycle_end':cycle_end.strftime('%Y-%m-%d'),'cycle_days':CYCLE_DAYS,
        'method':'大六壬','timestamp':target_date.strftime('%Y-%m-%d %H:%M:%S'),
        'basic_info':{'year':year,'month':month,'day':day,'hour':hour,'shichen':shichen,'yuejiang':yuejiang,'yuejiang_name':yj_name,'ri_gan':ri_gan,'ri_zhi':ri_zhi,'ri_gan_zhi':ri_gan+ri_zhi},
        'si_ke':si_ke,'san_chuan':san_chuan_list,'sanchuan_tianjiang':tianjiang_list,'keti':keti,'qifa':qifa,'tiandi_pan':tiandi_pan,
        'analysis':{'xun_kong':list(xun_kong),'kong_info':kong_info,'liuqin':liuqin_list,'wangshuai':wangshuai_list,'relationships':relationships,'yong_shen':yong_shen_analysis,'cai_shi_er_qi':cai_analysis,'stock':stock_analysis,'keti_duanyu':kb,'tianjiang':tianjiang_detail,'sike_qi':sike_qi_analysis,'sanchuan_zhijiu':sanchuan_zhijiu,'guishen_jixiong':guishen_jixiong,'ba_sha':ba_sha,'shen_qiang_ruo':shen_qiang_ruo,'shen_sha':shen_sha,'full_analysis':full_analysis,'evo_data':evo_data},
        'prediction':{'trend':trend_prediction,'score':trend_score,'confidence':round(confidence,1),'reasons':trend_reasons},
        'for_comparison':{'prediction_type':'liuren','target_index':'上证指数','trend_score_normalized':round((trend_score+10)/20*100,1)},
    }
    # 标记股票路径（区别于古例路径缺 _zhanlei；供 judgment_fusion 股票域自有特征库门控）
    result['analysis']['_is_stock'] = True
    # ── 64 课判断引擎（2026-08-15 憨爷拍板：动态判定课体，非查表硬编码）──
    try:
        from engine.liuren_64ke_judge import judge_64_keti
        _lunar_m, _lunar_d, _jq = 0, 0, ''
        try:
            import sxtwl as _sx
            _lx = _sx.fromSolar(year, month, day)
            _lunar_m, _lunar_d = _lx.getLunarMonth(), _lx.getLunarDay()
            if _lx.hasJieQi():
                _jq = _lx.getJieQi()
        except Exception:
            pass
        _kj_env = {
            'ri_gan': ri_gan, 'ri_zhi': ri_zhi,
            'sike': si_ke, 'sanchuan': san_chuan_list,
            'chu': san_chuan_list[0] if san_chuan_list else '',
            'zhong': san_chuan_list[1] if len(san_chuan_list) > 1 else '',
            'mo': san_chuan_list[2] if len(san_chuan_list) > 2 else '',
            'yue_jiang': yuejiang, 'yue_jian': yuejian_zhi,
            'nian_zhi': nian_zhi,
            'chu_tianjiang': tianjiang_list[0] if tianjiang_list else '',
            'tian_jiang': tian_jiang_map, 'tdp': tiandi_pan,
            'kong_wang': list(xun_kong) if xun_kong else [],
            'lunar_month': _lunar_m, 'lunar_day': _lunar_d, 'jieqi': _jq,
            # 【BUG-FIX 2026-09-01】天网课需占时 shichen，原环境未传 → 天网永不触发
            'shichen': shichen,
        }
        result['analysis']['keti_judged'] = judge_64_keti(_kj_env)
    except Exception:
        result['analysis']['keti_judged'] = []
    # ---- 支柱④ CBR 检索 + 壬归寻原叙事层(须先于融合层: 其结论作为「综合叙事」新证据组注入概率) ----
    try:
        # 回填 rizhu（holistic_synthesis 优先读顶层 rizhu 以驱动 CBR 日干匹配）
        if not result.get('rizhu'):
            _bi = result.get('basic_info') or {}
            _rg = _bi.get('ri_gan') or ''
            _rz = _bi.get('ri_zhi') or ''
            if _rg or _rz:
                result['rizhu'] = _rg + _rz
        from engine.holistic_synthesis import holistic_judge
        result['holistic_judgment'] = holistic_judge(result)
    except Exception as _hj_err:
        result['holistic_judgment'] = {'error': str(_hj_err)}
    # ---- 精准判断引擎 · 融合层(门控+D-S), 含 综合叙事(CBR) 证据组, 零风险叠加, 不改动原有 prediction ----
    try:
        from engine.judgment_fusion import fuse
        result['fused_judgment'] = fuse(result)
    except Exception as _fj_err:
        result['fused_judgment'] = {'error': str(_fj_err)}

    # ---- 股票路径 valence 隔离（2026-07-30 定稿）----
    # 股票域方向预测禁用古例占卜域 valence（_shen_sha_valence / _qiucai / _guansong / _taichan）。
    # 原此处误在股票路径置 _shen_sha_valence（古例校准值），违反文档"股票路径不置该键→零影响"，
    # 且实证拖累 M3 至近随机；已移除。DISABLE_STOCK_VALENCE（顶部）同时关闭 collect_signals
    # L330-340 的设计内 extract_stock_valence。古例路径不受影响（不 import 本模块）。

    # ---- 构建 reasoning_chain（17步结构化推理）从 analysis 子字典映射 ----
    # 前端按此 17 键渲染推理过程面板；有值显示✅内容，无值显示⬜未填充。
    try:
        a = result.get('analysis', {}) or {}
        bi = result.get('basic_info', {}) or {}
        pr = result.get('prediction', {}) or {}
        fj = result.get('fused_judgment', {}) or {}

        rc = {}
        # 1. 课体
        kd = a.get('keti_duanyu') or {}
        kname = kd.get('keti_name', keti) or keti or '--'
        klevel = kd.get('level', '') or ''
        kduanyu = (kd.get('duanyu') or '')[:120] if isinstance(kd.get('duanyu'), str) else ''
        rc['课体'] = f'{kname} [{klevel}]' + (f'\n{kduanyu}' if kduanyu else '')

        # 2. 四课加临
        sq = a.get('sike_qi') or {}
        sq_items = sq.get('四课关系', []) if isinstance(sq.get('四课关系'), list) else []
        if sq_items:
            rc['四课加临'] = '\n'.join(f"  {it.get('类型','')}：{it.get('描述','')[:60]}" for it in sq_items[:4])
        else:
            rc['四课加临'] = f"{sq.get('描述','') or sq.get('四课关系','') or '--'}"

        # 3. 用神五气
        ys = a.get('yong_shen') or {}
        rc['用神五气'] = f"用神：{ys.get('用神','--')} | 旺衰：{ys.get('旺衰','--')}\n{ys.get('分析','')[:100]}"

        # 4. 三传
        sc_names = ' → '.join(san_chuan_list) if san_chuan_list else '--'
        sz = a.get('sanchuan_zhijiu') or {}
        rc['三传'] = f"{sc_names}\n{sz.get('制救分析','') or sz.get('气之趋势','') or ''}"

        # 5. 六亲分析
        lq = a.get('liuqin') or []
        if lq:
            rc['六亲分析'] = '\n'.join(f"  {it.get('地支','')}({it.get('五行','')}) {it.get('六亲','')}" for it in lq[:6])
        else:
            rc['六亲分析'] = '(已禁用 DISABLE_LIUQIN)' if os.environ.get('DISABLE_LIUQIN') else '--'

        # 6. 天将分析
        tj = a.get('tianjiang') or {}
        tj_items = [tj.get(k) for k in ['初传','中传','末传'] if tj.get(k)]
        if tj_items:
            rc['天将分析'] = ' → '.join(tj_items) + (f"\n贵人方位：{tj.get('贵人','--')}" if tj.get('贵人') else '')

        # 7. 五行
        rg_wx = GAN_WX.get(ri_gan, '?')
        rz_wx = ZHI_WX.get(ri_zhi, '?')
        rc['五行'] = f"日干{ri_gan}({rg_wx}) 日支{ri_zhi}({rz_wx})"

        # 8. 旬空
        xk = a.get('xun_kong') or []
        rc['旬空'] = ', '.join(xk) if xk else '无'

        # 9. 旺衰
        ws = a.get('wangshuai') or []
        if ws:
            rc['旺衰'] = '\n'.join(f"  {it.get('地支','')}：{it.get('旺衰','--')}" for it in ws[:6])

        # 10. 神煞
        ss = a.get('shen_sha') or {}
        ss_keys = [k for k in list(ss.keys())[:12] if ss.get(k)]
        if ss_keys:
            rc['神煞'] = ', '.join(ss_keys)

        # 11. 刑冲合害
        rel = a.get('relationships') or []
        rel_texts = [r for r in [
            *(r.get('六合','') or '' for r in rel if r.get('六合')),
            *(r.get('六冲','') or '' for r in rel if r.get('六冲')),
            *(r.get('三刑','') or '' for r in rel if r.get('三刑')),
            *(r.get('六害','') or '' for r in rel if r.get('六害')),
        ] if r]
        if rel_texts:
            rc['刑冲合害'] = '\n'.join(rel_texts[:8])

        # 12. 八杀
        bs = a.get('ba_sha') or {}
        bsd = bs.get('八杀明细', []) if isinstance(bs.get('八杀明细'), list) else []
        if bsd:
            active = [b for b in bsd if b.get('出现')]
            rc['八杀'] = '\n'.join(f"  {b['杀']}：{','.join(b['出现'])} ({b.get('评分',0)}分)" for b in active[:6]) or '无现杀'
            rc['八杀'] += f"\n总评：{bs.get('吉凶','--')} | {bs.get('描述','')[:80]}"

        # 13. 十二气财星
        cs = a.get('cai_shi_er_qi') or {}
        cs_items = cs.get('三传十二气', []) if isinstance(cs.get('三传十二气'), list) else []
        if cs_items:
            rc['十二气财星'] = '\n'.join(f"  {it.get('三传','')}{it.get('地支','')}({it.get('十二气','')}) {it.get('吉凶','')}: {it.get('求财含义','')[:40]}" for it in cs_items[:3])

        # 14. 身强身弱
        sqr = a.get('shen_qiang_ruo') or {}
        rc['身强身弱'] = f"身强{sqr.get('身强评分',0)} | 财星{sqr.get('财星评分',0)}\n{sqr.get('身强身弱','') or ''}"

        # 15. 趋势判断
        rc['趋势判断'] = f"{pr.get('trend','--')} (score={pr.get('score',0)}, conf={pr.get('confidence',0)})"
        reasons = pr.get('reasons') or []
        if reasons:
            rc['趋势判断'] += '\n' + '\n'.join(f"  • {r}" for r in reasons[:8])

        # 16. 应期（股票域=周期末）
        rc['应期'] = f"预测周期：{result.get('cycle_start','?')} ~ {result.get('cycle_end','?')}"

        # 17. 风险提示
        gj = a.get('guishen_jixiong') or {}
        gj_text = gj.get('天乙状态', '') or ''
        conflict = fj.get('conflict', 0)
        risk_parts = []
        if gj_text: risk_parts.append(gj_text)
        if conflict > 0.5: risk_parts.append(f"信号冲突度较高({conflict:.0%})")
        if abs(pr.get('score', 0)) < 2: risk_parts.append("信号接近中性，方向不确定")
        rc['风险提示'] = '\n'.join(risk_parts) if risk_parts else '无明显风险信号'

        result['reasoning_chain'] = rc
    except Exception as _rc_err:
        result['reasoning_chain'] = {'error': str(_rc_err)}

    return result


def save_liuren_prediction(prediction, filepath=None):
    if filepath is None: filepath = LIUREN_DATA / f'liuren_prediction_{prediction.get("cycle_start", datetime.now().strftime("%Y-%m-%d"))}.json'
    with open(filepath, 'w', encoding='utf-8') as f: json.dump(prediction, f, ensure_ascii=False, indent=2, default=str)
    return filepath


def load_liuren_prediction(date_str=None):
    if date_str is None: date_str = datetime.now().strftime('%Y-%m-%d')
    fp = LIUREN_DATA / f'liuren_prediction_{date_str}.json'
    return json.load(open(fp, 'r', encoding='utf-8')) if fp.exists() else None


def get_liuren_history(limit=10):
    history = []
    for fp in sorted(LIUREN_DATA.glob('liuren_prediction_*.json'), reverse=True)[:limit]:
        try: history.append(json.load(open(fp, 'r', encoding='utf-8')))
        except: pass
    return history


def run_both_predictions(target_date=None):
    from quant_predictor import get_quant_signal
    lr = get_liuren_20d_signal(target_date); qr = get_quant_signal(target_date)
    return {'cycle_start':lr['cycle_start'],'cycle_end':lr['cycle_end'],
            'comparison':{'liuren_trend':lr['prediction']['trend'],'liuren_score':lr['prediction']['score'],'liuren_confidence':lr['prediction']['confidence'],'quant_trend':qr.get('trend_prediction','?'),'quant_confidence':qr.get('confidence',0),'agreement':lr['prediction']['trend']==qr.get('trend_prediction','')},'liuren':lr,'quant':qr}
