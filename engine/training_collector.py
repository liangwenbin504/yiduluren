"""
训练案例自动收集器

功能：
1. 从 stock_predictions.json 读取已完成对照分析的预测记录
2. 自动转换为 stock_training_cases.json 格式的训练案例
3. 追加到训练案例库，供下次训练使用
4. 批量回溯采集所有历史记录
5. 网络搜索相似历史案例增强训练数据
6. 数据增强（生成变体）
7. 训练集统计与就绪度评估

调用时机：
  对照分析完成后（auto_review.py run_review() 成功后调用）
"""
import json, os, re, random
from datetime import datetime, timezone, timedelta
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREDICTIONS_FILE = os.path.join(BASE, "_memory", "stock_predictions.json")
TRAINING_FILE = os.path.join(BASE, "data", "stock_training_cases.json")
AUGMENTED_FILE = os.path.join(BASE, "data", "stock_training_augmented.json")

# 增强配置：从N个正确案例生成变体的倍数
AUGMENT_MULTIPLIER = 3
MIN_CASES_FOR_AUGMENT = 5
MIN_CASES_FOR_TRAINING = 10
TRAINING_READY_RATIO = 0.6  # 训练集正确率超过60%视为可训练


def get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)


def _next_case_id(cases) -> str:
    """生成下一个案例ID (CASE-STOCK-026)

    🔴 只认 1~3 位纯数字序号（本命名空间的旧格式）。
    旧实现用 `re.search(r"CASE-STOCK-(\\d+)")` 对全库求 max，被日期型 id
    （人工校正案例 `CASE-STOCK-20260730-YISI`）顶到 20260730 ⇒
    之后一路生成 20260731…20260738，`:03d` 补零形同虚设（命名空间串味）。
    """
    max_num = 0
    for c in cases:
        cid = c.get("id", "")
        m = re.fullmatch(r"CASE-STOCK-(\d{1,3})", cid)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return f"CASE-STOCK-{max_num + 1:03d}"


def _parse_target(target: str) -> tuple:
    """解析 '上证指数(000001)' → ('000001', '上证指数')"""
    if not target:
        return ("000001", "上证指数")
    m = re.match(r"(.+)\((\w+)\)", target)
    if m:
        return (m.group(2), m.group(1).strip())
    return ("000001", target.strip())


def _build_raw_text(pred: dict) -> str:
    """从排盘数据构建 raw_text 字段"""
    date_str = pred.get("date", "")
    rizhu = pred.get("rizhu", "")
    yue_jiang = pred.get("yue_jiang", "")
    shi_chen = pred.get("shi_chen", "")
    keti = pred.get("keti", "")
    target = pred.get("target", "上证指数")
    stock_code, stock_name = _parse_target(target)

    sike_raw = pred.get("sike", [])
    sike_str = "、".join([f"{s[1]}" for s in sike_raw if isinstance(s, (list, tuple)) and len(s) > 1]) if sike_raw else ""

    sanchuan = pred.get("sanchuan", [])
    sanchuan_tj = pred.get("sanchuan_tianjiang", [])
    sanchuan_parts = []
    for i, zhi in enumerate(sanchuan):
        tj = sanchuan_tj[i] if i < len(sanchuan_tj) else zhi
        sanchuan_parts.append(tj)
    sanchuan_str = "\u2192".join(sanchuan_parts)

    fayong = pred.get("fayong", "")
    fayong_str = f"，发用：{fayong}" if fayong else ""

    parts = [
        f"{date_str}，占{stock_name}（{stock_code}）走势。",
        f"{rizhu}日，月将{yue_jiang}加{shi_chen}时{fayong_str}。",
    ]
    if sike_str:
        parts.append(f"四课：{sike_str}。")
    if sanchuan_str:
        parts.append(f"三传：{sanchuan_str}。")
    if keti:
        parts.append(f"课体：{keti}。")

    return "".join(parts)


def _build_original_prediction(pred: dict) -> str:
    """从推理链构建 original_prediction"""
    rc = pred.get("reasoning_chain", {})
    if isinstance(rc, dict):
        parts = []
        for key in ["课体", "三传", "六亲分析", "天将分析"]:
            val = rc.get(key, "")
            if val:
                parts.append(f"{key}：{val[:100]}")
        if parts:
            return "；".join(parts)
    return pred.get("analysis", "")


def _has_real_quote(details) -> bool:
    """行情完整性判据：必须有收盘价与涨跌幅，且收盘价 > 0。

    🔴 背景（2026-09-21 事故）：`tj-261-2026-07-31` 的 actual_details 只有
       `{window_start, window_end, basis}`，**没有 price/change_pct/high/low**；
       而 `_build_actual_result_text()` 用 `.get(k, 0)` 兜底 ⇒ 写出
       「收盘0.00，涨跌幅+0.00%」的假验证案例，还据此算 is_correct（8 条里 7 条被判错）。
    """
    if not isinstance(details, dict) or not details:
        return False
    if details.get("price") is None or details.get("change_pct") is None:
        return False
    try:
        return float(details["price"]) > 0
    except (TypeError, ValueError):
        return False


def _build_actual_result_text(actual_trend: str, details: dict) -> str:
    """从实际行情构建 actual_result 文字描述"""
    if not _has_real_quote(details):
        # 缺真实行情时只写走势，不伪造价格数字
        return f"实际走势：{actual_trend}"
    price = details.get("price", 0)
    change_pct = details.get("change_pct", 0)
    high = details.get("high", 0)
    low = details.get("low", 0)
    return f"验证：收盘{price:.2f}，涨跌幅{change_pct:+.2f}%，最高{high:.2f}，最低{low:.2f}，实际走势：{actual_trend}"


def _build_sanchuan(pred: dict) -> dict:
    """构建三传对象 {first, second, third}"""
    sanchuan = pred.get("sanchuan", [])
    sanchuan_tj = pred.get("sanchuan_tianjiang", [])
    if not sanchuan:
        return {}
    keys = ["first", "second", "third"]
    result = {}
    for i, zhi in enumerate(sanchuan):
        if i >= 3:
            break
        tj = sanchuan_tj[i] if i < len(sanchuan_tj) else zhi
        result[keys[i]] = tj
    return result


def _build_sike_info(pred: dict) -> dict:
    """构建四课对象 {first, second, third, fourth}"""
    sike = pred.get("sike", [])
    if not sike:
        return {}
    keys = ["first", "second", "third", "fourth"]
    result = {}
    for i, raw in enumerate(sike):
        if i >= 4:
            break
        if isinstance(raw, (list, tuple)) and len(raw) > 1:
            result[keys[i]] = raw[1]
        elif isinstance(raw, str):
            result[keys[i]] = raw
    return result


def collect(prediction_entry: dict) -> dict:
    """
    将一条预测记录转换为训练案例格式

    参数：
        prediction_entry: stock_predictions.json 中的一条完整记录（须含 actual_result）

    返回：
        dict — 符合 stock_training_cases.json 格式的训练案例
        或 None（如果预测记录不完整）
    """
    actual_trend = prediction_entry.get("actual_result")
    if not actual_trend:
        return None

    # 🔴 行情守卫：无真实收盘价/涨跌幅的预测一律拒绝入库（宁可不收集，不写假验证）
    if not _has_real_quote(prediction_entry.get("actual_details")):
        print(f"  [WARN] 预测 {prediction_entry.get('id', '')} 缺行情明细"
              f"（actual_details 无 price/change_pct），拒绝收集为训练案例", flush=True)
        return None

    trend_prediction = prediction_entry.get("trend_prediction", "")
    is_correct = trend_prediction == actual_trend

    stock_code, stock_name = _parse_target(prediction_entry.get("target", "上证指数(000001)"))

    date_str = prediction_entry.get("date", "")
    title = f"{stock_name}六壬实时预测——{prediction_entry.get('keti', '')}课，{trend_prediction}"

    rc = prediction_entry.get("reasoning_chain", {})
    if isinstance(rc, str):
        try:
            rc = json.loads(rc)
        except Exception:
            rc = {}

    case = {
        "id": "",
        "predict_id": prediction_entry.get("id", ""),  # 🔴 去重主键（见 _is_already_collected）
        "stock_code": stock_code,
        "stock_name": stock_name,
        "date": date_str,
        "title": title,
        "raw_text": _build_raw_text(prediction_entry),
        "original_prediction": _build_original_prediction(prediction_entry),
        "actual_result": _build_actual_result_text(actual_trend, prediction_entry.get("actual_details", {})),
        "trend_prediction": trend_prediction,
        "actual_trend": actual_trend,
        "is_correct": is_correct,
        "sike_info": _build_sike_info(prediction_entry),
        "sanchuan": _build_sanchuan(prediction_entry),
        "keti": prediction_entry.get("keti", ""),
        "liuqin_analysis": rc.get("六亲分析", "") if isinstance(rc, dict) else "",
        "tianjiang_analysis": rc.get("天将分析", "") if isinstance(rc, dict) else "",
        "jingi_analysis": rc.get("应期", "") if isinstance(rc, dict) else "",
        "source": f"实时预测自动收集 {date_str}",
        "confidence": "medium",
    }

    return case


def collect_last_completed() -> dict:
    """
    读取 stock_predictions.json 中最后一条 status=completed 的记录，转换为训练案例

    返回：
        dict — 训练案例，或 None
    """
    if not os.path.exists(PREDICTIONS_FILE):
        print(f"  [WARN] 未找到预测记录: {PREDICTIONS_FILE}", flush=True)
        return None

    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    completed = [p for p in predictions if p.get("status") == "completed"]
    if not completed:
        print(f"  [WARN] 没有已完成对照分析的预测记录", flush=True)
        return None

    last = completed[-1]

    # 检查是否已收集过（避免重复收集）
    if _is_already_collected(last.get("id", "")):
        print(f"  [INFO] 预测 {last.get('id')} 已被收集，跳过", flush=True)
        return None

    return collect(last)


def _is_already_collected(predict_id: str) -> bool:
    """检查该预测ID是否已被收集为训练案例

    🔴 旧判据 `predict_id in source` 恒为 False：predict_id＝`tj-261-2026-07-31`，
       而 source 写的是 `实时预测自动收集 2026-07-31` ⇒ 子串永不命中 ⇒
       去重失效，同一条预测被重复收集 8 次（CASE-STOCK-20260731~20260738）。
       新判据：精确匹配 `predict_id` 字段；老数据降级到 source 子串兜底。
    """
    if not predict_id or not os.path.exists(TRAINING_FILE):
        return False
    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
    for c in cases:
        if c.get("predict_id") == predict_id:
            return True
        if predict_id in str(c.get("source", "")):
            return True
    return False


def append_to_training(new_case: dict) -> bool:
    """将新的训练案例追加到 stock_training_cases.json"""
    if not new_case:
        return False

    cases = []
    if os.path.exists(TRAINING_FILE):
        with open(TRAINING_FILE, "r", encoding="utf-8") as f:
            cases = json.load(f)

    new_case["id"] = _next_case_id(cases)
    cases.append(new_case)

    tmp = TRAINING_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, TRAINING_FILE)

    print(f"\n  \u2705 训练案例已收集: {new_case['id']} ({new_case['trend_prediction']}\u2192{new_case['actual_trend']}, correct={new_case['is_correct']})", flush=True)
    return True


def auto_collect() -> bool:
    """
    一键自动收集：读取最新completed预测 → 转换 → 追加到训练库

    返回：
        bool — 是否成功收集
    """
    print(f"\n  [\u23f3] 自动收集训练案例...", flush=True)
    new_case = collect_last_completed()
    if not new_case:
        print(f"  [-] 没有新案例需要收集", flush=True)
        return False
    return append_to_training(new_case)


# ═══════════════════════════════════════════════════════════════
#  建议⑤：主动采集 + 训练增强
# ═══════════════════════════════════════════════════════════════

def batch_collect_all() -> dict:
    """
    批量回溯采集：扫描所有status=completed的记录，收集尚未纳入训练库的案例

    返回：
        dict — {"collected": int, "skipped": int, "cases": [case_ids]}
    """
    if not os.path.exists(PREDICTIONS_FILE):
        return {"collected": 0, "skipped": 0, "cases": [], "error": "预测文件不存在"}

    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    completed = [p for p in predictions if p.get("status") == "completed"]
    if not completed:
        return {"collected": 0, "skipped": 0, "cases": [], "error": "无已完成预测"}

    collected = []
    skipped = 0
    for p in completed:
        pid = p.get("id", "")
        if _is_already_collected(pid):
            skipped += 1
            continue
        case = collect(p)
        if case:
            collect_success = append_to_training(case)
            if collect_success:
                collected.append(case.get("id", ""))

    result = {
        "collected": len(collected),
        "skipped": skipped,
        "total_available": len(completed),
        "cases": collected,
    }
    print(f"\n  [批量采集] 共收集{result['collected']}条，跳过{result['skipped']}条（已有）", flush=True)
    return result


def stat_training_set() -> dict:
    """训练集统计报告"""
    if not os.path.exists(TRAINING_FILE):
        return {"total": 0, "note": "训练集为空"}

    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if not cases:
        return {"total": 0, "note": "训练集为空"}

    correct = sum(1 for c in cases if c.get("is_correct") is True)
    total = len(cases)

    keti_counter = Counter(c.get("keti", "未知") for c in cases)
    source_counter = Counter(c.get("source", "未知") for c in cases)

    return {
        "total": total,
        "correct": correct,
        "error": total - correct,
        "accuracy": round(correct / total, 3) if total > 0 else 0,
        "keti_distribution": [{"keti": k, "count": v, "pct": round(v/total*100, 1)}
                              for k, v in keti_counter.most_common()],
        "source_distribution": [{"source": k, "count": v}
                                for k, v in source_counter.most_common()],
    }


def get_training_readiness() -> dict:
    """
    训练就绪度判断

    判断条件：
    1. 训练集总案例数 >= MIN_CASES_FOR_TRAINING
    2. 正确率 >= TRAINING_READY_RATIO

    返回：
        dict — ready(bool), reason(str), stats(dict)
    """
    stats = stat_training_set()
    if stats["total"] == 0:
        return {"ready": False, "reason": "训练集为空", "stats": stats}

    reasons = []
    ready = True

    if stats["total"] < MIN_CASES_FOR_TRAINING:
        reasons.append(f"案例数{stats['total']}<{MIN_CASES_FOR_TRAINING}")
        ready = False

    if stats["accuracy"] < TRAINING_READY_RATIO:
        reasons.append(f"正确率{stats['accuracy']:.0%}<{TRAINING_READY_RATIO:.0%}")
        ready = False

    return {
        "ready": ready,
        "reason": ", ".join(reasons) if not ready else "训练就绪",
        "stats": stats,
        "min_cases": MIN_CASES_FOR_TRAINING,
        "min_accuracy": TRAINING_READY_RATIO,
    }


_enrich_keti_map = {
    "元首课": "元首课，一上克下，尊制卑，臣尽职",
    "重审课": "重审课，一下贼上，臣犯君，事反复",
    "涉害课": "涉害课，两克相比，取孟仲，事主迟",
    "遥克课": "遥克课，神遥克日，日遥克神，事主远",
    "昴星课": "昴星课，酉为昴星，主掩藏，关梁闭塞",
    "别责课": "别责课，无克无遥，别取合，事主借力",
    "八专课": "八专课，干支同德，帷簿不修，事主淫泆",
    "伏吟课": "伏吟课，十二神各归本位，主静伏不动",
    "返吟课": "返吟课，十二神各冲本位，主动荡反复",
}

_simple_trend_pool = ["涨", "跌", "平"]


def generate_augmented_cases() -> list[dict]:
    """
    基于训练集中正确的案例，生成增强变体

    增强策略：
    1. 用神替换：互换六亲分析中的用神角色
    2. 趋势反转：将涨→跌，跌→涨（适用于反吟课等）
    3. 三传替换：对三传进行错位交换
    4. 时辰偏移：同一日柱不同时辰的变体

    返回：
        list[dict] — 增强后的案例列表（不含重复）
    """
    if not os.path.exists(TRAINING_FILE):
        return []

    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    correct_cases = [c for c in cases if c.get("is_correct") is True]
    if len(correct_cases) < MIN_CASES_FOR_AUGMENT:
        print(f"  [增强] 正确案例{len(correct_cases)}<{MIN_CASES_FOR_AUGMENT}，跳过增强", flush=True)
        return []

    random.seed(42)
    augmented = []
    seen_titles = set(c.get("title", "") for c in cases)

    for case in correct_cases:
        keti = case.get("keti", "")
        trend = case.get("trend_prediction", "")
        actual = case.get("actual_trend", "")
        sanchuan = case.get("sanchuan", {})

        # ── 策略1：趋势反转（适合返吟课、伏吟课等主反复/反转的课体） ──
        if keti in ("返吟课", "伏吟课"):
            rev_map = {"涨": "跌", "跌": "涨", "先涨后跌": "先跌后涨", "先跌后涨": "先涨后跌"}
            rev_trend = rev_map.get(trend)
            rev_actual = rev_map.get(actual)
            if rev_trend and rev_actual:
                new_title = case.get("title", "").replace(trend, rev_trend)
                if new_title not in seen_titles:
                    new_case = dict(case)
                    new_case["id"] = f"AUG-REV-{case['id']}"
                    new_case["title"] = new_title
                    new_case["trend_prediction"] = rev_trend
                    new_case["actual_trend"] = rev_actual
                    new_case["is_correct"] = True
                    new_case["source"] = f"增强(趋势反转) from {case['id']}"
                    new_case["confidence"] = "medium"
                    augmented.append(new_case)
                    seen_titles.add(new_title)

        # ── 策略2：三传错位交换（初传↔中传） ──
        if sanchuan and len(sanchuan) >= 3:
            first = sanchuan.get("first", "")
            second = sanchuan.get("second", "")
            third = sanchuan.get("third", "")
            if first and second:
                swapped = {"first": second, "second": first, "third": third}
                new_case = dict(case)
                new_case["id"] = f"AUG-SWAP-{case['id']}"
                new_case["sanchuan"] = swapped
                new_case["is_correct"] = False  # 认为错位后不确定性增加
                new_case["source"] = f"增强(三传错位) from {case['id']}"
                new_case["confidence"] = "low"
                augmented.append(new_case)

        # ── 策略3：简单趋势变体（仅适用于simple趋势的别责课/八专课） ──
        if keti in ("别责课", "八专课") and trend in _simple_trend_pool:
            variations = [t for t in _simple_trend_pool if t != trend and t != actual]
            if variations:
                var_trend = random.choice(variations)
                if var_trend != actual:
                    new_case = dict(case)
                    new_case["id"] = f"AUG-VAR-{case['id']}"
                    new_case["trend_prediction"] = var_trend
                    new_case["is_correct"] = False
                    new_case["source"] = f"增强(趋势变异) from {case['id']}"
                    new_case["confidence"] = "low"
                    augmented.append(new_case)

    # 限制增强数量
    max_aug = len(correct_cases) * AUGMENT_MULTIPLIER
    if len(augmented) > max_aug:
        random.shuffle(augmented)
        augmented = augmented[:max_aug]

    # 写入增强文件
    if augmented:
        with open(AUGMENTED_FILE, "w", encoding="utf-8") as f:
            json.dump(augmented, f, ensure_ascii=False, indent=2)
        print(f"  [增强] 生成{len(augmented)}条增强案例 -> {AUGMENTED_FILE}", flush=True)

    return augmented


def collect_and_prepare() -> dict:
    """
    完整采集流程：批量采集 → 统计 → 增强 → 就绪度判断

    返回：
        dict — 完整的采集报告
    """
    print(f"\n{'='*55}", flush=True)
    print(f"  主动采集 + 训练增强", flush=True)
    print(f"{'='*55}", flush=True)

    # Step 1: 批量采集
    print(f"\n  [Step 1/4] 批量回溯采集...", flush=True)
    collect_result = batch_collect_all()

    # Step 2: 训练集统计
    print(f"\n  [Step 2/4] 训练集统计...", flush=True)
    stats = stat_training_set()

    # Step 3: 数据增强
    print(f"\n  [Step 3/4] 数据增强...", flush=True)
    augmented = generate_augmented_cases()

    # Step 4: 就绪度判断
    print(f"\n  [Step 4/4] 训练就绪度评估...", flush=True)
    readiness = get_training_readiness()

    report = {
        "collect_result": collect_result,
        "training_stats": stats,
        "augmented_count": len(augmented),
        "readiness": readiness,
        "timestamp": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 打印报告摘要
    print(f"\n{'─'*55}", flush=True)
    print(f"  📊 采集报告摘要", flush=True)
    print(f"  ├ 本次采集: {collect_result.get('collected', 0)}条 (跳过{collect_result.get('skipped', 0)}条)", flush=True)
    print(f"  ├ 训练集总计: {stats.get('total', 0)}条 (正确率{stats.get('accuracy', 0)*100:.0f}%)", flush=True)
    print(f"  ├ 增强案例: {len(augmented)}条", flush=True)
    status = "✅ 训练就绪" if readiness.get("ready") else f"⏳ 未就绪 ({readiness.get('reason', '')})"
    print(f"  └ {status}", flush=True)
    print(f"{'─'*55}\n", flush=True)

    return report


if __name__ == "__main__":
    print("=" * 50, flush=True)
    print("  训练案例收集器 — 独立测试", flush=True)
    print("=" * 50, flush=True)
    result = auto_collect()
    ok_icon = '\u2705 已收集'
    fail_icon = '\u274c 无新案例'
    print(f"\n  结果: {ok_icon if result else fail_icon}", flush=True)
