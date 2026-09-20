# -*- coding: utf-8 -*-
"""类神取用选择器 —— 分层取用（据《大六壬断案疏正》44 处「类神」判据）

【背景】原 `leishen_engine.get_category_leishen` 只做「查表取候选」，
候选**并列输出**、不分主次，不参与年命/行年，空亡仅事后减分。
本模块把**原文已有的取用次序**落进代码。

【原文依据】（`engine/duanan_knowledge_base.py`）
  第1层 入传否   「类神入传者行人即至」「类神不入传主不见无期」
  第2层 入传位置 「类神临初传速，中传中，末传迟」「臨初传主速见，临末传主迟见」
  第3层 临日辰   「类神加日辰不空主定见，应期速」
  第4层 空亡     「类神不宜落空亡」「类神逢空主走失寻不得，待填实之日」
                 「类神与日或刑冲破害或空亡绝不济事」
  第5层 生旺     「类神临生旺大吉，临死绝囚墓大凶」「临生旺主一生得助，休囚主蹉跎」
                 「类神临生旺之方或今日长生之方则大吉」
  第6层 与日关系 「类神所临之宫生日或比则可蓄养孳息利益」
                 「所临之处克或刑或害则不可养损失不利」
  第7层 行年     「类神**次看**行年方位便知去住留还」← 原文用"次看"，明标次序在后
  补充           「类神临处地盘为物命」

【设计】纯新增模块，**不改老引擎**，供 A/B 对照使用。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
LIUCHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
LIUHAI = {'子': '未', '未': '子', '丑': '午', '午': '丑', '寅': '巳', '巳': '寅',
          '卯': '辰', '辰': '卯', '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'}
XING = {'寅': '巳', '巳': '申', '申': '寅', '丑': '戌', '戌': '未', '未': '丑',
        '子': '卯', '卯': '子', '辰': '辰', '午': '午', '酉': '酉', '亥': '亥'}
# 季节 → 旺相休囚死（支五行状态）
SEASON_WANG = {'春': '木', '夏': '火', '秋': '金', '冬': '水'}
SEASON_XIANG = {'春': '火', '夏': '土', '秋': '水', '冬': '木'}
SEASON_XIU = {'春': '水', '夏': '木', '秋': '土', '冬': '金'}
SEASON_QIU = {'春': '金', '夏': '水', '秋': '火', '冬': '土'}
SEASON_SI = {'春': '土', '夏': '金', '秋': '木', '冬': '火'}

# 档次（按原文语义，从低到高）
TIERS = ['绝不济事', '无期', '迟应', '中应', '速应', '定见速应']


def _wx(z):
    return GAN_WX.get(z, '') or ZHI_WX.get(z, '')


def _wx_state(zhi, season):
    """旺相休囚死（据季节）"""
    w = _wx(zhi)
    if not w or not season:
        return ''
    if SEASON_WANG.get(season) == w:
        return '旺'
    if SEASON_XIANG.get(season) == w:
        return '相'
    if SEASON_XIU.get(season) == w:
        return '休'
    if SEASON_QIU.get(season) == w:
        return '囚'
    if SEASON_SI.get(season) == w:
        return '死'
    return ''


def _season_of(ri_zhi):
    return {'寅': '春', '卯': '春', '辰': '春', '巳': '夏', '午': '夏', '未': '夏',
            '申': '秋', '酉': '秋', '戌': '秋', '亥': '冬', '子': '冬', '丑': '冬'}.get(ri_zhi, '')


def score_leishen(z, *, sanchuan, gan_shang='', zhi_shang='', ri_gan='', ri_zhi='',
                  kongwang=(), tian_jiang=None, xing_nian='', season='',
                  di_pan_of=None):
    """按原文 7 层给单个候选类神打分

    返回 {'leishen','score','tier','evidence':[...],'dims':{...}}
    """
    sc = list(sanchuan or [])
    kw = set(x for x in (kongwang or []) if x)
    tj = tian_jiang or {}
    season = season or _season_of(ri_zhi)
    score = 0
    tier = '无期'
    ev = []
    dims = {}

    # ── 第1层：入传否（原文第一原则）──
    if z in sc:
        pos = sc.index(z)
        tier = ['速应', '中应', '迟应'][pos]
        score += [5, 3, 2][pos]
        ev.append('入%s' % ['初传', '中传', '末传'][pos])
        dims['入传'] = ['初传', '中传', '末传'][pos]
    else:
        score -= 2
        ev.append('不入传（无期）')
        dims['入传'] = '不入'

    # ── 第2层：临日辰（"加日辰不空主定见，应期速"）──
    if z and z == gan_shang:
        score += 4
        tier = TIERS[max(TIERS.index(tier), TIERS.index('定见速应'))]
        ev.append('临干上（定见）')
        dims['临日辰'] = '干上'
    elif z and z == zhi_shang:
        score += 3
        tier = TIERS[max(TIERS.index(tier), TIERS.index('速应'))]
        ev.append('临支上')
        dims['临日辰'] = '支上'

    # ── 第3层：空亡（"绝不济事"）──
    if z in kw:
        score -= 6
        tier = '绝不济事'
        ev.append('落空亡（绝不济事）')
        dims['空亡'] = True
    else:
        dims['空亡'] = False

    # ── 第4层：生旺休囚（"临生旺大吉，临死绝囚墓大凶"）──
    st = _wx_state(z, season)
    if st:
        dims['旺衰'] = st
        if st in ('旺', '相'):
            score += 2
            ev.append('临%s' % st)
        elif st in ('囚', '死'):
            score -= 2
            ev.append('临%s（衰）' % st)
        # 「临生旺之方或今日长生之方则大吉」——临长生另计
    # 临长生之地（原文"临长生之地主…速"）
    CS = {'木': '亥', '火': '寅', '金': '巳', '水': '申', '土': '申'}
    if ri_gan and _wx(ri_gan) and CS.get(_wx(ri_gan)) == z:
        score += 2
        ev.append('临日干长生（大吉）')
        dims['长生'] = True

    # ── 第5层：与日关系（"生日或比则可…克或刑或害则不可"）──
    gw = _wx(ri_gan)
    zw = _wx(z)
    if gw and zw:
        if SHENG.get(zw) == gw:
            score += 2
            ev.append('生日干')
            dims['与日'] = '生'
        elif zw == gw:
            score += 1
            ev.append('与日比')
            dims['与日'] = '比'
        elif KE.get(zw) == gw:
            score -= 3
            ev.append('克日干')
            dims['与日'] = '克'
    if ri_zhi and z:
        if LIUCHONG.get(z) == ri_zhi:
            score -= 3
            ev.append('与日支相冲')
            dims['刑冲破害'] = '冲'
        if XING.get(z) == ri_zhi:
            score -= 2
            ev.append('刑日支')
            dims.setdefault('刑冲破害', '刑')
        if LIUHAI.get(z) == ri_zhi:
            score -= 2
            ev.append('害日支')
            dims.setdefault('刑冲破害', '害')

    # ── 第6层：所临地盘（"类神临处地盘为物命"）──
    if di_pan_of and z in di_pan_of:
        dims['所临地盘'] = di_pan_of[z]

    # ── 第7层：行年（原文"次看行年方位"）──
    if xing_nian and z == xing_nian:
        score += 2
        ev.append('临行年')
        dims['行年'] = True

    # ── 天将（辅助：乘吉将加分，凶将减分；与占类吉凶取向配合见上层）──
    jiang = tj.get(z, '')
    if jiang:
        dims['天将'] = jiang

    return {'leishen': z, 'score': score, 'tier': tier, 'evidence': ev, 'dims': dims}


def select_leishen(candidates, *, sanchuan, gan_shang='', zhi_shang='', ri_gan='',
                   ri_zhi='', kongwang=(), tian_jiang=None, xing_nian='',
                   season='', tiandi_pan=None, top_n=3):
    """从候选类神中**分层优选**，定出主类神

    参数 candidates: 候选类神地支（list）—— 沿用旧引擎的 zhi_list
    返回 {'主类神','档次','取用依据','候选明细','候选数'}
    """
    sc = list(sanchuan or [])
    # 天盘支 → 地盘支（反查，"类神临处地盘为物命"）
    di_pan_of = {}
    for dp, tp in (tiandi_pan or {}).items():
        if tp:
            di_pan_of.setdefault(tp, dp)

    uniq = []
    for c in (candidates or []):
        if c and c not in uniq:
            uniq.append(c)
    if not uniq:
        return {'主类神': '', '档次': '无候选', '取用依据': [], '候选明细': [], '候选数': 0}

    rows = [score_leishen(c, sanchuan=sc, gan_shang=gan_shang, zhi_shang=zhi_shang,
                          ri_gan=ri_gan, ri_zhi=ri_zhi, kongwang=kongwang,
                          tian_jiang=tian_jiang, xing_nian=xing_nian, season=season,
                          di_pan_of=di_pan_of)
            for c in uniq]
    # 排序：先按档次（原文语义优先），再按分数
    rows.sort(key=lambda r: (-TIERS.index(r['tier']), -r['score']))
    best = rows[0]
    return {
        '主类神': best['leishen'],
        '档次': best['tier'],
        '取用依据': best['evidence'],
        '候选明细': rows[:max(1, top_n)],
        '候选数': len(uniq),
    }
