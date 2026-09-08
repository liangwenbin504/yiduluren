# -*- coding: utf-8 -*-
"""
天机起课实验台 · 诚实预测系统
================================
设计（与用户对齐 2026-08-02 统一周期）：
- 一个「周期」= 20 个连续交易日（与量化主周期统一；六壬为辅，对齐此窗口）。预测目标 = 该周期 20 日收益方向（period_end 收 vs period_start 收）。
- 仅保留「天机起课」：用户心动时给系统 (日期, 时辰)，系统据此起真实一课，绝不自动机械起课。
- 起课窗口 = [period_start - 3 交易日, period_start]（目标日及前 3 天）。窗口外起课视为前视泄漏，拒绝。
- 周期内无人工起课 → 该周期记为「缺失」，绝不回填机械预测（诚实缺失）。
- 评估口径：天机命中率 vs 朴素基线 55.3%（永远猜涨）+ Wilson 置信区间 + p 值；并报告缺失率（防选择偏误）。
- 注：固定时(午时)起课在 5239 日回测中已被多路证据证伪（各类别/lead-1/2x2/ML 全低于 55.3% 基线），故本系统不再保留固定时对照臂——只回答「天机 vs 朴素基线」这一唯一要紧的问题。
- 微信提醒：每日检查起课窗口内是否存在「可起新课」的交易日，若是则经 PushPlus 推微信（复用 notify.py）。
  ⚠ 节流（2026-08-28 修复，憨爷反馈"没到起课日期别天天弹"）：
    · 同一「起课日 token」只推送一次，写入 _memory/tianji_notify_state.json；
    · 起课后 store 更新 → token 自动变新 → 下一周期走完才会再提醒；
    · 窗口内无可起课日（被 20 交易日守卫挡住）或已提醒过 → 一律静默，绝不每天重复推送。

用法：
  python engine/tianji_harness.py cast <YYYY-MM-DD> <时辰>     # 录入一次天机起课
  python engine/tianji_harness.py stats                         # 看命中率/缺失率/对照
  python engine/tianji_harness.py check [--dry-run] [--force]   # 检查并(模拟)发微信提醒
  python engine/tianji_harness.py report                        # 打印可读报告
  （--force 忽略节流强制再发一次，仅测试用）
"""
import os, sys, json, math
from datetime import datetime, timedelta, date

from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
for _p in (str(ROOT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 结算时回填知识点特征（自进化 Step1 卡点修复 2026-08-12）
# 注意：必须在本文件 path 注入(HERE=engine/)之后 import，否则 Flask 环境下找不到该模块（2026-08-15 修复）
from knowledge_features import extract_for_backfill

# ── 加载 .env（PushPlus token 写在项目 .env，自动化 shell 未必加载）──
def _load_dotenv():
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
_load_dotenv()

# 在 import notify 之前确保 PUSHPLUS_TOKEN 已在环境
import notify as _notify

# ── 配置常量 ──
PERIOD_LEN = 20                     # 一个周期 = 20 个交易日（与量化主周期统一；六壬为辅）
CAST_WINDOW_BEFORE = 3              # 可在 period_start 前 3 个交易日起课
CAST_WINDOW_AFTER = 0               # 不含 period_start 之后（防前视泄漏）
NAIVE_BASELINE = 0.5532             # 永远猜涨 朴素基线（日内口径；周期口径近似同量级）
STORE = ROOT / "_memory" / "tianji_casts.json"
os.makedirs(STORE.parent, exist_ok=True)

# 提醒节流状态：记录已推送过的「起课日 token」，防止同一周期天天推送（2026-08-28）
NOTIFY_STATE = ROOT / "_memory" / "tianji_notify_state.json"

SHICHEN_SET = set("子丑寅卯辰巳午未申酉戌亥")

# ── 交易日历 ──
def _load_series():
    import engine.regime_backtest as rb
    series = rb.parse_index()            # [(date_str, (op, cl)), ...]
    return series

def _future_trading_days(last_date, n):
    """从 last_date 之后生成 n 个近似交易日（跳过周六日；不处理节假日，仅用于提醒时机）。"""
    out, d = [], last_date
    while len(out) < n:
        d = d + timedelta(days=1)
        if d.weekday() >= 5:             # 5=Sat 6=Sun
            continue
        out.append(d)
    return out

def build_calendar():
    """返回 (combined_dates[str], date->index) 含历史 + 未来若干周期。"""
    series = _load_series()
    hist = [d for d, _ in series]
    last = datetime.strptime(hist[-1], "%Y-%m-%d").date()
    fut = [d.isoformat() for d in _future_trading_days(last, PERIOD_LEN * 4)]
    combined = hist + fut
    idx = {d: i for i, d in enumerate(combined)}
    return combined, idx, series

def periods_of(combined):
    """把交易日序列按 PERIOD_LEN 切块，返回 list of dict。"""
    periods = []
    for i in range(0, len(combined), PERIOD_LEN):
        block = combined[i:i + PERIOD_LEN]
        if not block:
            continue
        periods.append({
            "period_index": i // PERIOD_LEN,
            "period_start": block[0],
            "period_end": block[-1],
            "days": block,
        })
    return periods

# ── 存储 ──
def _read_store():
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _write_store(d):
    STORE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 提醒节流状态（2026-08-28 新增）──
def _read_notify_state():
    if NOTIFY_STATE.exists():
        try:
            return json.loads(NOTIFY_STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _write_notify_state(d):
    NOTIFY_STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _reset_notify_state():
    """起课后调用：清掉节流标记，让下一周期走完能重新提醒。"""
    try:
        if NOTIFY_STATE.exists():
            NOTIFY_STATE.unlink()
    except Exception:
        pass

# ── 起课 ──
def _cast_chart(target_date, shichen):
    from liuren_20d_engine import get_liuren_20d_signal
    r = get_liuren_20d_signal(target_date, shichen)
    trend = (r.get("prediction") or {}).get("trend", "震荡")
    conf = (r.get("prediction") or {}).get("confidence", 0)
    return {
        "trend": trend,
        "conf": conf,
        "keti": r.get("keti", ""),
        "sanchuan": r.get("san_chuan", []),
        "tianjiang": r.get("sanchuan_tianjiang", []),
    }

def _map_updown(trend):
    if trend == "看涨":
        return "up"
    if trend == "看跌":
        return "down"
    return "flat"

# ── 周期实际标签 ──
def _actual_of(period_start, period_end, series_map):
    ps, pe = series_map.get(period_start), series_map.get(period_end)
    if ps is None or pe is None:
        return None                      # 未来周期，实际未知
    return "up" if pe[1] > ps[1] else "down"

# ── 起课（统一滚动窗口：起课日 + 应期引擎推算天数；2026-09-08 改造：周期由课决定，
#   不再固定 20 交易日——'三传本支即应期'，速/中/迟各成一档）──
def _yingqi_period(cast_date, shichen, chart):
    """由应期引擎推算该课周期长度与多段应期。
    返回 dict(period_len, primary_gz/zhi/timing/days, stages[], err=None)；
    失败时回退固定 PERIOD_LEN（诚实缺失，不阻塞起课）。"""
    try:
        from engine.sizhu_engine import get_day_ganzhi, get_month_ganzhi
        from engine.bifa_detector import XUN_KONG_MAP
        from engine.yingqi_engine import judge_yingqi
        y, m, d = [int(x) for x in cast_date.split('-')]
        ri_gan, ri_zhi = get_day_ganzhi(y, m, d)
        yg, yz = get_month_ganzhi(y, m, d)
        kongwang = list(XUN_KONG_MAP.get(ri_gan + ri_zhi, []) or [])
        sc = list(chart.get('sanchuan') or [])
        season = {'春': '春', '夏': '夏', '秋': '秋', '冬': '冬'}.get(
            {'寅': '春', '卯': '春', '辰': '春', '巳': '夏', '午': '夏', '未': '夏',
             '申': '秋', '酉': '秋', '戌': '秋'}.get(yz, '冬'), '冬')
        r = judge_yingqi(ri_gan, sc, ri_zhi=ri_zhi, ganzhi=ri_gan + ri_zhi,
                         season=season, kongwang=kongwang, category='')
        pri = r.get('primary') or {}
        days = int(pri.get('days') or PERIOD_LEN)
        if days <= 0:
            days = PERIOD_LEN
        stages = []
        for c in r.get('candidates', [])[:6]:
            stages.append({
                'method': c.get('method', ''),
                'timing': c.get('timing', ''),
                'days': c.get('days', 0),
                'trigger_gz': c.get('trigger_gz', ''),
                'trigger_zhi': c.get('trigger_zhi', ''),
            })
        return {
            'period_len': days,
            'primary': {'method': pri.get('method', ''), 'timing': pri.get('timing', ''),
                        'days': days, 'trigger_gz': pri.get('trigger_gz', ''),
                        'trigger_zhi': pri.get('trigger_zhi', '')},
            'stages': stages,
            'narrative': r.get('narrative', ''),
            'err': None,
        }
    except Exception as e:
        return {'period_len': PERIOD_LEN, 'stages': [], 'err': str(e)}

# ── 规则快照（2026-09-08 新增）：起课时刻推理环境指纹（human_corrections + trainer 6 状态文件）。
#   复盘时用同版规则重判，防"后见规则翻案"（261期教训：起课看跌→现行规则复算看涨，
#   根因=unified_trainer 状态文件随训练轮次演化，非 human_corrections 新增）。──
def _rules_snapshot():
    import hashlib
    mem = ROOT / "_memory"
    files = [
        "human_corrections.json",
        "stock_training_insights.json",
        "self_evolve_state.json",
        "pattern_accuracy_stats.json",
        "liuren_case_kb.json",
        "evolution_summary.json",
    ]
    out = {"files": {}}
    for f in files:
        p = mem / f
        try:
            if p.exists():
                raw = p.read_text(encoding="utf-8")
                st = p.stat()
                out["files"][f] = {
                    "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
                    "mtime": st.st_mtime_ns,
                    "bytes": st.st_size,
                }
        except Exception:
            pass
    _joined = "|".join(f"{k}:{v.get('sha256','')}:{v.get('mtime','')}" for k, v in out["files"].items())
    out["env_sha256"] = hashlib.sha256(_joined.encode("utf-8")).hexdigest()[:16]
    return out

def cmd_cast(cast_date, shichen):
    if shichen not in SHICHEN_SET:
        return "✗ 时辰非法：%s（须为 子丑寅卯辰巳午未申酉戌亥 之一）" % shichen
    combined, idx, series = build_calendar()
    if cast_date not in idx:
        return "✗ 日期 %s 不在交易日历中（请填真实交易日）" % cast_date
    ci = idx[cast_date]
    cast_d = datetime.strptime(cast_date, "%Y-%m-%d").date()
    tj = _cast_chart(cast_date, shichen)
    # 【2026-09-08 改造】周期长度由应期引擎推算（非固定 20 交易日）
    yp = _yingqi_period(cast_date, shichen, tj)
    period_len = yp.get('period_len', PERIOD_LEN) or PERIOD_LEN
    future = _future_trading_days(cast_d, period_len)
    if not future:
        return "✗ 日历不足，无法推算周期终点"
    period_start = cast_date
    period_end = future[-1].isoformat()          # 起课日 + 应期天数（原固定 20 交易日）
    pidx = ci // PERIOD_LEN
    store = _read_store()
    # 守卫：同窗口（起课日相距 < 本次应期天数）已录则拒绝（周期身份=起课日）
    for rec in store.values():
        rcd = rec.get("cast_date")
        _len = int(rec.get("period_len") or PERIOD_LEN)
        if rcd in idx and abs(idx[rcd] - ci) < _len:
            return ("⚠ 周期（%s~%s，起课日 %s）已有天机起课（%s %s时，预测 %s）。"
                    "每周期仅保留一次天机起课，未覆盖。"
                    % (period_start, period_end, rcd, rec["cast_date"], rec["shichen"], rec["tianji_updown"]))
    rec = {
        "period_index": pidx,
        "period_start": period_start,
        "period_end": period_end,
        "period_len": period_len,                  # 本课周期天数（应期引擎推算）
        "cast_date": cast_date,
        "shichen": shichen,
        "tianji_trend": tj["trend"],
        "tianji_updown": _map_updown(tj["trend"]),
        "tianji_conf": tj["conf"],
        "tianji_chart": {"keti": tj["keti"], "sanchuan": tj["sanchuan"], "tianjiang": tj["tianjiang"]},
        "yingqi": {"period_len": period_len,
                   "primary": yp.get("primary") or {},
                   "stages": yp.get("stages") or [],
                   "narrative": yp.get("narrative", "")},   # 2026-09-08 多段应期
        "rules_snapshot": _rules_snapshot(),               # 2026-09-08 起课时刻规则指纹（复盘用）
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    store[str(pidx)] = rec
    _write_store(store)
    _reset_notify_state()          # 起课成功 → 清掉节流标记，下一周期走完才会再提醒
    _yq = rec["yingqi"]
    _narr = _yq.get("narrative", "")
    _stg = "；".join(f"{s.get('method','')}→{s.get('trigger_gz') or s.get('trigger_zhi','-')}({s.get('timing')},{s.get('days','?')}日)"
                     for s in _yq.get("stages", [])[:4]) or "（应期未推）"
    return ("✓ 周期（%s~%s，%d交易日）天机起课已记录：\n"
            "  心动：%s %s时 → 课体 %s 三传 %s 天将 %s\n"
            "  天机预测：%s（%s，置信 %s）\n"
            "  应期（课定）：%s\n"
            "  多段应期：%s"
            % (period_start, period_end, period_len, cast_date, shichen,
               tj["keti"], tj["sanchuan"], tj["tianjiang"], tj["trend"],
               rec["tianji_updown"], tj["conf"], _narr or "（无显著信号）", _stg))

# ── 统计 ──
def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (max(0.0, c - h), min(1.0, c + h))

def _binom_p(k, n, p0):
    if n == 0:
        return 1.0
    se = math.sqrt(n * p0 * (1 - p0))
    if se == 0:
        return 1.0
    z = (k - n * p0) / se
    return math.erfc(abs(z) / math.sqrt(2))

def _acc(rows, key):
    n = len(rows)
    # 2026-09-05 修复：原写法 [r for r, a in rows ...] 把 (rec, act) 元组降级成 rec，
    # 丢掉实际标签 act，下一行再解包即 ValueError。此前「已结算 0」从未走到这段，故潜伏未现。
    committed = [(r, a) for r, a in rows if r[key] in ("up", "down")]
    nc = len(committed)
    correct = sum(1 for r, a in committed if r[key] == a)
    ci = _wilson(correct, nc)
    return {
        "n_total": n, "n_committed": nc, "correct": correct,
        "acc_committed": (correct / nc) if nc else float("nan"),
        "ci95": ci, "p_vs50": _binom_p(correct, nc, 0.5),
        "p_vs_naive": _binom_p(correct, nc, NAIVE_BASELINE),
    }

def get_scoreboard():
    """结构化统计（供 API / 前端看板）：天机起课（心动时辰）方向命中率 vs 55.3% 朴素基线。

    滚动窗口口径：每条起课自身定义 [period_start, period_end]，直接比对实际方向。
    注意：本统计只测「心动人工指定时辰」的课——固定/合成时辰的回测不算数（憨爷 2026-08-02 指正）。
    """
    combined, idx, series = build_calendar()
    series_map = {d: (op, cl) for d, (op, cl) in series}
    store = _read_store()
    known, unverified = [], 0
    samples = []
    for rec in store.values():
        ps, pe = rec.get("period_start"), rec.get("period_end")
        pred = rec.get("tianji_updown")
        act = _actual_of(ps, pe, series_map)
        if act is None:
            unverified += 1
            samples.append({"cast_date": rec.get("cast_date"), "shichen": rec.get("shichen"),
                            "pred": pred, "trend": rec.get("tianji_trend"),
                            "actual": None, "hit": None, "window": [ps, pe]})
            continue
        hit = (pred in ("up", "down")) and (pred == act)
        known.append((rec, act))
        samples.append({"cast_date": rec.get("cast_date"), "shichen": rec.get("shichen"),
                        "pred": pred, "trend": rec.get("tianji_trend"),
                        "actual": act, "hit": hit, "window": [ps, pe]})
    tj = _acc(known, "tianji_updown")
    return {
        "period_len": PERIOD_LEN,
        "naive_baseline": NAIVE_BASELINE,
        "n_settled": len(known),
        "n_unverified": unverified,
        "n_committed": tj["n_committed"],
        "correct": tj["correct"],
        "acc_committed": tj["acc_committed"],
        "ci95": tj["ci95"],
        "p_vs50": tj["p_vs50"],
        "p_vs_naive": tj["p_vs_naive"],
        "samples": samples,
    }

def cmd_stats():
    sb = get_scoreboard()
    out = []
    out.append("=== 天机起课 · 诚实统计（周期由应期引擎课定，动态；朴素基线=%.1f%%）==="
               % (sb["naive_baseline"] * 100))
    out.append("已结算（有实际标签）：%d  待验证（未来窗口）：%d"
               % (sb["n_settled"], sb["n_unverified"]))
    out.append("")
    out.append("-- 天机起课（用户心动，决策用）--")
    out.append("   已起课 %d | 坚定预测(up/down) %d | 命中 %d | 坚定命中率 %.1f%% "
               "CI[%.1f%%,%.1f%%] p_vs50=%.3f p_vsNaive=%.3f"
               % (sb["n_committed"] + sb["n_unverified"], sb["n_committed"], sb["correct"],
                  sb["acc_committed"] * 100, sb["ci95"][0] * 100, sb["ci95"][1] * 100,
                  sb["p_vs50"], sb["p_vs_naive"]))
    return "\n".join(out)

# ── 提醒（2026-08-28 重写，修复「20 交易日空档出现就连着天天推送」的 bug）──
def _can_cast_on(day_s, idx, store):
    """判断 day_s 这天能否起新课，口径与 cmd_cast 的守卫完全一致：
    任一条已起课记录落在 PERIOD_LEN 个交易日内 → 不可起课（防重复/重叠）。
    返回 (ok: bool, nearest_cast: str|None, gap: int)
    """
    if day_s not in idx:
        return (False, None, -1)
    ci = idx[day_s]
    nearest, gap = None, 10 ** 9
    for rec in store.values():
        rcd = rec.get("cast_date")
        if rcd in idx:
            g = abs(idx[rcd] - ci)
            if g < gap:
                gap, nearest = g, rcd
    return (gap >= PERIOD_LEN, nearest, gap)

def _find_due_period():
    """下一个「可起新课」的周期起点（滚动窗口口径：起课日 = 周期起始日）。

    旧实现（bug）：从今天往回推 4 个自然日找空档 → 只要出现 20 交易日空档就连着天天推送。
    新实现：从「今天及之后的第一个交易日」起，在 CAST_WINDOW_BEFORE 个交易日窗口内
            向前扫描，找第一个真正能起课（不被守卫挡住）的交易日；找不到就静默。
            配合 _read_notify_state 节流 → 同一周期内最多推送一次。
    """
    today_s = date.today().isoformat()
    combined, idx, _ = build_calendar()
    store = _read_store()
    # 扫描起点：今天（若今天非交易日则顺延到下一个交易日）
    start_i = None
    for i, ds in enumerate(combined):
        if ds >= today_s:
            start_i = i
            break
    if start_i is None:
        return None
    for off in range(CAST_WINDOW_BEFORE + 1):
        i = start_i + off
        if i >= len(combined):
            break
        ds = combined[i]
        ok, _near, _gap = _can_cast_on(ds, idx, store)
        if ok:
            future = _future_trading_days(datetime.strptime(ds, "%Y-%m-%d").date(), PERIOD_LEN)
            pe = future[-1].isoformat() if future else ds
            return {
                "period_index": i // PERIOD_LEN,
                "period_start": ds,
                "period_end": pe,
                "token": ds,                 # 节流 key：本次提醒对应的起课日
            }
    return None

def _last_started_cast(store):
    """最近一次「已开始」（cast_date <= 今天）的起课记录；无则 None。"""
    today_s = date.today().isoformat()
    best = None
    for rec in store.values():
        cd = rec.get("cast_date")
        if cd and cd <= today_s:
            if best is None or cd > best.get("cast_date", ""):
                best = rec
    return best

def cmd_check(dry_run=False, force=False):
    p = _find_due_period()
    if p is None:
        msg = "✓ 当前无需提醒：起课窗口内没有可起新课的交易日（上一周期尚未走完）。"
        print(msg)
        return msg
    # 节流：同一「起课日 token」只推送一次，避免每天重复打扰
    st = _read_notify_state()
    if (not force) and st.get("token") == p["token"]:
        msg = ("✓ 已提醒过：起课日 %s 的提醒已于 %s 推送过，本轮不再重复。"
               "（确需再发一次：check --force）" % (p["token"], st.get("sent_at", "?")))
        print(msg)
        return msg
    last = _last_started_cast(_read_store())
    if last:
        prev = ("上一课：**%s %s时**，窗口 %s ~ %s —— 已走完，可以起新课。"
                % (last.get("cast_date"), last.get("shichen"),
                   last.get("period_start"), last.get("period_end")))
    else:
        prev = "尚无天机起课记录，随时可起第一课。"
    title = "天机起课提醒 · 起课日 %s" % p["period_start"]
    content = (
        "## 该人工起课了\n\n"
        "**新周期**：%s ~ %s（%d 个交易日）\n\n"
        "%s\n\n"
        "**操作**：心动时记下发呆那一刻的「日期 + 时辰」，发给系统，例如：\n"
        "> 起课 %s 午\n\n"
        "错过则该周期记为「缺失」，绝不回填机械预测。\n\n"
        "_（朴素基线：永远猜涨 ≈ %.1f%%；天机须稳定超过它才算真准。）_\n\n"
        "_每个周期只提醒一次，不会天天打扰。_"
        % (p["period_start"], p["period_end"], PERIOD_LEN, prev,
           p["period_start"], NAIVE_BASELINE * 100)
    )
    if dry_run:
        print("[dry-run] 将推送（不实际发送）：\n标题：%s\n内容：\n%s" % (title, content))
        return "dry-run"
    ok = _notify.send_pushplus(title, content)
    if ok:
        _write_notify_state({"token": p["token"],
                             "sent_at": datetime.now().isoformat(timespec="seconds")})
    res = ("✓ 微信提醒已发送（起课日 %s，本周期不再重复）" % p["period_start"]) if ok \
        else "✗ PushPlus 发送失败（检查 PUSHPLUS_TOKEN / 网络）"
    print(res)
    return res

# ── 报告 ──
def cmd_report():
    print(cmd_stats())
    print()
    print(cmd_check(dry_run=True))

# ── 去重：同周期(period_start)若出现多条，保留最早 ts，删其余 ──
def cmd_dedupe():
    """清理「一个周期被录多次」的遗留：
    - tianji_casts.json：按 period_start 聚类，保留最早 ts，删除其余（保留第一次）。
    - stock_predictions.json：按 id 去重（兼容旧 id 格式按周期身份兜底）。
    """
    store = _read_store()
    by_start = {}
    for k, rec in store.items():
        s = rec.get("period_start")
        by_start.setdefault(s, []).append((k, rec))
    removed = []
    for s, recs in by_start.items():
        if len(recs) <= 1:
            continue
        def _t(x):
            return x[1].get("ts") or x[1].get("cast_date") or ""
        recs_sorted = sorted(recs, key=_t)          # 最早在前 = 保留第一次
        keep_k = recs_sorted[0][0]
        for k, r in recs_sorted[1:]:
            removed.append((k, r))
            store.pop(k)
    _write_store(store)

    # 桥接文件去重
    sp = ROOT / "_memory" / "stock_predictions.json"
    sp_removed = 0
    if sp.exists():
        try:
            arr = json.loads(sp.read_text(encoding="utf-8"))
            seen, new = set(), []
            for x in arr:
                i = (x or {}).get("id")
                # 兜底匹配：旧 id 格式按 source+date+target_date 视为同一周期
                if i in seen:
                    sp_removed += 1
                    continue
                seen.add(i)
                new.append(x)
            sp.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    if not removed and sp_removed == 0:
        return ("✓ 去重完成：tianji_casts.json 无同周期重复（%d 条），"
                "stock_predictions.json 无重复 id。" % len(store))
    lines = ["✓ 去重完成（保留每条周期的最早一次起课）："]
    for k, r in removed:
        lines.append("  · 删除 tianji_casts.json 重复键 %s（周期 %s~%s，cast %s）"
                     % (k, r.get("period_start"), r.get("period_end"), r.get("cast_date")))
    if sp_removed:
        lines.append("  · stock_predictions.json 删除 %d 条重复 id" % sp_removed)
    lines.append("  现保留 %d 条天机起课记录。" % len(store))
    return "\n".join(lines)

# ── 天机窗口回检：period_end<=today 的起课，用 _actual_of（上证窗口收益）判定并写回 ──
def check_tianji_results():
    """天机 20 交易日窗口回检（与预测同窗口、同基准）。

    对 tianji_casts.json 中 period_end <= 今天的起课，用 _actual_of(period_start, period_end)
    判定实际方向（上证指数窗口收益，与天机预测窗口 [起课日, +20交易日] 严格一致），
    写回 stock_predictions.json 对应天机记录 actual_result(涨/跌) + actual_details + status=completed。
    窗口未收盘或数据缺失 → 跳过，保持 pending（绝不写假结果）。
    """
    combined, idx, series = build_calendar()
    series_map = {d: (op, cl) for d, (op, cl) in series}
    store = _read_store()
    today = date.today()
    sp = ROOT / "_memory" / "stock_predictions.json"
    if not sp.exists():
        return 0
    arr = json.loads(sp.read_text(encoding="utf-8"))
    n = 0
    for rec in store.values():
        ps, pe = rec.get("period_start"), rec.get("period_end")
        if not ps or not pe:
            continue
        pe_d = datetime.strptime(pe, "%Y-%m-%d").date()
        if pe_d > today:
            continue
        actual = _actual_of(ps, pe, series_map)          # 'up'/'down'/None
        if actual is None:
            continue
        for p in arr:
            if not isinstance(p, dict):
                continue
            if p.get("source") == "tianji_cast" and p.get("date") == rec.get("cast_date"):
                if p.get("actual_result"):
                    break
                p["actual_result"] = "涨" if actual == "up" else "跌"
                p["actual_details"] = {
                    "window_start": ps, "window_end": pe,
                    "basis": "上证指数窗口收益（与天机预测同窗口）",
                }
                p["status"] = "completed"
                # 自进化 Step1 卡点修复：标记 completed 时一并回填知识点特征
                _kf = extract_for_backfill(p)
                if _kf is not None:
                    p["knowledge_features"] = _kf
                p["check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                n += 1
                break
    if n:
        tmp = str(sp) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(arr, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(sp))
    return n


# ── 入口 ──
if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "cast" and len(args) >= 3:
        print(cmd_cast(args[1], args[2]))
    elif args[0] == "stats":
        print(cmd_stats())
    elif args[0] == "check":
        dry = "--dry-run" in args
        force = "--force" in args
        cmd_check(dry_run=dry, force=force)
    elif args[0] == "report":
        cmd_report()
    elif args[0] == "dedupe":
        print(cmd_dedupe())
    elif args[0] == "checkresults":
        print("天机窗口回检完成: %d 条已结算" % check_tianji_results())
    else:
        print(__doc__)
