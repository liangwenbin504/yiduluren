# -*- coding: utf-8 -*-
"""择日×古例变通桥（2026-08-21）——项目核心：把有印证的古例课式变通到现代择日断语。

原理：
  六壬课式由 (日柱, 月将, 时辰) 三元唯一决定 → 天地盘/四课/三传/天将全链一致。
  古例（壬占汇选/断案疏正 747 案）标注了 day_ganzhi/yue_jiang/shichen/占类/吉凶/断语，
  现代择日排出同指纹的课 → "同年同月同时同月将"同课 → 分层变通：

  A 层（基调直迁）：课体/毕法/变格/吉凶 label —— 与占类无关，直接可引
  B 层（占类桥翻译）：古例事象 × 择日类型 → 择日域事象提示（吉凶评级不变，事象换域）
  C 层（应期重算）：按现代主命/山向重算提示（古例应期仅参考，不直套）

输出结构：{'matched', 'cases': [...], '基调': [...], '变通': [...], '应期': [...], 'narr'}
"""
import os
import re

_ROOT = os.path.dirname(os.path.abspath(__file__))

# ── 课式指纹：{ (日柱, 月将, 时辰): [case...] }（惰性构建）──
_FINGERPRINT = None
_FP_CASES = None


def _norm_fp(day_ganzhi: str, yuejiang: str, shichen: str):
    day = re.sub(r'日$', '', str(day_ganzhi or '').strip())
    yj = str(yuejiang or '').replace('将', '').strip()
    shi = str(shichen or '').strip()
    if len(day) != 2 or not yj or not shi:
        return None
    return (day, yj, shi)


def _load_index():
    global _FINGERPRINT, _FP_CASES
    if _FINGERPRINT is not None:
        return _FINGERPRINT
    from engine.cbr_retrieval import _load_cases
    cases = _load_cases()
    fp = {}
    for c in cases:
        k = _norm_fp(c.get('day_ganzhi', ''), c.get('yue_jiang', ''), c.get('shichen', ''))
        if not k:
            continue
        fp.setdefault(k, []).append(c)
    _FINGERPRINT = fp
    _FP_CASES = cases
    return fp


def find_same_ke(ri_gan: str, ri_zhi: str, yuejiang: str, shichen: str) -> list:
    """现代课 (日干,日支,月将,时辰) → 同课古例列表（含排序：优先带吉凶 label 的）。"""
    fp = _load_index()
    k = _norm_fp(ri_gan + ri_zhi, yuejiang, shichen)
    if not k:
        return []
    out = list(fp.get(k, []))
    out.sort(key=lambda c: 0 if str(c.get('label') or '') in ('吉', '凶') else 1)
    return out[:6]


# ── B 层：占类桥（古例占类 × 择日类型 → 事象提示）──
_ZHANLEI_BRIDGE = {
    # 古例占类: { 择日类型关键词: 变通事象 }
    '求财': {'开业': '古占求财同课：课内财象可引为开市进财之证', '交易': '古占求财同课：交易得财有古例印证',
             '安葬': '古占求财同课：安葬主家财路，财象宜参', 'default': '古占求财同课：财利事象可参'},
    '疾病': {'安葬': '古占疾病同课：葬课宜防疾厄血光之应', 'default': '古占疾病同课：疾厄事象可参，用事宜慎'},
    '官讼': {'婚嫁': '古占官讼同课：婚课防口舌官非纠缠', '立碑': '古占官讼同课：立碑防讼争，宜择贵课',
             '安葬': '古占官讼同课：葬课防官非口舌', 'default': '古占官讼同课：防口舌是非'},
    '出行': {'出行': '古占出行同课：行路事象有古例印证', '上任': '古占出行同课：赴任之行有古例印证',
             'default': '古占出行同课：出行事象可参'},
    '家宅': {'动土': '古占家宅同课：动土修造家宅事象可参', '入宅': '古占家宅同课：入宅安居家宅事象可参',
             'default': '古占家宅同课：家宅事象可参'},
    '胎产': {'婚嫁': '古占胎产同课：婚课利子息，有古例印证', 'default': '古占胎产同课：子息事象可参'},
    '婚姻': {'婚嫁': '古占婚姻同课：婚嫁事象有古例直接印证', 'default': '古占婚姻同课：婚姻事象可参'},
    '走失': {'出行': '古占走失同课：出行防失，宜慎', 'default': '古占走失同课：防失防盗事象'},
    '功名': {'上任': '古占功名同课：赴任功名有古例印证', '考试': '古占功名同课：考试前程有古例印证',
             'default': '古占功名同课：功名事象可参'},
    '学业': {'考试': '古占学业同课：考试学业有古例印证', 'default': '古占学业同课：学业事象可参'},
    '征战': {'default': '古占征战同课：用事刚决，主竞争之象'},
    '其他': {'default': ''},
}

# 格局关键词 → 择日域事象（B 层追加；吉凶以 label 定）
_KEYWORD_EVENT = [
    ('白虎', '血光/凶险'), ('螣蛇', '惊疑/怪异'), ('朱雀', '口舌/文书'), ('玄武', '失盗/暗昧'),
    ('官鬼', '官非/疾厄'), ('子孙', '子息'), ('财', '进财'), ('墓', '阻滞/埋葬'), ('贵人', '得贵扶助'),
    ('空亡', '虚而不实'), ('三奇', '科名'), ('驿马', '行动'), ('闭口', '闭藏难言'),
]


def _zeri_type_class(t: str) -> str:
    for k in ('开业', '交易', '婚嫁', '立碑', '安葬', '出行', '上任', '考试', '动土', '入宅'):
        if k in str(t or ''):
            return k
    return 'default'


def bridge_to_zeri(cases: list, zetiri_type: str = '', shan: str = '', ming: str = '',
                  ri_gan: str = '', ri_zhi: str = '') -> dict:
    """同课古例 → 分层变通断语。ri_gan/ri_zhi 用于 C 层主命旬空判定。"""
    if not cases:
        return {'matched': False, 'cases': [], '基调': [], '变通': [], '应期': [], 'narr': ''}
    zc = _zeri_type_class(zetiri_type)
    out_cases, ji_tiao, bian_tong = [], [], []
    for c in cases[:3]:
        info = {
            'case_id': c.get('case_id', ''), 'source': '汇选' if c.get('source') == 'Corpus_A' else '数征',
            'zhanlei': c.get('zhanlei', ''), 'label': c.get('label', ''),
            'day_ganzhi': c.get('day_ganzhi', ''), 'yue_jiang': c.get('yue_jiang', ''),
            'shichen': c.get('shichen', ''), 'year': c.get('year', ''),
            'duanyu': (str(c.get('duanyu') or ''))[:160],
            'keti': (c.get('features') or {}).get('keti', []),
            'bifa': [(b[0] if isinstance(b, (list, tuple)) else b) for b in (c.get('features') or {}).get('bifa', [])],
            'bianjie': (c.get('features') or {}).get('bianjie', []),
        }
        out_cases.append(info)
        lbl = str(c.get('label') or '')
        jx = '吉' if lbl == '吉' else ('凶' if lbl == '凶' else '未详')
        # A 层：基调直迁
        ke = '、'.join(info['keti'][:4]) or '—'
        ji_tiao.append(f"古课{info['day_ganzhi']}日{info['yue_jiang']}将{info['shichen']}时（{info['source']}·{info['zhanlei']}占）{jx}：课体{ke}"
                       + (f"；毕法{('、'.join(info['bifa'][:2]))}" if info['bifa'] else ''))
        # B 层：占类桥翻译
        b = _ZHANLEI_BRIDGE.get(info['zhanlei'], {}).get(zc, _ZHANLEI_BRIDGE.get(info['zhanlei'], {}).get('default', ''))
        ev = ''
        for kw, evt in _KEYWORD_EVENT:
            if kw in (str(c.get('duanyu') or '') + ' '.join(info['bifa'])):
                ev = evt
                break
        if b:
            _lbl_txt = info['label'] or '吉凶未详'
            if ev:
                bian_tong.append(f"{b}；古例{_lbl_txt}，主{ev}")
            else:
                bian_tong.append(f"{b}；古例{_lbl_txt}")
        else:
            # 占类桥未覆盖（含'其他'）：不强行翻译事象，直引古例原文断语为证
            _lbl_txt2 = info['label'] or '吉凶未详'
            _dy = str(c.get('duanyu') or '').replace(chr(10), ' ').strip()
            bian_tong.append(f"古例断语（原文）：{_dy[:80]}{'…' if len(_dy) > 80 else ''}（古例{_lbl_txt2}）")
    # C 层：应期重算提示（主命禄马信号简版：复用 zeri_hecan_engine 的主命禄马判定）
    yingqi_tips = []
    try:
        from zeri_hecan_engine import zeri_signals as _zs
        _sig = _zs('', zetiri_type, sizhu={}, shan=shan, ming=ming,
                   ri_gan=ri_gan, ri_zhi=ri_zhi)
        if _sig.get('主命禄马_犯旬空'):
            yingqi_tips.append('主命禄马落旬空：应期难定，古例应期不可直套')
        elif _sig.get('主命禄马_不空坐日柱'):
            yingqi_tips.append('主命禄马坐日柱不空：古例应期可参考现代主命推')
        if ming:
            yingqi_tips.append('应期宜按主命' + str(ming) + '行年重算，勿照古例应人')
    except Exception:
        pass
    narr = '；'.join(ji_tiao[:2]) + ('；' + '；'.join(bian_tong[:2]) if bian_tong else '')
    conf = 0.9 if out_cases and all(c['label'] in ('吉', '凶') for c in out_cases) else 0.7
    return {'matched': True, 'cases': out_cases, '基调': ji_tiao, '变通': bian_tong,
            '应期': yingqi_tips, 'narr': narr, '置信度': conf}


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, os.path.dirname(_ROOT))
    fp = _load_index()
    print('课式指纹:', len(fp), '个；案例:', len(_FP_CASES))
    # 自检：取一个指纹样例
    k = next(iter(fp))
    print('样例指纹', k, '→', len(fp[k]), '例')
    r = bridge_to_zeri(fp[k], '安葬', shan='辛', ming='甲申')
    print('narr:', r['narr'][:200])
