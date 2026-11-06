# -*- coding: utf-8 -*-
"""
六亲×神煞 冲突守卫（零评分层）
==============================================================
【起因 2026-10-19】真实案例 #004 断错（INC-20240426-001）：
  三传 庚申 → 甲寅 → 丁巳，憨爷断「吉」，实际大亏二三十万＋官讼。
  根因是**同一个错误犯了两次**：
    初传 庚申：取了「禄神」，舍了「兄弟（劫财）」
    末传 丁巳：取了「长生」，舍了「官鬼（官讼）」
  ⇒ 他舍掉的每一个字，都成了现实。

【本守卫要做什么】不是替人断，是**把歧义点摆到台面上**：
  当某一爻「六亲属性」与「神煞属性」指向相反时，标注出来，
  并提示「一字多义，须先定六亲」。
  ⛔ **零评分：绝不修改 score / grade / veto，只产出展示字段。**

【设计原则】
  1. 只检「凶亲 + 吉神」一种冲突（#004 型，最明确、误报最低）。
     「吉亲 + 凶煞」方向不检 —— 吉亲本身吉凶依占类而变，易误报。
  2. 六亲只把 **兄弟、官鬼** 视为明确凶亲（劫财 / 鬼），其余标中性。
  3. 天将单列「参考」，不参与冲突判定 —— 憨爷定则原话是「六亲优先于**神煞**」。

依据：
  · 六亲真源 ＝ `engine/liuqin_engine.LiuQinCalculator`（生产同源，⛔ 不另算）
  · 神煞真源 ＝ `shensha_xiang.落点`（⛔ 不另起例）
  · 禄 / 长生 不在 shensha_xiang 层，按日干查表补算（下表有原文出处）
  · 铁律「一字多义时，六亲优先于神煞」（MEMORY · 术语/叙事）

⛔ 本模块只读、纯函数、无副作用、不起线程。
"""
from typing import Any, Dict, List

# ── 日干之禄（甲禄寅…癸禄子）：通解·上「禄」起例 ──
_GAN_LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
           '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}

# ── 日干长生（十干长生，火土同宫）：通解·上「十二长生」 ──
_GAN_CHANGSHENG = {'甲': '亥', '乙': '午', '丙': '寅', '丁': '酉', '戊': '寅',
                   '己': '酉', '庚': '巳', '辛': '子', '壬': '申', '癸': '卯'}

# ── 六亲凶亲（劫财 / 鬼）—— 通用倾向，不随占类变 ──
# ⚠️ 2026-10-19：LiuQinCalculator.get_liuqin() 实际返回**单字**
#    （父/鬼/子/财/兄），非双字。初版按双字写导致正例检不出（自检当场抓出）。
#    故此处单双字并存，兼容不同调用源的写法。
_XIONG_QIN = {
    '兄': '劫财、分夺、竞争',
    '兄弟': '劫财、分夺、竞争',
    '鬼': '鬼祟、官讼、病灾、克身',
    '官鬼': '鬼祟、官讼、病灾、克身',
}

# 展示用全称（单字→全称）
_QIN_LABEL = {'父': '父母', '鬼': '官鬼', '子': '子孙', '财': '妻财', '兄': '兄弟'}

# ── 吉神（禄 / 长生 由表算；其余在此登记，便于以后扩展）──
_JI_SHEN = {
    '禄神': '日干临官之地，主俸禄、根基',
    '长生': '日干长生之地，主生发、不绝',
}

# ── shensha_xiang 中视为「吉」的煞名（其余一律不计入冲突，避免误报）──
# ⚠️ 2026-10-19：本表只列**吉神**。⛔ 不得加入任何带歧义史的煞名
#    （闸口 `_test_shensha_xiang.py` 对特定词做「engine/ 内恰好 2 文件」断言，
#     本模块写入即会触发 FAIL —— 连注释里出现都不行，因闸口为全文检索）。
_JI_SHA = {'天喜', '生气', '天医', '成神', '皇书', '天马'}


def _lu_of(ri_gan: str) -> str:
    return _GAN_LU.get(ri_gan or '', '')


def _cs_of(ri_gan: str) -> str:
    return _GAN_CHANGSHENG.get(ri_gan or '', '')


def _sha_by_zhi(shensha_xiang: Dict[str, Any]) -> Dict[str, List[str]]:
    """从 shensha_xiang.落点 汇总：{支: [煞名...]}"""
    out: Dict[str, List[str]] = {}
    if not isinstance(shensha_xiang, dict):
        return out
    for item in (shensha_xiang.get('落点') or []):
        zhi = str(item.get('支') or '')
        sha = str(item.get('煞') or '')
        if zhi and sha:
            out.setdefault(zhi, [])
            if sha not in out[zhi]:
                out[zhi].append(sha)
    return out


def detect(ri_gan: str, sanchuan: List[str],
           tianjiang_map: Dict[str, str] = None,
           shensha_xiang: Dict[str, Any] = None,
           zhanlei: str = '') -> Dict[str, Any]:
    """检测「凶亲 + 吉神」并存之爻。

    参数：
        ri_gan         日干（如 '庚'）
        sanchuan       三传地支列表 [初,中,末]
        tianjiang_map  {天盘支: 天将}（仅作参考展示，不参与判定）
        shensha_xiang  神煞象意层输出（只取 .落点）
        zhanlei        占类（仅展示，不改判定）

    返回（零评分层，仅供展示）：
        {'守卫': True, '冲突数': n, '冲突': [...], '说明': [...], '依据': [...]}
    """
    ri_gan = (ri_gan or '').strip()[:1]
    # ⚠️ 2026-10-19：调用源可能传 {天盘支:天将}（dict）或 三传天将列表（list）。
    #    列表形式按三传顺序 zip 成 dict，避免调用方各自转换出错。
    if isinstance(tianjiang_map, (list, tuple)):
        tianjiang_map = {z: j for z, j in zip((sanchuan or [])[:len(tianjiang_map)],
                                              tianjiang_map)}
    tianjiang_map = tianjiang_map or {}
    sha_map = _sha_by_zhi(shensha_xiang)

    try:
        from engine.liuqin_engine import LiuQinCalculator
        LQ = LiuQinCalculator()
    except Exception:
        LQ = None

    lu_zhi = _lu_of(ri_gan)
    cs_zhi = _cs_of(ri_gan)

    conflicts: List[Dict[str, Any]] = []
    notes: List[str] = []

    for idx, zhi in enumerate((sanchuan or [])[:3]):
        if not zhi:
            continue
        pos = ['初传', '中传', '末传'][idx]

        liuqin = ''
        if LQ is not None:
            try:
                liuqin = LQ.get_liuqin(ri_gan, zhi) or ''
            except Exception:
                liuqin = ''

        # 该爻命中的「吉神」
        ji_hits: List[str] = []
        if zhi and zhi == lu_zhi:
            ji_hits.append('禄神')
        if zhi and zhi == cs_zhi:
            ji_hits.append('长生')
        for s in sha_map.get(zhi, []):
            if s in _JI_SHA and s not in ji_hits:
                ji_hits.append(s)

        # 该爻命中的「凶煞」（仅展示，不参与冲突判定）
        xiong_sha = [s for s in sha_map.get(zhi, []) if s not in _JI_SHA]

        jiang = tianjiang_map.get(zhi, '')

        if liuqin in _XIONG_QIN and ji_hits:
            full = _QIN_LABEL.get(liuqin, liuqin)
            conflicts.append({
                '位': pos,
                '支': zhi,
                '六亲': full,
                '六亲凶义': _XIONG_QIN[liuqin],
                '同爻吉神': ji_hits,
                '同爻凶煞': xiong_sha,
                '天将': jiang,
                '冲突类型': '凶亲配吉神',
                '原文原字': liuqin,
                '提示': ('一字多义：%s既是「%s」又是「%s」。'
                         '按「六亲优先于神煞」，须先以六亲定事体，'
                         '再议神煞吉凶 —— ⛔ 不可只取吉义。'
                         % (zhi, full, '、'.join(ji_hits))),
            })

    zl = ('（占类：%s）' % zhanlei) if zhanlei else ''
    if conflicts:
        notes.append('本课有 %d 处「凶亲配吉神」%s，属取喜忘忌高风险结构：'
                     '真实案例 #004 即因此断吉而实大凶。' % (len(conflicts), zl))
        notes.append('⛔ 本守卫只提示歧义，不改变吉凶判定 —— 请人工裁定。')
    else:
        notes.append('未检出「凶亲配吉神」结构%s。' % zl)

    return {
        '守卫': True,
        '冲突数': len(conflicts),
        '冲突': conflicts,
        '说明': notes,
        '依据': [
            '六亲真源＝LiuQinCalculator（生产同源）',
            '神煞真源＝shensha_xiang.落点',
            '禄／长生按日干查表（通解·上 禄起例 / 十二长生）',
            '铁律：一字多义时六亲优先于神煞（MEMORY·术语）',
            '案例出处：INC-20240426-001（2024 占烤烟，断吉实大凶）',
        ],
        '评分影响': '无（零评分层）',
    }
