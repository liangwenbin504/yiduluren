"""
全局配置 — 仪度六壬择日 · 量化交易系统
========================================

双子系统并行架构
────────────────
量化预测与六壬预测为两个独立的子系统，并行运行、数据隔离：
  量化子系统：11维因子评分驱动买卖 → _memory/quant_portfolio.json
  六壬子系统：六壬一课多断信号驱动买卖 → _memory/liuren_portfolio.json

两者从同一选股池出发（score >= 50），各自独立决策、独立建仓平仓、
独立记账，互不干涉。2~3年后直接��比两张成绩单。

六壬预测当前仍处训练验证期 —— 3个核心不确定性：
  1. 个股类象定义模糊（一课多断的"类神"映射尚未标准化）
  2. 系统仍在训练阶段，历史精准度尚未通过验证
  3. 六壬推理链（课体→股市映射）尚不完善

因此六壬子系统独立运行、独立验证，不影响量化子系统的任何决策。
"""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ── 项目根路径 ──
BASE = Path(__file__).parent
MEMORY = BASE / "_memory"
os.makedirs(MEMORY, exist_ok=True)

# ── 常用文件路径 ──
STOCK_REPORTS = MEMORY / "stock_reports"
ML_PREDICTIONS = MEMORY / "ml_predictions.json"
STOCK_PREDICTIONS = MEMORY / "stock_predictions.json"

# ── 工具函数 ──
def get_beijing_now():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def classify_trend(score):
    if score > 3: return '涨'
    elif score < -3: return '跌'
    return '平'


# ═════════════════════════════════════════════════════════════
# 达标择日 · 内测免费时段配置
# 在此时间范围内（含起止日）进入达标择日页面 → 一律免费放行，
# 不再要求扫码付费/会员/每日限免。服务上线前请把"已结束"改回 False。
# 留空任一值则内测时段关闭（仅本地IP/白名单手机号免费）。
# ═════════════════════════════════════════════════════════════
BETA_WINDOW_ENABLED = True     # 总开关
BETA_WINDOW_START = "2026-08-24"   # 内测免费开始日期（含）
BETA_WINDOW_END   = "2026-09-30"   # 内测免费结束日期（当天仍免费）
BETA_CODE  = "8888"            # 内测验证码（前端"内测验证"页提交用）
BETA_MOBILES = {}              # 追加内测手机号白名单 {"13800000000": "张三"}

# ── 双子系统模式 ──
DUAL_SUBSYSTEM_MODE = True  # 双轨并行（量化 + 六壬 各自独立运行）

# ── 六壬定位（不影响量化子系统决策）──
LIUREN_REFERENCE_ONLY = True

# ── 验证观察期起点 ──
LIUREN_OBSERVATION_START = "2026-07-28"

# ── 目标验证周期（年）──
LIUREN_VALIDATION_YEARS = 3

# ── 量化子系统配置 ──
QUANT_BUY_THRESHOLD = 50       # 选股器 score >= 50 才进入量化建仓池

# ── 六壬子系统配置 ──
LIUREN_MIN_CONFIDENCE = 0.40   # 六壬置信度下限（低于此值不采纳预测）
LIUREN_BUY_THRESHOLD = 50      # 选股器 score >= 50 才进入六壬预测池（与量化同起跑线）
