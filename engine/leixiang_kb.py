#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代类象学习闭环 (engine/leixiang_kb.py)
=========================================
【用户拍板 2026-08-25】择日时按类型推演现代类象 → 存历史库 →
记录"应验结果象 vs 推演类象"出入 → 反馈校准 → 叙事越用越具体。

核心设计（用户认可）：
  A. 类象置信度：每条 {象, 次数, 命中率, 来源}（升级 self_evolve_state 思路）
  B. 按择日类型分库：安葬/婚嫁/开业… 分开存（赵师：环境所断，其他环境不能这么断）
  C. 自动对比 + 人工确认双通道（防机器自我强化错误）
  D. 反馈进批语：下次同类择日引用"上次此类应验过××象"
  E. 争议类象标记 △争议，不自动覆盖已验证条目

数据文件：_memory/leixiang_kb.json
  结构：
  {
    "version": 1,
    "by_zeri_type": {
        "安葬": {
            "推演类象": [...],          # 初始推演（来自推演表）
            "历史案例": [
                {"date": "2030-02-28", "shichen": "子", "推演": ["墓地","骨灰"],
                 "应验": ["医院"], "出入": ["墓地→医院"], "确认": false, "note": ""}
            ],
            "类象统计": {"墓地": {"count": 3, "hit": 2, "hit_rate": 0.67, "source": "历史"}}
        }
    }
  }

用法：
    from engine.leixiang_kb import LeixiangKB
    kb = LeixiangKB()
    kb.push_leixiang('安葬', ['墓地', '骨灰'])           # 择日时推演入库
    kb.record_feedback('安葬', date, 推演, 应验, note)   # 用后反馈
    kb.get_narrative('安葬')                             # 批语引用历史
"""
import json
import os
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
MEMORY = BASE / "_memory"
KB_FILE = MEMORY / "leixiang_kb.json"

# ── 各择日类型的初始现代类象推演（来自 docs/现代事物六壬类象推演表.md 方法论）──
# 每类：按"这类事在现代会应什么象"推演（传统象组合），标注来源
INITIAL_LEIXIANG = {
    "安葬": {
        "推演类象": [
            "墓地、骨灰、墓碑、风水堪舆（戌=坟墓/墓库）",
            "祭拜、花圈、亲友（太常=宴席/衣物）",
            "棺木/骨灰盒（卯=舟车/器物，酉=贵重物件）",
            "墓碑刻字（寅=文书/雕刻）",
        ],
        "参考": "戌=坟墓、辰=水库/坟、酉=碑石、卯=器物",
    },
    "婚嫁": {
        "推演类象": [
            "婚宴、喜酒（太常=宴席，亥=酒）",
            "礼服/婚纱（太常=衣物）",
            "车队（卯=车）",
            "彩礼/嫁妆（财=妻财）",
            "证婚/文书（寅=文书/证）",
        ],
        "参考": "六合=婚姻、太常=酒食衣物、卯=车、财=妻",
    },
    "开业": {
        "推演类象": [
            "门面/店铺（巳=门面店铺）",
            "营业执照/合同（寅=文书/契约）",
            "招牌/广告（朱雀=标签/信息）",
            "开张仪式（青龙=喜庆/财帛）",
            "员工/伙计（六合=多人）",
        ],
        "参考": "巳=店铺、青龙=财、朱雀=招牌、六合=合伙",
    },
    "动土修造": {
        "推演类象": [
            "挖掘机/工程（辰=墙/土方，勾陈=田土）",
            "地基/打桩（辰=墙）",
            "建材/砖石（戌=块状/陶瓷）",
            "工人（六合=多人，勾陈=劳力）",
        ],
        "参考": "辰=墙、戌=陶瓷/块、勾陈=田土工程",
    },
    "入宅": {
        "推演类象": [
            "搬家/家具（卯=家具/车）",
            "钥匙/门锁（卯=门户）",
            "乔迁宴（太常=宴席）",
            "家电（巳=电器/电）",
        ],
        "参考": "亥=房屋、卯=门户、巳=电器",
    },
    "出行": {
        "推演类象": [
            "交通工具（卯=车/舟，申=道路/飞机）",
            "行李（申=传送/箱包）",
            "证件/机票（寅=文书/票）",
            "导航/路线（申=道路/传送）",
        ],
        "参考": "申=道路/传送/飞机、卯=车、寅=票证",
    },
    "立碑": {
        "推演类象": [
            "墓碑/碑文（酉=碑石，寅=文书刻字）",
            "石材/雕刻（酉=玉器/贵重，太阴=雕刻）",
            "揭幕仪式（青龙=喜庆）",
        ],
        "参考": "酉=碑石/玉器、太阴=雕刻、寅=文书",
    },
    "作灶": {
        "推演类象": [
            "炉灶/燃气（巳=炉灶）",
            "厨房电器（巳=电器/火）",
            "炊具（午=酒食，酉=锅）",
        ],
        "参考": "巳=炉灶、午=酒食、酉=器物",
    },
}

# ── 现代事物→传统象 对照（供推演时组合；来源见推演表）──
MODERN_MAP = {
    "墓地": "戌（坟墓/墓库）", "骨灰": "戌（墓库）", "墓碑": "酉（碑石）",
    "手机": "卯朱雀+戌网络+巳信息", "银行卡": "朱雀（卡）", "取款机": "朱雀+午虎+亥水",
    "汽车": "卯（车）", "飞机": "申青龙（天空）", "网络": "戌（火库信息）",
    "银行": "戌财库青龙", "贷款": "亥马天后坐金库丑", "交警": "申青龙/勾陈",
    "部队": "亥太常白虎/戌", "医院": "巳天医+白虎病", "药": "卯（药）",
    "房子": "亥（房屋）", "门": "卯（门户）", "墙": "辰（墙）",
    "热水管": "巳螣蛇青龙癸", "电器": "巳（电）", "警察": "勾陈/申青龙",
    "酒": "亥（酒）", "茶具": "酉/太阴（玉器）", "衣服": "太常（衣物）",
    "文件": "寅（文书）", "合同": "寅+六合", "手术": "酉（刀剑）+勾陈",
    "小孩": "亥（小孩）", "怀孕": "午胎地六合", "桃花": "酉/午/卯",
}


# 【2026-09-11】前端传参占位符集合：这些值不得建键（原会累积 '??' / '' 脏键）
_PLACEHOLDER_TYPES = {'', '?', '??', '？', '？？', 'none', 'null', 'undefined', 'nan'}


def _norm_type(t):
    """归一化择日类型。空值/占位符 → 返回 ''（调用方须跳过，不建键）。"""
    s = str(t or '').strip()
    return '' if s.lower() in _PLACEHOLDER_TYPES else s


def _load_kb():
    if KB_FILE.exists():
        try:
            with open(KB_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 1, "by_zeri_type": {}}


def _save_kb(kb):
    KB_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(KB_FILE) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(KB_FILE))


class LeixiangKB:
    """现代类象知识库管理器（推演+存库+对比+校准+置信度）。"""

    def __init__(self):
        self.kb = _load_kb()
        self._ensure_types()

    def _ensure_types(self):
        """确保各择日类型有初始推演类象。"""
        bz = self.kb.setdefault("by_zeri_type", {})
        for t, data in INITIAL_LEIXIANG.items():
            d = bz.setdefault(t, {"推演类象": [], "历史案例": [], "类象统计": {}})
            if not d.get("推演类象"):
                d["推演类象"] = list(data.get("推演类象", []))

    # ── 推演 ──
    def push_leixiang(self, zeri_type, leixiang_list=None, date="", shichen="", source="类象链"):
        """择日时推演现代类象并入库。
        返回：{ok, 已推演, 历史佐证}

        source：类象来源标记（2026-09-11 起统一为「类象链」——驱动源已由按占类写死的
                「初始推演」改为 engine/leixiang_chain 的课象推演候选）。
        """
        # 【2026-09-11 守卫】前端未传/传占位符时不再建键（原会累积 '??' 与 '' 脏键）
        zeri_type = _norm_type(zeri_type)
        if not zeri_type:
            return {"ok": False, "error": "zeri_type 为空或占位符，已跳过",
                    "推演": [], "历史佐证": []}
        self._ensure_types()
        d = self.kb["by_zeri_type"].setdefault(zeri_type, {"推演类象": [], "历史案例": [], "类象统计": {}})
        if not leixiang_list:
            leixiang_list = list(d.get("推演类象", []))
        # 统计出现
        stats = d.setdefault("类象统计", {})
        for lx in leixiang_list:
            key = lx.split("（")[0].strip()
            s = stats.setdefault(key, {"count": 0, "hit": 0, "hit_rate": 0.0, "source": source})
            s["count"] += 1
            s["source"] = source
        _save_kb(self.kb)
        # 历史佐证（批语引用用）
        history = d.get("历史案例", [])[-3:]
        confirmed = [h for h in history if h.get("确认")]
        return {
            "ok": True,
            "zeri_type": zeri_type,
            "推演": leixiang_list,
            "历史佐证": [h.get("应验", "") for h in confirmed],
        }

    # ── 反馈 ──
    def record_feedback(self, zeri_type, date="", shichen="", 推演=None, 应验=None, note="", 确认=False):
        """
        用后反馈：记录"应验结果象 vs 推演类象"出入。
        推演/应验 为字符串列表（类象描述）。
        返回：{ok, 出入列表, 命中率更新}
        """
        # 【2026-09-11 守卫】同 push_leixiang：脏类型不建键
        zeri_type = _norm_type(zeri_type)
        if not zeri_type:
            return {"ok": False, "error": "zeri_type 为空或占位符，已跳过", "出入": [], "案例数": 0}
        self._ensure_types()
        d = self.kb["by_zeri_type"].setdefault(zeri_type, {"推演类象": [], "历史案例": [], "类象统计": {}})
        推演 = 推演 or []
        应验 = 应验 or []
        # 出入对比
        出入 = []
        for y in 应验:
            if y not in 推演:
                出入.append(f"{y}（推演未涉及）")
        for x in 推演:
            if x not in 应验:
                出入.append(f"{x}（未应验）")
        case = {
            "date": date, "shichen": shichen,
            "推演": 推演, "应验": 应验, "出入": 出入,
            "确认": bool(确认), "note": note,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        d.setdefault("历史案例", []).append(case)
        # 更新置信度：确认的应验类象 hit+1
        stats = d.setdefault("类象统计", {})
        if 确认:
            for y in 应验:
                key = y.split("（")[0].strip()
                s = stats.setdefault(key, {"count": 0, "hit": 0, "hit_rate": 0.0, "source": "人工确认"})
                s["count"] += 1
                s["hit"] += 1
                s["hit_rate"] = round(s["hit"] / s["count"], 3)
                s["source"] = "人工确认"
        _save_kb(self.kb)
        return {"ok": True, "出入": 出入, "案例数": len(d.get("历史案例", []))}

    # ── 批语引用 ──
    def get_narrative(self, zeri_type):
        """批语引用：返回该类型历史应验类象（确认过的）与统计，供叙事用。"""
        self._ensure_types()
        d = self.kb["by_zeri_type"].get(zeri_type, {})
        confirmed = [h for h in d.get("历史案例", []) if h.get("确认")]
        parts = []
        if confirmed:
            yans = []
            for h in confirmed:
                for y in h.get("应验", []):
                    if y not in yans:
                        yans.append(y)
            parts.append(f"此类型此前应验类象：{'、'.join(yans)}")
        stats = d.get("类象统计", {})
        hot = sorted(stats.items(), key=lambda kv: -(kv[1].get("hit", 0) or 0))[:3]
        if hot:
            parts.append("高频类象：" + "、".join(f"{k}({v.get('hit',0)}次应验)" for k, v in hot))
        return "；".join(parts) if parts else ""

    # ── 争议标记 ──
    def mark_dispute(self, zeri_type, case_idx, note=""):
        """将某案例标为争议（不覆盖已验证条目）。"""
        d = self.kb["by_zeri_type"].get(zeri_type, {})
        cases = d.get("历史案例", [])
        if 0 <= case_idx < len(cases):
            cases[case_idx]["确认"] = False
            cases[case_idx]["note"] = (cases[case_idx].get("note", "") + f" [争议]{note}").strip()
            _save_kb(self.kb)
            return {"ok": True}
        return {"ok": False, "error": "案例索引越界"}

    def stats(self, zeri_type=None):
        """统计概览。"""
        bz = self.kb.get("by_zeri_type", {})
        if zeri_type:
            d = bz.get(zeri_type, {})
            return {
                "zeri_type": zeri_type,
                "推演类象数": len(d.get("推演类象", [])),
                "历史案例数": len(d.get("历史案例", [])),
                "类象统计数": len(d.get("类象统计", {})),
            }
        return {k: {
            "推演类象数": len(v.get("推演类象", [])),
            "历史案例数": len(v.get("历史案例", [])),
            "类象统计数": len(v.get("类象统计", {})),
        } for k, v in bz.items()}


if __name__ == "__main__":
    import os, sys, tempfile, pathlib
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # 【2026-09-11】自测改用**临时库**：原实现会写生产数据 _memory/leixiang_kb.json，
    # 每跑一次自测就多一条假的"历史案例"，污染置信度闭环。
    KB_FILE = pathlib.Path(tempfile.gettempdir()) / 'leixiang_kb_selftest.json'
    globals()['KB_FILE'] = KB_FILE
    print("== leixiang_kb 自测（临时库，不动生产数据） ==")
    kb = LeixiangKB()
    print("类型:", list(kb.stats().keys()))
    # 模拟：安葬择日推演
    r = kb.push_leixiang("安葬", ["墓地", "骨灰", "墓碑"], date="2030-02-28", shichen="子")
    print("推演:", r["推演"])
    # 模拟：用后反馈（应验与推演有出入）
    r2 = kb.record_feedback("安葬", date="2030-02-28", shichen="子",
                            推演=["墓地", "骨灰", "墓碑"],
                            应验=["墓地", "医院"], 确认=True, note="骨灰未应，应医院（申太阴=医院类）")
    print("反馈出入:", r2["出入"])
    # 批语引用
    print("批语引用:", kb.get_narrative("安葬"))
    print("统计:", kb.stats("安葬"))
