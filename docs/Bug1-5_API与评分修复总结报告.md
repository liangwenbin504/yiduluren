# Bug1-5 修复总结报告

* **项目**：仪度六壬择日系统

* **修复日期**：2026-08-31 \~ 2026-09-01

* **状态**：✅ 全部完成并验证通过

* **涉及模块**：API 接口层（api\_server.py）、评分引擎层（yidu\_liuren\_yaojue.py）、批量择日层（batch\_zeri\_optimizer.py）、前端展示（stock\_dashboard.html）

***

## 一、概述

本次修复针对系统 **4 个 API 接口调用错误** 和 **1 个评分系统口径分裂问题**，按用户拍板方案逐一解决。

两类根因：

1. **API 层**：接口调用方使用了不存在的类方法 / 参数错位，未做「公历日期 → 六壬排盘参数（日干/日支/月将/时辰）」换算。
2. **评分层**：`analyze_yidu_full` 中「凶在日时(内)」罚分因 `is_ideal` 条件被永久吞掉；且单课分析（analyze\_yidu\_full）与批量择日（calculate\_new\_score）存在两套评分口径。

***

## 二、Bug 明细

### Bug 1：`/api/comprehensive_score` 接口 500（综合评分）

| 项  | 内容                                                                                                                                 |
| -- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 问题 | 调用不存在的 `scorer.score(data)` 方法，接口 500                                                                                              |
| 根因 | `comprehensive_scorer.py` 真实方法为 `calculate_comprehensive_score(douhou_score, yanqin_score, daliuren_score)`，接口调用方捏造了 `score(data)` |
| 修复 | 改为调用真实方法，并支持 `douhou/yanqin/daliuren_weight` 自定义权重参数                                                                               |
| 验证 | 默认权重 `0.4×90 + 0.3×70 + 0.3×80 = 81` ✅                                                                                             |

### Bug 2：`/api/guiren` 接口 500（贵人盘）

| 项  | 内容                                                                                                           |
| -- | ------------------------------------------------------------------------------------------------------------ |
| 问题 | 调用不存在的 `calculator.calculate()` 方法，接口 500                                                                    |
| 根因 | `gui_ren_engine.py` 真实方法为 `arrange_gui_ren_pan(ri_gan, tian_pan, shichen)`；调用方缺少日期→排盘参数换算                    |
| 修复 | 新增 `_date_to_paipan_params` 辅助函数（`get_sizhu`→日干/日支、`get_yuejiang_by_date`→月将、时辰映射），再调用 `arrange_gui_ren_pan` |
| 验证 | 返回 200：贵人亥、天将 12 项 ✅                                                                                         |

### Bug 3：`/api/daliuren`、`/api/tiandipan` 接口 500（四课三传/天地盘）

| 项  | 内容                                                                                                                        |
| -- | ------------------------------------------------------------------------------------------------------------------------- |
| 问题 | 以 `(year, month, day, hour)` 时间参数直调 V2 引擎，参数错位，接口 500                                                                     |
| 根因 | `sike_sanchuan_engine.py` 需 `calculate(ri_gan, ri_zhi, yuejiang, shichen)` / `get_tiandi_pan(yuejiang, shichen)`，接口未做干支换算 |
| 修复 | 经 `_date_to_paipan_params` 换算后正确调用两个引擎方法                                                                                  |
| 验证 | 返回 200：tiandipan 月将巳/12 项、daliuren 日丁丑/四课 4 组 ✅                                                                           |

### Bug 4：斗首「凶在日时(内)」罚分永不生效（评分核心逻辑）

| 项  | 内容                                                                                                                  |
| -- | ------------------------------------------------------------------------------------------------------------------- |
| 问题 | 凶课（贪官/破鬼临日时）靠拱格、到山到向堆分仍可 90+「上上吉」，凶课误判为吉                                                                            |
| 根因 | `analyze_yidu_full` 中 `is_ideal` 为真才应用 `jixiong_check['score']`；而「凶在日时(内)」出现时 `is_ideal` 必为 False → **-15 罚分被永久吞掉** |
| 修复 | 移除 `is_ideal` 条件，正负分均生效（`jx_score>0` 加分 / `<0` 罚分并记录）                                                               |
| 验证 | 贪官日时课 68→53（吉→平）；破鬼日柱课 93 上上吉→78 中吉；正常吉课 75 不受误伤 ✅                                                                  |

### Bug 5：两套评分口径分裂（单课 vs 批量）

| 项          | 内容                                                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------- |
| 问题         | 单课 `analyze_yidu_full` 与批量 `calculate_new_score` 各算各的，同一日课两种分数                                                 |
| 决策         | 用户拍板：**以** **`calculate_new_score`** **为权威骨架** + **斗首凶在内（日时）一定不能用**                                            |
| 修复 ① 统一口径  | `analyze_yidu_full` 重构 = 禄马贵人到山到向权威骨架（`luma_base`）+ 加分项（斗首六想增量 / 三元三武 / 凶在外吉在内 / 拱格 / 活禄马 / 高级课格 / 补元，`bonus`） |
| 修复 ② 一票否决  | `jixiong_check['score'] < 0`（贪官/破鬼临日时）→ 综合分压至 ≤39、grade=不宜、标记 `vetoed`/`veto_reason`                           |
| 修复 ③ 全链路同步 | 4 处调用点（单课接口、批量 `_build_zeri_candidate`、`BatchZeriOptimizer`、开学择日）+ 前端展示口径全部对齐；批量择日命中 veto 直接淘汰候选               |
| 验证         | 5 案例全过：1 例吉课 100 上上吉（骨架 100 + 加分 28）；4 例命中「凶在日时(内)」全部 veto（分=39 不宜）；不变量 `总分 = clamp(骨架+加分)`、三项拆解之和 = 总分 ✅      |

***

## 三、涉及文件

| 文件                               | 修改内容                                                                                                     |
| -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `api_server.py`                  | 新增 `_date_to_paipan_params`；修复 4 个接口（comprehensive\_score / guiren / daliuren / tiandipan）               |
| `engine/yidu_liuren_yaojue.py`   | Bug4 罚分生效；Bug5 统一评分口径 + 一票否决机制；新增返回字段 `luma_base` / `bonus` / `doushou_bonus` / `vetoed` / `veto_reason` |
| `stock_dashboard.py`             | 单课/批量调用传 `shichen`/`ke_ti`；暴露 veto 标记；批量构建候选时 veto 直接淘汰                                                  |
| `engine/batch_zeri_optimizer.py` | Phase3 三项拆解对齐新口径（斗首=加分 / 到向=骨架 / 六壬=差值）；Candidate 新增 `vetoed` 字段，veto 候选直接淘汰                             |
| `school_opening_select.py`       | `analyze_yidu_full` 调用参数同步（`shichen`/`ke_ti`）                                                            |
| `stock_dashboard.html`           | 24山批量优化结果展示对齐「斗首 + 到向 + 六壬」口径（原为计数型展示）                                                                   |
| `_bug5_verify.py`                | Bug5 统一口径与 veto 机制回归测试（验证后已随临时文件清理删除）                                                                    |

***

## 四、相关工程约定

* **API 调用路径**：接口 → 干支换算（`_date_to_paipan_params`）→ 引擎真实方法；不再直接传公历参数。

* **统一评分口径**：`总分 = luma_base（禄马贵人到山到向骨架） + bonus（斗首/拱格/补元等加分）`，clamp 至 \[20, 100]。

* **一票否决**：斗首「凶在日时(内)」→ 综合分 ≤ 39、grade=不宜、候选淘汰。

***

## 五、遗留事项与后续建议

* **遗留**：无（前端展示口径已对齐；根目录临时文件已清理，10138 → 277 个文件）。

* **建议**：

  1. 评分修复后凶课分数下降，批量择日的达标吉期数量会相应变化 —— 建议做一次全量端到端抽样对比，确认吉期数量与分布符合预期。
  2. 一票否决目前仅在 `analyze_yidu_full` 层实现，未来新增独立斗首快筛入口时，需确认同样应用该规则。

