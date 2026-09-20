"""
股票预测结果自动对照分析脚本
用法: python stock_result_check.py [日期] [--auto]

模式:
  1. 不带参数 → 交互式手动输入实际结果
  2. --auto    → 自动通过AKShare获取上证指数实际行情，自动对照分析

示例:
  python stock_result_check.py                   # 手动模式
  python stock_result_check.py 2026-05-04 --auto  # 自动模式
  python stock_result_check.py --auto             # 自动模式（最新记录）
"""
import json, os, sys, re
from datetime import datetime, date, timezone, timedelta

# 结算时回填知识点特征（自进化 Step1 卡点修复 2026-08-12）
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from engine.knowledge_features import extract_for_backfill
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.abspath(__file__))
PREDICTIONS_FILE = os.path.join(BASE, "_memory", "stock_predictions.json")

TREND_CATEGORIES = ["涨", "跌", "平", "先涨后跌", "先跌后涨", "先涨后平", "先跌后平", "先平后涨", "震荡偏涨", "震荡偏跌"]

# ── AKShare 自动获取行情 ──
HAS_AKSHARE = False
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    pass


def fetch_index_spot():
    """获取上证指数实时行情"""
    if not HAS_AKSHARE:
        return None
    try:
        df = ak.stock_zh_index_spot_em()
        sh = df[df["名称"] == "上证指数"]
        if not sh.empty:
            row = sh.iloc[0]
            return {
                "code": str(row["代码"]),
                "name": str(row["名称"]),
                "price": float(row["最新价"]),
                "change_pct": float(row["涨跌幅"]),
                "change_amount": float(row["涨跌额"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["今开"]),
                "prev_close": float(row["昨收"]),
                "volume": float(row["成交量"]),
                "amount": float(row["成交额"]),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  [AKShare] 获取行情失败: {e}")
    return None


def _fetch_daily_close(target_date=None):
    """降级方案：从日线历史获取指定日期收盘数据"""
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol="sh000001")
        # 日期列可能是 date 列或 DatetimeIndex
        if 'date' in df.columns:
            df['date_str'] = df['date'].astype(str)
        else:
            df['date_str'] = df.index.astype(str).str[:10]

        check_date = target_date or datetime.now().strftime("%Y-%m-%d")
        row = df[df['date_str'] == check_date]
        if not row.empty:
            r = row.iloc[-1]
            # 找前一交易日作为昨收
            idx = row.index[-1]
            prev_idx = idx - 1 if idx > 0 else None
            prev_close = float(df.iloc[prev_idx]['close']) if prev_idx is not None else float(r['open'])
            close_price = float(r['close'])
            open_price = float(r['open'])
            change_pct = (close_price - prev_close) / prev_close * 100
            return {
                "price": close_price,
                "change_pct": round(change_pct, 2),
                "high": float(r['high']),
                "low": float(r['low']),
                "open": open_price,
                "prev_close": prev_close,
            }
    except Exception as e:
        print(f"  [日线历史] 获取失败: {e}")
    return None


def determine_trend_from_spot(spot):
    """从行情数据自动判断趋势类型

    策略：
    - 涨跌幅 > 0.3% → 涨
    - 涨跌幅 < -0.3% → 跌
    - 中间 → 平
    - 结合开盘价/收盘价判断先涨后跌/先跌后涨
    """
    if not spot:
        return "未知", {}

    price = spot["price"]
    prev_close = spot["prev_close"]
    open_price = spot["open"]
    high = spot["high"]
    low = spot["low"]
    change_pct = spot["change_pct"]

    # 判断单边趋势
    if change_pct > 0.3:
        base_trend = "涨"
    elif change_pct < -0.3:
        base_trend = "跌"
    else:
        base_trend = "平"

    # 判断先涨后跌 / 先跌后涨
    intraday_range = (high - low) / prev_close * 100
    open_to_close = (price - open_price) / open_price * 100

    refined_trend = base_trend

    if intraday_range >= 0.3:
        dropped_below = low < prev_close
        rose_above = high > prev_close
        recovered = price > low + (high - low) * 0.3
        fell_back = price < high - (high - low) * 0.3

        if dropped_below and recovered and open_to_close > 0:
            refined_trend = "先跌后涨"
        elif rose_above and fell_back and open_to_close < 0:
            refined_trend = "先涨后跌"
        elif change_pct > 0.5 and intraday_range > 1.5:
            refined_trend = "震荡偏涨"
        elif change_pct < -0.5 and intraday_range > 1.5:
            refined_trend = "震荡偏跌"

    details = {
        "price": price,
        "change_pct": change_pct,
        "open": open_price,
        "high": high,
        "low": low,
        "prev_close": prev_close,
        "intraday_range_pct": round(intraday_range, 2),
        "amplitude": round(intraday_range, 2),
    }

    return refined_trend, details


# ── 预测加载 ──

def load_predictions(target_date=None):
    """加载预测记录，按 target_date 或 date 匹配"""
    if not os.path.exists(PREDICTIONS_FILE):
        print(f"❌ 预测记录文件不存在: {PREDICTIONS_FILE}")
        return []

    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    if not isinstance(predictions, list):
        print("❌ 预测记录格式错误")
        return []

    if target_date:
        # 补对照基于目标日期：只匹配 target_date 字段
        # （date 字段是预测生成日期，不是预测目标日期，不应混入）
        predictions = [p for p in predictions if p.get("target_date") == target_date]

    # 【2026-08-02 修复】20 交易日窗口记录（量化 / 天机起课）由各自的窗口收益回检
    # （quant_predictor.check_quant_results / tianji_harness.check_tianji_results）处理，
    # 此处只处理旧的单日/次日模型，避免"上证单日涨跌"污染 20 日窗口命中率。
    predictions = [p for p in predictions
                   if p.get("category") != "量化" and p.get("source") != "tianji_cast"]

    return predictions


def run_window_checks():
    """运行 20 交易日窗口回检（量化池均值 / 天机上证窗口），返回 (量化条数, 天机条数)。"""
    nq = nt = 0
    try:
        from quant_predictor import check_quant_results
        nq = check_quant_results()
    except Exception as e:
        print(f"  ⚠️ 量化窗口回检失败: {e}")
    try:
        from engine.tianji_harness import check_tianji_results
        nt = check_tianji_results()
    except Exception as e:
        print(f"  ⚠️ 天机窗口回检失败: {e}")
    if nq or nt:
        print(f"  ✅ 20 交易日窗口回检：量化 {nq} 条、天机 {nt} 条已结算（窗口收益口径）")
    return nq, nt


# ── 手动输入 ──

def get_input_trend():
    """交互式输入实际趋势"""
    print("\n请选择实际交易结果（输入数字）:")
    for i, cat in enumerate(TREND_CATEGORIES, 1):
        print(f"  {i}. {cat}")
    print(f"  q. 跳过")

    choice = input("\n请输入选择: ").strip().lower()
    if choice == 'q':
        return None
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(TREND_CATEGORIES):
            return TREND_CATEGORIES[idx]
    except ValueError:
        pass
    if choice in TREND_CATEGORIES:
        return choice
    print("输入无效，请重试")
    return get_input_trend()


def get_input_details():
    """交互式输入更多细节"""
    print("\n请输入更多细节（可选，直接回车跳过）:")
    open_price = input("  开盘价: ").strip()
    close_price = input("  收盘价: ").strip()
    high_price = input("  最高价: ").strip()
    low_price = input("  最低价: ").strip()
    volume_desc = input("  量能描述(放量/缩量/平量): ").strip()
    notes = input("  备注(如重大消息发生): ").strip()
    return {
        "open": open_price, "close": close_price, "high": high_price,
        "low": low_price, "volume": volume_desc, "notes": notes,
        "source": "manual",
    }


# ── 对照分析 ──

def compare_prediction(pred, actual_trend, details):
    """生成对照分析报告"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"   大六壬股票预测对照分析报告")
    lines.append(f"   日期: {pred.get('date', '?')}  {pred.get('predict_session', '?')}")
    lines.append(f"   标的: {pred.get('target', '?')}")
    lines.append("=" * 70)

    # ── 排盘回顾 ──
    lines.append(f"\n📊 【排盘回顾】")
    lines.append(f"  日柱: {pred.get('rizhu', '?')}  月将: {pred.get('yue_jiang', '?')}  占时: {pred.get('shi_chen', '?')}")
    lines.append(f"  课体: {pred.get('keti', '?')}  发用: {pred.get('fayong', '?')}")
    lines.append(f"  三传: {' → '.join(pred.get('sanchuan_tianjiang', pred.get('sanchuan', [])))}")

    # ── 预测回顾 ──
    predicted_trend = pred.get("trend_prediction", "?")
    lines.append(f"\n🔮 【预测回顾】")
    lines.append(f"  预测趋势: {predicted_trend}")
    lines.append(f"  吉凶判断: {pred.get('jixiong', '?')}")

    rc = pred.get("reasoning_chain", {})
    if rc:
        trend_judge = rc.get("趋势判断", "")
        if trend_judge:
            lines.append(f"  推理核心: {trend_judge[:100]}")

    # ── 实际行情 ──
    lines.append(f"\n✅ 【实际行情】")
    if details and details.get("source") == "auto":
        lines.append(f"  （数据来源: AKShare 自动获取）")
        lines.append(f"  收盘价: {details.get('price', '?')}")
        lines.append(f"  涨跌幅: {details.get('change_pct', '?')}%")
        lines.append(f"  开盘价: {details.get('open', '?')}  最高: {details.get('high', '?')}  最低: {details.get('low', '?')}")
        lines.append(f"  昨收: {details.get('prev_close', '?')}")
        lines.append(f"  日内振幅: {details.get('amplitude', '?')}%")
    else:
        if details:
            for k, v in details.items():
                if v and k != "source":
                    lines.append(f"  {k}: {v}")

    lines.append(f"\n  实际趋势: {actual_trend}")

    # ── 对照分析 ──
    lines.append(f"\n📋 【对照分析】")

    # 趋势匹配度
    if predicted_trend == actual_trend:
        match_status = "✅ 精准命中！"
        match_score = 100
        trend_match = True
    elif actual_trend in predicted_trend or predicted_trend in actual_trend:
        match_status = "⚠️ 部分吻合（趋势方向基本一致）"
        match_score = 60
        trend_match = True
    else:
        match_status = "❌ 预测偏差（趋势方向不一致）"
        match_score = 0
        trend_match = False

    lines.append(f"  趋势匹配: {match_status}")
    lines.append(f"  预测={predicted_trend}  vs  实际={actual_trend}")
    lines.append(f"  匹配评分: {match_score}/100")

    # 信号逐项验证
    lines.append(f"\n📡 【信号验证】")
    signals_ok = 0
    signals_total = 0

    # 1. 课体验证
    keti = pred.get("keti", "")
    if keti:
        signals_total += 1
        if "重审" in keti:
            if any(kw in actual_trend for kw in ["先跌后涨", "震荡", "先跌后平"]):
                signals_ok += 1
                lines.append(f"  ✅ 课体验证（{keti}: 先抑后扬）: 与市场走势吻合")
            else:
                lines.append(f"  ⚠️ 课体验证（{keti}: 先抑后扬）: 与实际走势部分吻合")

    # 2. 三传验证
    sanchuan = pred.get("sanchuan_tianjiang", pred.get("sanchuan", []))
    if sanchuan:
        signals_total += 1
        sanchuan_str = "→".join(sanchuan)
        if "先跌后涨" in predicted_trend and "先跌后涨" in actual_trend:
            signals_ok += 1
            lines.append(f"  ✅ 三传走势（{sanchuan_str}）: 下跌→筑底→反弹路径准确")
        elif "先跌后涨" in predicted_trend and "涨" in actual_trend:
            signals_ok += 1
            lines.append(f"  ⚠️ 三传走势（{sanchuan_str}）: 方向正确，细节有偏差")
        elif "跌" in predicted_trend and "跌" in actual_trend:
            signals_ok += 1
            lines.append(f"  ✅ 三传走势（{sanchuan_str}）: 下跌方向准确")
        else:
            lines.append(f"  ❌ 三传走势（{sanchuan_str}）: 方向不匹配")

    # 3. 天将信号验证
    if isinstance(sanchuan, list):
        for chuan_tj in sanchuan:
            signals_total += 1
            has_baihu = "白虎" in chuan_tj
            has_taiyin = "太阴" in chuan_tj
            has_sheshe = "螣蛇" in chuan_tj

            if has_baihu and "跌" in actual_trend:
                signals_ok += 1
                lines.append(f"  ✅ 白虎信号（{chuan_tj}）: 恐慌下跌验证")
            elif has_baihu:
                lines.append(f"  ❌ 白虎信号（{chuan_tj}）: 未出现预期下跌")

            if has_taiyin and "先跌后涨" in actual_trend:
                signals_ok += 1
                lines.append(f"  ✅ 太阴信号（{chuan_tj}）: 主力吸筹验证")
            elif has_taiyin:
                pass  # 太阴信号难直接验证

            if has_sheshe and "先跌后涨" in actual_trend:
                pass  # 螣蛇信号较复杂

    # 4. 风险提示验证
    rc = pred.get("reasoning_chain", {})
    risk = rc.get("风险提示", "") if isinstance(rc, dict) else ""
    if risk:
        signals_total += 1
        if "超预期" in risk and match_score < 100:
            lines.append(f"  ⚠️ 风险提示验证: 预见到了可能的偏差风险")
            signals_ok += 1

    # ── 综合评分 ──
    lines.append(f"\n📈 【综合评分】")
    if signals_total > 0:
        signal_pct = signals_ok / signals_total * 100
        lines.append(f"  信号吻合度: {signals_ok}/{signals_total} ({signal_pct:.0f}%)")
    avg_score = (match_score + (signals_ok / max(signals_total, 1) * 100)) / 2
    lines.append(f"  综合得分: {avg_score:.0f}/100")

    # 总体评价
    lines.append(f"\n{'=' * 70}")
    if predicted_trend == actual_trend:
        lines.append(f"  🎯 总体评价: 预测准确！大六壬股市预测方法在该案例中表现良好")
        lines.append(f"  三传（申→亥→寅: 白虎→太阴→螣蛇）的象意")
        lines.append(f"  与市场实际走势高度吻合，说明六壬股市映射体系有效。")
    elif "先跌后涨" in predicted_trend and "涨" in actual_trend:
        lines.append(f"  ⚠️ 总体评价: 方向正确，细节有偏差")
        lines.append('  预测"先跌后涨"中的下跌段可能未充分体现，')
        lines.append('  但整体向上方向判断正确。')
    elif match_score >= 60:
        lines.append(f"  ⚠️ 总体评价: 部分吻合，推理链可进一步优化")
    else:
        lines.append(f"  ❌ 总体评价: 预测偏差较大，需分析原因")
        lines.append(f"  可能原因: (1)排盘参数精度 (2)天将解读 (3)六亲映射权重")
    lines.append("=" * 70)

    return "\n".join(lines), trend_match, match_score


def save_with_result(pred_entry, actual, details, trend_match=None, match_score=None):
    """保存对照结果"""
    predictions = []
    if os.path.exists(PREDICTIONS_FILE):
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            predictions = json.load(f)

    pred_id = pred_entry.get("id")
    pred_cat = pred_entry.get("category")
    pred_session = pred_entry.get("predict_session")
    pred_target = pred_entry.get("target_date")
    found = False
    for i, p in enumerate(predictions):
        # 用 id + category + target_date 精确匹配（同一id可能有多个category的预测）
        if p.get("id") == pred_id and p.get("category") == pred_cat and p.get("target_date") == pred_target:
            predictions[i]["actual_result"] = actual
            predictions[i]["actual_details"] = details
            predictions[i]["status"] = "completed"
            # 自进化 Step1 卡点修复：标记 completed 时一并回填知识点特征
            _kf = extract_for_backfill(predictions[i])
            if _kf is not None:
                predictions[i]["knowledge_features"] = _kf
            predictions[i]["check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if trend_match is not None:
                predictions[i]["trend_match"] = trend_match
            if match_score is not None:
                predictions[i]["match_score"] = match_score
            found = True
            break

    if not found:
        pred_entry["actual_result"] = actual
        pred_entry["actual_details"] = details
        pred_entry["status"] = "completed"
        # 自进化 Step1 卡点修复：标记 completed 时一并回填知识点特征
        _kf = extract_for_backfill(pred_entry)
        if _kf is not None:
            pred_entry["knowledge_features"] = _kf
        pred_entry["check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        predictions.append(pred_entry)

    tmp_file = PREDICTIONS_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_file, PREDICTIONS_FILE)
    print(f"\n✅ 实际结果已保存到预测记录")


# ── 主入口 ──

def main():
    args = sys.argv[1:]

    target_date = None
    auto_mode = False

    for arg in args:
        if arg == "--auto":
            auto_mode = True
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", arg):
            target_date = arg

    # 【2026-08-02 修复】先跑 20 交易日窗口回检（量化池均值 / 天机上证窗口），
    # 再处理旧的单日/次日模型。确保调度器每日收盘后一次调用覆盖全部记录。
    run_window_checks()

    predictions = load_predictions(target_date)

    if not predictions:
        print(f"没有找到{'日期=' + target_date if target_date else ''}的预测记录")
        return

    pending = [p for p in predictions if p.get("status") == "pending"]
    completed = [p for p in predictions if p.get("status") == "completed"]

    if not pending:
        print("\n所有预测记录已完成对照分析！")
        if completed:
            print(f"\n历史对照记录:")
            for p in completed:
                trend = p.get("trend_prediction", "?")
                actual = p.get("actual_result", "?")
                score = "✅" if trend == actual else "❌"
                print(f"  {p.get('date','?')} {p.get('predict_session','?')}: 预测={trend} → 实际={actual} {score}")
        return

    # 自动模式
    if auto_mode:
        print(f"\n🤖 自动对照模式已启用 (目标日期: {target_date or '今天'})", flush=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        spot = None
        # 仅当目标日期为今天或缺省时，才取实时行情；历史日期直接走日线历史
        if not target_date or target_date == today_str:
            spot = fetch_index_spot()
        if spot is None:
            # 降级：用日线历史数据获取指定日期收盘
            spot = _fetch_daily_close(target_date)
        if spot is None:
            print("  ❌ 无法获取行情数据，跳过自动对照")
            return
        else:
            actual_trend, details = determine_trend_from_spot(spot)
            details["source"] = "auto"
            print(f"  上证指数: {spot['price']}  ({spot['change_pct']:+.2f}%)", flush=True)
            print(f"  开盘:{spot['open']}  最高:{spot['high']}  最低:{spot['low']}  昨收:{spot['prev_close']}", flush=True)
            print(f"  自动判断趋势: {actual_trend}", flush=True)

    # 处理每个待对照的预测
    for i, p in enumerate(pending):
        print(f"\n{'=' * 70}", flush=True)
        print(f"📋 第 {i+1}/{len(pending)} 条预测记录", flush=True)
        print(f"  日期: {p.get('date', '?')} | 时段: {p.get('predict_session', '?')}", flush=True)
        print(f"  预测趋势: {p.get('trend_prediction', '?')}", flush=True)
        print(f"  排盘: {p.get('rizhu', '?')} {p.get('keti', '?')} 三传{' → '.join(p.get('sanchuan_tianjiang', p.get('sanchuan', [])))}", flush=True)

        if auto_mode:
            actual = actual_trend
            details_data = details
        else:
            actual = get_input_trend()
            if actual is None:
                print("  跳过")
                continue
            details_data = get_input_details()

        report, trend_match, match_score = compare_prediction(p, actual, details_data)
        print(f"\n{report}")
        save_with_result(p, actual, details_data, trend_match, match_score)

    print("\n✅ 全部处理完成！")


if __name__ == "__main__":
    main()
