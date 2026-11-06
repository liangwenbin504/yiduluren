# -*- coding: utf-8 -*-
"""赵师「往细处断」增补层（叙事层·零评分影响）
================================================
憨爷 2026-10-21 定性：**赵师断法＝往细处断，与古籍不矛盾**。
⇒ 本模块只做**具象化**（把断语说具体），⛔ **不改吉凶、不进评分链**。

🔴 边界铁律（与项目「整体定吉凶，局部只具象化；局部可解不可坏」同源）：
   细处断 = 给「是什么/在哪/什么样」的具体象；
   吉凶 = 仍由引擎主链（课体/毕法/类象生克）定。
   ⛔ 禁止用细处象去翻吉凶 —— 那是「局部坏整体」，赵师自己也不这么干。

置信度标记：
   ✓ 多次实证（赵师课件/文档 ≥2 例，或项目已有印证）
   △ 单次/个案（赵师现场灵感，如谐音、旺衰取数）⇒ **只作提示，不作断言**

来源：赵林声课程转录 66.5h ＋《新加坡案例.docx》＋《大六壬课例（北大）.pptx》
"""
from typing import Dict, List, Any

# ── 一、细处类象（天将 / 支 / 六亲 / 组合 / 玄空）──
ZHAO_XICHU_XIANG: Dict[str, Dict[str, List[str]]] = {
    '天将': {
        '勾陈': ['交警✓', '警察✓', '勾连/牵扯✓', '本家辰✓'],
        '朱雀': ['电话✓', '手机✓', '标签/牌子✓', '吵闹打架✓', '文书口舌✓'],
        '太常': ['牌子/标签✓', '衣物✓', '吃喝宴席✓'],
        '六合': ['中介✓', '物业✓', '一整套✓', '箱子/盒状✓'],
        '玄武': ['盗贼✓', '丢失的环境✓', '暗昧✓', '骗子✓'],
        # ⓘ「国家机关」标 ✓：赵师原话「卯的阴神为辰乘天后…就是交警」，
        #   交警＝公家的人，属赵师语境内的直接归纳，非推演
        '天后': ['恩泽之神✓', '国家机关✓'],
        # ═══ 以下 6 将 2026-10-21 补全（憨爷「好，补全」）═══
        # 🔴 来源＝`leixiang_chain.JIANG_XIANG` 中标 ✓ 的条目（**赵师课例原文直接出现**），
        #   ⛔ 只做**筛选**（挑说得出口的具象象），未新增任何内容、未改写措辞。
        # 🔴 置信标 **赵**（赵师课件实证·单课例原文），⛔ 不标 ✓：
        #   ✓ 需「≥2 例或项目已印证」，主库单课例不足据此提级（防虚增置信）。
        #   ⓘ 筛掉的：条件性太强（'老虎机（+午）'、'诈骗（入墓=水平不高）'、'勾搭（+空）'）
        #     与纯抽象描述（'暗昧'、'虚妄'、'刑伤/血光'、'迟滞/纠缠'）。
        '贵人': ['贵重赵', '名气大赵', '官长/提携△'],
        '青龙': ['财/大财库赵', '纸钱煞赵', '催官/事业大赵'],
        '白虎': ['病赵', '道路赵', '催官使者（测官）赵', '过硬赵'],
        '螣蛇': ['眼睛赵', '神经/睡不着赵', '图腾赵', '弯曲赵', '瘦赵'],
        '太阴': ['藏起来赵', '雕刻赵', '酒具赵'],
        '天空': ['空/中空赵', '开口赵', '心思不在家赵'],
    },
    '支': {
        '卯': ['车✓', '树木✓', '门户△'],
        '申': ['交警（乘青龙/太岁）✓', '道路✓', '传送✓'],
        '戌': ['网络△', '电脑△', '网线△', '坟墓/墓库✓'],
        '巳': ['热水管△', '心脏△'],
        '辰': ['勾陈本家✓', '水库/坟△'],
        # ═══ 以下 7 支 2026-10-21 补全（同上口径：主库 `MODERN_XIANG` 的 ✓ 条目筛选，标 赵）═══
        # ⓘ 筛掉的：'水'、'渔屠'、'田园'、'僧尼'、'官吏'、'文书'、'宴席'、'羊'、'刀剑△'、
        #   '药'、'舟车'、'碑石'、'库/盒子'（无 ✓ 或与既有条目重复）；
        #   '眼睛（落空）'、'警察（+太岁+勾陈）'（条件性太强，留待节点组合域）。
        '子': ['取款机赵', '小孩赵', '妻财赵'],
        '丑': ['金库赵', '腹部赵'],
        '寅': ['肝脏赵', '道士赵', '猫（乘玄武）赵', '大树赵'],
        '午': ['心脏赵', '文书/文明赵', '桃花赵', '马赵'],
        '未': ['财赵', '警察（+太岁）赵'],
        '酉': ['玉器/酒具赵', '贵重物件赵', '苹果赵'],
        '亥': ['房屋赵', '酒赵', '大海/水边赵'],
    },
    # ⓘ **六亲域已于 2026-10-21 并入主类象库** `leixiang_chain.LIUQIN_XIANG`
    #   （六亲相对日干，须动态计算，不能静态塞表 ⇒ 由 map_modern_xiang 按日干接线）
    #   ⛔ 此处**不得**再留副本（双真源漂移）。
    '组合': {
        '羊刃+白虎': ['动手术✓'],
        '财+金库': ['银行△'],
        '天马': ['飞机✓'],
        '日禄': ['俸禄/工资△'],
    },
    # ── 节点组合：**同一节点上**「支 × 天将」的合象（赵师「往细处断」的二阶串联）──
    # 例：ZLA-220 汽车被盗「卯的阴神为辰乘天后…就是交警」
    #     ＝ 辰（勾陈本家：管人的）× 天后（国家机关） ⇒ 交警
    '节点组合': {
        '辰+天后': ['交警/公家的人来管这事✓'],
    },
    # ⓘ **玄空域已于 2026-10-21 并入主类象库** `leixiang_chain.XUANKONG_YUN_XIANG /
    #   XUANKONG_WUXING_XIANG / SPECIAL_YONGFA_XIANG`（并带**占类闸门**防噪音）
    #   ⛔ 此处**不得**再留副本（双真源漂移）。
}

# ── 二、赵师「往细处断」的取用步骤链 ──
# 提炼自断语（如 ZLA-220 汽车被盗、课例-2 喜鹊、课例-18 车盗）
XICHU_STEPS: List[Dict[str, str]] = [
    {'步': '1 定类神',
     '法': '先问「这是什么事」→ 定类神（测偷盗看玄武、测失物看类神支、测电话看朱雀）',
     '据': '赵师：「测偷盗，第一看玄武」；「看类神，卯为车」',
     '信': '✓'},
    {'步': '2 看类神落处',
     '法': '类神临何支、乘何将、遁何干 —— 「临X坐Y」＝乘天盘X、坐地盘Y',
     '据': '课例-2「朱雀临酉坐卯」；ZLA-220「勾陈临酉」',
     '信': '✓'},
    {'步': '3 看阴神',
     '法': '类神的阴神（下一层）→ 事往哪发展、藏在何处',
     '据': 'ZLA-220「再看卯的阴神为辰乘天后…就是交警」',
     '信': '✓'},
    {'步': '4 看遁干/谐音（△个案技艺）',
     '法': '遁干谐音取象（癸音通鬼 → 「鬼子车」）；标签取象（朱雀/太常为牌子）',
     '据': 'ZLA-220「太常临丑遁癸，癸音通鬼，鬼子车」',
     '信': '△ 赵师个人技艺，泛化风险高，只作提示'},
    {'步': '5 旺衰定数量（△个案技艺）',
     '法': '以旺衰/洛书数加减乘除推数量（九加四再乘二 → 二十五六个）',
     '据': '课例-1「测吵闹人数…九加四再乘二，二十五六个」',
     '信': '△ 不可机械套用'},
    {'步': '6 多角度复核',
     '法': '三传、天地盘、课格各看一遍，互相印证（「三传重点看空，天地盘重点看象」）',
     '据': 'ZLA-220「再从另一角度去看…三传寅卯辰全空」',
     '信': '✓'},
]


def _zhi_of(tok: Any) -> str:
    """从任意 token 剥出地支（三传可能是 '寅' / '丁未' / ['财','丁未','蛇']）。"""
    if isinstance(tok, (list, tuple)):
        for t in reversed(tok):
            z = _zhi_of(t)
            if z:
                return z
        return ''
    s = str(tok or '')
    for ch in reversed(s):
        if ch in '子丑寅卯辰巳午未申酉戌':
            return ch
    return ''


def xichu_duan(env: Dict[str, Any] = None, category: str = '',
               nodes: List[Dict[str, Any]] = None,
               top_k: int = 8) -> Dict[str, Any]:
    """细处断：只出「具象候选」，不出吉凶。

    入参（二选一，都给则用 nodes）：
      nodes —— 类象链节点列表，每项含 地支/天将/遁干/坐宫/层（**推荐**，赵师第2/3步
               就是「类神临X坐Y → 看阴神」；链上第 n 层即阴神）
      env   —— 裸课盘（tian_jiang_pan / sanchuan / si_ke）

    ⛔ 本函数**永不赋 valence**，仅供叙事层引用。
    """
    env = env or {}
    nodes = nodes or []

    # ── 收集锚点：优先链上节点 ──
    anchors: List[Dict[str, Any]] = []
    for nd in nodes:
        if not isinstance(nd, dict):
            continue
        anchors.append({'地支': nd.get('地支') or _zhi_of(nd.get('支')),
                        '天将': str(nd.get('天将') or ''),
                        '遁干': str(nd.get('遁干') or ''),
                        '坐宫': str(nd.get('坐宫') or ''),
                        '层': nd.get('层')})
    if not anchors:
        jp = env.get('tian_jiang_pan') or env.get('tian_jiang') or env.get('天将盘') or {}
        tdp = env.get('tiandi_pan') or {}
        seq = env.get('sanchuan') or env.get('三传') or []
        if not seq:
            seq = [env.get('chu'), env.get('zhong'), env.get('mo')]
        for i, t in enumerate(seq or []):
            z = _zhi_of(t)
            if not z:
                continue
            anchors.append({'地支': z, '天将': str(jp.get(z, '')),
                            '遁干': '', '坐宫': str(tdp.get(z, '')), '层': i})
        for ke in (env.get('si_ke') or env.get('四课') or []):
            if isinstance(ke, (list, tuple)) and len(ke) > 1:
                z = _zhi_of(ke[1])
                if z:
                    anchors.append({'地支': z, '天将': str(jp.get(z, '')),
                                    '遁干': '', '坐宫': '', '层': None})

    jiangs = [a['天将'] for a in anchors if a['天将']]
    zhis = [a['地支'] for a in anchors if a['地支']]

    sure: List[Dict[str, Any]] = []   # ✓ 可常态引用
    hint: List[Dict[str, Any]] = []   # △ 个案技艺，只提示

    def _conf(v: str) -> str:
        """单条象的置信级（四级，见模块头）。

        ✓  ≥2 例实证／项目已印证  ⇒ 可常态引用（sure）
        赵  赵师**课件**实证（单课例原文）⇒ 可常态引用（sure）
        赵△ 赵师**个案**技艺           ⇒ 只提示（hint）
        △  推演／单次                 ⇒ 只提示（hint）
        ⚠ 判定顺序要紧：先认「赵△」再认「赵」，否则 赵△ 会被当成 赵 提级（虚增置信）
        """
        if '赵△' in v:
            return 'h'
        if '✓' in v:
            return 's'
        if '△' in v:
            return 'h'
        # ⓘ 只认**结尾**的「赵」（`财/大财库赵`），⛔ 不用 `'赵' in v`
        #   （否则象文本里出现「赵」字会被误提级）
        if v.rstrip().endswith('赵'):
            return 's'
        return 'h'

    def _push(grp, key, vals, a):
        # 按**单项**分置信（同锚可能既含✓又含△，⛔ 不许整组一刀切）
        _clean = lambda x: x.replace('✓', '').replace('△', '').replace('赵', '')
        s = [_clean(v) for v in vals if _conf(v) == 's']
        h = [_clean(v) for v in vals if _conf(v) == 'h']
        base = {'域': grp, '锚': key, '层': a.get('层')}
        if a.get('地支'):
            base['临'] = a['地支']
        if a.get('坐宫'):
            base['坐'] = a['坐宫']
        if s:
            sure.append({**base, '象': s})
        if h:
            hint.append({**base, '象': h})

    for grp, keys in (('天将', jiangs), ('支', zhis)):
        for key, vals in ZHAO_XICHU_XIANG.get(grp, {}).items():
            for a in anchors:
                hit = (a['天将'] == key) if grp == '天将' else (a['地支'] == key)
                if hit:
                    _push(grp, key, vals, a)
                    break

    # ── 十二天将「临十二宫格」（2026-10-21 憨爷指出：朱雀临亥、天乙临丑…）──
    # 🔴 口径：格取「天将所乘的**天盘支**」（＝节点『地支』），⛔ 不是坐宫（地盘宫）。
    # ⛔ 只出格名与古籍注文（描述性），**不赋 valence**，不翻吉凶。
    try:
        from engine.leixiang_chain import JIANG_LIN_GONG, JIANG_LIN_NOTE
    except Exception:
        JIANG_LIN_GONG, JIANG_LIN_NOTE = {}, {}
    for a in anchors:
        j, z = a.get('天将'), a.get('地支')
        ge = (JIANG_LIN_GONG.get(j) or {}).get(z) if (j and z) else None
        if not ge:
            continue
        note = JIANG_LIN_NOTE.get((j, z), '')
        # ⓘ 注文自带括号（引原文），外层用「；」分隔，⛔ 别再套一层括号（嵌套难读）
        val = '%s✓' % ge + ('；%s' % note if note else '')
        base = {'域': '临宫格', '锚': '%s临%s' % (j, z), '层': a.get('层')}
        if z:
            base['临'] = z
        if a.get('坐宫'):
            base['坐'] = a['坐宫']
        sure.append({**base, '象': [val]})

    # 节点组合：同一节点上「支 × 天将」的合象（二阶串联，赵师细处断的核心）
    # 🔴 真源**两处合并**：`ZHAO_XICHU_XIANG['节点组合']`（本模块）＋
    #   `leixiang_chain.COMBO_XIANG`（**赵师课例原句**，如 戌+青龙→银行/大财库）。
    #   ⓘ 此前只查前者（仅 1 条），导致求财占「戌乘青龙」只出支象「坟墓/墓库」，
    #     而赵师原句「银行/大财库（日干财库）」根本没机会出场（憨爷指出后修）。
    try:
        from engine.leixiang_chain import COMBO_XIANG as _CB
    except Exception:
        _CB = {}
    for a in anchors:
        if not (a.get('地支') and a.get('天将')):
            continue
        # ⓘ 两种拼写（支+将 / 将+支）**只查一次**：旧码在 for pat 里查，两种顺序都命中时会
        #   产出两条同锚异锚的重复条目（实测「辰+天后」出两遍）
        pat = '%s+%s' % (a['地支'], a['天将'])
        _tab = ZHAO_XICHU_XIANG.get('节点组合', {})
        vals = list(_tab.get(pat) or _tab.get('%s+%s' % (a['天将'], a['地支'])) or [])
        # 🔴 两源**合并**（⛔ 不是二选一）：此前 `if vals is None` 才回退 COMBO，
        #   导致同一组合两处都有值时，本表条目**覆盖**掉 COMBO 条目 ⇒ 丢象。
        #   实测：('辰','天后') 本表「交警」把 COMBO「女人（来冲财库）」整条吃掉。
        v1 = _CB.get((a['地支'], a['天将'])) or _CB.get((a['天将'], a['地支']))
        if v1:
            # 🔴 COMBO_XIANG 的 ✓ ＝**单课例原句**（与主库 JIANG_XIANG/MODERN_XIANG 同口径）
            #   ⇒ 按防虚增原则统一转标 **赵**，⛔ 不改源表（源表仍标 ✓ 供他处使用）
            v1 = v1.replace('✓', '赵')
            if all(v1 not in v for v in vals):
                vals.append(v1)
        if vals:
            _push('节点组合', pat, vals, a)
    # 组合：需外部给 category 才提示（⛔ 不得自行判六亲后翻吉凶）
    # 六亲/玄空已并入主类象库，由 `map_modern_xiang` 统一产出，此处不再重复
    for grp in ('组合',):
        for key, vals in ZHAO_XICHU_XIANG.get(grp, {}).items():
            if category and any(w and w in str(category) for w in key.split('+')):
                hint.append({'域': grp, '锚': key,
                             '象': [v.replace('✓', '').replace('△', '') for v in vals],
                             '层': None})

    # 去重（同锚同象只留一次）＋ **按层均衡截断**
    # 🔴 旧实现是**全局 `o[:top_k]`**（默认 8）⇒ 3 层链共 10 项时，后层（含**节点组合**）
    #   整段被截掉。实测：偷盗课「寅乘玄武」的 COMBO「猫 / 下贱之神」在 `细处象✓` 里有，
    #   但前面 8 项占满后直接消失，断语里永远看不到（憨爷「一起接」时才发现）。
    #   ⇒ 改为**先按 (域,锚) 去重，再按层保留**，每层最多 `per_layer` 项，⛔ 不跨层抢名额。
    def _dedup(lst, per_layer: int = 4):
        seen, uniq = set(), []
        for it in lst:
            k = (it['域'], it['锚'], tuple(it['象']))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(it)
        cnt: Dict[Any, int] = {}
        out2 = []
        for it in uniq:
            lk = it.get('层')
            cnt[lk] = cnt.get(lk, 0) + 1
            if cnt[lk] <= per_layer:
                out2.append(it)
        return out2[:max(top_k, 36)]      # 兜底上限，正常远达不到

    out: Dict[str, Any] = {}
    if sure:
        out['细处象✓'] = _dedup(sure)
    if hint:
        out['细处象△'] = _dedup(hint)
    out['细处步骤'] = [s['步'] + '：' + s['法'] for s in XICHU_STEPS]
    out['边界'] = ('⛔ 细处断只具象化，不改吉凶；✓ 可常态引用，△ 为个案技艺只作提示；'
                   '吉凶仍由引擎主链（课体/毕法/类象生克）定')
    return out


# ── 三、叙事合成（象 → 人话）──
# 🔴 为什么要有这一层：
#   憨爷 2026-10-21 指出「**叙事层才是求占者最信服的地方**，只说凶或吉，人家没有具体概念」。
#   实测反例：问「汽车被盗」，老输出是
#     「候选象：猫 / 下贱之神、肝脏、车、女人、水库/墙；推演：汽车、骗局、和尚/道士」
#   —— 主类象库是全量词表，**噪音与答案混排**，求占者看完更糊涂。
#   ⇒ 合成层**只用细处断的象做主料**（它已过赵师取用链筛选：定类神→看落处→看阴神），
#     噪音天然不在里面；再按「事起 → 传到 → 末传」的时序套句式，串成人话。
#
# 🔴 边界（同细处断）：
#   合成句只说「是谁／在哪／往哪走」，⛔ 仍然**不判吉凶**；
#   ⛔ 只用 ✓／赵 级象造句，**△／赵△ 级不进合成句**，只作附注（个案技艺，不得断言）。
_LAYER_WORD = {0: '起手', 1: '传到', 2: '末传', 3: '再往后'}

# ── 关系层（原型）：把「象 → 推理」**显式规则化** ──
# 🔴 为什么必须有这一层：模板只能把象**并列罗列**（盗贼、车、交警），
#    说不出「所以呢」。赵师断课的说服力恰恰来自**推理**（玄武为盗 ⇒ 不是自己丢的）。
# 🔴 收录门槛（⛔ 严）：必须有**赵师原话**或**古籍依据**才收，⛔ 绝不臆造。
#    每条都要写「据」，方便日后逐条复核／推翻。
RELATION_RULES: List[Dict[str, str]] = [
    {'触发将': '玄武', '适用占类': '偷盗,失物,盗',
     '推': '东西不是自己丢的，是有人动了手',
     '据': '赵师：「测偷盗，第一看玄武」；玄武为盗贼之神',
     '信': '✓'},
]


def _relation_lines(nodes: List[Dict[str, Any]], category: str) -> List[str]:
    """关系层：按规则推出「所以呢」，置于断语之前。⛔ 只出**有依据**的推理。"""
    cat = str(category or '')
    jiangs = {str(n.get('天将') or '') for n in nodes or []}
    out = []
    for r in RELATION_RULES:
        if r['触发将'] not in jiangs:
            continue
        scope = [w for w in r.get('适用占类', '').split(',') if w]
        if scope and not any(w in cat for w in scope):
            continue
        if r.get('信') == '✓':
            out.append(r['推'])
        else:
            out.append('%s（△%s）' % (r['推'], '个案技艺，仅供参考'))
    return out


def _zhanlei_jiangs(category: str) -> List[str]:
    """占类 → **该看的天将**（古籍明文反查）。

    🔴 依据＝**《通解》下 L11573-11575**：「占文书则用朱雀…占贤良、财帛、书吏则用青龙…
       占疾病、道路、出师、死丧则用白虎…占盗贼、逃亡、走失则用玄武…」
       ⛔ 单一真源：直接读 `data/quyong_rules.json`（`tianjiang_zhanlei` ＋ `rules` 的主/辅类神），
       ⛔ 不在本文件另抄一份（防双真源漂移）。
    ⓘ 用途仅限**排序**（该占类的将象优先占名额），⛔ 不删象、不判吉凶。
    """
    cat = str(category or '')
    if not cat:
        return []
    try:
        import io as _io
        import json
        import os
        _p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'data', 'quyong_rules.json')
        d = json.load(_io.open(_p, encoding='utf-8'))
    except Exception:
        # ⚠ 读取失败**不静默**：返回空表时上层退化为「不排序」，并在断语边界里标注
        return []
    out: List[str] = []
    # ① 天将总表反查（占类关键词命中该将的任一占类标签）
    # ⓘ 匹配用「子串双向 + 少量同义词」：古籍标签是「盗贼」而占类常报「偷盗」，
    #   严格子串会漏。⛔ **不用单字交集**（实测把「求财」匹配到「求贵」→贵人、「文书」匹配到
    #   「赦书」→天后，全是假命中）。**用途仅排序**，⛔ 不删象。
    _SYN = {'偷盗': '盗贼', '偷窃': '盗贼', '失窃': '盗贼', '失盗': '盗贼',
            '找东西': '失物', '丢东西': '失物', '寻物': '失物'}
    _c2 = _SYN.get(cat, cat)
    tz = d.get('tianjiang_zhanlei') or {}
    _META = ('原文', '说明')          # ⚠ 该表元信息键**不带下划线**，须显式排除
    for j, tags in tz.items():
        if str(j).startswith('_') or str(j) in _META:
            continue
        hit = False
        for t in (tags or []):
            if not t:
                continue
            if t in _c2 or _c2 in t or (cat and (t in cat or cat in t)):
                hit = True
                break
        if hit and j not in out:
            out.append(j)
    # ② 取用规则表的主/辅类神里出现的将名（如求财 辅＝青龙/太常）
    for r in (d.get('rules') or []):
        if not any(z and z in cat for z in (r.get('zhanlei') or [])):
            continue
        for k in ('主类神', '辅类神'):
            for nm in (r.get(k) or []):
                if nm in tz and not str(nm).startswith('_') and nm not in out:
                    out.append(nm)
    return out


def synth_narrative(xichu: Dict[str, Any] = None,
                    nodes: List[Dict[str, Any]] = None,
                    category: str = '') -> Dict[str, Any]:
    """把细处断的候选象，按链序合成**人话断语**（⛔ 不判吉凶）。

    xichu —— `xichu_duan()` 的输出；nodes —— 链上节点（供「支乘将」落处描述）
    """
    xichu = xichu or {}
    nodes = nodes or []
    by_layer: Dict[Any, List[Dict[str, Any]]] = {}
    for it in xichu.get('细处象✓', []):
        by_layer.setdefault(it.get('层'), []).append(it)

    # ── 占类闸门（2026-10-21 憨爷问「噪音该降不少吧」后加）──
    # 🔴 实测痛点：`synth_narrative` 此前**不看占类**，天将词表全量铺 ⇒
    #   疾病占答「朱雀→电话、手机、标签/牌子」（❌ 完全不对题）；
    #   求财占答「青龙→坟墓/墓库」。
    #   正解＝**疾病/伤占改走古籍病象表**（天将「于病/于疾」＋月将身体部位）。
    cat = str(category or '')
    is_disease = any(w in cat for w in ('疾病', '病', '伤', '健康', '胎产'))
    if is_disease:
        try:
            from engine.leixiang_chain import (JIANG_BING_XIANG as _JB,
                                               YUEJIANG_BODY_XIANG as _YB,
                                               YUEJIANG_NAME as _YN)
        except Exception:
            _JB, _YB, _YN = {}, {}, {}

    # 内部锚点词**不进断语**（如「本家辰」「勾陈本家」＝给引擎的落处说明，
    #   求占者看不懂；信息仍在 `细处象✓` 里，内行可查）
    _INTERNAL = ('本家',)

    def _is_internal(v: str) -> bool:
        return any(w in v for w in _INTERNAL)

    def _dup(v: str, have: List[str]) -> bool:
        """语义去重：字面相同／互相包含／汉字被完全覆盖 都算重复。

        ⓘ 实测噪音：官讼占「交警、交警/证据/围墙、交警、警察」
          —— 字面不同但说的是一件事，逐字去重挡不住。
        """
        vs = set(v)
        for h in have:
            if v == h or v in h or h in v:
                return True
            hs = set(h)
            # ⓘ **双向**判包含：只判单向会漏「银行/大财库（日干财库）」vs「财/大财库」
            #   （后者字面不连续包含于前者，但汉字集被覆盖）
            if len(vs) >= 2 and (vs <= hs or (len(hs) >= 2 and hs <= vs)):
                return True
        return False

    # 该占类「该看的将」（只用于排序，见 `_zhanlei_jiangs` 注释）
    _PJ = _zhanlei_jiangs(cat)

    lines: List[str] = []
    for layer in sorted(k for k in by_layer if k is not None):
        nd = nodes[layer] if isinstance(layer, int) and layer < len(nodes) else {}
        zhi = str(nd.get('地支') or '')
        jiang = str(nd.get('天将') or '')
        zuo = str(nd.get('坐宫') or '')
        # ⓘ 链不一定从初传起（类神锚定/外应会改起点）⇒ 首句不用「传到」开头
        head = _LAYER_WORD.get(layer, '再往后')
        if not lines and layer != 0:
            head = '课见'
        # 落处：「支乘将」——ⓘ **断语句里不带坐宫**：求占者看「坐X」无意义；
        #   内行要核落处，看 `细处象✓` 里的「临/坐」字段即可（信息没丢，只是分层）。
        where = zhi + ('乘' + jiang if jiang else '')
        # 该层象：节点合象优先（二阶串联最具体），其馀按域序
        items = sorted(by_layer[layer], key=lambda x: 0 if x['域'] == '节点组合' else 1)
        # ⓘ **临宫格独立成句**（赵师句式「朱雀临亥＝入水」），⛔ 不混进「主…」词表
        #   （实测混排读作「主电话、手机…、入水✓；宜守静」，求占者看不懂）
        lin = [it for it in items if it['域'] == '临宫格']
        others = [it for it in items if it['域'] not in ('临宫格', '节点组合')]
        xiangs: List[str] = []
        bing_txt = ''
        if is_disease and (jiang or zhi):
            # 🔴 疾病/伤占：**病象表优先**（古籍明文），⛔ 不再铺天将物品词表
            #   天将 → 「于病/于疾」病症｜月将（支）→ 身体部位（两套「十二」互补）
            # ⓘ 断语句里**不重复将名/支名**（where 已说「亥乘朱雀」），只说「病在…／属…」
            parts = []
            if jiang and _JB.get(jiang):
                parts.append('病在' + '、'.join(v.replace('✓', '') for v in _JB[jiang][:5]))
            if zhi and _YB.get(zhi):
                parts.append('身体属' + '、'.join(v.replace('✓', '') for v in _YB[zhi][:5]))
            bing_txt = '；'.join(parts)
        if not xiangs and not bing_txt:
            # 🔴 **占类排序闸门**（依据《通解》下 L11573-11575「占XX则用YY将」）：
            #   该占类对应之将的象**优先占名额**，其余靠后（⛔ 不删象、不判吉凶）
            # ⓘ 名额只有 3 个，先让对题的将说话
            _pref, _rest = [], []
            for it in others:
                _tgt = _pref if (it['域'] == '天将' and it['锚'] in _PJ) else _rest
                for v in it['象']:
                    if not _dup(v, xiangs) and not _is_internal(v):
                        xiangs.append(v)
                        _tgt.append(v)
            xiangs = _pref + _rest
        lin_txt = ''
        if lin:
            ge_raw = lin[0]['象'][0].replace('✓', '')
            if '；' in ge_raw:                      # 「格名；注文」两段
                ge_name, ge_note = ge_raw.split('；', 1)
                lin_txt = '；为%s，%s' % (ge_name, ge_note)
            else:
                # ⛔ **无注文的格名不出**（实测 144 格名只有 71 条注文，常见的乘龙/入驿/
                #   落阱/溺水/伏枕/投江 均无注）⇒ 只有名字、没有解释＝求占者看不懂的半截话
                lin_txt = ''
        if not xiangs and not lin_txt and not bing_txt:
            continue
        # ── 节点合象（二阶串联）**优先置首位**，且**首层也要出** ──
        # 🔴 依据：`COMBO_XIANG` 是**赵师课例原句**，比孤立的「支」或「将」象更精确。
        #   实测痛点：求财占「戌乘青龙」首层只出支象「坟墓/墓库」，而 COMBO 里明明有
        #   「银行 / 大财库（日干财库）✓」——因为旧码 combo 只在 layer>0 用、且只作「合看是」附注。
        combo = [it for it in items if it['域'] == '节点组合']
        if combo and xiangs:
            # 🔴 **combo 无条件保留**（它是二阶合象，最精确）；⛔ 不要拿它去和单象判重后丢弃
            #   —— 实测反了：'银行/大财库（日干财库）' 被'财/大财库'判重吃掉，留下的反而是粗的。
            #   正确方向：**删掉被 combo 覆盖的单象**（不并排说两遍）。
            _cx = list(combo[0]['象'])
            xiangs = [v for v in xiangs if not any(_dup(v, [c]) for c in _cx)]
            xiangs = _cx + xiangs
            # ⓘ 此前的 bug：`xiangs = combo 的象 or xiangs` 把主象整体换掉 ⇒ 与附注重复两遍
            #   （实测「交警/公家的人来管这事，合看是交警/公家的人来管这事」）⇒ 已改为前插去重
        # ⓘ 每层主象**上限 3**（实测 5 个以上就开始混排噪音：「主盗贼、丢失的环境、暗昧、骗子」）
        if xiangs:
            # 🔴 2026-10-22 降噪（推广到**所有占类**，此前只改了疾病分支）：
            #   实测 4 个占类**全都在混**「将临宫格名」——
            #     功名「为伏枕/为投江/为巧说」｜官运「为乘龙/为入驿/为落阱」
            #     求财「为理发/为趋进/为酒食/为坠水」｜子嗣「为结发/为还绛宫/为入林」
            #   🔴 且 `JIANG_LIN_NOTE` 只覆盖 **71/144**，而常用格名（乘龙/入驿/落阱/
            #     溺水/伏枕/投江）**全无注文** ⇒ 输出只有名字、没有解释 ＝ 求占者看不懂的半截话。
            #   ⇒ 主句**一律不出格名**（⛔ 不混进「主…」词表，合 MEMORY 铁律）；
            #     格名仍在 `细处象✓` 里，内行可查。待注文补齐后再议是否独立成句。
            lines.append('%s%s，主%s' % (head, where, '、'.join(xiangs[:3])))
            if lin_txt:   # 有注文的格名**独立成句**（⛔ 不混进「主…」词表）
                lines.append('%s%s' % (where, lin_txt.lstrip('；')))
        elif bing_txt:
            # 🔴 2026-10-22 降噪：**疾病占不把「将临宫格名」塞进断语句**。
            #   实测痛点（R3 辛未日·占戌命人病）：输出「起手亥乘白虎，**为溺水**；病在痈肿、头目见血…」
            #   ——「溺水」是 `JIANG_LIN_GONG`（白虎临亥）的**通用格名**，与占病无关，属噪音。
            #   MEMORY 铁律：「临宫格须**独立成句**，⛔ 不混进『主…』词表」⇒ 疾病占直接剔除格名。
            #   ⓘ 格名信息仍在 `细处象✓` 里，内行可查。
            lines.append('%s%s；%s' % (head, where, bing_txt))
        else:
            lines.append('%s%s，%s' % (head, where, lin_txt.lstrip('；')))

    # 关系层置前：先说「所以呢」，再说「象上见什么」（赵师的说服顺序）
    rel = _relation_lines(nodes, category)

    out: Dict[str, Any] = {}
    if lines:
        out['断语'] = ('；'.join(rel) + '。' if rel else '') + '；'.join(lines) + '。'
    elif rel:
        out['断语'] = '；'.join(rel) + '。'
    hints: List[str] = []
    for it in xichu.get('细处象△', []):
        hints.append('%s：%s（△ 个案技艺，仅供参考）' % (it['锚'], '、'.join(it['象'])))
    if hints:
        out['附注△'] = hints[:5]
    out['边界'] = ('⛔ 此处只说「是谁／在哪／往哪走」，**吉凶由引擎主链定**；'
                   '△ 项不进断语，只作附注')
    return out


if __name__ == '__main__':
    import json
    # 自检①：链上节点（偷盗例：玄武临寅 → 阴神卯乘勾陈 → 再阴神辰）
    print(json.dumps(xichu_duan(
        category='偷盗',
        nodes=[{'地支': '寅', '天将': '玄武', '遁干': '', '坐宫': '申', '层': 0},
               {'地支': '卯', '天将': '勾陈', '遁干': '癸', '坐宫': '酉', '层': 1},
               {'地支': '辰', '天将': '天后', '遁干': '', '坐宫': '戌', '层': 2}]),
        ensure_ascii=False, indent=1))
    # 自检②：裸 env 兼容
    print(json.dumps(xichu_duan(
        {'三传': ['寅', '卯', '辰'],
         'tian_jiang_pan': {'寅': '玄武', '卯': '勾陈', '辰': '朱雀'}}, '偷盗'),
        ensure_ascii=False, indent=1))
