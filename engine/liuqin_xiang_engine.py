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
        return out
    except Exception as e:                            # 🔴 异常绝不外溢
        out['error'] = str(e)
        return out
