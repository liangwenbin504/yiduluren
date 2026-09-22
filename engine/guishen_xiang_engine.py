# -*- coding: utf-8 -*-
"""鬼神／祠庙取象层（2026-09-22 新建；🔴 **零评分影响**，只出"祷于何处"不进分）

【背景】
单案回测《断案疏正》§疾病13·169（戊午日亥将戌时占病）时，邵公断「急告东岳」，
此前判定为"师承专名、无原文支撑、永久搁置"。2026-09-22 重查《通解》后**修正该判断**：
原文支撑的不是"东岳"这个专名，而是「**鬼神/寺观象域 ＋ 方位 ＋ 神格 ＋ 远近**」这套象法。

【原文依据】
  未＝神鬼·祭祀　　：「未主五味、**祭祀、神鬼**、酒食、桑木、樽壶」　下 L9631
  未临宅＝鬼神　　　：「申加未，未临宅，**未主鬼神**也」　　　　　　　下 L1182
  子＝祷祝鬼神　　　：「子主妇人、布帛、裁制、**祷祝鬼神**」　　　　　下 L9598
  寅申＝寺观　　　　：「**寅申为寺观**，申乃空亡，是空中神祇来克我也」下 L4556
  辰＝寺观　　　　　：「龙居辰上，**主寺观**」　　　　　　　　　　　　下 L10788
  申＝僧（谐音法）　：「申与僧同音，故曰询之僧人」　　　　　　　　　　下 L10788
  戌＝塑画（神像）　：「戌主印绶、兵器、**塑画**、土物、刑狱」　　　　下 L9643
  地支方位　　　　　：「寅卯辰东方…丑寅东北、卯正东、辰巳东南、午正南、
    　　　　　　　　　 未申西南、酉正西、戌亥西北」（子正北）　　　　上 L865

【算法】三段式的前两段（第三段"定名"⛔ 引擎不做，交回人与当地环境）
  ① 象域判定：课传六处见神祠支 **且** 同现幽冥煞/幽冥将 ⇒ 鬼神象域成立
  ② 候选排序：按 位置(发用>支上>干上>中>末) ＋ 神格(大帝级/小祠) ＋ 旺衰 ＋ 方位 ＋ 远近
     输出 **top-3 候选**，每条带原文行号；**不产出唯一专名**。

【产出】{象域, 强度, 候选[], 建议语, 依据[]}
⛔ 只提示不判分；⛔ 用户回填的"当地真实庙名"属第③段，**绝不反向进入评分链**。
"""
from typing import Any, Dict, List

ZHI_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火',
          '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土',
          '丑': '土', '未': '土'}
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# ── 神祠支 →（建筑类, 取象用法, 原文依据）──
#    ⛔ 用法分类来自 218 案回测（2026-09-22）：邵公取此象 63% 断**地**、33% 断**人**、4% 断**物事**。
SHENCI_ZHI = {
    '寅': ('寺观', '地', '下L4556「寅申为寺观」'),
    '申': ('寺观／僧舍', '地·人', '下L4556 寅申为寺观；下L10788「申与僧同音」'),
    '辰': ('寺观', '地', '下L10788「龙居辰上，主寺观」'),
    '未': ('神鬼·祭祀之所', '事', '下L9631「未主祭祀、神鬼」；下L1182「未临宅，未主鬼神」'),
    '子': ('祷祝鬼神之所', '事', '下L9598「子主…裁制、祷祝鬼神」'),
    '戌': ('塑像神祠', '物', '下L9643「戌主…塑画」'),
}
# 取象用法 → 类象陈述（⛔ 陈述"课上有何象"，不作"应当如何"的建议）
YONGFA_TEXT = {
    '地': '所涉之地近寺观、神祠，或事在寺观僧舍之中',
    '地·人': '所涉之地近寺观，所涉之人或为僧道',
    '人': '所涉之人或为僧道、方外之士',
    '事': '主鬼神、祭祀、祷祝之事，或为祟扰、怪异之象',
    '物': '主神像、塑画、香火之物',
}
# ── 地支方位（上 L865）──
ZHI_FANGWEI = {'子': '正北', '丑': '东北', '寅': '东北', '卯': '正东',
               '辰': '东南', '巳': '东南', '午': '正南', '未': '西南',
               '申': '西南', '酉': '正西', '戌': '西北', '亥': '西北'}
# ── 幽冥将（主鬼神、阴私、怪异）──
YOU_MING_JIANG = ('螣蛇', '玄武', '太阴', '白虎', '天空')
# ── 幽冥煞（由 shensha_xiang 层产出）──
YOU_MING_SHA = ('天鬼', '死神', '死气', '病符', '丧门', '吊客')
# ── 大帝级天将（主神大庙：东岳、城隍级）──
DA_DI_JIANG = ('贵人', '青龙', '太常')
# ── 小祠类天将（土地庙、社庙、路边小祠、阴庙）──
XIAO_CI_JIANG = ('螣蛇', '玄武', '天空', '勾陈', '白虎', '朱雀', '六合', '太阴')

# 位置 → (权重, 远近)
POS_WEIGHT = {'初传': (5, '近（发用最显）'), '支上': (4, '宅内／近邻'),
              '干上': (3, '自身所近'), '中传': (2, '中'), '末传': (1, '远')}


def _wangshuai(zhi: str, yue_jian: str) -> str:
    """地支相对月建的旺相休囚死（同气旺、月生相、支生月休、支克月囚、月克支死）。"""
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


def _is_wangxiang(zhi: str, yue_jian: str) -> bool:
    """旺或相（沿用 rangjie_engine「未传旺相」的同口径）。"""
    return _wangshuai(zhi, yue_jian) in ('旺', '相')


def _six_positions(env: Dict[str, Any]) -> List[tuple]:
    """课传六处（口径与 _judge_shensha_xiang 一致：三传＋干上＋支上）。"""
    sc = list(env.get('sanchuan') or [])
    return [('初传', sc[0] if len(sc) > 0 else ''),
            ('中传', sc[1] if len(sc) > 1 else ''),
            ('末传', sc[2] if len(sc) > 2 else ''),
            ('干上', env.get('gan_shang', '') or ''),
            ('支上', env.get('zhi_shang', '') or '')]


def suggest(env: Dict[str, Any], judged: Dict[str, Any]) -> Dict[str, Any]:
    """产出鬼神／祠庙取象（🔴 不进评分链）。"""
    out: Dict[str, Any] = {'象域': False, '强度': 0, '候选': [],
                           '类象语': '', '祷所': '', '依据': []}
    try:
        tj = dict(env.get('tian_jiang') or {})          # 🔴 {天盘支: 天将}，不过天地盘
        yue_jian = env.get('yue_zhi', '') or env.get('yue_jian', '') or ''
        ss = (judged.get('shensha_xiang') or {})
        ss_luo = ss.get('落点') or []
        sha_hit = sorted({x.get('煞') for x in ss_luo
                          if isinstance(x, dict) and x.get('煞') in YOU_MING_SHA})

        # ── ① 象域判定 ──
        pos_list = _six_positions(env)
        hits = [(p, z) for p, z in pos_list if z in SHENCI_ZHI]
        if not hits:
            return out
        you_ming_jiang_hit = any(tj.get(z, '') in YOU_MING_JIANG for _, z in hits)
        if not (sha_hit or you_ming_jiang_hit):
            return out                                   # 无幽冥煞亦无幽冥将 ⇒ 不立象域
        out['象域'] = True
        out['强度'] = len({z for _, z in hits}) + len(sha_hit) + (1 if you_ming_jiang_hit else 0)

        # ── ② 候选排序 ──
        for p, z in hits:
            cls, yongfa, src = SHENCI_ZHI[z]
            jiang = tj.get(z, '') or ''
            ws = _wangshuai(z, yue_jian)
            w, far = POS_WEIGHT.get(p, (0, ''))
            score = float(w)
            if _is_wangxiang(z, yue_jian):
                score += 1.0
            if jiang in YOU_MING_JIANG:
                score += 1.0
            if jiang in DA_DI_JIANG:
                grade = '大帝级（东岳庙、城隍庙、泰山行宫之类主神大庙）'
                score += 0.5
            elif jiang in XIAO_CI_JIANG:
                grade = '小祠级（土地庙、社庙、路边小祠、阴庙之类）'
            else:
                grade = '神格未定（视当地实况）'
            out['候选'].append({
                '支': z, '位置': p, '建筑类': cls, '用法': yongfa, '天将': jiang,
                '方位': ZHI_FANGWEI.get(z, ''), '远近': far,
                '旺衰': ws, '神格': grade, '分': round(score, 1),
                '原文': src,
            })
        out['候选'].sort(key=lambda x: -x['分'])
        out['候选'] = out['候选'][:3]
        if sha_hit:
            out['依据'].append('幽冥煞落课传：' + '、'.join(sha_hit))
        for c in out['候选']:
            out['依据'].append('%s在%s：%s' % (c['支'], c['位置'], c['原文']))
        out['依据'].append('方位：上L865「寅卯辰东方…丑寅东北、卯正东…」（总体属方＋具体方位）')

        # ── 主输出：**陈述式类象**（回测后改定位；⛔ 不作"应当如何"的建议）──
        parts = []
        for c in out['候选']:
            parts.append('课传见%s之象（%s·%s·乘%s·%s，%s）——%s'
                         % (c['建筑类'], c['支'], c['位置'], c['天将'] or '—',
                            c['旺衰'] or '—', c['方位'],
                            YONGFA_TEXT.get(c['用法'], '')))
        out['类象语'] = '；'.join(parts)

        # ── 「宜祷于X方」**降级**：仅当禳解层判「宜禳」时才追加 ──
        #    218 案回测：邵公把此象用作祷祈禳解者仅 0.7%（1/137）；
        #    ⇒ 素材层（本层）与决策层（rangjie）**不可混同**，是否要祷由禳解层说了算。
        if (judged.get('rangjie') or {}).get('宜禳'):
            top = out['候选'][0]
            out['祷所'] = ('宜祷于%s之%s（%s·%s·乘%s·%s）'
                           % (top['方位'], top['建筑类'], top['支'], top['位置'],
                              top['天将'] or '—', top['旺衰'] or '—'))
            out['祷所'] += '——当地为东岳庙、城隍庙抑或土地庙，视本地实况而定（引擎不落专名）。'
        return out
    except Exception as e:                              # 🔴 异常绝不外溢
        out['error'] = str(e)
        return out
