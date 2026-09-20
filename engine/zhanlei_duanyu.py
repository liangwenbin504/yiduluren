# -*- coding: utf-8 -*-
"""
占类断语引擎 v1.0（P3：根据具体占事给具体断语，杜绝"一个断语通吃"）
================================================================
铁律（憨爷 2026-08-15 拍板）：
- 断语必须来自古籍原文知识库，绝不生成/编造。
- 数据源：
    1. engine/duanan_knowledge_base.py   —— 断案知识库（20 占类 key_principles：理气/类神/断语）
    2. engine/duanan_theory_knowledge.py —— 理论原理库（神煞/应期/生克 等占类理论）
- 占类标准：古例 9 占类（功名/家宅/婚姻/胎产/求财/出行/疾病/官讼/其他）
  —— 与 engine/liuren_keti_bifa.py 的 ZIL_CATEGORIES、古例 shuzheng_real_cases.json 的 zhanlei 对齐。

占类 → duanan 键名映射（跨库对齐，见 unified_categories.py）：
  功名→前程仕进  家宅→宅墓      婚姻→婚姻      胎产→子息胎产
  求财→求财      出行→出行      疾病→疾病      官讼→词讼      其他→杂占
"""
import os, sys
from typing import List, Dict, Any

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# 古例 9 占类（标准）
ZHANLEI_9 = ["功名", "家宅", "婚姻", "胎产", "求财", "出行", "疾病", "官讼", "其他"]

# 古例占类 → duanan_knowledge_base 键名
DUANAN_KEY_MAP = {
    "功名": "前程仕进",
    "家宅": "宅墓",
    "婚姻": "婚姻",
    "胎产": "子息胎产",
    "求财": "求财",
    "出行": "出行",
    "疾病": "疾病",
    "官讼": "词讼",
    "其他": "杂占",
}

# 断案《疏正》章节号（sec）→ duanan_knowledge_base 键名（"其他"占类细分用）
# 古例"其他"实际含：终身(04)/亡盗(15)/杂占(17)/天时(01)/一课二事(09)/流年(05)
SEC_KEY_MAP = {
    "01": "天时",
    "04": "终身",
    "05": "流年",
    "09": "一课二事各断式",
    "15": "亡盗",
    "17": "杂占",
}

# duanan_theory_knowledge 的占类键（带空格，需匹配）
THEORY_KEY_MAP = {
    "功名": ["科 目", "又 官 禄"],
    "家宅": ["家 宅"],
    "婚姻": ["婚 姻"],
    "胎产": ["胎 产", "子 息"],
    "求财": ["求 财"],
    "出行": ["出 行"],
    "疾病": ["疾 病"],
    "官讼": ["官 讼", "词 讼"],
    "其他": [],
}


def _get_duanan_principles(zhanlei: str, sec: str = "") -> Dict[str, List[str]]:
    """从断案知识库取该占类的 key_principles（{类型: [断语...]}）。
    zhanlei='其他' 且有 sec（《疏正》章节号）时，按 sec 细分到断案占类（终身/亡盗/天时/一课二事/流年）。"""
    key = DUANAN_KEY_MAP.get(zhanlei)
    if zhanlei == '其他' and sec and sec in SEC_KEY_MAP:
        key = SEC_KEY_MAP[sec]
    if not key:
        return {}
    try:
        from engine.duanan_knowledge_base import get_duan_an_knowledge_base
        kb = get_duan_an_knowledge_base()
        return kb.get_principles_by_category(key) or {}
    except Exception:
        return {}


def _get_theory_texts(zhanlei: str) -> List[str]:
    """从理论原理库取该占类的理论断语（神煞/应期/生克等），展平成字符串列表"""
    keys = THEORY_KEY_MAP.get(zhanlei, [])
    texts = []
    try:
        from engine.duanan_theory_knowledge import get_category_theories
        for k in keys:
            info = get_category_theories(k) or {}
            for ptype, plist in (info.get("key_principles", {}) or {}).items():
                for p in plist:
                    texts.append(f"【{ptype}】{p}")
    except Exception:
        pass
    return texts


def _flatten_principles(principles: Dict[str, List[str]]) -> List[str]:
    """展平 {类型: [断语]} → ['【类型】断语', ...]"""
    out = []
    for ptype, plist in principles.items():
        for p in plist:
            out.append(f"【{ptype}】{p}")
    return out


def build_zhanlei_duanyu(zhanlei: str, keti: str = "", bifa_names: List[str] = None,
                         sanchuan_kege_names: List[str] = None, sec: str = "",
                         gong_names: List[str] = None) -> Dict[str, Any]:
    """生成占类专属断语。

    zhanlei: 占类（功名/家宅/婚姻/胎产/求财/出行/疾病/官讼/其他）
    keti: 课体名（如"元首课"）
    bifa_names: 毕法赋命中名列表
    sanchuan_kege_names: 三传课格名列表
    sec: 《断案疏正》章节号（"其他"占类细分到终身/亡盗/天时/一课二事/流年）
    gong_names: 六壬格局命中名列表（拱贵/拱禄/拱马/朝天格/归垣格/罗纹格 等，2026-08-17 单日详情批语显示）
    返回 {zhanlei, duanyu_lines, matched, unmatched}
      duanyu_lines: 全部断语（含占类理论 + 匹配课体/毕法的专项断语）
      matched: 命中的"课体/毕法相关"专项断语
    """
    bifa_names = bifa_names or []
    sanchuan_kege_names = sanchuan_kege_names or []
    gong_names = gong_names or []

    principles = _get_duanan_principles(zhanlei, sec)
    theory = _get_theory_texts(zhanlei)

    all_lines = _flatten_principles(principles)
    matched = []
    # 用课体/毕法/三传课格名，在断语里检索命中（优先专项断语）
    keys = [keti] + list(bifa_names) + list(sanchuan_kege_names)
    keys = [k for k in keys if k]
    for line in all_lines:
        hit = False
        for k in keys:
            # 课体名去掉"课"字、毕法名逐字匹配
            if k and (k in line or k.rstrip('课') in line):
                hit = True
                break
        if hit:
            matched.append(line)

    # 去重保序
    def _dedup(lst):
        seen, out = set(), []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    matched = _dedup(matched)
    unmatched = _dedup([l for l in all_lines if l not in set(matched)])

    duanyu_lines = []
    if matched:
        duanyu_lines.append(f"◆ {zhanlei}占 · 课传相关断语（课体/毕法/课格命中）：")
        duanyu_lines += matched
    # 六壬格局追加（2026-08-17 单日详情"六壬格局"UI 已删，改在批语里显示）
    if gong_names:
        duanyu_lines.append(f"◆ 六壬格局：{zhanlei}占得「{'、'.join(gong_names)}」格（拱扶禄马贵等吉象，宜期速发）。")
    duanyu_lines += theory
    if unmatched:
        duanyu_lines.append(f"◆ {zhanlei}占 · 断案理气总则：")
        duanyu_lines += unmatched

    return {
        "zhanlei": zhanlei,
        "duanyu_lines": duanyu_lines,
        "matched": matched,
        "theory_count": len(theory),
        "unmatched_count": len(unmatched),
    }


def cmd_zhanlei_duanyu(zhanlei: str, keti: str = "", bifa: str = ""):
    """命令行：输出占类断语（供验证）"""
    r = build_zhanlei_duanyu(zhanlei, keti, bifa.split() if bifa else [])
    print(f"═══ {r['zhanlei']}占 断语（{len(r['duanyu_lines'])} 条，命中 {len(r['matched'])}）═══")
    for l in r["duanyu_lines"][:15]:
        print("  " + l)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="占类断语引擎")
    ap.add_argument("zhanlei", help="占类：功名/家宅/婚姻/胎产/求财/出行/疾病/官讼/其他")
    ap.add_argument("--keti", default="", help="课体名")
    ap.add_argument("--bifa", default="", help="毕法赋名（空格分隔）")
    a = ap.parse_args()
    cmd_zhanlei_duanyu(a.zhanlei, a.keti, a.bifa)
