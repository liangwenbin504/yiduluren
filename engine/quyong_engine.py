# -*- coding: utf-8 -*-
"""「问事 → 类神取用」执行器 —— 形式化『问事』这一维（2026-10-03）。

原文依据
--------
· **类神定义**（通解_**上** L1366）：「所谓类神，指的是和事体相关贴切的类象，譬如
  **占文书，看朱雀；占见贵，看天乙；占惊怪，看螣蛇；占婚姻，男方为青龙，女方为天后**。」
· **取用链**（通解_**上** L1387 注释①）：「王学决断**先看七处，次看类神**，以七处为关键，
  **看类神是否入七处**，看其**落何宫**，遇何**神将**，有无**刑冲破害**及其**旺相休囚死**、
  当令与否、有气无气、**空亡**否，然后就类神吉凶**结合课式而断**。」
· **显隐铁律**（同上）：「**类神入课传为显，入年命次之，俱不入为晦**。」「凡有其象，必有其事。」
· **变通法**（通解_**下** L11577）：「占贵人、尊长看天乙…**占求财，有青龙看青龙，无青龙，
  功曹出现，立功曹为用**，青龙、功曹俱无，而太常出现，则立太常为用，此为变通之法。」

⛔ 本模块**只做取用与呈现**（叙事层），不进 valence、不改吉凶排序。
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RULES_FILE = os.path.join(_ROOT, 'data', 'quyong_rules.json')

_ZHI = '子丑寅卯辰巳午未申酉戌亥'
_ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
           '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
_GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
           '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
_KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}      # 我克
# 天将名（类神常以天将代称）
_JIANG = ('贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙', '天空', '白虎',
          '太常', '玄武', '太阴', '天后', '腾蛇')

_cached = None


def load_rules():
    global _cached
    if _cached is None:
        with io.open(_RULES_FILE, encoding='utf-8') as f:
            _cached = json.load(f)
    return _cached


def match_rules(zhanlei='', question=''):
    """按占类/问题文本匹配规则（命中多条时全部返回，⛔ 不武断取一）。"""
    txt = '%s %s' % (zhanlei or '', question or '')
    out = []
    for r in load_rules().get('rules', []):
        for kw in r.get('zhanlei', []):
            if kw and kw in txt:
                out.append(r)
                break
    return out


_CHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
          '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}


def lookup_tianjiang(zhanlei='', question=''):
    """🔴 查**十二天将占类表**（通解_**下** L11573-11575）⇒ 返回候选天将（按表序）。

    原文：「占贤良、**财帛**、书吏则用**青龙**…占盗贼、逃亡、走失、水利则用**玄武**…」
    ⚠️ 一个占类可能命中多个天将（如「婚姻」在六合与天后下都有）⇒ **全部返回，不武断**。
    """
    txt = '%s %s' % (zhanlei or '', question or '')
    tab = load_rules().get('tianjiang_zhanlei', {})
    out = []
    for jiang, kws in tab.items():
        if jiang.startswith('_') or jiang == '原文':
            continue
        for kw in kws:
            if kw and kw in txt:
                out.append(jiang)
                break
    return out


def biantong_chain(zhanlei='', question=''):
    """🔴 **变通法优先链**（通解_**下** L11577）—— 轻重权衡的原文依据。

    原文：「占求财，**有青龙看青龙，无青龙，功曹出现，立功曹为用**，青龙、功曹俱无，
    而太常出现，则立太常为用，**此为变通之法**。」
    ⇒ 返回该占类的取用链（**有序**，前为尊）。
    """
    txt = '%s %s' % (zhanlei or '', question or '')
    bt = load_rules().get('biantong', {}).get('链', {})
    for key, chain in bt.items():
        if key in ('通用兜底',):
            continue
        for kw in key.split('/'):
            if kw and kw in txt:
                return list(chain)
    return list(bt.get('通用兜底', []))


def judge_nianming(ctx):
    """🔴 **年命判据**（一课多断的区别所在）—— 通解_**下** L11576。

    原文：「再看**与日辰行年**相生旺合则吉，冲克则凶。惟日年制凶神尚可言吉，
    若**日年落空，百事无成**，惟类自作空，不以空论。」
    返回 [(事主, 支, 上神, 与日辰关系)]。
    """
    tdp = ctx.get('tiandi_pan') or {}
    rz = ctx.get('ri_zhi', '')
    out = []
    for lbl, z in (('本命', ctx.get('ben_ming', '')), ('行年', ctx.get('xing_nian', ''))):
        if not z:
            continue
        up = tdp.get(z, '')
        rel = ''
        if up and rz:
            gw, zw = _ZHI_WX.get(up, ''), _ZHI_WX.get(rz, '')
            if up == rz:
                rel = '与日辰同支'
            elif _CHONG.get(up) == rz:
                rel = '冲日辰'
            elif zw and gw and _KE.get(gw) == zw:
                rel = '年命上神克日辰'
            elif zw and gw and _KE.get(zw) == gw:
                rel = '日辰克年命上神'
            elif zw and gw and _SHENG.get(gw) == zw:
                rel = '年命上神生日辰（吉）'
            elif zw and gw and _SHENG.get(zw) == gw:
                rel = '日辰生年命上神（泄）'
        out.append((lbl, z, up, rel))
    return out


def _liuqin(ri_gan, zhi):
    """支相对日干的六亲。"""
    g, z = _GAN_WX.get(ri_gan or ''), _ZHI_WX.get(zhi or '')
    if not g or not z:
        return ''
    if z == g:
        return '兄弟'
    if _SHENG.get(g) == z:
        return '子孙'
    if _KE.get(g) == z:
        return '妻财'
    if _SHENG.get(z) == g:
        return '父母'
    if _KE.get(z) == g:
        return '官鬼'
    return ''


def _liuqin_names(ri_gan):
    """该日干下：六亲 → 对应五行。"""
    g = _GAN_WX.get(ri_gan or '')
    if not g:
        return {}
    inv_sheng = {v: k for k, v in _SHENG.items()}
    inv_ke = {v: k for k, v in _KE.items()}
    return {
        '兄弟': g,
        '子孙': _SHENG.get(g, ''),
        '妻财': _KE.get(g, ''),
        '父母': inv_sheng.get(g, ''),
        '官鬼': inv_ke.get(g, ''),
    }


def _resolve(name, ctx):
    """把「类神名」解析成**具体地支**（可能多个）。
    支持三类：① 天将名 → 该将所乘之支；② 六亲名 → 合该五行之支；③ 地支/生肖 → 本身。"""
    res = []
    name = (name or '').strip()
    if not name:
        return res
    tj = ctx.get('tianjiang') or {}
    if name in _JIANG or name == '天乙':
        key = '贵人' if name == '天乙' else name
        for z, j in tj.items():
            if str(j) == key and z in _ZHI:
                res.append((z, '天将%s所乘' % key))
        return res
    if name in ('父母', '兄弟', '子孙', '妻财', '官鬼'):
        wx = _liuqin_names(ctx.get('ri_gan', '')).get(name, '')
        # 🔴 原文「类神**入课传为显**，入年命次之，俱不入为晦」⇒ 只在**七处**里找
        #    合该六亲之支（⛔ 不铺全部同五行支，否则「晦」被淹没）
        seen = set()
        for _lab, zz in _seven_positions(ctx):
            if _ZHI_WX.get(zz) == wx and zz not in seen:
                seen.add(zz)
                res.append((zz, '%s(五行%s)' % (name, wx)))
        return res
    if name == '驿马':
        rz = ctx.get('ri_zhi', '')
        ma = {'申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申',
              '巳': '亥', '酉': '亥', '丑': '亥', '亥': '巳', '卯': '巳', '未': '巳'}.get(rz, '')
        return [(ma, '驿马(按日支%s取)' % rz)] if ma else []
    if name in _ZHI:
        res.append((name, '直取地支'))
        return res
    return res


def _seven_positions(ctx):
    """七处 → [label, 支]（入课传为显，年命次之）。"""
    out = []
    sc = [z for z in (ctx.get('sanchuan') or []) if z]
    for i, nm in enumerate(('初传', '中传', '末传')):
        if i < len(sc):
            out.append((nm, sc[i]))
    if ctx.get('gan_shang'):
        out.append(('干上', ctx['gan_shang']))
    if ctx.get('zhi_shang'):
        out.append(('支上', ctx['zhi_shang']))
    if ctx.get('ben_ming'):
        out.append(('本命', ctx['ben_ming']))
    if ctx.get('xing_nian'):
        out.append(('行年', ctx['xing_nian']))
    return out


def quyong(zhanlei='', question='', ri_gan='', ri_zhi='', sanchuan=None,
           gan_shang='', zhi_shang='', ben_ming='', xing_nian='',
           tianjiang=None, yuejiang='', kongwang=None, tiandi_pan=None) -> dict:
    """问事 → 类神 → 取用链。返回结构化 dict（⛔ 叙事层，不进 valence）。"""
    ctx = {'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'sanchuan': sanchuan or [],
           'gan_shang': gan_shang, 'zhi_shang': zhi_shang, 'ben_ming': ben_ming,
           'xing_nian': xing_nian, 'tianjiang': tianjiang or {}, 'yuejiang': yuejiang,
           'tiandi_pan': tiandi_pan or {}}
    rules = match_rules(zhanlei, question)
    # 🆕 十二天将占类表（下 L11573-11575）—— 独立于 rules 的**直取通道**
    tj_names = lookup_tianjiang(zhanlei, question)
    if not rules and not tj_names:
        return {'占类': zhanlei, '命中规则': [], '类神': [],
                '年命': judge_nianming(ctx), '变通链': biantong_chain(zhanlei, question),
                '叙述': '未匹配到取用规则 ⇒ 按六亲通法（占财看妻财／占官看官鬼／占宅看父母）'}

    positions = _seven_positions(ctx)
    kw = set(kongwang or [])
    items = []
    for r in rules:
        for nm in list(r.get('主类神', [])) + list(r.get('辅类神', [])):
            is_main = nm in (r.get('主类神') or [])
            for z, how in _resolve(nm, ctx):
                hit = [(lab, zz) for lab, zz in positions if zz == z]
                ju = '显' if [h for h in hit if h[0] in ('初传', '中传', '末传', '干上', '支上')] \
                    else ('次' if hit else '晦')
                ws = ''
                try:
                    from engine.liuchen_shensha import wang_shuai as _ws
                    ws = _ws(_ZHI_WX.get(z, ''), yuejiang) if yuejiang else ''
                except Exception:
                    ws = ''
                items.append({
                    '类神': nm, '主/辅': '主' if is_main else '辅', '地支': z, '解析': how,
                    '依据': r.get('依据', ''), '断法': r.get('断', ''),
                    '入七处': [h[0] for h in hit], '显隐': ju,
                    '乘将': (tianjiang or {}).get(z, ''), '旺衰': ws,
                    '旬空': (z in kw) if kw else None,
                })
    # 🆕 天将直取（通解_下 L11573-11575）：占类 → 天将 → 所乘之支
    for nm in tj_names:
        for z, how in _resolve(nm, ctx):
            hit = [(lab, zz) for lab, zz in positions if zz == z]
            ju = '显' if [h for h in hit if h[0] in ('初传', '中传', '末传', '干上', '支上')] \
                else ('次' if hit else '晦')
            _ws2 = ''
            try:
                from engine.liuchen_shensha import wang_shuai as _wsf
                _ws2 = _wsf(_ZHI_WX.get(z, ''), yuejiang) if yuejiang else ''
            except Exception:
                _ws2 = ''
            items.append({'类神': nm, '主/辅': '主(天将直取)', '地支': z, '解析': how,
                          '依据': '通解_下 L11573-11575', '断法': '占类直取该天将（有则先用）',
                          '入七处': [h[0] for h in hit], '显隐': ju,
                          '乘将': (tianjiang or {}).get(z, ''), '旺衰': _ws2,
                          '旬空': (z in kw) if kw else None})
    seen = {}
    for it in items:
        k = (it['类神'], it['地支'])
        old = seen.get(k)
        # 🐛 首版 bug：同名同支经**两条路径**进入（rules 辅类神 ＋ 天将直取）⇒ 去重留了「辅」。
        #    修正：**取「主」**（天将直取＝原文点名，优先于辅类神）。
        if old is None:
            seen[k] = it
        elif str(it['主/辅']).startswith('主') and not str(old['主/辅']).startswith('主'):
            seen[k] = it
    uniq = list(seen.values())
    # 🔴 轻重权衡 ＝ **变通法优先链**（「有青龙看青龙…此为变通之法」，下 L11577）
    #    排序：显/次/晦 → 链内序次 → 主/辅
    chain = biantong_chain(zhanlei, question)

    def _rank(it):
        s = 0 if it['显隐'] == '显' else (1 if it['显隐'] == '次' else 2)
        # 🐛 首版 bug：链外「主类神」被赋 rank 0 ⇒ 与链首青龙并列，六亲反排在青龙前。
        #    修正：**链内按链序**，链外一律排在**链尾之后**（变通法「有青龙看青龙」⇒ 链内优先）。
        if it['类神'] in chain:
            c = chain.index(it['类神'])
        else:
            c = len(chain) + (0 if str(it['主/辅']).startswith('主') else 1)
        return (s, c)

    uniq.sort(key=_rank)
    return {'占类': zhanlei, '命中规则': [r.get('zhanlei', [''])[0] for r in rules],
            '天将直取': tj_names, '变通链': chain,
            '类神': uniq, '年命': judge_nianming(ctx),
            '取用链依据': '通解_上 L1387 注①＋下 L11573/11577'}


def narrate(res: dict) -> str:
    """把取用结果转成一行行叙述。"""
    if not res.get('类神'):
        return res.get('叙述', '')
    lines = ['取用链（据『先看七处，次看类神』）：']
    for it in res['类神']:
        p = []
        p.append('%s%s' % ('★' if str(it['主/辅']).startswith('主') else '·', it['类神']))
        p.append('→%s(%s)' % (it['地支'], it['解析']))
        p.append('显隐:%s' % it['显隐'])
        if it['入七处']:
            p.append('入' + '/'.join(it['入七处']))
        if it['乘将']:
            p.append('乘%s' % it['乘将'])
        if it['旺衰']:
            p.append(it['旺衰'])
        if it['旬空']:
            p.append('旬空')
        lines.append('  ' + ' '.join(p))
        if it['断法']:
            lines.append('    断法：%s（%s）' % (it['断法'], it['依据']))
    if res.get('变通链'):
        lines.append('变通优先链：%s（有前者先用，⛔ 不跳级）' % ' → '.join(res['变通链']))
    for lbl, z, up, rel in (res.get('年命') or []):
        if up:
            lines.append('  【年命】%s%s 上神%s %s' % (lbl, z, up, rel))
    return '\n'.join(lines)


if __name__ == '__main__':
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    demo = dict(zhanlei='求财', ri_gan='乙', ri_zhi='未',
                sanchuan=['丑', '戌', '未'], gan_shang='丑', zhi_shang='戌',
                tianjiang={'丑': '青龙', '戌': '太常', '未': '白虎'}, yuejiang='戌')
    print(narrate(quyong(**demo)))
