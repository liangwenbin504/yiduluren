# -*- coding: utf-8 -*-
"""六亲象域展示层（A′ 方案，2026-09-23；🔴 **零评分影响**，只陈述课象、不预测归属）

【为何是 A′ 而不是 A】
憨爷原意 A＝"凶应落在谁身上／由何事引发"。2026-09-23 可行性验证（218 案）：
  · 预测「最凶位的六亲」命中 **27.4%**，低于随机基线 **40.3%**／恒猜众数 **43.5%**
  · 公平特征扫描（25 特征 × 5 六亲）：单一特征**全哑**，进榜组合**互相矛盾**
    （末传妻财→兄弟 2.53x、初传父母→子孙 1.91x）⇒ 多重比较假象，**确证无信号**
⇒ 故 **A（预测式归属）不可做**；本层降级为 **A′：照实陈述课传各位的六亲与状态**，
   ⛔ **不写"凶应在某人"**，⛔ 不给归属结论，⛔ 不进评分链。

【原文依据】
  六亲定义：**「同类者为兄弟，生我者为父母，我生者为子孙，克我者为官鬼，我克者为妻财」**　下 L13114
  我克为财：「**我克者为财**，有就地取财之义」　　　　　　　　　　　　　　　　　　　　　上 L3240
  我克/克我：「**我克者为死，克我者为囚**」　　　　　　　　　　　　　　　　　　　　　　中 L1544
  生我者空亡：「占父母病死尤急，如占子息病无畏…缘**生我者空亡**故也」　　　　　　　　中 L4763
  　　　　　　「如**生我者空亡**，占父母上人病，主不救，占干上位亦是徒然」　　　　　　中 L8046
  　　　　　　「惟**生我者**及救神并天德、生气、财官…并不宜空亡，皆返为凶兆」　　　　中 L8037

【取用处】干上·干阴·支上·支阴·初传·中传·末传·年命（与 guishen_xiang_engine 同口径）
【六亲真源】`engine.liuqin_engine.LiuQinCalculator.get_liuqin`（生产同源，⛔ 不另立一份）
"""
from typing import Any, Dict, List

ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
          '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

# 六亲 →（关系说明, 原文）
LIUQIN_REL = {
    '父': ('生我者', '下L13114「生我者为父母」'),
    '鬼': ('克我者', '下L13114「克我者为官鬼」'),
    '子': ('我生者', '下L13114「我生者为子孙」'),
    '财': ('我克者', '下L13114「我克者为妻财」；上L3240「我克者为财」'),
    '兄': ('同类者', '下L13114「同类者为兄弟」'),
}
# ── 十二长生（🆕 2026-11-25 补）
#    起因：《断案》§疾病13·166「亥加申、巳加寅，各临长生」——该支**自身五行**的长生位在地盘。
#    ⛔ 勿与「巳为庚之长生」（该支是**日干**的长生位）混为一谈，二者是两回事；
#    ⛔ 更不能读成「巳去生金」——长生是「位」的关系，不是生克动作。
#   十干长生（阳顺阴逆）：甲亥・乙午・丙寅・丁酉・戊寅・己酉・庚巳・辛子・壬申・癸卯
#   五行长生（土双位：水土同宫申 / 火土同宫寅）：木亥・火寅・土(申,寅)・金巳・水申
#   五行墓／绝：木未/申・火戌/亥・土辰/(巳,亥)・金丑/寅・水辰/巳
#   ⚠️ 只在**展示层**标注，⛔ 不参与六亲判定、⛔ 不进评分链。
CHANG_SHENG_10 = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
                  '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}
WX_CHANG_SHENG = {'木': '亥', '火': '寅', '土': ('申', '寅'), '金': '巳', '水': '申'}
WX_MU = {'木': '未', '火': '戌', '土': '辰', '金': '丑', '水': '辰'}
WX_JUE = {'木': '申', '火': '亥', '土': ('巳', '亥'), '金': '寅', '水': '巳'}


def _lin_changsheng(z: str, tdp: dict) -> str:
    """**临长生**（原文口径）：该支所临地盘 ＝ 其**自身五行**的长生位。
    例：《通解》下卷 §疾病13·166「亥加申、巳加寅，各临长生」——
        亥水长生在申（天盘亥临地盘申）、巳火长生在寅（天盘巳临地盘寅）⇒ 水火寒热往来之象。
    ⚠️ 与 `_cs_jue_mu`（该支是否为**日干**之长生/墓/绝）是两回事，⛔ 不可混。"""
    if not z:
        return ''
    cs = WX_CHANG_SHENG.get(ZHI_WX.get(z, ''), '')
    cands = list(cs) if isinstance(cs, (tuple, list)) else [cs]
    for d, t in (tdp or {}).items():
        if t == z and d in [x for x in cands if x]:
            return '%s加%s' % (z, d)
    return ''


def _cs_jue_mu(z: str, ri_gan: str) -> str:
    """该支相对**日干**的十二长生标记：长生／墓／绝（都不是则 ''）。
    十干长生与五行长生**两路都认**（庚金：十日干长生=巳、五行金长生=巳，二者同指）。"""
    if not z or not ri_gan:
        return ''
    gwx = GAN_WX.get(ri_gan, '')

    def _in(val, target):
        if isinstance(val, (tuple, list, set)):
            return target in val
        return bool(val) and val == target
    if z == CHANG_SHENG_10.get(ri_gan, '') or _in(WX_CHANG_SHENG.get(gwx, ''), z):
        return '长生'
    if _in(WX_MU.get(gwx, ''), z):
        return '墓'
    if _in(WX_JUE.get(gwx, ''), z):
        return '绝'
    return ''


# 位权重（显要度，仅用于排序；⛔ 不用于预测）
POS_W = {'初传': 5, '支上': 4, '干上': 3, '年命': 3,
         '干阴': 2, '支阴': 2, '中传': 2, '末传': 1}


def _wangshuai(zhi: str, yue_jian: str) -> str:
    zw, yw = ZHI_WX.get(zhi, ''), ZHI_WX.get(yue_jian, '')
    if not zw or not yw:
        return ''
    if zw == yw:
        return '旺'
    if WX_SHENG.get(yw) == zw:
        return '相'
    if WX_SHENG.get(zw) == yw:
        return '休'
    if WX_KE.get(zw) == yw:
        return '囚'
    return '死'


def _qu_yong_chu(env: Dict[str, Any]) -> List[tuple]:
    """取用处：四课四上神＋三传＋年命（与 guishen_xiang_engine._qu_yong_chu 同口径）"""
    sc = list(env.get('sanchuan') or [])
    sk = env.get('sike') or env.get('si_ke') or []

    def _shang(i):
        try:
            return sk[i][1] or ''
        except Exception:
            return ''

    pos = [('干上', env.get('gan_shang') or _shang(0)),
           ('干阴', _shang(1)),
           ('支上', env.get('zhi_shang') or _shang(2)),
           ('支阴', _shang(3)),
           ('初传', sc[0] if len(sc) > 0 else ''),
           ('中传', sc[1] if len(sc) > 1 else ''),
           ('末传', sc[2] if len(sc) > 2 else '')]
    bm = env.get('ben_ming_zhi') or ''
    if bm:
        pos.append(('年命', bm))
    return [(p, z) for p, z in pos if z]


def suggest(env: Dict[str, Any], judged: Dict[str, Any] = None) -> Dict[str, Any]:
    """产出「课传各位的六亲与状态」——🔴 **只陈述，不预测归属**，零评分影响。"""
    out: Dict[str, Any] = {'象域': False, '位': [], '类象语': '',
                           '原文直引': [], '依据': []}
    try:
        ri_gan = str(env.get('ri_gan') or '')
        if not ri_gan:
            return out
        # 🔴 六亲真源＝生产同源 LiuQinCalculator（⛔ 不用 calibration.liuqin_of，
        #    那份走十神名且历史上有死代码 BUG；生产显示走的是 liuqin_engine）
        from engine.liuqin_engine import LiuQinCalculator
        _lqc = LiuQinCalculator()
        tj = dict(env.get('tian_jiang') or {})       # 🔴 {天盘支: 天将}
        kw = set(env.get('kongwang') or [])
        yue_jian = env.get('yue_zhi', '') or env.get('yue_jian', '') or ''
        gwx = GAN_WX.get(ri_gan, '')

        rows = []
        for p, z in _qu_yong_chu(env):
            q = str(_lqc.get_liuqin(ri_gan, z) or '')
            if not q:
                continue
            rel, src = LIUQIN_REL.get(q, ('', ''))
            ws = _wangshuai(z, yue_jian)
            zwx = ZHI_WX.get(z, '')
            ke_note = ''
            if gwx and zwx:
                if WX_KE.get(zwx) == gwx:
                    ke_note = '支克干'
                elif WX_KE.get(gwx) == zwx:
                    ke_note = '干克支'
            rows.append({
                '位': p, '支': z, '六亲': q, '关系': rel, '天将': tj.get(z, '') or '',
                '空亡': z in kw, '旺衰': ws, '生克': ke_note,
                '长生': _cs_jue_mu(z, ri_gan),      # 长生／墓／绝（相对**日干**）
                '临长生': _lin_changsheng(z, env.get('tiandi_pan') or {}),   # 临**自身五行**长生（原文口径）
                '显': POS_W.get(p, 0), '原文': src,
            })
        if not rows:
            return out
        rows.sort(key=lambda r: -r['显'])
        out['位'] = rows
        out['象域'] = True

        # ── 陈述式类象语（⛔ 只说"课上是何六亲、何状态"，不说"凶应在谁"）──
        segs = []
        for r in rows:
            s = '%s%s为%s' % (r['位'], r['支'], r['六亲'])
            tail = []
            if r['天将']:
                tail.append('乘' + r['天将'])
            if r['旺衰']:
                tail.append(r['旺衰'])
            if r['空亡']:
                tail.append('空')
            if r['生克']:
                tail.append(r['生克'])
            if tail:
                s += '（' + '·'.join(tail) + '）'
            # 🆕 「巳为庚之长生」这类必须能看见：读者才知道该支在日干处是「位」不是「克」
            # 「临长生」只在**水火**两支入类象语：原文取亥、巳以象寒热往来；
            # 其余支同样临长生时不逐一铺陈（字段里仍有，需要可查）。
            if r.get('临长生') and ZHI_WX.get(r['支']) in ('水', '火'):
                s += '｜%s（临长生·寒热之象）' % r['临长生']
            if r.get('长生'):
                s += '｜%s为%s之%s' % (r['支'], ri_gan, r['长生'])
            segs.append(s)
        out['类象语'] = '；'.join(segs)

        # ── 原文直引（⛔ 只在原文**明确说了**时才引，不是推断）──
        for r in rows:
            if r['六亲'] == '父' and r['空亡']:
                out['原文直引'].append(
                    '%s%s为父母而空：中L8046「生我者空亡，占父母上人病，主不救」'
                    '／中L4763「占父母病死尤急…缘生我者空亡故也」' % (r['位'], r['支']))
        out['依据'].append('下L13114「同类者为兄弟，生我者为父母，我生者为子孙，'
                           '克我者为官鬼，我克者为妻财」')
        out['依据'].append('上L3240「我克者为财，有就地取财之义」／中L1544「我克者为死，克我者为囚」')
        out['依据'].append('「临长生」＝该支所临地盘为其**自身五行**长生位'
                           '（《通解》下卷 §疾病13·166「亥加申、巳加寅，各临长生」）；'
                           '类象语只列水火两支以象寒热，其余支临长生同理不赘')
        out['依据'].append('十二长生（十干：甲亥乙午丙寅丁酉戊寅己酉庚巳辛子壬申癸卯；'
                           '五行：木亥火寅土申/寅金巳水申）—— 「长生」与「六亲」是**两个维度**，'
                           '巳对庚金既是克我之鬼、又是金之长生，二义并存 ⛔ 不相废')
        return out
    except Exception as e:                            # 🔴 异常绝不外溢
        out['error'] = str(e)
        return out
