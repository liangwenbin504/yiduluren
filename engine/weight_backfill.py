#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine/weight_backfill.py — 结果反哺权重（自进化 Step 1，小、可逆）
==============================================================

从已完成（status=='completed' 且 actual_result 非空）的六壬预测中，按维度重算各特征
的「方向对齐率」，写出「学得权重」回 _memory/stock_training_insights.json 的 factor_impact；
带时间戳快照（可回滚）；只回灌、不删旧值；小样本安全 no-op。

维度（与 unified_trainer.UnifiedTrainer.get_knowledge_feature_impact 消费的 key 对齐）：
  1) 四组关系        -> rel_{name}_{rel_name}           （引擎原生消费，无需改动）
  2) 用神旺衰        -> yong_wangshuai_{wgrade}          （引擎原生消费，无需改动）
  3) 空亡            -> kongwang                         （需引擎增量消费，见 unified_trainer hook）
  4) 刚柔净额        -> gangrou                          （需引擎增量消费）
  5) 毕法赋·交车     -> bifa_jiaoche                     （需引擎增量消费）
  6) 三传·进茹/退茹  -> chuanbian                        （需引擎增量消费）

安全策略：
  * 默认 dry-run（不写盘）；显式 --apply 才写。
  * 每个 key 仅当「方向样本数」>= min_samples（默认 5）才写；否则保留原值（no-op）。
  * 学得权重 = 领域基准 signed × blend，blend ∈ [0,1]，永不翻转符号（最保守）。
  * 写盘前对 stock_training_insights.json 做时间戳快照到 _memory/backfill_snapshots/。
  * 每次运行写 _memory/weight_backfill_log.json，记录变更与统计，便于审计与回滚。

CLI:
  python engine/weight_backfill.py                                   # 干跑（只报告，不写）
  python engine/weight_backfill.py --apply                           # 实际写回
  python engine/weight_backfill.py --apply --min-samples 8           # 提高样本下限
  python engine/weight_backfill.py --rollback _memory/backfill_snapshots/stock_training_insights_2026....json
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

BASE = Path(__file__).resolve().parent.parent
MEMORY = BASE / "_memory"
PRED_FILE = MEMORY / "stock_predictions.json"
INSIGHTS_FILE = MEMORY / "stock_training_insights.json"
SNAP_DIR = MEMORY / "backfill_snapshots"
LOG_FILE = MEMORY / "weight_backfill_log.json"

MIN_SAMPLES_DEFAULT = 5
SNAPSHOT_KEEP = 10

# 用神旺衰 基准方向与幅度（与领域默认 signed 同向；休为中性=0）
WANGSHUAI_BASE = {
    "旺": 0.5, "相": 0.3, "休": 0.0, "囚": -0.3, "死": -0.5,
}
# 单单位基准幅度（空亡/刚柔/毕法/传变 的「每单位」权重幅度基准）
UNIT_BASE = 0.2


def _now() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _log(msg: str):
    print(f"[weight_backfill] {msg}", flush=True)


def normalize_direction(label) -> int:
    """把趋势标签归一为方向: +1 涨 / -1 跌 / 0 平震荡（无法判断方向）。"""
    if not label:
        return 0
    s = str(label)
    if "涨" in s:
        return 1
    if "跌" in s:
        return -1
    return 0


def load_predictions() -> List[dict]:
    if not PRED_FILE.exists():
        return []
    try:
        with open(PRED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        _log(f"读取预测库失败: {e}")
        return []
    return data if isinstance(data, list) else []


def get_eligible_predictions() -> List[dict]:
    """已完成对照且带有知识点特征的预测（即可以拿来反哺的样本）。"""
    out = []
    for p in load_predictions():
        if p.get("status") == "completed" and p.get("actual_result") and p.get("knowledge_features"):
            out.append(p)
    return out


def load_insights() -> dict:
    if not INSIGHTS_FILE.exists():
        return {}
    try:
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _log(f"读取洞察库失败: {e}")
        return {}


def snapshot_insights() -> Optional[str]:
    """写盘前快照，返回快照路径；失败返回 None。"""
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now()
    dst = SNAP_DIR / f"stock_training_insights_{ts}.json"
    try:
        shutil.copy2(INSIGHTS_FILE, dst)
    except Exception as e:
        _log(f"快照失败: {e}")
        return None
    # 仅保留最近 SNAPSHOT_KEEP 个快照
    try:
        snaps = sorted(SNAP_DIR.glob("stock_training_insights_*.json"),
                       key=lambda p: p.stat().st_mtime)
        while len(snaps) > SNAPSHOT_KEEP:
            snaps.pop(0).unlink()
    except Exception:
        pass
    return str(dst)


def _extract_dimensions(kf: dict, actual_dir: int) -> List[Tuple[str, float, int]]:
    """
    从一条预测的 knowledge_features 抽取各维度的 (key, 基准signed, 内在方向)。
    内在方向 = 该特征「指向」的方向（+1 看涨 / -1 看跌）。
    仅返回「有信号」的维度；无信号（如 比和、休）不参与该维度学习。
    actual_dir==0（平/震荡）无法判断方向，调用方已跳过。
    """
    out: List[Tuple[str, float, int]] = []
    if not isinstance(kf, dict) or actual_dir == 0:
        return out

    # 1) 四组关系
    for name, info in kf.get("relations", {}).items():
        signed = info.get("signed", 0.0)
        if not signed:
            continue
        rel_name = info.get("relation", "")
        key = f"rel_{name}_{rel_name}"
        out.append((key, signed, 1 if signed > 0 else -1))

    # 2) 用神旺衰
    liqi = kf.get("liqi", {}) or {}
    wgrade = liqi.get("用神旺衰", "")
    if wgrade in WANGSHUAI_BASE:
        base = WANGSHUAI_BASE[wgrade]
        if base != 0.0:
            out.append((f"yong_wangshuai_{wgrade}", base, 1 if base > 0 else -1))

    # 3) 空亡（偏空）
    kc = liqi.get("空亡数", 0) or 0
    if kc:
        out.append(("kongwang", -UNIT_BASE, -1))

    # 4) 刚柔净额（柔神主导=看涨，刚煞主导=看跌）
    lx = kf.get("leixiang", {}) or {}
    gang_net = lx.get("刚柔净额", 0) or 0
    if gang_net:
        base = UNIT_BASE * (1 if gang_net > 0 else -1)
        out.append(("gangrou", base, 1 if gang_net > 0 else -1))

    # 5) 毕法赋·交车（合多=看涨，克/刑/冲多=看跌）
    bf = kf.get("bifa", {}) or {}
    jiaoche = bf.get("交车", []) or []
    if jiaoche:
        he = sum(1 for x in jiaoche if "合" in x)
        ke = sum(1 for x in jiaoche if ("克" in x or "刑" in x or "冲" in x))
        net = he - ke
        if net:
            base = UNIT_BASE * (1 if net > 0 else -1)
            out.append(("bifa_jiaoche", base, 1 if net > 0 else -1))

    # 6) 三传·进茹(气进)=看涨 / 退茹(气退)=看跌
    sc = kf.get("sanchuan", {}) or {}
    cb = sc.get("传变", "")
    if cb == "进茹(气进)":
        out.append(("chuanbian", UNIT_BASE, 1))
    elif cb == "退茹(气退)":
        out.append(("chuanbian", -UNIT_BASE, -1))

    return out


def accumulate(preds: List[dict]) -> Dict[str, dict]:
    """
    累加各维度方向对齐信息。
    返回 {key: {"sum_agree": int, "n_dir": int, "base": float, "intrinsic_dir": int}}
    sum_agree: 每样本 +1 表示「特征方向 == 实际方向」（对齐），-1 表示反向。
    """
    acc: Dict[str, dict] = {}
    for p in preds:
        actual_dir = normalize_direction(p.get("actual_result"))
        if actual_dir == 0:
            continue
        kf = p.get("knowledge_features") or {}
        for key, base, intrinsic_dir in _extract_dimensions(kf, actual_dir):
            a = acc.setdefault(key, {"sum_agree": 0, "n_dir": 0,
                                     "base": base, "intrinsic_dir": intrinsic_dir})
            a["sum_agree"] += 1 if intrinsic_dir == actual_dir else -1
            a["n_dir"] += 1
    return acc


def _round2(x: float) -> float:
    return round(x, 3)


def compute_learned_weights(acc: Dict[str, dict], min_samples: int) -> List[dict]:
    """
    把累加结果转成变更列表。
    alignment = sum_agree / n_dir ∈ [-1, 1]
    blend     = 0.5 + 0.5*alignment ∈ [0, 1]
    学得权重   = base * blend  （符号与 base 一致，永不翻转）
    仅保留 n_dir >= min_samples 且 |learned| >= 0.05 的变更。
    """
    changes = []
    for key, a in acc.items():
        n = a["n_dir"]
        if n < min_samples:
            continue
        alignment = a["sum_agree"] / n
        blend = 0.5 + 0.5 * alignment
        learned = _round2(a["base"] * blend)
        if abs(learned) < 0.05:
            continue
        changes.append({
            "key": key,
            "n_dir": n,
            "sum_agree": a["sum_agree"],
            "alignment": _round2(alignment),
            "base": _round2(a["base"]),
            "learned": learned,
        })
    return changes


def run_weight_backfill(apply: bool = False,
                        min_samples: int = MIN_SAMPLES_DEFAULT) -> dict:
    """
    主入口。apply=False 时只报告不写盘。返回报告 dict（供 scheduler 打印/审计）。
    """
    preds = get_eligible_predictions()
    acc = accumulate(preds)
    changes = compute_learned_weights(acc, min_samples)

    insights = load_insights()
    old_fi = insights.get("factor_impact") or {}
    if not isinstance(old_fi, dict):
        old_fi = {}
    old_fi = dict(old_fi)

    report = {
        "time": datetime.now().isoformat(),
        "applied": bool(apply),
        "min_samples": min_samples,
        "n_eligible_predictions": len(preds),
        "n_dimension_keys_seen": len(acc),
        "n_changes": 0,
        "changes": [],
        "snapshot": None,
        "note": "",
    }

    if not changes:
        report["note"] = ("无足够方向样本（每个维度方向样本需 >= %d），本次为安全 no-op，"
                          "不改动 factor_impact。" % min_samples)
        _log(report["note"])
        _save_log(report)
        return report

    # 组装变更（对比旧值）
    new_fi = dict(old_fi)
    for c in changes:
        key = c["key"]
        old_val = old_fi.get(key)
        c["old"] = _round2(old_val) if isinstance(old_val, (int, float)) else None
        new_fi[key] = c["learned"]
        report["changes"].append(c)
    report["n_changes"] = len(report["changes"])

    if not apply:
        report["note"] = ("dry-run：将写入 %d 个学得权重（未落盘）。用 --apply 实际写回。"
                           % report["n_changes"])
        _log(report["note"])
        for c in report["changes"]:
            _log(f"  {c['key']}: old={c['old']} -> learned={c['learned']} "
                 f"(n={c['n_dir']}, align={c['alignment']:+.2f})")
        _save_log(report)
        return report

    # 实际写回：先快照
    snap = snapshot_insights()
    report["snapshot"] = snap
    insights["factor_impact"] = new_fi
    insights["_backfilled_at"] = datetime.now().isoformat()
    try:
        with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
        report["note"] = f"已写回 {report['n_changes']} 个学得权重。快照: {snap}"
        _log(report["note"])
        for c in report["changes"]:
            _log(f"  {c['key']}: old={c['old']} -> learned={c['learned']} "
                 f"(n={c['n_dir']}, align={c['alignment']:+.2f})")
    except Exception as e:
        report["note"] = f"写回失败: {e}"
        _log(report["note"])
    _save_log(report)
    return report


def _save_log(report: dict):
    try:
        history = []
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        if not isinstance(history, list):
            history = []
        history.append(report)
        if len(history) > 100:
            history = history[-100:]
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log(f"写日志失败: {e}")


def rollback(snapshot_path: str) -> dict:
    src = Path(snapshot_path)
    if not src.exists():
        return {"ok": False, "error": f"快照不存在: {snapshot_path}"}
    try:
        shutil.copy2(src, INSIGHTS_FILE)
        return {"ok": True, "restored": str(INSIGHTS_FILE), "from": str(src)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="结果反哺权重（自进化 Step 1）")
    ap.add_argument("--apply", action="store_true",
                    help="实际写回 factor_impact（默认 dry-run）")
    ap.add_argument("--min-samples", type=int, default=MIN_SAMPLES_DEFAULT,
                    help="每个维度方向样本下限（默认 5）")
    ap.add_argument("--rollback", metavar="SNAPSHOT",
                    help="从指定快照回滚 factor_impact")
    args = ap.parse_args()

    if args.rollback:
        r = rollback(args.rollback)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    report = run_weight_backfill(apply=args.apply, min_samples=args.min_samples)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
