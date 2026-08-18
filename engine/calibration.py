# -*- coding: utf-8 -*-
"""
支柱③：训练库反向校准层 (Learned Calibration)
================================================
用标注语料（古例 + 股例）反向校准融合层 judgment_fusion 的两个核心手调参数：

  1. 每个引擎组(engine group)的「经验可靠度权重」→ 替换 fuse() 里写死的 group_mult=1.0
  2. 从融合原始分 → 校准概率 P(涨) 的「逻辑回归映射」→ 替换「信念质量」直接当概率

设计原则
--------
* ML 不替代 17 个引擎，只学「怎么融合它们」——与支柱②一致。
* 只校准训练数据里「能观测到的引擎组」；其余组维持先验(=1.0)。诚实，不假装见过没见过的数据。
* 三个语料分工：
    - Corpus A (sanchuan_kege_annotated_cases.json, 334例): 自带干净 stock_signal 方向标签 → 主训练集
    - Corpus B (daliuren_shuzheng_cases.json, 224例): 大师 interpretation 抽吉/凶极性 → 弱标签，交叉验证课体/课格组可靠度
    - 股例 (stock_training_cases.json + augmented, 12例): 真值最干净 → 留出测试集（不进训练）
* 标注来源说明：Corpus A 的 stock_signal 是早前自动标注的产物，属「代理标签(proxy)」，
  因此学出的权重应视作「先验」而非金科玉律；12 股例是真实回测，作为最终验证。

可用引擎组（依数据可观测性）
----------------------------
  三传课格(kege) | 六亲(liuqin) | 三传旺衰(wangshuai) | 课体(keti) | 旬空(xunkong, 含初传空交互)
其余 12 个引擎组在古例字段里不可观测 → 维持 group_mult=1.0。

外部依赖：numpy（系统 Python 3.12 已带）。无 sklearn 依赖（逻辑回归手写）。
"""
import json
import math
import os
from collections import defaultdict, Counter

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
PARAMS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration_params.json")

# ----------------------------------------------------------------------------- 领域词典
# 课格极性：值∈[-1,1]，正值≈吉/涨，负值≈凶/跌，绝对值=该格对方向的「把握强度」。
# 仅覆盖 Corpus A 实际出现的 51 种。
KEGE_POLARITY = {
    "全局课": 0.0, "玄胎": -0.3, "退连茹": -0.4, "进连茹": 0.4,
    "进间传": 0.2, "曲直课": 0.3, "稼穑课": 0.0, "润下课": -0.3, "炎上课": 0.3,
    "亨通课": 0.6, "退间传": -0.2, "三阴": -0.8, "重阴": -0.6, "铸印": 0.4,
    "呈斗": 0.3, "正阳": 0.5, "从革课": -0.2, "升阶": 0.5, "返驾": 0.2,
    "登三天": 0.5, "殃咎课": -0.8, "联芳": 0.4, "游子": -0.3, "就燥": -0.2,
    "凝阴": -0.6, "极阴": -0.8, "顾祖": 0.2, "将泰": 0.6, "从吉": 0.5,
    "流金": -0.3, "献刃": -0.7, "地角": -0.4, "革故从新": -0.3, "涉三渊": -0.6,
    "登庸": 0.5, "向三阳": 0.5, "龙潜": -0.3, "正和": 0.4, "入墓": -0.7,
    "冥阳": -0.3, "五墓": -0.8, "高盖乘轩": 0.5, "迅戾": -0.6, "出户": 0.2,
    "溟蒙": -0.4, "斫轮": 0.2, "人局": -0.3, "回春": 0.6, "出奇": 0.3, "正己": 0.3,
}

# 课体极性：仅覆盖 Corpus B 实际出现的 12 种。
KETI_POLARITY = {
    "元首": 0.6, "伏吟": -0.5, "八专": 0.1, "重审": 0.4, "比用": 0.1,
    "涉害": 0.2, "遥克": 0.1, "昴星": -0.2, "别责": -0.1, "反吟": -0.6,
    "闭口": 0.0, "回环": 0.2,
}

# 六亲极性（股市语义：财=涨，官鬼=跌/管制，印=护持平偏吉，食伤=生财偏吉，比劫=耗散偏凶）
LIUQIN_POLARITY = {
    "比肩": 0.0, "劫财": -0.2, "食神": 0.3, "伤官": -0.2, "正财": 0.6,
    "偏财": 0.5, "正官": -0.2, "七杀": -0.5, "正印": 0.2, "偏印": -0.1,
}

# 旺衰极性
WANGSHUAI_POLARITY = {"旺": 0.5, "相": 0.3, "休": -0.1, "囚": -0.4, "死": -0.5}

# 季节→当旺五行（用于四季旺衰推算）
SEASON_ELEMENT = {"春": "木", "夏": "火", "秋": "金", "冬": "水", "四季": "土"}

# 天干/地支五行与阴阳
GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
              "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
GAN_YINYANG = {"甲": "阳", "丙": "阳", "戊": "阳", "庚": "阳", "壬": "阳",
               "乙": "阴", "丁": "阴", "己": "阴", "辛": "阴", "癸": "阴"}
DIZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
DIZHI_YINYANG = {"子": "阳", "寅": "阳", "辰": "阳", "午": "阳", "申": "阳", "戌": "阳",
                 "丑": "阴", "卯": "阴", "巳": "阴", "未": "阴", "酉": "阴", "亥": "阴"}
GAN_ORDER = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 旬空表（按旬首支）
XUNKONG_BY_SHOU = {
    "子": ("戌", "亥"), "戌": ("申", "酉"), "申": ("午", "未"),
    "午": ("辰", "巳"), "辰": ("寅", "卯"), "寅": ("子", "丑"),
}

# Corpus B interpretation 极性词典（弱标签用）
GOOD_WORDS = ["吉", "利", "成", "喜", "得", "生", "兴", "旺", "安", "顺", "益", "荣",
              "泰", "祥", "福", "遂", "通", "亨", "升", "进", "明", "和", "庆", "德",
              "康", "宁", "宜", "佳", "优", "发", "盛"]
BAD_WORDS = ["凶", "败", "损", "病", "死", "亡", "讼", "囚", "耗", "灾", "殃", "咎",
             "困", "破", "伤", "危", "祸", "厄", "滞", "退", "沉", "忧", "愁", "散",
             "离", "崩", "废", "衰", "陷", "欺", "盗", "贼", "丧", "苦", "难"]


# ----------------------------------------------------------------------------- 基础工具
def _ten_gods(ri_gan, tw, ty):
    """日干 ri_gan 对目标五行 tw/阴阳 ty 的十神。"""
    w = GAN_WUXING[ri_gan]
    y = GAN_YINYANG[ri_gan]
    if tw == w:
        return "比肩" if ty == y else "劫财"
    sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # 我生
    ke = {"木": "土", "火": "金", "金": "木", "水": "火", "土": "水"}      # 我克
    if sheng[w] == tw:
        return "食神" if ty == y else "伤官"
    if ke[w] == tw:
        return "偏财" if ty == y else "正财"
    ke2 = {v: k for k, v in ke.items()}     # 克我者
    if ke2[tw] == w:
        return "七杀" if ty == y else "正官"
    sheng2 = {v: k for k, v in sheng.items()}  # 生我者
    if sheng2[tw] == w:
        return "偏印" if ty == y else "正印"
    return "比肩"


def liuqin_of(ri_gan, dizhi):
    tw = DIZHI_WUXING.get(dizhi, "土")
    ty = DIZHI_YINYANG.get(dizhi, "阴")
    return _ten_gods(ri_gan, tw, ty)


def xunkong_of(ganzhi):
    """返回 (旬首支, (空支1, 空支2))。ganzhi 如 '甲子'/'乙巳'。"""
    if not ganzhi or len(ganzhi) < 2:
        return None, ()
    g, z = ganzhi[0], ganzhi[1]
    dg = GAN_ORDER.index(g)
    # 旬首支 = 把 z 往回退 dg 位（同旬内 干从 甲 开始）
    shou_idx = (ZHI_ORDER.index(z) - dg) % 12
    shou = ZHI_ORDER[shou_idx]
    k1, k2 = XUNKONG_BY_SHOU.get(shou, ())
    return shou, (k1, k2)


def wangshuai_of(dizhi, season):
    """季节→旺衰状态。season∈春/夏/秋/冬/四季。"""
    if season not in SEASON_ELEMENT:
        return "平"
    E = SEASON_ELEMENT[season]
    D = DIZHI_WUXING.get(dizhi, "土")
    table = {
        "木": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
        "火": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
        "金": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
        "水": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
        "土": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
    }
    return table[E].get(D, "平")


# ----------------------------------------------------------------------------- 特征提取
def extract_group_signals(case, source):
    """
    从一条语料记录抽可观测引擎组信号。
    返回 {group: (signed, conf)}，signed∈[-1,1] 已含极性，conf∈[0,1] 为该组观测完整度。
    source ∈ {'A','B','stock'}
    """
    sig = {}
    if source == "A":
        kege_list = case.get("kege_list") or []
        sanchuan = case.get("sanchuan_dizhi") or []
        ri_gan = case.get("ri_gan", "")
        season = case.get("season", "")
        ganzhi = case.get("ganzhi", "")
        # 三传课格
        if kege_list:
            s = sum(KEGE_POLARITY.get(k, 0.0) for k in kege_list)
            s = max(-1.0, min(1.0, s))
            sig["三传课格"] = (s, 1.0)
        # 六亲（三传地支 vs 日干）
        if sanchuan and ri_gan in GAN_WUXING:
            s = 0.0
            for d in sanchuan:
                lq = liuqin_of(ri_gan, d)
                s += LIUQIN_POLARITY.get(lq, 0.0)
            s = max(-1.0, min(1.0, s / max(1, len(sanchuan))))
            sig["六亲"] = (s, 1.0)
        # 三传旺衰
        if sanchuan and season:
            s = 0.0
            for d in sanchuan:
                ws = wangshuai_of(d, season)
                s += WANGSHUAI_POLARITY.get(ws, 0.0)
            s = max(-1.0, min(1.0, s / max(1, len(sanchuan))))
            sig["三传旺衰"] = (s, 1.0)
        # 旬空（含初传空交互）
        _, kong = xunkong_of(ganzhi)
        if kong and sanchuan:
            chu_kong = sanchuan[0] in kong
            # 旬空组：初传空→显著减力（负向），否则中性
            s = -0.6 if chu_kong else 0.0
            sig["旬空"] = (s, 1.0)
            if chu_kong:
                sig["_初传空"] = (1.0, 1.0)  # 交互标记特征
    elif source == "B":
        keti = case.get("ke_ti") or ""
        sanchuan = []
        sc = case.get("sanchuan") or ""
        if sc and "→" in sc:
            sanchuan = [x.strip() for x in sc.split("→") if x.strip()]
        ri_gan = case.get("ri_gan", "")
        ganzhi = None
        if case.get("year") and case.get("day"):
            ganzhi = str(case.get("day", ""))[:2]  # day 字段形如 '庚寅'
        # 课体
        keti_list = [t.strip() for t in str(keti).split("、") if t.strip()]
        if keti_list:
            s = sum(KETI_POLARITY.get(t, 0.0) for t in keti_list)
            s = max(-1.0, min(1.0, s))
            sig["课体"] = (s, 1.0)
        # 六亲（如有三传+日干）
        if sanchuan and ri_gan in GAN_WUXING:
            s = 0.0
            for d in sanchuan:
                if d in DIZHI_WUXING:
                    lq = liuqin_of(ri_gan, d)
                    s += LIUQIN_POLARITY.get(lq, 0.0)
            if sanchuan:
                s = max(-1.0, min(1.0, s / len(sanchuan)))
                sig["六亲"] = (s, 1.0)
        # 旬空（B 有 day 干支）
        if ganzhi:
            _, kong = xunkong_of(ganzhi)
            if kong and sanchuan:
                chu_kong = sanchuan[0] in kong
                sig["旬空"] = (-0.6 if chu_kong else 0.0, 1.0)
                if chu_kong:
                    sig["_初传空"] = (1.0, 1.0)
    # stock 语料：sanchuan 多为 {first:'白虎+金',...} 天将+五行 结构，抽天将组信号
    elif source == "stock":
        sc = case.get("sanchuan") or {}
        tj_vals = []
        if isinstance(sc, dict):
            for v in sc.values():
                if isinstance(v, str) and "+" in v:
                    tj = v.split("+")[0].strip()
                    if tj in TIANJIANG_POLARITY:
                        tj_vals.append(TIANJIANG_POLARITY[tj])
        elif isinstance(sc, list):
            for x in sc:
                tj = x.get("天将", x) if isinstance(x, dict) else x
                if tj in TIANJIANG_POLARITY:
                    tj_vals.append(TIANJIANG_POLARITY[tj])
        if tj_vals:
            s = max(-1.0, min(1.0, sum(tj_vals) / len(tj_vals)))
            sig["天将"] = (s, 1.0)
        # 若含 ri_gan 与三传地支则再抽六亲
        ri_gan = case.get("ri_gan") or ""
        dz = []
        if isinstance(sc, list):
            dz = [x.get("地支", x) if isinstance(x, dict) else x for x in sc]
        if dz and ri_gan in GAN_WUXING:
            s = 0.0
            for d in dz:
                if d in DIZHI_WUXING:
                    s += LIUQIN_POLARITY.get(liuqin_of(ri_gan, d), 0.0)
            if dz:
                sig["六亲"] = (max(-1.0, min(1.0, s / len(dz))), 1.0)
    return sig


# 天将极性（股市语义：青龙/贵人/六合/太常吉，白虎/玄武/勾陈/天空凶）
TIANJIANG_POLARITY = {
    "贵人": 0.4, "青龙": 0.4, "六合": 0.3, "太常": 0.1, "天后": 0.2, "太阴": 0.1,
    "朱雀": 0.0, "勾陈": -0.3, "螣蛇": -0.3, "白虎": -0.5, "玄武": -0.4, "天空": -0.2,
}


def label_of(case, source):
    """返回标签∈[-1,1]（涨=+1，跌=-1，平/震荡=0），无法标注返回 None。"""
    if source == "A":
        ss = case.get("stock_signal")
        if ss is None:
            return None
        m = {"涨": 1.0, "震荡偏涨": 0.6, "平": 0.0, "震荡": 0.0,
             "震荡偏跌": -0.6, "跌": -1.0}
        return m.get(ss)
    if source == "stock":
        at = case.get("actual_trend")
        if not at or "待实盘验证" in str(at) or "校正案例" in str(at):
            return None
        m = {"涨": 1.0, "平": 0.0, "跌": -1.0,
             "先涨后跌": -0.3, "先跌后平": -0.3, "震荡偏跌": -0.6, "震荡偏涨": 0.6}
        return m.get(at.strip()) if isinstance(at, str) else None
    if source == "B":
        # 弱标签：从 interpretation 抽吉凶极性
        txt = case.get("interpretation") or ""
        g = sum(txt.count(w) for w in GOOD_WORDS)
        b = sum(txt.count(w) for w in BAD_WORDS)
        tot = g + b
        if tot == 0:
            return 0.0
        pol = (g - b) / tot  # ∈[-1,1]
        if abs(pol) < 0.15:
            return 0.0
        return max(-1.0, min(1.0, pol))
    return None


# ----------------------------------------------------------------------------- 数据装载
def load_labeled():
    """返回 (train_records, stock_records)。
    train = Corpus A(强标签) + Corpus B(弱标签)；stock = 股例(辅助描述性核对，不进训练)。
    注意：股例当前缺 ri_gan 与三传地支、且 actual_trend 为叙述，无法作为严谨回测，
    故仅作辅助展示。"""
    train, stock = [], []
    # Corpus A
    p = os.path.join(DATA, "sanchuan_kege_annotated_cases.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        for c in d.get("cases", []):
            lab = label_of(c, "A")
            if lab is None:
                continue
            sig = extract_group_signals(c, "A")
            if sig:
                train.append({"sig": sig, "label": lab, "weak": False, "src": "A"})
    # Corpus B
    p = os.path.join(DATA, "daliuren_shuzheng_cases.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        for c in d:
            lab = label_of(c, "B")
            if lab is None:
                continue
            sig = extract_group_signals(c, "B")
            if sig:
                train.append({"sig": sig, "label": lab, "weak": True, "src": "B"})
    # 股例（辅助）
    for fname in ["stock_training_cases.json", "stock_training_augmented.json"]:
        p = os.path.join(DATA, fname)
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            for c in d:
                lab = label_of(c, "stock")
                if lab is None:
                    continue
                sig = extract_group_signals(c, "stock")
                stock.append({"sig": sig, "label": lab, "weak": False, "src": "stock",
                              "meta": {"id": c.get("id"), "name": c.get("stock_name"),
                                       "date": c.get("date"), "trend": c.get("trend_prediction")}})
    return train, stock


# ----------------------------------------------------------------------------- 学习
def learn_reliability(train):
    """各引擎组经验可靠度：符号一致率（带拉普拉斯平滑）→ 相对机会的乘子。
    返回 {group: multiplier∈[0.3,1.8]}。另返回交互项 初传空 的可靠度修正。"""
    # 统计每个组：信号与标签同号次数、总次数
    agree = defaultdict(int)
    total = defaultdict(int)
    # 初传空交互：在 初传空 子集内 vs 全集，六亲/旺衰组一致率对比
    chu_total = defaultdict(int)
    chu_agree = defaultdict(int)
    for r in train:
        lab = r["label"]
        lab_s = 1 if lab > 0 else (-1 if lab < 0 else 0)
        chu = "_初传空" in r["sig"]
        for g, (s, conf) in r["sig"].items():
            if g.startswith("_"):
                continue
            if abs(s) < 1e-6 or lab_s == 0:
                continue
            s_s = 1 if s > 0 else -1
            total[g] += 1
            if s_s == lab_s:
                agree[g] += 1
            if chu:
                chu_total[g] += 1
                if s_s == lab_s:
                    chu_agree[g] += 1
    mult = {}
    for g in total:
        # 拉普拉斯：伪计数 1 同意 1 反对
        p = (agree[g] + 1) / (total[g] + 2)
        # 相对机会(0.5)的乘子：p>0.5 升，p<0.5 降
        m = p / 0.5
        mult[g] = round(max(0.3, min(1.8, m)), 3)
    # 初传空交互：若初传空子集内一致率明显低于全集 → 该组在初传空时应再降权
    interaction = {}
    for g in total:
        if chu_total[g] >= 5:
            p_all = (agree[g] + 1) / (total[g] + 2)
            p_chu = (chu_agree[g] + 1) / (chu_total[g] + 2)
            delta = round(p_chu - p_all, 3)  # <0 表示初传空时更不可靠
            interaction[g] = delta
    return mult, interaction


def fit(train, groups):
    """完整训练流程，返回 params dict。手写逻辑回归(含偏置列) + L2。"""
    X, y, sw = [], [], []
    for r in train:
        feat = [1.0]
        for g in groups:
            feat.append(r["sig"].get(g, (0.0, 0.0))[0])
        feat.append(1.0 if "_初传空" in r["sig"] else 0.0)
        X.append(feat)
        y.append(1.0 if r["label"] > 0 else 0.0)
        sw.append(0.4 if r["weak"] else 1.0)
    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)
    sw = np.array(sw, dtype=float)
    W = np.zeros(X.shape[1])
    lr, l2 = 0.1, 1e-3
    for _ in range(4000):
        z = 1.0 / (1.0 + np.exp(-(X @ W)))
        grad = (X.T @ ((z - y) * sw)) / (sw.sum() + 1e-9) + l2 * W
        W -= lr * grad
    w0 = float(W[0])
    weights = {g: round(float(W[i + 1]), 4) for i, g in enumerate(groups)}
    w_chu = round(float(W[-1]), 4)
    mult, interaction = learn_reliability(train)
    return {
        "groups": groups,
        "group_reliability": mult,
        "interaction_初传空": interaction,
        "prob_logistic": {"w0": round(w0, 4), "weights": weights, "w_chu": w_chu},
        "n_train": len(train),
        "n_A": sum(1 for r in train if r["src"] == "A"),
        "n_B": sum(1 for r in train if r["src"] == "B"),
    }


# ----------------------------------------------------------------------------- 应用
def load_params():
    if os.path.exists(PARAMS_PATH):
        return json.load(open(PARAMS_PATH, encoding="utf-8"))
    return None


def group_reliability_multiplier(params, group):
    """返回某组的可靠度乘子（默认 1.0）。供 judgment_fusion 调用。"""
    if not params:
        return 1.0
    return params.get("group_reliability", {}).get(group, 1.0)


def calibrate_probability(params, sig):
    """用学习到的逻辑回归把「各组合信号(原始极性)」映射为校准 P(涨)∈[0,1]。
    sig 为 extract_group_signals 的返回值。返回 (P涨, P跌)。"""
    if not params:
        return None, None
    lg = params["prob_logistic"]
    weights = lg["weights"]
    w0 = lg["w0"]
    w_chu = lg["w_chu"]
    logit = w0
    for g, w in weights.items():
        v = sig.get(g, (0.0, 0.0))[0]
        logit += w * v
    if "_初传空" in sig:
        logit += w_chu
    p_up = 1.0 / (1.0 + math.exp(-logit))
    return p_up, 1.0 - p_up


# ----------------------------------------------------------------------------- 验证
def _decide(p_up, s_before):
    """统一决策规则：P(涨)≥0.55→涨；≤0.45→跌；中间→平。s_before 用于未校准基线。"""
    if p_up is None:
        if s_before > 0.05:
            return 1
        if s_before < -0.05:
            return -1
        return 0
    if p_up >= 0.55:
        return 1
    if p_up <= 0.45:
        return -1
    return 0


def cv_evaluate(train, groups, n_folds=5):
    """5 折交叉验证（仅在干净标注的 Corpus A 上）：
    对比「未校准引擎求和」vs「可靠度加权+逻辑回归校准」的方向准确率与 Brier。"""
    A = [r for r in train if r["src"] == "A"]
    B = [r for r in train if r["src"] == "B"]
    rng = np.random.default_rng(42)
    order = rng.permutation(len(A))
    folds = np.array_split(order, n_folds)
    b_acc = b_brier = a_acc = a_brier = 0.0
    b_cnt = a_cnt = 0
    for fold in folds:
        held = [A[i] for i in fold]
        tr_A = [A[i] for i in range(len(A)) if i not in set(fold.tolist())]
        params = fit(tr_A + B, groups)
        for r in held:
            lab_s = 1 if r["label"] > 0 else (-1 if r["label"] < 0 else 0)
            s_before = sum(v for g, (v, _) in r["sig"].items() if not g.startswith("_"))
            p_up, _ = calibrate_probability(params, r["sig"])
            pred_b = _decide(None, s_before)
            pred_a = _decide(p_up, None)
            # 方向准确率仅统计涨跌样本
            if lab_s != 0:
                b_cnt += 1
                a_cnt += 1
                if pred_b == lab_s:
                    b_acc += 1
                if pred_a == lab_s:
                    a_acc += 1
            ind = 1.0 if r["label"] > 0 else 0.0
            p_b = max(0.0, min(1.0, 0.5 + s_before * 0.5))
            p_a = p_up if p_up is not None else p_b
            b_brier += (p_b - ind) ** 2
            a_brier += (p_a - ind) ** 2
    n = len(A)
    return {
        "n_A": n,
        "before_dir_acc": b_acc / b_cnt if b_cnt else None,
        "after_dir_acc": a_acc / a_cnt if a_cnt else None,
        "before_brier": b_brier / n,
        "after_brier": a_brier / n,
    }


def stock_appendix(stock):
    """股例辅助核对（非严谨回测）：展示天将信号 + 朴素预测 vs 实际。"""
    rows = []
    for r in stock:
        lab_s = 1 if r["label"] > 0 else (-1 if r["label"] < 0 else 0)
        s = sum(v for g, (v, _) in r["sig"].items() if not g.startswith("_"))
        pred = "涨" if s > 0.05 else ("跌" if s < -0.05 else "平/震荡")
        m = r.get("meta", {})
        rows.append({
            "id": m.get("id"), "name": m.get("name"), "date": m.get("date"),
            "tianjiang_sig": round(s, 3), "naive_pred": pred,
            "actual_trend": m.get("trend"), "label": r["label"],
        })
    return rows


# ----------------------------------------------------------------------------- CLI
def main():
    train, stock = load_labeled()
    all_groups = set()
    for r in train:
        for g in r["sig"]:
            if not g.startswith("_"):
                all_groups.add(g)
    groups = sorted(all_groups)
    print(f"训练样本: {len(train)} (A强标签 {sum(1 for r in train if r['src']=='A')} + "
          f"B弱标签 {sum(1 for r in train if r['src']=='B')}) | 股例辅助: {len(stock)}")
    print(f"参与校准引擎组: {groups}")

    params = fit(train, groups)
    params["_note"] = ("支柱③校准参数：group_reliability 替换 fuse() 的 group_mult 基线；"
                       "prob_logistic 把各组合信号映射为校准 P(涨)。仅覆盖训练集可观测组，"
                       "其余 12 组维持先验=1.0。")
    with open(PARAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
    print(f"\n已写出校准参数 -> {PARAMS_PATH}")
    print("group_reliability:", json.dumps(params["group_reliability"], ensure_ascii=False))
    print("interaction_初传空(部分):",
          {k: v for k, v in list(params["interaction_初传空"].items())[:6]})
    print("prob_logistic.w0:", params["prob_logistic"]["w0"],
          "| w_chu:", params["prob_logistic"]["w_chu"],
          "| weights:", params["prob_logistic"]["weights"])

    cv = cv_evaluate(train, groups, n_folds=5)
    print("\n=== 5折交叉验证（Corpus A 干净标注, 仅统计涨跌样本的方向准确率）===")
    print(f"  样本数(A): {cv['n_A']}")
    if cv["before_dir_acc"] is not None:
        print(f"  校准前(引擎求和): 方向准确率={cv['before_dir_acc']:.2%}  Brier={cv['before_brier']:.3f}")
    if cv["after_dir_acc"] is not None:
        print(f"  校准后(可靠度+逻辑回归): 方向准确率={cv['after_dir_acc']:.2%}  Brier={cv['after_brier']:.3f}")

    if stock:
        print("\n=== 股例辅助核对（非严谨回测，数据未就绪见说明）===")
        for row in stock_appendix(stock):
            print(f"  {row['id']} {row['name']} {row['date']}: 天将信号={row['tianjiang_sig']:+.2f} "
                  f"→朴素预判={row['naive_pred']} | 记录预判={row['actual_trend']} | 实际={row['label']}")


if __name__ == "__main__":
    main()
