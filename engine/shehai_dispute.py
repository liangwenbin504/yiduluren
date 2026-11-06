# -*- coding: utf-8 -*-
"""涉害法争议检测（叙事层·零评分影响）
================================================
背景：涉害是九宗门中唯一自带争议的起课法（深浅算法各家不同；
     本项目另有 09-10 移植的邵公古法「干来加支即发用」会短路深浅）。

本模块**不改三传、不进评分**，只把「同一课存在两说」显式化，避免静默取一。

古籍链（另说口径）：下贼上优先于上克下 → 比用（与日干阴阳比）→ 涉害深浅 → 打平取孟仲季
古籍依据：
  《六壬辑要启蒙》「临孟发用曰见机……则以临于寅申巳亥上者为用。因临孟者涉害较深。」
  《六壬精要》例二（丙子日 辰时 亥将）「巳火为孟神，便弃去寅木，取孟上子水发用」
  《断案》§交易谋为10·148 / §亡盗15·188 / §六畜走失14·185（干来加支即发用，现行取法依据）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2  # noqa: E402

MENG = set('寅申巳亥')     # 四孟
ZHONG = set('子午卯酉')    # 四仲
JI = set('辰戌丑未')       # 四季


def _rank(pos):
    if pos in MENG:
        return 3
    if pos in ZHONG:
        return 2
    return 1                # 季


def shehai_dispute(ri_gan, ri_zhi, yue_jiang, shi_chen):
    """返回争议描述 dict；非涉害课返回 None"""
    c = SiKeSanChuanCalculator2()
    tp = c.get_tiandi_pan(yue_jiang, shi_chen)
    sike = c.qi_sike(ri_gan, ri_zhi, tp)
    r = c.fa_sanchuan(sike, ri_gan, ri_zhi, tp, shi_chen)
    fa = str(r.get('起法', ''))
    if '涉害' not in fa:
        return None
    cur = r.get('初传')

    # ---- 另说：古籍链重算 ----
    yang_ri = c.is_yang_ri(ri_gan)
    zei, ke = [], []        # 下贼上 / 上克下
    for _name, shang, xia, _j in sike:
        if c.is_ke(shang, xia, ri_gan):
            # 下贼上：下神克上神；上克下：上神克下神（此处用 is_ke 粗判，再细分）
            pass
    # 细分上下（用 c.is_ke 只能判「有克」），改按五行自判
    WX = c.DIZHI_WU_XING
    KE = c.WU_XING_KE       # {A: B} A克B ?
    for _name, shang, xia, _j in sike:
        xg = c.TIAN_GAN_JI_GONG.get(xia, xia)      # 下神（天干转寄宫）
        sw, xw = WX.get(shang, ''), WX.get(xg, '')
        if not sw or not xw:
            continue
        if xw and sw and KE.get(xw) == sw:         # 下克上
            zei.append((shang, xia))
        elif KE.get(sw) == xw:                     # 上克下
            ke.append((shang, xia))
    cand = zei if zei else ke
    if not cand:
        return None

    # 比用：与日干阴阳比者
    bi = [(s, x) for s, x in cand
          if c.is_yang_zhi(s) == yang_ri]
    if not bi:
        bi = cand

    # 涉害深浅
    def depth(s, x):
        return c._calculate_she_hai_depth(s, x, tp)

    scored = [(depth(s, x), s, x) for s, x in bi]
    mx = max(d for d, _, _ in scored)
    top = [(s, x) for d, s, x in scored if d == mx]
    if len(top) == 1:
        other, tie = top[0][0], False
    else:
        # 打平 → 孟仲季（按上神所临地盘位）
        def pos_of(s, x):
            xg = c.TIAN_GAN_JI_GONG.get(x, x)
            # 上神 s 所临地盘位
            for d, t in tp.items():
                if t == s and d == xg:
                    return d
            # 回退：当下神位置即上神所临
            return xg
        top.sort(key=lambda sx: -_rank(pos_of(*sx)))
        other, tie = top[0][0], True

    if other == cur:
        return None
    return {
        '争议': True,
        '现行初传': cur,
        '现行起法': fa,
        '另说初传': other,
        '另说口径': '涉害深浅%s' % ('打平取孟仲季' if tie else '最深者'),
        '备注': '涉害为九宗门中唯一有争议之门；现行取法若为「干来加支」则系邵公古法短路深浅',
    }


if __name__ == '__main__':
    print(shehai_dispute('甲', '辰', '申', '戌'))   # 北大 image14
