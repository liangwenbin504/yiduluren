# -*- coding: utf-8 -*-
"""占事断语生成器（P3 · 2026-08-18）

按具体占事（求财/婚姻/疾病/出行/官讼/功名/家宅/胎产/贼盗）生成六壬断语，
解决"一个断语通吃天下"的一刀切问题。三源合成：

1. 起课：权威 V2 引擎 SiKeSanChuanCalculator2（中气换将月将 + 九宗门完整）
2. 课体断语：liuren_keti_duanyu.LiuRenKetiDuanyu.get_keti_duanyu（课体话术）
3. 占类专属信号：liuren_keti_bifa 的 9 个 extract_*_valence（确定性·古籍出处）→ details 即人话断语
4. 毕法条文：BiFaDetector.detect → 命中条文 → data/bifa_100_knowledge_base.json 查 application/core_rule
"""
import json
import os
import sys
from typing import Dict, List, Any

# 无论被 import 还是直接运行，都能找到 engine 包（脚本位于 engine/ 下）
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── 前端 category 键 → 占类中文（与 9 抽取器口径一致）──
CATEGORY_MAP = {
    'general': '其他', 'stock': '求财', 'illness': '疾病', 'travel': '出行',
    'career': '功名', 'marriage': '婚姻', 'wealth': '求财', 'litigation': '官讼',
    'exam': '功名', 'lost': '贼盗', 'child': '胎产', 'house': '家宅',
    'business': '求财',
}

# ── 占类中文 → 抽取器（惰性 import，避免模块级重依赖）──
_EXTRACTORS = None


def _get_extractors():
    global _EXTRACTORS
    if _EXTRACTORS is None:
        from engine.liuren_keti_bifa import (
            extract_taichan_valence, extract_guansong_valence, extract_qiucai_valence,
            extract_gongming_valence, extract_disease_valence, extract_jiazhai_valence,
            extract_chuxing_valence, extract_hunyin_valence, extract_zeidao_valence,
        )
        _EXTRACTORS = {
            '胎产': extract_taichan_valence, '官讼': extract_guansong_valence,
            '求财': extract_qiucai_valence, '功名': extract_gongming_valence,
            '疾病': extract_disease_valence, '家宅': extract_jiazhai_valence,
            '出行': extract_chuxing_valence, '婚姻': extract_hunyin_valence,
            '贼盗': extract_zeidao_valence,
        }
    return _EXTRACTORS


# ── 毕法 KB（100 条，含 application/core_rule）──
_BIFA_KB = None


def _get_bifa_kb():
    global _BIFA_KB
    if _BIFA_KB is None:
        _here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(os.path.dirname(_here), 'data', 'bifa_100_knowledge_base.json')
        with open(p, encoding='utf-8') as f:
            _BIFA_KB = {r.get('name'): r for r in json.load(f).get('rules', [])}
    return _BIFA_KB


def paipan_v2(ri_gan: str, ri_zhi: str, yuejiang: str, shichen: str) -> Dict[str, Any]:
    """权威 V2 起课：天地盘/四课/三传/课体/天将"""
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    from engine.gui_ren_engine import GuiRenCalculator
    calc = SiKeSanChuanCalculator2()
    tdp = calc.get_tiandi_pan(yuejiang, shichen)
    sike = calc.qi_sike(ri_gan, ri_zhi, tdp)
    sc = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tdp)
    sanchuan = [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')]
    tjm = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shichen).get('天将映射', {})
    return {
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'yuejiang': yuejiang, 'shichen': shichen,
        'tiandi_pan': tdp, 'sike': sike, 'sanchuan': sanchuan,
        'keti': sc.get('课体', ''), 'qifa': sc.get('起法', ''),
        'tianjiang_map': tjm,
        'tianjiang_list': [tjm.get(z, '') for z in sanchuan],
    }


# 抽取器三传参数名（个别不同：胎产=san_chuan、疾病=san_chuan_dizhi，其余=sanchuan_dizhi）
_SC_PARAM = {
    '胎产': 'san_chuan', '疾病': 'san_chuan_dizhi',
}


def _zhanshi_class_signal(pan: Dict[str, Any], zhanlei: str) -> Dict[str, Any]:
    """按占类调对应抽取器，取 details（人话断语）+ level"""
    exs = _get_extractors()
    ex = exs.get(zhanlei)
    if not ex:
        return {'score': 0, 'level': '平', 'details': [], 'fired': ''}
    kw = dict(ri_gan=pan['ri_gan'], ri_zhi=pan['ri_zhi'],
              tianjiang_list=pan['tianjiang_list'], zhanlei=zhanlei)
    sc_key = _SC_PARAM.get(zhanlei, 'sanchuan_dizhi')
    try:
        return ex(**{sc_key: pan['sanchuan']}, si_ke=pan['sike'], **kw)
    except TypeError:
        return ex(**{sc_key: pan['sanchuan']}, **kw)


def _bifa_duanyu(pan: Dict[str, Any]) -> List[Dict[str, str]]:
    """毕法检测 → 命中条文 → KB 查白话/占事应用"""
    from engine.bifa_detector import BiFaDetector
    from engine.liuren_keti_bifa import _derive_gan_zhi_shang
    gan_shang, zhi_shang = _derive_gan_zhi_shang(pan['sike'], pan['tiandi_pan'], pan['ri_gan'], pan['ri_zhi'])
    r = BiFaDetector().detect(
        sanchuan_dizhi=pan['sanchuan'], ri_gan=pan['ri_gan'], ri_zhi=pan['ri_zhi'],
        ganzhi=pan['ri_gan'] + pan['ri_zhi'], yuejiang=pan['yuejiang'], season='',
        gan_shang_shen=gan_shang, zhi_shang_shen=zhi_shang,
        si_ke_info=pan['sike'], tian_jiang=pan['tianjiang_map'], tiandi_pan=pan['tiandi_pan'],
    )
    kb = _get_bifa_kb()
    out = []
    for name in (r.get('匹配法条') or []):
        item = kb.get(name, {})
        out.append({
            '条文': name,
            '白话': item.get('core_rule', ''),
            '占事应用': item.get('application', ''),
            '古例': (item.get('example') or '')[:120],
        })
    return out


def generate(ri_gan: str, ri_zhi: str, yuejiang: str, shichen: str,
             zhanshi: str = '其他', category: str = '') -> Dict[str, Any]:
    """按占事生成完整断语。zhanshi 为中文占类；category 为前端英文键（二选一，category 优先映射）。"""
    if category:
        zhanshi = CATEGORY_MAP.get(category, zhanshi)
    pan = paipan_v2(ri_gan, ri_zhi, yuejiang, shichen)

    # 课体断语
    keti_text = ''
    keti_level = ''
    try:
        from engine.liuren_keti_duanyu import LiuRenKetiDuanyu
        kd = LiuRenKetiDuanyu().get_keti_duanyu(pan['keti'])
        keti_text = kd.get('断语', '') or kd.get('详细断语', {}).get('总论', '')
        keti_level = kd.get('等级', '')
    except Exception:
        pass

    # 占类专属断语
    zl_signal = _zhanshi_class_signal(pan, zhanshi)
    zl_details = list(zl_signal.get('details', []))

    # 毕法断语
    bifa = _bifa_duanyu(pan)
    bifa_duanyu = [f'{b["条文"]}：{b["白话"]}' for b in bifa if b.get('白话')]

    # 综合评级：占类信号优先，其次课体等级，默认平
    level = zl_signal.get('level') if zl_signal.get('score') else (keti_level or '平')

    return {
        'zhanshi': zhanshi,
        'paipan': {
            'ri_gan': pan['ri_gan'], 'ri_zhi': pan['ri_zhi'],
            'yuejiang': pan['yuejiang'], 'shichen': pan['shichen'],
            'sanchuan': pan['sanchuan'], 'keti': pan['keti'], 'qifa': pan['qifa'],
            'tianjiang': pan['tianjiang_list'],
        },
        'level': level,
        'keti_duanyu': keti_text,
        'zhanshi_duanyu': zl_details,
        'bifa_duanyu': bifa_duanyu,
        'bifa_detail': bifa[:3],
        'summary': '；'.join(filter(None, [keti_text] + zl_details + bifa_duanyu[:2])) or '课体平稳，需结合具体占事详参。',
    }


if __name__ == '__main__':
    for zl, cat in [('求财', 'wealth'), ('婚姻', 'marriage'), ('疾病', 'illness'), ('出行', 'travel'), ('官讼', 'litigation')]:
        r = generate('甲', '子', '亥', '寅', zhanshi=zl)
        print('[' + zl + '] 课体=' + r['paipan']['keti'] + ' 等级=' + r['level'])
        print('   占类断语: ' + str(r['zhanshi_duanyu']))
        print('   毕法: ' + str([b['条文'] for b in r['bifa_detail']]))
