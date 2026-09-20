# 自进化 Step 1（结果反哺权重）两周复查报告
**日期**：2026-08-12 ｜ **检查项**：weight_backfill.py 干跑 + 上游回填步链路

## 1. 干跑结果：合格样本数 = 0

```
python engine/weight_backfill.py   (dry-run)
→ n_eligible_predictions = 0   (status=completed 且含 actual_result 与 knowledge_features)
→ 安全 no-op，未改动 factor_impact
```
这是自 2026-07-29 起**连续第 9 次** `n_eligible=0`（日志 `_memory/weight_backfill_log.json` 历次均为 0）。

当前 `stock_predictions.json` 共 18 条记录：
| 类别 | 条数 | status 字段 | 有 actual_result | 有 knowledge_features |
|---|---|---|---|---|
| 量化 (category=量化) | 11 | 全部 None | 无 | 无 |
| 天机 (source=tianji_cast) | 1 | None | 无 | 无 |
| ml_predict | 2 | None | 无 | 无 |
| manual | 0 | — | — | — |

**没有任何一条同时满足** `status=completed` + `actual_result` + `knowledge_features`，故 0 合格。

## 2. 为什么 =0：两层原因（并非单纯"回填步坏了"）

### (A) 主因——窗口尚未收盘（符合预期，非 bug）
`stock_result_check.py --auto` 的 `run_window_checks()` 对量化/天机记录按 **20 交易日窗口** 回检，
窗口未收盘（`target_date > 今天`）时正确跳过、绝不写假结果。今天 2026-08-12，18 条中 **16 条窗口仍 OPEN**：

- 11 条量化 + 1 条天机（起课 7-31/8-03/8-09），`target_date` = **2026-08-23 ~ 08-29**
- 最早一批（8-03 起课）约 **2026-08-23** 收盘，多数要等到 **8-28/8-29**

→ 调度器每日 `--auto` 跑到现在只能"等"，尚无任何已结算样本。这是设计内的等待期。

### (B) 真问题——`knowledge_features` 从未被回填步写入（结构性缺口）
即使窗口收盘、`check_quant_results` / `check_tianji_results` 会写 `status=completed` + `actual_result`，
**三者（`check_quant_results`、`check_tianji_results`、`save_with_result`）都没有写 `knowledge_features`**。
而 `weight_backfill.py` 的合格门槛要求**三者俱全**。因此：

> 即便窗口全部收盘，Step 1 仍会一直报 `n_eligible=0`，除非先把 `knowledge_features` 补上。

验证：`engine/knowledge_features.py:extract_knowledge_features(entry)` 对真实记录可正常产出全部所需键
（`relations`/`liqi`/`leixiang`/`bifa`/`sanchuan` 均 present）。**修复可行**：回填步在标记 completed 时
调用一次 `entry['knowledge_features'] = extract_knowledge_features(entry)` 即可。

另：`ml_predict` 这 2 条窗口虽已收盘（target 7-28、8-09），但 `category=ml_predict` 不被窗口回检处理、
且 `status=None`（非 pending）也不进人工对照循环 → 完全被遗漏，需一并纳入。

## 3. 学得权重 / 对齐率：无数据可判
- `_memory/weight_backfill_log.json`：历次 `n_changes=0`，无变更。
- `_memory/backfill_snapshots/`：**目录不存在**（从未发生过 `--apply` 写盘）。
- `factor_impact` 内 `rel_*`/`yong_wangshuai_*`/`kongwang`/`gangrou`/`bifa_jiaoche`/`chuanbian` 键：未出现。
- "预测方向 vs 实际涨跌对齐率是否随学得权重上升"：**无法评估**——尚无任何样本，遑论学得权重。

## 4. 结论与建议

**结论**：两周复查，Step 1 仍 `n_eligible=0`。主因是 18 条预测窗口尚未收盘（最早 8-23、多数 8-28/29），
属正常等待期；但存在**结构性缺口**——回填步从不写 `knowledge_features`，会导致 Step 1 在窗口收盘后
**依然永久卡在 0**，无法产出任何学得权重。

**建议（按优先级）**：
1. **先修结构性缺口（必修）**：在 `check_quant_results` / `check_tianji_results` / `save_with_result`
   标记 completed 时，补 `entry['knowledge_features'] = extract_knowledge_features(entry)`。
   否则窗口再怎么收盘，Step 1 永远 no-op，Step 2 无从谈起。
2. **顺手收口 ml_predict**：把 `ml_predict` 纳入窗口回检（或起课即置 `status=pending` 走人工对照），
   并同样补 `knowledge_features`，让那 2 条已收盘样本能被利用。
3. **继续等待窗口收盘**：最早 2026-08-23 起，每日 `--auto` 会陆续结算；建议 8 月底窗口基本全部收盘后
   再跑一次本复查。
4. **暂不要推进 Step 2**：案例库带结果做正负例 CBR + self_evolve 的前提是有已结算的正负样本。
   现在 0 样本，强行 Step 2 无米之炊。先让 (1)(3) 落地、攒够样本，再据"对齐率是否随学得权重上升"
   决定是否进 Step 2。若届时对齐率不升，才回头查特征提取/证据包质量。

---
**傻妞建议**：第 1 项改动很小且是 Step 1 的真正卡点，建议现在就改（3 处各加一行），
不必等窗口收盘。改完可重跑干跑确认口径对齐。要我直接动手吗？
