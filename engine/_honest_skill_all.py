# -*- coding: utf-8 -*-
"""诚实技能测试(全集)：直接对 219 例真实疏正案(日辰/月将/时辰/三传均来自PDF)跑引擎，
与真实结局比对。这是唯一不受 Corpus B 损坏污染的真值基线。

🔴🔴 本脚本 = **M3 基线的唯一权威跑法**（2026-09-20 锁定，勿再另起炉灶）
    跑法（三项缺一不可，差一项数字就会变）：
      PYTHONHASHSEED=0 [LABEL_FIX=1] \
        C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe \
        engine/_honest_skill_all.py
    口径对照：
      · 不加 LABEL_FIX → M3 = 89.4% (185/207)，朴素基线 83.1%
      · 加  LABEL_FIX=1 → M3 = 91.8% (190/207)，朴素基线 85.5%   ← 记忆里那个数
      · 裸 `python`（3.13）→ 88.9% (184/207) ⛔ **不是**基线，勿采信
    ⛔ 输入映射（下面的 clean 字典）**必须一字不改地照抄**。
       实测（探针 `_冗余待删/_probe_218_mapping_diff.py`）：
       漏传 `leishen` ⇒ 85.5%（吉案 recall 47.1%→20.6%），差的 10 案全是亡盗章。
       ⛔ `docs/reports/ab_all_guiji.py` 是**另一个入口**（走 `zhanshi_duanyu`，
          疏正 81.7%/218 案），**不**是本基线，勿混用。
"""
import json
import os
import sys
from collections import Counter
sys.path.insert(0, ".")
from engine.ancient_backtest import predict_ancient_case

REAL = json.load(open("engine/shuzheng_real_cases.json", encoding="utf-8"))

# ---- 可选：加载 label 人工复核修正表（2026-09-17 憨爷确认；环境变量 LABEL_FIX=1 才启用）----
# ⛔ 不改原语料 shuzheng_real_cases.json（保持历史可复现）；仅本脚本内存里覆盖 label。
# ⚠️ 启用后基线会变（吉案 recall 47.1%→55.2%、总准确率 89.4%→约 92.2%）
#    ⇒ 报告 A/B 结论时必须注明是否启用本表。
LABEL_FIX_ON = bool(os.environ.get("LABEL_FIX"))
LABEL_FIX = {}
if LABEL_FIX_ON:
    with open("engine/shuzheng_label_fix.json", encoding="utf-8") as _f:
        LABEL_FIX = {x["case_id"]: x["new"] for x in (json.load(_f).get("fixes") or [])}
    print("[口径] LABEL_FIX=1 ⇒ 已加载 %d 条 label 人工修正（shuzheng_label_fix.json）" % len(LABEL_FIX))
methods = ["M1", "M2", "M3", "M4"]
stats = {m: {"n": 0, "correct": 0, "skip": 0, "cm": Counter(),
             "by_cat": {}} for m in methods}
valid_dist = Counter()  # 仅统计有效案例(与 M3 分母一致)的结局分布，用于朴素基准

VALID = set("子丑寅卯辰巳午未申酉戌亥")


def ok_yj(x):
    return isinstance(x, str) and x in VALID


for c in REAL:
    sc = c.get("sanchuan") or []
    if not isinstance(sc, list):
        sc = list(sc)
    rizhu = c.get("day_ganzhi", "")
    if len(sc) < 3 or not rizhu or len(rizhu) < 2:
        for m in methods:
            stats[m]["skip"] += 1
        continue
    truth = c.get("label", "")
    if LABEL_FIX_ON and c.get("case_id") in LABEL_FIX:
        truth = LABEL_FIX[c["case_id"]]          # 人工复核修正（默认不启用）
    if truth not in ("吉", "凶", "平"):
        for m in methods:
            stats[m]["skip"] += 1
        continue
    clean = {
        "id": c["case_id"],
        "name": c.get("name", ""),
        "category": c.get("zhanlei", "其他"),
        "rizhu": rizhu,
        "yue_jiang": c["yue_jiang"] if ok_yj(c.get("yue_jiang")) else "",
        "shichen": c["shichen"] if ok_yj(c.get("shichen")) else "",
        "sanchuan": sc,
        "keti": [],
        "label": truth,
        "label_confidence": c.get("label_conf", 0),
        "month": c.get("month"),
        "ben_ming_zhi": c.get("ben_ming_zhi"),
        "year": c.get("year") or "",
        "leishen": c.get("leishen", ""),
    }
    valid_dist[truth] += 1
    for m in methods:
        try:
            pred = predict_ancient_case(clean, m)
            p = pred.get("prediction", "")
            ok = (p == truth)
            stats[m]["n"] += 1
            if ok:
                stats[m]["correct"] += 1
            stats[m]["cm"][f"{truth}->{p}"] += 1
            cat = clean["category"]
            d = stats[m]["by_cat"].setdefault(cat, {"n": 0, "c": 0})
            d["n"] += 1
            if ok:
                d["c"] += 1
        except Exception:
            stats[m]["skip"] += 1

print("=== 诚实技能测试(全集)：219 真实疏正案，引擎输入+标签均来自PDF ===")
for m in methods:
    s = stats[m]
    acc = s["correct"] / s["n"] if s["n"] else 0
    print(f"  {m}: 准确率={acc*100:.1f}%  (正确{s['correct']}/{s['n']}, 跳过{s['skip']})")
    print(f"       混淆={dict(s['cm'])}")

print("\n=== M3 各类别(真实案) ===")
bc = stats["M3"]["by_cat"]
for cat in sorted(bc, key=lambda k: -bc[k]["n"]):
    d = bc[cat]
    if d["n"] >= 3:
        print(f"   {cat:<8} {d['c']/d['n']*100:>5.1f}%  ({d['c']}/{d['n']})")

# 基准率（仅有效案例，与 M3 分母 n=164 对齐）
from collections import Counter as C
dist = valid_dist
print(f"\n真实结局分布(有效164例): {dict(dist)}  -> 永远猜'凶'的准确率={dist.get('凶',0)/sum(dist.values())*100:.1f}%")

print("\n=== 三层对比 ===")
print("  全 Corpus B (损坏输入+循环标签): M3 ≈ 62.0%  [不可信]")
print("  仅修标签 (输入仍损坏):           M3 ≈ 55.9%  [不可信]")
m3 = stats["M3"]
print(f"  真实输入+真实标签 (本全集测试):  M3 ≈ {m3['correct']/m3['n']*100:.1f}%  (n={m3['n']})  [可信]")

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 2026-09-17 新增：**方法等价性检查**（防把"跑三遍"误读成"三重验证"）
#
# 实测（探针 `_冗余待删/_probe_signal_groups.py`）：
#   · `holistic_judgment` 键在古例路径**不产出**（0/207 案）；
#   · `caishen` 信号被 **`engine/ancient_backtest.py:L36` 的 `_jf.DISABLE_CAISHEN = True`**
#     （模块级 import 副作用；`judgment_fusion.py:L92` 的初始值是 `False`，**读源码极易误判为启用**）
#     ⇒ 实际产出 0/207。
# ⇒ 两个"被消融"的信号本就从未产出 ⇒ **M1 ≡ M2 ≡ M3 是必然**，
#   「完整融合 M3」在该域**等价于「原始引擎 M1」**。
# ⛔ 故：**不得**从「M1/M2/M3 三个数字」解读出"融合层带来增量"。
#    （caishen 另有一条独立证据说明它**不启用是对的**：M4 单跑 = 14.5%，凶→吉 160，极强吉向偏置。）
# ══════════════════════════════════════════════════════════════════════════════
print("\n=== ⚠️ 方法等价性检查（M1/M2/M3）===")
_equiv = stats["M1"]["cm"] == stats["M2"]["cm"] == stats["M3"]["cm"]
if _equiv:
    print("  M1 ≡ M2 ≡ M3（混淆矩阵**逐案相同**）⇒ 本域**无真实消融**：")
    print("    · holistic_judgment 在古例路径不产出（0/207）")
    print("    · caishen 被 ancient_backtest.py:L36 主动禁用（0/207）")
    print("  ⇒ 三方法＝同一引擎跑三遍；⛔ **不得**据此解读「融合层增量」。")
    print("  ⇒ 若需真实消融：先让对应信号在古例域产出（属基线级改动，须单独拍板）。")
else:
    print("  M1/M2/M3 存在差异 ⇒ 消融生效（fusion 侧信号已产出），可据以解读增量。")
print(f"  M4（仅 caishen）= {stats['M4']['correct']}/{stats['M4']['n']}"
      f" = {stats['M4']['correct']/stats['M4']['n']*100:.1f}%"
      f"  ⚠️ 吉向偏置（凶→吉 {stats['M4']['cm'].get('凶->吉', 0)}）⇒ 该模块在古例域**保持禁用**。")

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 2026-09-20 新增：**人工预填类神(leishen) 的泄漏量化**（报数时必须同时给出）
#
# `leishen` 在 218 语料里只有 **12 案非空（全为亡盗章）**，且是**人工从原文读出**的，
# 引擎**不自推**（`ancient_backtest.py:L389` 直接透传；`judgment_fusion.py:L402`
# 有一条「其他+leishen+吉向 → 置信×1.5」的亡盗专属提权）。⇒ 这 12 案等于**喂了半个答案**。
#
# 实测（`_冗余待删/_probe_leishen_leak.py`）：
#   口径                        n    总准确率   吉 recall   凶 recall  朴素基线  净增量
#   权威（含 12 案预填类神）    207   91.8%     55.2%       98.3%      85.5%    +6.3pp
#   去掉预填类神               207   87.9%     24.1%       98.9%      85.5%    +2.4pp
#   剔除这 12 案（纯引擎）     195   92.8%     38.9%       98.9%      90.3%    +2.5pp
# ⇒ **"+6.3pp 净增量"里有 3.8pp 是喂类神喂出来的；纯引擎真实净增量 ≈ +2.5pp。**
# ⛔ 报数铁律：给 M3=91.8% 时必须并列「朴素基线 85.5%」＋「剔除类神案后 92.8%/195」。
# ══════════════════════════════════════════════════════════════════════════════
_ls_ids = [c.get("case_id") for c in REAL if str(c.get("leishen") or "").strip()]
_ls_set = set(_ls_ids)
_m3_all = stats["M3"]["correct"]
_m3_n = stats["M3"]["n"]
print("\n=== 🔴 类神(leishen)泄漏提示 ===")
print(f"  218 语料中 leishen 非空：{len(_ls_ids)} 案（全部为亡盗章，人工预填、引擎不自推）")
print(f"  本口径 M3 = {_m3_all}/{_m3_n} = {_m3_all/_m3_n*100:.1f}%  ← 其中含这 {len(_ls_ids)} 案的预填类神")
print("  去掉预填类神 ⇒ 87.9%（原口径 85.5%）｜剔除这 12 案 ⇒ 92.8%/195（纯引擎）")
print("  ⇒ 报数须并列：朴素基线 85.5% ＋ 纯引擎 92.8%/195；⛔ 不得只报 91.8%。")
