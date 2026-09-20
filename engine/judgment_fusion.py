# -*- coding: utf-8 -*-
"""
精准判断引擎 · 融合层 (门控元控制器 + Dempster-Shafer 证据融合)
====================================================================

取代 liuren_20d_engine 的「各维度 ±分 再求和」线性加权。

设计要点
--------
1. 17 路独立判断引擎(BEV) 各自只负责一件小事, 吐出对 {涨,跌,平} 的
   「信念质量(mass)」+ 置信度(conf)。它们本身不改变。
2. ① 门控(Gate): 读 课体/四课/八杀/神煞/毕法/空亡, 决定每个引擎是否激活、
   权重倍率、是否有 override。例: 阴不备→明面引擎降权并置底不确定性；
   德神临传→凶引擎减半；罗网(谋划类)→毕法升权且强指跌。
3. ② D-S 组合规则融合: 交互被保留, 冲突不相互抵消而是变成「不确定性质量」。
4. 输出: trend / prob_up / prob_down / prob_flat / confidence / conflict / reasons。

本模块复用 liuren_scoring_config 的评分函数作为「单一数据源」, 从盘面组件
重建每个引擎的信念质量, 与现有 20d 引擎逻辑零分歧。
"""

from __future__ import annotations
import os
from typing import Dict, List, Any, Tuple, Optional

# ---- 复用单一数据源评分函数 ----
from engine.liuren_scoring_config import (
    get_keti_level_score, get_liuqin_score, get_wangshuai_score,
    get_kongwang_score, get_changsheng_score, get_changsheng_kong_score,
)

# 三传天将吉凶评分(与 20d 引擎保持一致)
TIANJIANG_SCORE = {
    '贵人': 1, '青龙': 1, '六合': 1, '太常': 1, '天后': 1, '太阴': 1,
    '朱雀': 0, '勾陈': -1, '螣蛇': -1, '白虎': -2, '玄武': -1, '天空': -1,
}

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
CHANGSHENG_POS = {'金': '巳', '木': '亥', '火': '寅', '水': '申', '土': '申'}
DIWANG_POS = {'金': '酉', '木': '卯', '火': '午', '水': '子', '土': '子'}

# ---- 支柱③: 训练库反向校准参数(可选; 缺 numpy 或参数文件时自动降级，不影响旧行为) ----
# 目前仅用 group_reliability 作为各引擎组权重基线; 逻辑回归概率映射暂不在 live 路径
# (见 fuse() 注释: 特征空间错配风险)。
CALIB_PARAMS = None
try:
    from engine.calibration import load_params as _calib_load
    CALIB_PARAMS = _calib_load()
except Exception:
    CALIB_PARAMS = None

# 分数 → 质量 的参考缩放(单维度最大绝对值约 6)
SREF = 4.0  # 降低缩放分母: 提高信号承诺质量, 减少⊤占比(古例回测校准)

# 各引擎基础置信度(合理先验; 后续由训练库③反向校准学习覆盖)
BASE_CONF = {
    'keti': 0.70, 'liuqin': 0.60, 'wangshuai': 0.60, 'kongwang': 0.70,
    'tianjiang': 0.65, 'ba_sha': 0.70, 'shen_sha': 0.65, 'bifa': 0.70,
    'sanchuan_kege': 0.60, 'special_kege': 0.60,     'changsheng': 0.55,
    'taichan': 0.90,   # 胎产专属：子孙生扶/德神临（占类化·确定性·无泄漏；仅古例胎产激活）
    'guansong': 0.90,  # 官讼专属：解厄吉/官鬼凶/连茹凶（占类化·确定性·无泄漏；仅古例官讼激活）
    'qiucai': 0.90,    # 求财专属：财爻生扶吉/青龙乘财吉/财虚凶（占类化·确定性·无泄漏；仅古例求财激活）
    'disease': 0.90,   # 疾病专属：虎鬼/子孙解厄/生龙/贵医/两蛇夹墓/华盖孝帛（占类化·确定性·无泄漏；仅古例疾病激活）
    'gongming': 0.90,  # 功名专属：临官帝旺/六阳数足/帘幕贵人(记录) + 朱雀值鬼/墓绝凶（仕宦章+选举章；仅古例功名激活）
    'jiazhai': 0.90,   # 家宅专属：虎入宅/墓神临支/三传泄气（阳宅章；仅古例家宅激活）
    'chuxing': 0.90,   # 出行专属：驿马空亡/中末空亡半路回（出行章；仅古例出行激活）
    'hunyin': 0.90,    # 婚姻专属：财居旬后/官坐空亡/后合卯酉私合（婚姻章；仅古例婚姻激活）
    'zeidao': 0.90,    # 贼盗专属：玄武乘鬼/财爻空陷（贼盗章；仅古例贼盗激活）
    'holistic': 0.70,  # 支柱④综合叙事/CBR 证据组(置信度由 holistic 自身给出, 此处仅作兜底)
    'caishen': 0.85,   # 求财类神专项增强(朱雀+六合+青龙+财爻, 置信度较高; 古例回测校准↑)
    # 股票域自有特征库（涨/跌 valence，复用古例已验证确定性原语；仅股票路径 _is_stock 激活）
    'stock_ba_sha': 0.90,    # 八杀 valence（占类化·确定性·无泄漏）
    'stock_shen_sha': 0.90,  # 神煞 valence（负向-only·确定性·无泄漏）
    'stock_qiucai': 0.90,    # 求财 valence（财爻生扶吉/青龙乘财吉/财虚凶·确定性·无泄漏）
}

FRAME = ['涨', '跌', '平', '⊤']

# ---- 神煞信号幅度倍率 `ZERI_SHENSHA_MULT`（2026-09-18 憨爷拍板做成开关）----
# 背景（2026-09-17 实测，探针 `_冗余待删/_diag_ba_sha_pressure.py`）：
#   `shen_sha`（神煞 valence）在三组（判对吉案／错判吉案／凶案）**均 100% 负向**，
#   明细恒为 ['桃花(-1.0)','劫煞(-1.0)','灾煞(-1.0)'] ⇒ **不给判别信息、只给恒定负偏置**
#   （这是引擎判凶率 89.9% ＞ 语料凶率 85.5% 的来源之一）。
# A/B 实测（207 案，label 修正后口径，探针 `_冗余待删/_ab_shensha.py`）：
#   1.0（默认）总 91.8% ｜ 吉案 recall 55.2% ｜ 凶案 recall 98.3%
#   0.5        总 87.9% ｜ 吉案 recall **62.1%** ｜ 凶案 recall 92.7%
#   0.0        总 82.1% ｜ 吉案 recall **62.1%** ｜ 凶案 recall 85.9%
# 🔴 **这是"取舍"不是"改进"**：削它 ＝ 决策边界整体右移 ＝ 吉案↑、凶案↓。
#   用途取向 ⇒ 偏「挑吉日」（少漏吉案）设 0.5；偏「避凶」保持 1.0。
# ⓘ 只作用于 `shen_sha`（古例域）；股票域的 `stock_shen_sha` 是另一个组名 ⇒ 不受影响。
ZERI_SHENSHA_MULT = float(os.environ.get('ZERI_SHENSHA_MULT', '1.0'))

# ---- 占类化：弱类 keti 降权 ----
# 诊断（164 真实案，仅推导）：求财/出行/胎产的错例 100% 为「吉→凶」（全局 keti 过度看跌
# 压住了这些占类的吉象）。故对这三类下调通用课体(keti)信号权重，让占类专属八杀/神煞主导。
# 仅古例路径置了 analysis['_zhanlei'] 才生效；股票路径不置该键 → 零影响。
# 注：出行经实测为「 wash 」——keti 降权虽修复 1 个 吉→凶 错例，却因放大了凶案的牛市六亲
# 而引入 1 个 凶→吉 假阳；移出集合后由 驿马 单独承接吉案修复，整体 M3 不被拖累。
WEAK_KETI_CATS = {"求财", "胎产"}
KETI_WEAK_MULT = 0.5

# ---- 领域开关：占卜(古例)域不应注入"求财类神"看涨偏置(其为股票域设计) ----
# 置 True 时，fuse() 既不收集 caishen 信号也不注入 caishen override。
# 默认 False（保持股票域原行为）。古例诚实基线测试时由调用方置 True。
# 🔴 2026-09-17 实测补注（排查「caishen 为何 0/207 产出」时踩到，后人务必看清）：
#   · 古例域的实际置位点是 **`engine/ancient_backtest.py:L36` 的 `_jf.DISABLE_CAISHEN = True`**
#     （模块级 import 副作用）—— ⛔ **只看本文件的 `= False` 会误判为"已启用"**。
#   · `caishen_enhance.get_caishen_signal_for_fusion()` **本身正常**（实测 207/207 正常返回、
#     |score| 0.4~8.0、conf 0.75~0.95）⇒ 零产出是**刻意禁用，不是故障**。
#   · 禁用有硬证据：古例盲测 **M4（仅 caishen）＝ 14.5%，凶→吉 160** ⇒ 极强吉向偏置，**启用即毁判定**。
DISABLE_CAISHEN = False

# 德神临传对凶引擎的降权倍率（"只解凶不助吉"）。
# 古例语料凶重(朴素"永远凶"=83.6%)，过强降权会把多数凶案误推为吉 → 回归。
# 探针校准：0.5(原)→0.7( milder )，消融验证。
DE_HALF_MULT = 0.7

# ---- 古例域六亲打分（两域语义隔离）----
# 股票域 LIUQIN_SCORE 的「官鬼=+1(主力动作偏多)」是股票术语；六壬古例里官鬼=克我者，
# 主灾祸/压力/官非，应为凶。A/B 实证（167 有效案，同种子）：官鬼 +1→-1 使 M3 84.1%→86.0%(+1.9pp)，
# 凶→吉 假阳 9→3，过 M3≥85.4% 闸口。故古例域(DISABLE_CAISHEN=True)用本表，股票域不动。
ANCIENT_LIUQIN_SCORE = {
    '妻财': 2,    # 我克者为财，吉
    '官鬼': -1,   # 克我者，灾祸/压力/官非，凶（六壬基本义理；股票域+1是"主力偏多"术语，不适用古例）
    '父母': 0,    # 生我者，庇护，中性
    '子孙': -1,   # 我生者，泄气，偏凶
    '兄弟': -2,   # 比劫，劫财，凶
}


# ======================================================================
# 信念质量构造
# ======================================================================
def mass_from_signed(score: float, conf: float, up_positive: bool = True) -> Dict[str, float]:
    """有符号分数(涨-positive) + 置信度 → mass 函数 {涨,跌,平,⊤}。

    committed = conf * strength(分数强度); 剩余 (1-committed) 归为 ⊤(无知)。
    """
    conf = max(0.02, min(0.98, conf))
    s = score if up_positive else -score
    if s > 0:
        fav, strength = '涨', min(1.0, s / SREF)
    elif s < 0:
        fav, strength = '跌', min(1.0, abs(s) / SREF)
    else:
        fav, strength = '平', 0.5
    committed = conf * strength
    m = {k: 0.0 for k in FRAME}
    m[fav] = committed
    m['⊤'] = 1.0 - committed
    return m


def ds_combine(m1: Dict[str, float], m2: Dict[str, float]) -> Tuple[Dict[str, float], float]:
    """Dempster 组合两个 mass 函数(帧 {涨,跌,平,⊤})。返回 (组合后mass, 冲突K)。"""
    combined = {k: 0.0 for k in FRAME}
    K = 0.0
    for a in FRAME:
        for b in FRAME:
            p = m1.get(a, 0.0) * m2.get(b, 0.0)
            if p == 0.0:
                continue
            if a == b:
                combined[a] += p
            elif a == '⊤':
                combined[b] += p
            elif b == '⊤':
                combined[a] += p
            else:
                K += p  # 两不同单点 → 冲突
    norm = 1.0 - K
    if norm <= 1e-9:
        return {k: 0.0 for k in FRAME} | {'⊤': 1.0}, 1.0
    return {k: v / norm for k, v in combined.items()}, K


# ======================================================================
# ① 门控元控制器 (Context-Gated MoE)
# ======================================================================
class Gate:
    """读盘面上下文, 输出每个引擎分组的权重倍率 + override + 不确定性地板。"""

    def __init__(self, ctx: Dict[str, Any]):
        self.ctx = ctx
        self.group_mult: Dict[str, float] = {}
        self.overrides: List[Tuple[str, float]] = []   # ('force_down', mag)
        self.uncertainty_floor: float = 0.0
        self.log: List[str] = []
        # 支柱③: 用训练库学得的可靠度作为各引擎组权重基线(未校准组维持 1.0)
        if CALIB_PARAMS:
            rel = CALIB_PARAMS.get('group_reliability', {})
            self.group_mult = {
                'wangshuai': rel.get('三传旺衰', 1.0),
                'liuqin': rel.get('六亲', 1.0),
                'keti': rel.get('课体', 1.0),
                'sanchuan_kege': rel.get('三传课格', 1.0),
                'kongwang': rel.get('旬空', 1.0),
                'ba_sha': rel.get('八杀', 1.0),
                'shen_sha': rel.get('神煞', 1.0),
                'holistic': rel.get('综合叙事', 1.0),
                'caishen': rel.get('求财类神', 1.0),  # 求财类神增强组(默认1.0, 待古例回测校准)
            }
        # 弱类 keti 降权：求财/出行/胎产 的错例 100% 为吉→凶（通用课体过度看跌压住吉象）
        zhanlei = self.ctx.get('zhanlei')
        if zhanlei in WEAK_KETI_CATS:
            cur = self.group_mult.get('keti', 1.0)
            self.group_mult['keti'] = cur * KETI_WEAK_MULT
            self.log.append(f'[门控] 弱类({zhanlei}) keti 权重×{KETI_WEAK_MULT} — 通用课体过度看跌, 降权让占类专属信号主导')
        self._apply()

    def _set(self, group: str, mult: float, reason: str) -> None:
        self.group_mult[group] = mult
        self.log.append(f'[门控] {group} 权重×{mult} — {reason}')

    def _is_bubei(self) -> bool:
        si_ke = self.ctx.get('si_ke', []) or []
        def pair(a, b):
            if not a or not b or len(a) < 3 or len(b) < 3:
                return False
            return (a[1], a[2]) == (b[1], b[2])
        for i in range(len(si_ke)):
            for j in range(i + 1, len(si_ke)):
                if pair(si_ke[i], si_ke[j]):
                    return True
        return False

    def _de_present(self) -> bool:
        ba_sha = self.ctx.get('ba_sha', {}) or {}
        shen_sha = self.ctx.get('shen_sha', []) or []
        if isinstance(ba_sha, dict):
            for x in ba_sha.get('八杀明细', []):
                if isinstance(x, dict) and x.get('杀') == '德':
                    return True
        # 精确检查: 神煞列表中明确有"德"/"天德"/"月德"神煞
        if isinstance(shen_sha, dict):
            for v in shen_sha.values():
                if isinstance(v, str) and '德' in v:
                    return True
        elif isinstance(shen_sha, list):
            for s in shen_sha:
                if isinstance(s, str) and ('天德' in s or '月德' in s or s.strip() == '德'):
                    return True
        return False

    def _apply(self) -> None:
        keti = self.ctx.get('keti', '') or ''
        bifa_summary = self.ctx.get('bifa_summary', '') or ''
        kong_info = self.ctx.get('kong_info', {}) or {}

        # 规则1 阴/阳不备: 明面因素不具体 → 降权 + 置底不确定性
        if self._is_bubei():
            for g in ('keti', 'liuqin', 'wangshuai', 'sanchuan_kege'):
                self._set(g, 0.25, '阴/阳不备·明面因素不具备')
            self.uncertainty_floor = max(self.uncertainty_floor, 0.25)
            self.log.append('[门控] 阴/阳不备 → 置底不确定性 +0.25')

        # 规则2 德神临传: 只解凶不助吉 → 凶引擎降权(倍率见 DE_HALF_MULT)
        if self._de_present():
            for g in ('tianjiang', 'ba_sha', 'bifa', 'special_kege'):
                self._set(g, DE_HALF_MULT, '德神临传·只解凶不助吉，凶性减半')
            self.log.append(f'[门控] 德神临传 → 凶引擎权重×{DE_HALF_MULT}')

        # 规则3 罗网(谋划类): 毕法升权 + 强指跌(想买涨反而跌)
        if '罗网' in bifa_summary or '所谋多拙' in bifa_summary:
            self._set('bifa', 1.6, '罗网·谋划类·想买涨反而跌')
            self.overrides.append(('force_down', 0.85))
            self.log.append('[门控] 罗网 → 毕法升权×1.6 且强指跌')

        # 规则4 用神/日支空亡: 该位六亲降权(信息失真)
        if any(kong_info.get(p, False) for p in ('初传', '中传', '末传')):
            self._set('liuqin', self.group_mult.get('liuqin', 1.0) * 0.6, '三传落空亡·六亲信息失真')

        # 规则5 伏吟/返吟: 静体·波动收敛 → 降极端 + 加不确定性
        if '伏吟' in keti or '返吟' in keti:
            for g in ('liuqin', 'wangshuai', 'keti'):
                self._set(g, self.group_mult.get(g, 1.0) * 0.7, '伏吟/反吟·静体·波动收敛')
            self.uncertainty_floor = max(self.uncertainty_floor, 0.15)


# ======================================================================
# 信号重建 (复用 20d 引擎同一套数据)
# ======================================================================
def collect_signals(result: Dict[str, Any]) -> List[Tuple[str, float, bool, float]]:
    """从 result 重建每个引擎的 (group, 涨-positive分数, up_positive, base_conf)。"""
    a = result.get('analysis', {}) or {}
    keti_duanyu = a.get('keti_duanyu', {}) or {}
    liuqin_list = a.get('liuqin', []) or []
    wangshuai_list = a.get('wangshuai', []) or []
    kong_info = a.get('kong_info', {}) or {}
    tianjiang_list = result.get('sanchuan_tianjiang', []) or []
    san_chuan = result.get('san_chuan', []) or []
    ba_sha = a.get('ba_sha', {}) or {}
    ri_gan = result.get('basic_info', {}).get('ri_gan', '')
    signals: List[Tuple[str, float, bool, float]] = []

    # 课体等级
    level = keti_duanyu.get('level', '平')
    signals.append(('keti', get_keti_level_score(level), True, BASE_CONF['keti']))

    # 六亲（十神）—— 消融开关 DISABLE_LIUQIN（env 置非空则关闭该信号组）
    # 古例域用 ANCIENT_LIUQIN_SCORE（官鬼=凶），股票域用 get_liuqin_score（官鬼=+1 主力偏多）
    if not os.environ.get('DISABLE_LIUQIN'):
        for it in liuqin_list:
            lq = it.get('六亲', '') if isinstance(it, dict) else ''
            if lq:
                _lq = ANCIENT_LIUQIN_SCORE.get(lq, get_liuqin_score(lq)) if DISABLE_CAISHEN else get_liuqin_score(lq)
                signals.append(('liuqin', _lq, True, BASE_CONF['liuqin']))

    # 旺衰
    for it in wangshuai_list:
        ws = it.get('旺衰', '') if isinstance(it, dict) else ''
        if ws:
            signals.append(('wangshuai', get_wangshuai_score(ws), True, BASE_CONF['wangshuai']))

    # 空亡(末传)
    if kong_info.get('末传'):
        signals.append(('kongwang', get_kongwang_score('末传'), True, BASE_CONF['kongwang']))

    # 三传天将(逐传)
    for tj in tianjiang_list:
        s = TIANJIANG_SCORE.get(tj, 0)
        if s != 0:
            signals.append(('tianjiang', s, True, BASE_CONF['tianjiang']))

    # 八杀 valence（占类化·确定性·无泄漏）：德/合/鬼/墓/破/害/刑/冲
    # 由 liuren_keti_bifa.extract_shen_sha_valence 预计算；仅当古例路径置了
    # _shen_sha_valence 才注入（生产股票路径不置该键 → 不受影响）。
    ss_val = a.get('_shen_sha_valence', {}) or {}
    ba_val = ss_val.get('ba_sha', {}) or {}
    if ba_val.get('score', 0) != 0:
        signals.append(('ba_sha', float(ba_val.get('score', 0)), True, BASE_CONF['ba_sha']))

    # 神煞 valence（占类化·确定性·无泄漏）：驿马/贵人/日德/劫煞/灾煞/天罗地网...
    ssha_val = ss_val.get('shen_sha', {}) or {}
    if ssha_val.get('score', 0) != 0:
        # 幅度倍率 `ZERI_SHENSHA_MULT`（默认 1.0 ＝ 原行为；0.5 ＝ 吉案取向；0 ＝ 关闭）
        _ss = float(ssha_val.get('score', 0)) * ZERI_SHENSHA_MULT
        if _ss != 0:
            signals.append(('shen_sha', _ss, True, BASE_CONF['shen_sha']))

    # 胎产专属：子孙生扶 / 德神临（确定性·无泄漏）
    # 仅古例 胎产 路径置了 _taichan_valence 且 score≠0 才注入（股票路径不置→零影响）。
    if a.get('_zhanlei') == '胎产':
        tc_val = a.get('_taichan_valence', {}) or {}
        if tc_val.get('score', 0) != 0:
            signals.append(('taichan', float(tc_val.get('score', 0)), True, BASE_CONF['taichan']))

    # 官讼专属：解厄吉 / 官鬼凶 / 连茹凶（确定性·无泄漏）
    # 仅古例 官讼 路径置了 _guansong_valence 且 score≠0 才注入（股票路径不置→零影响）。
    # 消融开关 DISABLE_GUANSONG：设为非空则跳过官讼信号（用于同种子 A/B 证明零回归）。
    if a.get('_zhanlei') == '官讼' and not os.environ.get('DISABLE_GUANSONG'):
        gs_val = a.get('_guansong_valence', {}) or {}
        gs_score = gs_val.get('score', 0)
        if gs_score != 0:
            # 约定: score 传幅度(正值), 方向由 up 表达(>0→吉, <0→凶)
            signals.append(('guansong', abs(float(gs_score)), gs_score > 0, BASE_CONF['guansong']))

    # 求财专属：财爻生扶吉 / 青龙乘财吉 / 财虚凶（确定性·无泄漏）
    # 仅古例 求财 路径置了 _qiucai_valence 且 score≠0 才注入（股票路径不置→零影响）。
    # 消融开关 DISABLE_QIUCAI：设为非空则跳过求财信号（用于同种子 A/B 证明零回归）。
    if a.get('_zhanlei') == '求财' and not os.environ.get('DISABLE_QIUCAI'):
        qc_val = a.get('_qiucai_valence', {}) or {}
        qc_score = qc_val.get('score', 0)
        if qc_score != 0:
            # 约定: score 传幅度(正值), 方向由 up 表达(>0→吉, <0→凶)
            signals.append(('qiucai', abs(float(qc_score)), qc_score > 0, BASE_CONF['qiucai']))

    # 疾病专属：虎鬼/子孙解厄/生龙/贵医/两蛇夹墓/华盖孝帛（确定性·无泄漏）
    # 仅古例 疾病 路径置了 _disease_valence 且 score≠0 才注入（股票路径不置→零影响）。
    if a.get('_zhanlei') == '疾病':
        dz_val = a.get('_disease_valence', {}) or {}
        dz_score = dz_val.get('score', 0)
        if dz_score != 0:
            # 约定: score 传幅度(正值), 方向由 up 表达(>0→吉, <0→凶)
            signals.append(('disease', abs(float(dz_score)), dz_score > 0, BASE_CONF['disease']))

    # 功名专属：临官帝旺/六阳数足/帘幕贵人(记录) + 朱雀值鬼/墓绝凶（仕宦章+选举章，确定性·无泄漏）
    # 仅古例 功名 路径置了 _gongming_valence 且 score≠0 才注入（股票路径不置→零影响）。
    # 消融开关 DISABLE_GONGMING：设为非空则跳过功名信号（用于同种子 A/B 证明零回归）。
    if a.get('_zhanlei') == '功名' and not os.environ.get('DISABLE_GONGMING'):
        gm_val = a.get('_gongming_valence', {}) or {}
        gm_score = gm_val.get('score', 0)
        if gm_score != 0:
            signals.append(('gongming', abs(float(gm_score)), gm_score > 0, BASE_CONF['gongming']))

    # 家宅/出行/婚姻 专属（凶向为主；阳宅/出行/婚姻章，确定性·无泄漏）
    # 仅古例对应占类置了 _*_valence 且 score≠0 才注入（股票路径不置→零影响）。
    # 消融开关 DISABLE_XZ（xinzang 等）：统一用 DISABLE_JIAZHAI/DISABLE_CHUXING 等。
    for _k, _key, _conf in (('家宅', '_jiazhai_valence', 'jiazhai'),
                            ('出行', '_chuxing_valence', 'chuxing'),
                            ('婚姻', '_hunyin_valence', 'hunyin')):
        if a.get('_zhanlei') == _k:
            _v = a.get(_key, {}) or {}
            _s = _v.get('score', 0)
            if _s != 0:
                signals.append((_conf, abs(float(_s)), _s > 0, BASE_CONF[_conf]))

    # 贼盗专属：玄武乘鬼/财爻空陷（贼盗章）+ 亡盗类神寻物（失物章）
    # 触发条件放宽：zhanlei=='贼盗'（原行为）或 zhanlei=='其他' 且 result 带 leishen
    # （亡盗案零涟漪隔离：其余"其他"案与股票路径无 leishen → 不触发）。
    if a.get('_zhanlei') == '贼盗' or (a.get('_zhanlei') == '其他' and result.get('leishen')):
        _v = a.get('_zeidao_valence', {}) or {}
        _s = _v.get('score', 0)
        if _s != 0:
            _conf = BASE_CONF['zeidao']
            # 亡盗寻得吉提权：邵师失物法以「类神在传/加日辰定见」为主断，
            # 通用八杀(破/刑/冲)在失物语境仅表物损(§199 酉破子/酉冲卯)而非寻不回。
            # 仅"其他"+leishen+吉向提权，贼盗章与凶向不受影响（零涟漪）。
            if a.get('_zhanlei') == '其他' and _s > 0:
                _conf = min(1.35, _conf * 1.5)
            signals.append(('zeidao', abs(float(_s)), _s > 0, _conf))

    # ---- 天狱课（通用课体凶信号，任何占类；天罡辰加日干长生位=日本 → 天狱，不有大服必有大祸）----
    # 仅古例路径置 _tianyu_valence（股票不置→零影响）；诊断 8/8 全凶（2026-08-02）。
    ty_val = a.get('_tianyu_valence', {}) or {}
    ty_score = ty_val.get('score', 0)
    if ty_score != 0:
        signals.append(('tianyu', abs(float(ty_score)), ty_score > 0, BASE_CONF.get('tianyu', 0.85)))

    # ---- 太岁临身（守卫版凶信号：排除胎产/官讼 + 三传乘青龙禁）----
    # 仅古例路径置 _tai_sui_valence（股票不置→零影响）；守卫版全量回测 8/8=100%（2026-08-02）。
    ts_val = a.get('_tai_sui_valence', {}) or {}
    ts_score = ts_val.get('score', 0)
    if ts_score != 0:
        signals.append(('tai_sui', abs(float(ts_score)), ts_score > 0, BASE_CONF.get('tai_sui', 0.85)))

    # ---- 股票域自有特征库：八杀/神煞 valence + 求财 valence（涨/跌，确定性·无泄漏）----
    # 复用 liuren_keti_bifa 已验证的确定性抽取原语，以 zhanlei="求财" 把股票当财运域处理。
    # 仅当股票路径置了 _is_stock 且未置 DISABLE_STOCK_VALENCE 才注入（古例路径不置 _is_stock → 零影响）。
    # 与 caishen 决裂：本库不注入任何看涨偏置，只如实反映盘面传统吉凶结构。
    if a.get('_is_stock') and not os.environ.get('DISABLE_STOCK_VALENCE'):
        try:
            from engine.stock_liuren_features import extract_stock_valence
            sv = extract_stock_valence(result)
            for comp in ('stock_ba_sha', 'stock_shen_sha', 'stock_qiucai'):
                sc = sv.get(comp, 0) or 0
                if sc != 0:
                    # 约定: score 传幅度(正值), 方向由 up 表达(>0→涨, <0→跌)
                    signals.append((comp, abs(float(sc)), sc > 0, BASE_CONF[comp]))
        except Exception:
            pass

    # 毕法赋(复用 keti_duanyu.bifa 的股市信号)
    bifa_result = keti_duanyu.get('bifa', {}) or {}
    bf = bifa_result.get('股市信号', {}) if isinstance(bifa_result, dict) else {}
    bf_t = bf.get('综合倾向', '平')
    bf_s = bf.get('信号强度', 0)
    bf_w = bf.get('各信号权重', {}) or {}
    if bf_t == '跌' and bf_s > 0.3:
        boost = -min(int(bf_w.get('跌', 0) * 1.5), 12)
        signals.append(('bifa', boost, True, BASE_CONF['bifa']))
    elif bf_t == '涨' and bf_s > 0.3:
        boost = min(int(bf_w.get('涨', 0) * 1.5), 12)
        signals.append(('bifa', boost, True, BASE_CONF['bifa']))

    # 三传课格
    sk = keti_duanyu.get('sanchuan_kege', {}) or {}
    sk_sig = sk.get('股市信号', {}) if isinstance(sk, dict) else {}
    if sk_sig.get('综合倾向') == '跌' and sk_sig.get('信号强度', 0) > 0.5:
        signals.append(('sanchuan_kege', -int(sk_sig.get('信号强度', 0) * 4), True, BASE_CONF['sanchuan_kege']))
    elif sk_sig.get('综合倾向') == '涨' and sk_sig.get('信号强度', 0) > 0.5:
        signals.append(('sanchuan_kege', int(sk_sig.get('信号强度', 0) * 4), True, BASE_CONF['sanchuan_kege']))

    # 特殊课格
    kg = keti_duanyu.get('special_kege', {}) or {}
    kg_sig = kg.get('信号汇总', {}) if isinstance(kg, dict) else {}
    if kg_sig.get('倾向') == '跌' and kg_sig.get('强度', 0) > 0.3:
        signals.append(('special_kege', -int(kg_sig.get('强度', 0) * 2), True, BASE_CONF['special_kege']))
    elif kg_sig.get('倾向') == '涨' and kg_sig.get('强度', 0) > 0.3:
        signals.append(('special_kege', int(kg_sig.get('强度', 0) * 2), True, BASE_CONF['special_kege']))

    # 十二长生/帝旺入传
    rw = GAN_WX.get(ri_gan, '金')
    cs = CHANGSHENG_POS.get(rw, '巳')
    dw = DIWANG_POS.get(rw, '酉')
    if cs in san_chuan:
        pos = san_chuan.index(cs)
        if kong_info.get(['初传', '中传', '末传'][pos], False):
            signals.append(('changsheng', get_changsheng_kong_score('长生'), True, BASE_CONF['changsheng']))
        else:
            signals.append(('changsheng', get_changsheng_score('长生'), True, BASE_CONF['changsheng']))
    if dw in san_chuan:
        pos = san_chuan.index(dw)
        if not kong_info.get(['初传', '中传', '末传'][pos], False):
            signals.append(('changsheng', get_changsheng_score('帝旺'), True, BASE_CONF['changsheng']))

    # ---- 支柱④ → 注入概率层: 综合叙事 / CBR 作为「新增 D-S 证据组」 ----
    hj = result.get('holistic_judgment') or {}
    if isinstance(hj, dict) and 'error' not in hj and 'score' in hj:
        hsc = float(hj.get('score') or 0.0)
        hconf = max(0.30, min(0.95, float(hj.get('confidence') or 0.70)))
        sgn = 1.0 if hsc >= 0 else -1.0
        mag = min(3.0, abs(hsc) * 3.0)
        signals.append(('holistic', sgn * mag, True, hconf))

    # ---- 求财类神专项增强 (朱雀+六合 > 财爻 > 青龙) ----
    # 用户明确指出: 股票预测中, 朱雀(消息)、六合(交易)、财爻、青龙是核心类神
    # 朱雀+六合同现四课/三传 → 最高优先级看涨信号
    try:
        from engine.caishen_enhance import get_caishen_signal_for_fusion
        si_ke = result.get('si_ke', []) or []
        tianjiang_map = result.get('tianjiang_map', {}) or {}
        liuqin_list = a.get('liuqin', []) or []
        score, up, conf, detail = get_caishen_signal_for_fusion(
            tianjiang_list, tianjiang_map, san_chuan, si_ke, liuqin_list, ri_gan
        )
        if not DISABLE_CAISHEN and conf > 0.1 and abs(score) > 0.1:
            signals.append(('caishen', score, up, conf))
            # 存储详情供仪表盘展示
            result['_caishen_detail'] = detail
    except Exception:
        pass  # 求财增强非关键路径，降级不影响主流程

    return signals


# ======================================================================
# 融合主入口
# ======================================================================
def fuse(result: Dict[str, Any]) -> Dict[str, Any]:
    """对单条预测 result 执行门控 + D-S 融合, 返回精准判断。"""
    a = result.get('analysis', {}) or {}
    keti_duanyu = a.get('keti_duanyu', {}) or {}

    ctx = {
        'keti': result.get('keti', ''),
        'si_ke': result.get('si_ke', []),
        'ba_sha': a.get('ba_sha', {}),
        'shen_sha': a.get('shen_sha', []),
        'bifa_summary': keti_duanyu.get('bifa_summary', '') or '',
        'kong_info': a.get('kong_info', {}),
        'tianjiang_list': result.get('sanchuan_tianjiang', []),
        'san_chuan': result.get('san_chuan', []),
        'ri_gan': result.get('basic_info', {}).get('ri_gan', ''),
        'zhanlei': a.get('_zhanlei'),
    }
    gate = Gate(ctx)
    signals = collect_signals(result)

    masses: List[Dict[str, float]] = []
    reasons: List[str] = []
    for group, score, up, bconf in signals:
        mult = gate.group_mult.get(group, 1.0)
        conf = max(0.02, min(0.98, bconf * mult))
        m = mass_from_signed(score, conf, up)
        masses.append(m)
        reasons.append(f'{group}({score:+.0f},conf={conf:.2f})')

    # override(罗网强指跌) — 这是完整 mass 函数, 正常进入组合
    for otype, mag in gate.overrides:
        if otype == 'force_down':
            masses.append(mass_from_signed(-3, mag, True))
            reasons.append(f'override(罗网·强指跌, conf={mag:.2f})')

    # caishen override: 当 caishen 信号强且置信度高时, 注入额外信念质量
    # v5修复: 天将缺失时阈值从1.0→0.5, 救回弱信号(如仅有六亲财爻无将)案例
    # 正常有将场景保持1.0阈值, 避免噪声信号误触
    # 占卜域(DISABLE_CAISHEN)跳过该股票域看涨注入器
    if DISABLE_CAISHEN:
        caishen_signals_list = []
        caishen_net = 0.0
    else:
        caishen_detail = result.get('_caishen_detail') or {}
        caishen_signals_list = caishen_detail.get('signals', []) if isinstance(caishen_detail, dict) else []
        caishen_bullish = float(caishen_detail.get('overall_bullish', 0)) if isinstance(caishen_detail, dict) else 0
        caishen_bearish = float(caishen_detail.get('overall_bearish', 0)) if isinstance(caishen_detail, dict) else 0
        caishen_net = caishen_bullish - caishen_bearish
        tianjiang_absent = not any(result.get('sanchuan_tianjiang', []))
        override_threshold = 0.5 if tianjiang_absent else 1.0
        if caishen_signals_list and abs(caishen_net) >= override_threshold:
            caishen_conf = 0.82  # 较高置信度注入(求财类神是用户明确指出的核心类神)
            caishen_mag = min(5.0, abs(caishen_net) * 1.3)  # 古例回测校准: 增强överride力度×1.3
            caishen_mass = mass_from_signed(caishen_mag if caishen_net > 0 else -caishen_mag, caishen_conf, True)
            masses.append(caishen_mass)
            reasons.append(f'caishen_ovr(net={caishen_net:+.1f},conf={caishen_conf:.2f})')

    # D-S 顺序组合(所有输入均为归一化 mass)
    combined = {'涨': 0.0, '跌': 0.0, '平': 0.0, '⊤': 1.0}
    K = 0.0
    for m in masses:
        combined, k = ds_combine(combined, m)
        K = max(K, k)

    # 不确定性地板(阴不备/伏吟返吟): 组合完成后注入无知质量, 保持总和=1
    if gate.uncertainty_floor > 0:
        fl = min(0.6, gate.uncertainty_floor)
        new_top = combined['⊤'] + fl * (1.0 - combined['⊤'])
        rest = combined['涨'] + combined['跌'] + combined['平']
        scale = (1.0 - new_top) / rest if rest > 1e-9 else 0.0
        for s in ('涨', '跌', '平'):
            combined[s] = combined[s] * scale
        combined['⊤'] = new_top
        reasons.append(f'uncertainty_floor(+{fl:.2f} 无知质量)')

    committed = combined['涨'] + combined['跌'] + combined['平']
    bet_up = combined['涨'] + combined['⊤'] / 3.0
    bet_down = combined['跌'] + combined['⊤'] / 3.0
    bet_flat = combined['平'] + combined['⊤'] / 3.0

    conflict = K
    # 置信度 = 承诺质量 ×(1-冲突): 冲突高 → 置信低, 但不再强制弃权
    confidence = round(committed * (1.0 - min(1.0, conflict)), 3)

    # 方向结论: 由净 pignistic 概率(已融合全部冲突后的净方向)决定。
    # 仅当最优与次优差距过小 或 置信过低才判震荡(真正的不确定),
    # 不再用「两两最大冲突>0.5」硬弃权——那会把 98%看跌误判为震荡。
    # v5校准: margin 0.04→0.02→0.01, confidence 0.08→0.05→0.03
    # 进一步放宽: 减少凶→平漏判(E类错误), 降低确定性要求
    bets = {'涨': bet_up, '跌': bet_down, '平': bet_flat}
    best = max(bets, key=bets.get)
    margin = bets[best] - max(v for k, v in bets.items() if k != best)
    # 当最优是平, 且平的概率确实领先 → 保留为平(不强制震荡)
    # 仅当确定性极低(margin<0.01 或 confidence<0.03)时才弃权为震荡
    if margin < 0.01 or confidence < 0.03:
        trend = '震荡'
    elif best == '平' and margin >= 0.02:
        trend = '平'
    elif best == '涨':
        trend = '看涨'
    else:
        trend = '看跌'

    # 最终概率: 以 D-S 融合质量为准(D-S 已结构性处理 冲突→不确定性 的校准映射)。
    # 注: 支柱③的逻辑回归概率映射(engine.calibration.calibrate_probability)目前
    # 仅在 Corpus A 的「自动标注特征空间」内做过 5折验证(方向准确率 65%→69%),
    # 与 20d 引擎 collect_signals 的信号尺度/语义存在错配, 不能直接覆盖 D-S 概率,
    # 否则会产生「绝不会涨的课被判 94% 涨」这类灾难性误判。故此处保持 D-S 概率,
    # 逻辑回归作为研究工具保留, 待在 20d 特征空间重训后(需把 558 标注案例跑通 20d
    # 引擎并标注)再考虑接入。支柱③的可靠度加权已通过 group_mult 基线生效。
    prob_up, prob_down, prob_flat = bet_up, bet_down, bet_flat

    return {
        'trend': trend,
        'prob_up': round(prob_up, 3),
        'prob_down': round(prob_down, 3),
        'prob_flat': round(prob_flat, 3),
        'confidence': confidence,
        'conflict': round(conflict, 3),
        'committed_mass': round(committed, 3),
        'mass': {k: round(v, 3) for k, v in combined.items()},
        'gate_log': gate.log,
        'active_signals': reasons,
        'signal_count': len(signals),
    }


if __name__ == '__main__':
    import json
    import sys
    sys.path.insert(0, '.')
    from liuren_20d_engine import get_liuren_20d_signal
    r = get_liuren_20d_signal(sys.argv[1] if len(sys.argv) > 1 else '2026-07-30', shichen='巳')
    fj = fuse(r)
    print(json.dumps(fj, ensure_ascii=False, indent=2))
