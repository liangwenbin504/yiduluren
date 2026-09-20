"""大六壬全自动调度器 v2.1
=====================================
【2026-07-31 改造】机械固定时/六亲类别预测已在 5239 日诚实回测中被证伪（全低于 55.3% 朴素基线），
故旧类别的自动预测已禁用。本调度器现仅保留：
  - 盘后对照分析（stock_result_check.py --auto）
  - 权重反哺训练（training_collector）
  - 20d 周期引擎（liuren_20d_engine，但仅在天机录入时触发，不再自动跑）
天机起课由 engine/tianji_harness.py + 仪表盘手动录入接管。
"""
import os, sys, json, time, subprocess, threading
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHECK_INTERVAL = 60
REVIEW_START = 15 * 60 + 30
REVIEW_END = 16 * 60 + 0

# ── 旧类别自动预测已禁用（2026-07-31 诚实评估结论：全低于 55.3% 基线）──
# 若某日需恢复（如做对照实验），设 _ENABLE_OLD_PREDICTIONS=True 并重启服务
_ENABLE_OLD_PREDICTIONS = os.environ.get("ENABLE_OLD_PREDICTIONS", "") == "TRUE"
AUTO_CATEGORIES = ["fixed_time","ri_gan_pian_cai","ri_zhi_pian_cai","ri_gan_shi_shen","ri_zhi_shi_shen",
                   "ri_gan_zheng_yin","ri_gan_pian_yin","ri_zhi_zheng_yin","ri_zhi_pian_yin","random"] if _ENABLE_OLD_PREDICTIONS else []
CAT_LABEL = {"fixed_time":"固定时辰","ri_gan_pian_cai":"日干偏财","ri_zhi_pian_cai":"日支偏财",
             "ri_gan_shi_shen":"日干食神","ri_zhi_shi_shen":"日支食神",
             "ri_gan_zheng_yin":"日干正印","ri_gan_pian_yin":"日干偏印",
             "ri_zhi_zheng_yin":"日支正印","ri_zhi_pian_yin":"日支偏印",
             "random":"随机","manual":"人工指定时"}

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE,"_memory")
STOCK_PREDICTIONS = os.path.join(MEMORY,"stock_predictions.json")
SCHEDULER_LOG = os.path.join(MEMORY,"scheduler_log.json")

def _beijing_now(): return datetime.now(timezone.utc)+timedelta(hours=8)
def _today_str(): return _beijing_now().strftime("%Y-%m-%d")
def _minutes(dt): return dt.hour*60+dt.minute

def _load_predictions():
    if not os.path.exists(STOCK_PREDICTIONS): return []
    with open(STOCK_PREDICTIONS,"r",encoding="utf-8") as f: return json.load(f)

def _prediction_exists_today(category):
    today = _today_str()
    for p in _load_predictions():
        if (p.get("date")==today or p.get("target_date")==today) and p.get("category")==category:
            return True
    return False

def _should_catchup_review(today_str):
    """检查是否应该补跑今日复盘：有今日预测且尚未复盘"""
    preds = _load_predictions()
    today_preds = [p for p in preds if p.get("target_date") == today_str or p.get("date") == today_str]
    if not today_preds:
        return False  # 今日无预测（可能是周末/节假日），无需复盘
    # 检查是否有已完成对照的预测（表示复盘链已跑过）
    reviewed = [p for p in today_preds if p.get("status") == "completed" and p.get("actual_result")]
    return len(reviewed) == 0  # 无已完成对照 → 需补跑

def _log_event(event):
    logs = []
    if os.path.exists(SCHEDULER_LOG):
        try:
            with open(SCHEDULER_LOG,"r",encoding="utf-8") as f: logs = json.load(f)
        except: pass
    logs.append(event)
    if len(logs)>200: logs=logs[-200:]
    with open(SCHEDULER_LOG,"w",encoding="utf-8") as f: json.dump(logs,f,ensure_ascii=False,indent=2)

def _run_predict_async(category, actions_today, today):
    label = CAT_LABEL.get(category,category)
    ak = f"{today}_{category}"
    try: print(f"\n{'='*60}\n  [{label}] {_beijing_now().strftime('%H:%M')}\n{'='*60}",flush=True)
    except: pass
    start = time.time()
    r = subprocess.run([sys.executable,"stock_daily_predict.py","--category",category],
                       capture_output=True,text=True,cwd=BASE,encoding="utf-8",errors="replace")
    try: print(r.stdout,flush=True)
    except: pass
    if r.stderr:
        try: print(f"  [stderr] {r.stderr[:300]}",flush=True)
        except: pass
    ok = r.returncode==0
    try: print(f"  [{'完成' if ok else '失败'}] {label} ({time.time()-start:.0f}s)",flush=True)
    except: pass
    actions_today[ak] = ok
    _log_event({"time":_beijing_now().isoformat(),"action":"predict","category":category,"success":ok})

def _run_review():
    try: print(f"\n{'='*60}\n  [盘后] {_beijing_now().strftime('%H:%M')} 执行对照分析...\n{'='*60}",flush=True)
    except: pass
    r = subprocess.run([sys.executable,"stock_result_check.py","--auto",_today_str()],
                       capture_output=True,text=True,cwd=BASE,encoding="utf-8",errors="replace")
    try: print(r.stdout,flush=True)
    except: pass
    ok = r.returncode==0
    
    # 三方对照入库
    try:
        from tech_analysis_predict import daily_save_comparison
        daily_save_comparison(_today_str())
        try: print("  [三方对照] 已入库",flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [三方异常] {e}",flush=True)
        except: pass
    
    # ML合并
    try:
        preds = _load_predictions()
        ml_file = os.path.join(MEMORY,"ml_predictions.json")
        if os.path.exists(ml_file):
            with open(ml_file,"r",encoding="utf-8") as f: mld = json.load(f)
            mll = mld if isinstance(mld,list) else mld.get("predictions",[])
            for ml in mll:
                td = ml.get("date","")
                preds = [p for p in preds if not(p.get("category")=="ml_predict" and p.get("target_date")==td)]
                preds.append({"category":"ml_predict","date":td,"target_date":td,
                    "trend_prediction":ml.get("trend_prediction","?"),
                    "jixiong":"吉" if "涨" in str(ml.get("trend_prediction","")) else "凶",
                    "confidence":ml.get("confidence",0),"system":"ML集成"})
            with open(STOCK_PREDICTIONS,"w",encoding="utf-8") as f:
                json.dump(preds,f,ensure_ascii=False,indent=2)
        try: print("  [ML合并] 已写入",flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [ML合并异常] {e}",flush=True)
        except: pass
    
    # 自进化复盘
    try:
        from self_evolve import run_evolve
        run_evolve()
        try: print("  [自进化] 复盘+模式学习完成",flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [自进化异常] {e}",flush=True)
        except: pass
    
    # ── 反馈回路: 逐条对照 → 更新在线学习器权重 ──
    try:
        from feedback_loop import get_feedback_loop
        fb = get_feedback_loop()
        completed_all = _load_predictions()
        completed_today = [p for p in completed_all
                          if p.get("actual_result") and p.get("status") == "completed"
                          and p.get("target_date") == _today_str()]
        fb_count = 0
        for p in completed_today:
            try:
                fb.record_result(p)
                fb_count += 1
            except Exception:
                pass
        try: print(f"  [反馈回路] {fb_count}条预测→online_learner权重已更新",flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [反馈回路异常] {e}",flush=True)
        except: pass
    
    # ── 训练收集: 将对照完成的预测自动转为训练案例 ──
    try:
        from engine.training_collector import collect_and_prepare
        collect_and_prepare()
        try: print("  [训练收集] 案例自动采集+增强完成",flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [训练收集异常] {e}",flush=True)
        except: pass
    
    # ── 结果反哺权重: 用已完成预测重算各维度对错率 → 写 factor_impact（自进化 Step 1）──
    try:
        from engine.weight_backfill import run_weight_backfill
        rep = run_weight_backfill(apply=True, min_samples=5)
        try:
            print(f"  [权重反哺] 合格样本={rep.get('n_eligible_predictions')} "
                  f"变更={rep.get('n_changes')} 备注={rep.get('note')}", flush=True)
        except: pass
    except Exception as e:
        try: print(f"  [权重反哺异常] {e}",flush=True)
        except: pass
    
    return ok

def _run_20d_cycle(actions_today, today):
    """每日一次：运行全部11类别的20天周期预测

    ⚠️ 2026-08-15 憨爷指令停用：机械类别（fixed_time/六亲/random）已在诚实回测中被
    证伪停用；天机起课（用户心动指定时辰）才是唯一有效路径，且**周期起课窗口未到绝不
    自动起课**。此函数原先每天 9:00 无参 get_liuren_20d_signal() 自动生成当天预测并
    save_liuren_prediction（覆盖 liuren_20d_data/{today}.json），是"反复瞎起课"的
    系统根源。保留函数壳便于追溯，调用点仍触发但立即返回（不生成、不落盘）。
    """
    try:
        print("[20天周期] 已停用（机械类别证伪 + 周期未到不自动起课，2026-08-15 憨爷指令）", flush=True)
    except: pass
    return
    # ── 以下为停用前的逻辑，不再执行 ──
    ak = f"{today}_20d_cycle"
    if actions_today.get(ak) is not None:
        return
    try:
        print(f"\n{'='*60}\n  [20天周期] {_beijing_now().strftime('%H:%M')} 全类别预测...\n{'='*60}", flush=True)
    except: pass

    from liuren_20d_engine import get_liuren_20d_signal, save_liuren_prediction
    preds = _load_predictions() or []

    for cat in AUTO_CATEGORIES:
        try:
            label = CAT_LABEL.get(cat, cat)
            result = get_liuren_20d_signal()
            result['category'] = cat
            result['category_label'] = label
            result['predict_type'] = '20d_cycle'
            save_liuren_prediction(result)

            ana = result.get('analysis', {})
            basic = result.get('basic_info', {})

            # ── 构建四课数据（清洗 si_ke 结构） ──
            sike_raw = result.get('si_ke', [])
            sike_clean = []
            for sk in sike_raw:
                if isinstance(sk, dict):
                    sike_clean.append([sk.get('name', ''), str(sk.get('top', '')), str(sk.get('bottom', ''))])
                elif isinstance(sk, (list, tuple)) and len(sk) >= 2:
                    sike_clean.append(list(sk) if len(list(sk)) >= 3 else [sk[0], str(sk[0] if len(sk) == 1 else ''), str(sk[1] if len(sk) > 1 else '')])
                elif isinstance(sk, str):
                    sike_clean.append([sk, '', ''])

            # ── 构建三传天将 ──
            tj_detail = ana.get('tianjiang', {})
            chuan_list = result.get('san_chuan', [])
            sanchuan_tj = [tj_detail.get('初传', ''), tj_detail.get('中传', ''), tj_detail.get('末传', '')]

            # ── 从训练系统的 full_analysis (12维度) 构建推理链 ──
            def _s(obj):
                if isinstance(obj, dict):
                    return json.dumps(obj, ensure_ascii=False)
                return str(obj) if obj else ''

            fa = ana.get('full_analysis', {})  # ← LiurenAnalysisEngine.analyze() 的完整输出

            rc = {}
            rc['旬空'] = _s(fa.get('旬空分析', fa.get('旬空', {})))
            rc['四季旺衰'] = _s(fa.get('旺衰分析', {}))
            rc['神煞'] = _s(fa.get('神煞', {}))
            rc['六亲'] = _s(fa.get('六亲分析', []))
            rc['刑冲合害'] = _s(fa.get('三传关系', []))
            rc['四课加临'] = _s(fa.get('四课加临', {}))
            rc['用神五气'] = _s(fa.get('用神分析', {}))
            rc['三传制救'] = _s(fa.get('三传制救', {}))
            rc['贵神吉凶'] = _s(fa.get('贵神吉凶', {}))
            rc['八杀体系'] = _s(fa.get('八杀分析', {}))
            rc['十二气财星'] = _s(fa.get('十二气财星', {}))
            rc['身强身弱'] = _s(fa.get('身强身弱分析', {}))
            # 补充：趋势判断、应期、风险提示（来自预测数据，非训练维度）
            rc['趋势判断'] = f"综合评分 {result['prediction']['score']} → {result['prediction']['trend']}; " + ('/'.join(result['prediction'].get('reasons', [])[:5]))
            rc['应期'] = f"20天周期 {result.get('cycle_start', '')} ~ {result.get('cycle_end', '')}"
            rc['风险提示'] = '课体' + result.get('keti', '') + (' (大凶)' if ana.get('keti_duanyu', {}).get('is_daxiong') else '')

            rc_filled = sum(1 for v in rc.values() if v)

            # ── analysis 转为易读字符串 ──
            keti_d = ana.get('keti_duanyu', {})
            _kn = keti_d.get('keti_name') or result.get('keti', '?')
            _kl = keti_d.get('level') or keti_d.get('等级', '?')
            _kd = keti_d.get('duanyu') or keti_d.get('断语', keti_d.get('zonglun', ''))
            analysis_text = (
                f"课体: {_kn}"
                f"（{_kl}）\n"
                f"断语: {_kd}\n"
                f"课格层级: {keti_d.get('ke_64_level', '未知')}"
            )
            if keti_d.get('is_daxiong'):
                analysis_text += '\n⚠️ 为大凶课！'

            preds.append({
                'id': f"20d_{today}_{cat}",
                'category': cat,
                'predict_time': _beijing_now().isoformat(),
                'target': '上证指数(000001)',
                'date': today,
                'rizhu': basic.get('ri_gan_zhi', ''),
                'yue_jiang': basic.get('yuejiang', ''),
                'shi_chen': basic.get('shichen', ''),
                'keti': result.get('keti', ''),
                'fayong': result.get('qifa', ''),
                'sike': sike_clean,
                'sanchuan': chuan_list,
                'sanchuan_tianjiang': sanchuan_tj,
                'trend_prediction': result['prediction']['trend'],
                'jixiong': '吉' if result['prediction']['score'] > 0 else '凶',
                'analysis': analysis_text,
                'reasoning_chain': rc,
                'rc_filled': rc_filled,
                'status': 'pending',
                'predict_session': '20天周期',
            })
            try: print(f"  [{label}] {result['prediction']['trend']} (评分:{result['prediction']['score']})", flush=True)
            except: pass
        except Exception as e:
            try: print(f"  [{label}] 失败: {e}", flush=True)
            except: pass

    with open(STOCK_PREDICTIONS, "w", encoding="utf-8") as f:
        json.dump(preds, f, ensure_ascii=False, indent=2)
    actions_today[ak] = True
    try: print(f"  [20天周期] 完成 11类预测已入库", flush=True)
    except: pass


def run_scheduler():
    try: print(f"\n{'='*60}\n  调度器 v2.0 {_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n",flush=True)
    except: pass
    last_date, actions_today = "", {}
    while True:
        try:
            now = _beijing_now(); today = _today_str(); mins = _minutes(now)
            is_weekday = now.weekday() < 5
            if today != last_date:
                last_date = today; actions_today = {}
                try: print(f"\n[新日] {today} ({'交易日' if is_weekday else '休市'})",flush=True)
                except: pass
            if not is_weekday:
                time.sleep(CHECK_INTERVAL*5)
                continue
            
            # 启动时补漏
            if actions_today.get(f"{today}_init") is None:
                actions_today[f"{today}_init"] = True
                missing = [c for c in AUTO_CATEGORIES if not _prediction_exists_today(c)]
                if missing:
                    try: print(f"\n[启动补漏] {len(missing)}个遗漏, 补跑...",flush=True)
                    except: pass
                    for c in missing:
                        t = threading.Thread(target=_run_predict_async,args=(c,actions_today,today),daemon=True)
                        t.start(); time.sleep(1)
            
            # 每天09:00：20天周期全类别预测
            if 9*60+0 <= mins < 9*60+5:
                t = threading.Thread(target=_run_20d_cycle, args=(actions_today, today), daemon=True)
                t.start()
            
            # 每天09:05：量化选股（海选）
            if 9*60+5 <= mins < 9*60+10:
                if actions_today.get(f"{today}_screener") is None:
                    try:
                        from stock_screener import QuantScreener
                        try: print(f"\n[选股] 多因子扫描（海选TOP15）...",flush=True)
                        except: pass
                        qs = QuantScreener()
                        qs.run(top_n=15)
                        qs.save()
                        try: print(f"  [选股] TOP15已保存",flush=True)
                        except: pass
                        actions_today[f"{today}_screener"] = True
                    except Exception as e:
                        try: print(f"  [选股异常] {e}",flush=True)
                        except: pass
                        # 标记为失败，09:10精选前会检查并重试
                        actions_today[f"{today}_screener"] = False

            # 每天09:10：一课多断 + 双阶段精选（正时/批量预测，非活时法）
            if 9*60+10 <= mins < 9*60+20:
                if actions_today.get(f"{today}_multi_stock") is None:
                    try:
                        from multi_stock_predict import predict_multi_stocks, dual_phase_select, load_screener_pool, get_market_timing
                        try: print(f"\n[个股] 一课多断 + 双阶段精选（正时批量）...",flush=True)
                        except: pass

                        # 漏洞1修复：选股失败时重试一次
                        if actions_today.get(f"{today}_screener") is False:
                            try: print("  [选股重试] 09:05选股失败，重试中...",flush=True)
                            except: pass
                            try:
                                from stock_screener import QuantScreener
                                qs = QuantScreener()
                                qs.run(top_n=15)
                                qs.save()
                                actions_today[f"{today}_screener"] = True
                                try: print("  [选股重试] 成功",flush=True)
                                except: pass
                            except Exception as e2:
                                try: print(f"  [选股重试] 仍失败: {e2}",flush=True)
                                except: pass

                        # ① 六壬择时：仅作参考记录（不影响选股决策）
                        timing = get_market_timing()
                        market_signal = timing.get('signal', 'neutral')
                        signal_map = {'bull': '📈看多', 'bear': '📉看空', 'neutral': '➡️中性'}
                        try:
                            from config import LIUREN_REFERENCE_ONLY
                        except Exception:
                            LIUREN_REFERENCE_ONLY = True
                        try: print(f"  [六壬择时·参考] {signal_map.get(market_signal, '?')} 吉凶:{timing.get('jixiong','?')} 趋势:{timing.get('trend','?')}（仅参考·不影响选股）",flush=True)
                        except: pass

                        # 参考模式：六壬择时不再跳过量化选股，始终执行双阶段精选
                        # 执行双阶段选股（量化→六壬标注，六壬仅参考）
                        dual_results = dual_phase_select(top_n=15)
                        results = dual_results[0] if isinstance(dual_results, tuple) else dual_results
                        timing_info = dual_results[1] if isinstance(dual_results, tuple) else timing
                        if results:
                            # 保存双阶段结果
                            import json as _json
                            import os as _os
                            from datetime import datetime as _dt
                            mem_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_memory")
                            _os.makedirs(mem_dir, exist_ok=True)
                            ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                            save_path = _os.path.join(mem_dir, f"dual_phase_{ts}.json")
                            with open(save_path, 'w', encoding='utf-8') as f:
                                _json.dump({
                                    "date": _dt.now().strftime("%Y-%m-%d"),
                                    "results": results,
                                    "market_timing": timing_info,
                                    "liuren_reference_only": LIUREN_REFERENCE_ONLY,
                                    "method": "批量预测(正时/真太阳时校正)",
                                }, f, ensure_ascii=False, indent=2)
                            try: print(f"  [双阶段] 已保存: {save_path}",flush=True)
                            except: pass
                        # 同时跑硬编码股票池预测（对照学习）
                        predict_multi_stocks()
                        try: print(f"  [个股] 预测完成",flush=True)
                        except: pass
                        actions_today[f"{today}_multi_stock"] = True
                    except Exception as e:
                        try: print(f"  [个股异常] {e}",flush=True)
                        except: pass

            # 盘后窗口 + 复盘补跑（进程重启后自动追赶遗漏的每日复盘）
            if actions_today.get(f"{today}_review") is None:
                if REVIEW_START <= mins < REVIEW_END:
                    # 正常窗口：15:30-16:00
                    _run_review()
                    actions_today[f"{today}_review"] = True
                elif mins >= REVIEW_END and _should_catchup_review(today):
                    # 补跑模式：16:00后仍未执行今日复盘 → 立即追赶
                    try: print(f"\n[复盘补跑] 错过15:30-16:00窗口，立即追赶今日复盘...",flush=True)
                    except: pass
                    _run_review()
                    actions_today[f"{today}_review"] = True
            
            # 每天 16:05：双子系统持仓管理（量化 + 六壬 各自建仓/平仓/更新盈亏）
            if 16*60+5 <= mins < 16*60+15:
                if actions_today.get(f"{today}_dual_subsystems") is None:
                    try:
                        from quant_position_manager import daily_run as quant_daily_run
                        from liuren_position_manager import daily_run as liuren_daily_run
                        try: print(f"\n{'='*50}\n[双子系统] 16:05 并行运行...\n{'='*50}", flush=True)
                        except: pass
                        quant_daily_run(today)
                        liuren_daily_run(today)
                        actions_today[f"{today}_dual_subsystems"] = True
                        try: print(f"\n  ✅ [双子系统] 量化+六壬 均已完成", flush=True)
                        except: pass
                    except Exception as e:
                        try: print(f"  [双子系统异常] {e}", flush=True)
                        except: pass
            
            # 22:00 日报+推送
            if 22*60 <= mins < 22*60+5:
                if actions_today.get(f"{today}_report") is None:
                    try:
                        from stock_report_generator import generate_report
                        rp = generate_report(now.date())
                        if rp:
                            try: print(f"  ✅ 报表: {rp}",flush=True)
                            except: pass
                        from notify import send_daily_report
                        nr = send_daily_report()
                        try: print(f"  📨 {nr}",flush=True)
                        except: pass
                        actions_today[f"{today}_report"] = True
                    except Exception as e:
                        try: print(f"  ❌ 报表失败: {e}",flush=True)
                        except: pass
            
            # 周五22:05 ML重训
            if now.weekday()==4 and 22*60+5 <= mins < 22*60+10:
                if actions_today.get(f"{today}_ml_retrain") is None:
                    try:
                        from ml_stock_predict import fetch_market_data,add_north_flow,engineer_features,train_final_model
                        try: print(f"\n[ML重训] 开始...",flush=True)
                        except: pass
                        df = fetch_market_data(years=3)
                        if df is not None:
                            df = add_north_flow(df)
                            ft = engineer_features(df)
                            models, cols = train_final_model(ft, train_days=500)
                            try: print(f"[ML重训] 完成 {len(cols)}特征",flush=True)
                            except: pass
                        actions_today[f"{today}_ml_retrain"] = True
                    except Exception as e:
                        try: print(f"  [ML重训异常] {e}",flush=True)
                        except: pass
            
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            try: print(f"\n[停止] {_beijing_now().strftime('%H:%M:%S')}",flush=True)
            except: pass
            break
        except Exception as e:
            try: print(f"  [异常] {e}",flush=True)
            except: pass
            time.sleep(CHECK_INTERVAL*2)

if __name__ == "__main__":
    run_scheduler()
