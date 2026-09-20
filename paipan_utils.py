#!/usr/bin/env python3
"""
排盘工具模块 — 双阶段推理链核心支撑
阶段1：从案例数据提取排盘参数 → 引擎计算正确排盘
阶段2：将引擎排盘注入prompt，AI基于正确排盘做推理演绎
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.daliuren_engine import DaLiuRenEngine
from data.斗首择日规则 import TIANJIANG, DIZHI, TIANGAN


# ============================================================
# 已知排盘参数覆盖表
# 格式: {case_id: {ri_gan, ri_zhi, yue_jiang, shi_chen}}
# yue_jiang 直接取月将字符，不经过月份号映射
# ============================================================
PAIPAN_OVERRIDES = {
    "CASE-天时-001": {
        "ri_gan": "甲",
        "ri_zhi": "子",
        "yue_jiang": "亥",
        "shi_chen": "巳"
    },
    "CASE-婚姻-005": {
        "ri_gan": "乙",
        "ri_zhi": "巳",
        "yue_jiang": "戌",
        "shi_chen": "午"
    },
    "CASE-流年-157": {
        "ri_gan": "丙",
        "ri_zhi": "辰",
        "yue_jiang": "卯",
        "shi_chen": "子"
    },
    "CASE-疾病-178": {
        "ri_gan": "己",
        "ri_zhi": "亥",
        "yue_jiang": "午",
        "shi_chen": "未"
    },
    "CASE-宅墓田宅-003": {
        "ri_gan": "丙",
        "ri_zhi": "寅",
        "yue_jiang": "巳",
        "shi_chen": "申"
    },
    "CASE-胎产子息-007": {
        "ri_gan": "丁",
        "ri_zhi": "卯",
        "yue_jiang": "辰",
        "shi_chen": "酉"
    },
    "CASE-胎产子息-160": {
        "ri_gan": "戊",
        "ri_zhi": "辰",
        "yue_jiang": "子",
        "shi_chen": "酉"
    },
}

# 日干对应的天将贵人起法
# 【BUG-FIX 2026-09-11】原 YANG_GUI/YIN_GUI 的 丁(酉/亥)、癸(卯/巳) 昼夜颠倒。
#   权威：《图解六壬大全》第1部 p.364「丙丁猪鸡位（丙丁日昼贵亥，夜贵酉）…
#   壬癸蛇兔藏（壬癸日昼贵巳，夜贵卯）」；《通解·上卷》「甲子日昼贵丑坐酉，夜贵未坐卯」。
#   本文件当前无任何模块导入（standalone），修复为零风险的一致性订正。
YANG_GUI = {
    "甲": "丑", "乙": "子", "丙": "亥", "丁": "亥",
    "戊": "丑", "己": "子", "庚": "丑",
    "辛": "午", "壬": "巳", "癸": "巳"
}
YIN_GUI = {
    "甲": "未", "乙": "申", "丙": "酉", "丁": "酉",
    "戊": "未", "己": "申", "庚": "未",
    "辛": "寅", "壬": "卯", "癸": "卯"
}

# 昼时: 卯→申, 夜时: 酉→寅
ZHOU_SHI = DIZHI[DIZHI.index("卯"):DIZHI.index("申") + 1]


def get_tianjiang_for_dizhi(ri_gan: str, shi_chen: str, tiandi_pan: dict = None) -> dict:
    """计算十二地支各位置对应的天将

    参数:
        ri_gan: 日干
        shi_chen: 时辰  
        tiandi_pan: 天地盘映射 {地盘:天盘}，提供时使用完整贵人落位顺逆规则

    天将顺逆规则:
        - 贵人落地盘在阳位（亥~辰）则顺行
        - 贵人落地盘在阴位（巳~戌）则逆行
    """
    if ri_gan in YANG_GUI:
        gui_dizhi = YANG_GUI[ri_gan]
    else:
        gui_dizhi = YANG_GUI.get(ri_gan, "丑")
    is_zhou = shi_chen in ZHOU_SHI
    if not is_zhou:
        gui_dizhi = YIN_GUI.get(ri_gan, gui_dizhi)

    if tiandi_pan is not None:
        # 完整规则：按贵人落地盘阴阳位置定顺逆
        gui_di_position = None
        for di_zhi, tian_zhi in tiandi_pan.items():
            if tian_zhi == gui_dizhi:
                gui_di_position = di_zhi
                break
        YANG_POSITIONS = ['亥', '子', '丑', '寅', '卯', '辰']
        if gui_di_position and gui_di_position not in YANG_POSITIONS:
            direction = -1  # 阴位逆行
        else:
            direction = 1   # 阳位顺行（含找不到时默认顺行）
    else:
        # 兼容模式：昼夜决定顺逆
        direction = 1 if is_zhou else -1

    gui_idx = DIZHI.index(gui_dizhi)
    result = {}
    for i, dz in enumerate(DIZHI):
        actual_idx = (gui_idx + direction * i) % 12
        result[dz] = TIANJIANG[actual_idx]
    return result


def run_engine_paipan(params: dict) -> dict:
    """运行排盘引擎，直接传月将（V2 权威引擎）

    2026-08-17 清理：由旧 DaLiuRenEngine 切换为 SiKeSanChuanCalculator2
    （与古例/天机起课同源；旧引擎 fa_san_chuan 在反吟/涉害/遥克等场景有差异）。
    """
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    engine = SiKeSanChuanCalculator2()
    yue_jiang = params["yue_jiang"]
    shi_chen = params["shi_chen"]
    ri_gan = params["ri_gan"]
    ri_zhi = params["ri_zhi"]

    r = engine.calculate(ri_gan, ri_zhi, yue_jiang, shi_chen)
    tiandi_pan = r['tiandi_pan']
    san_chuan = r['sanchuan']
    sike_v2 = r['sike']  # [(课名, 上神, 下神, 天将)]
    si_ke = [{'name': n, 'top': s, 'bottom': x} for n, s, x, _ in sike_v2]
    chuan_list = [san_chuan.get('初传', ''), san_chuan.get('中传', ''),
                  san_chuan.get('末传', '')]
    chuan_list = [c for c in chuan_list if c]
    # 禄马贵：标准查表（日干禄/日支驿马/日干贵人），旧引擎此方法仅查表无误
    lu_ma_gui = DaLiuRenEngine().get_lu_ma_gui(ri_gan, ri_zhi)

    tianjiang_map = get_tianjiang_for_dizhi(ri_gan, shi_chen, tiandi_pan)
    chuan_with_tj = []
    for chuan in chuan_list:
        tj = tianjiang_map.get(chuan, "")
        chuan_with_tj.append(f"{chuan}({tj})" if tj else chuan)

    sike_strs = [f"{ke['top']}→{ke['bottom']}" for ke in si_ke]
    guiren_str = "/".join(lu_ma_gui.get("贵人", []))

    return {
        "月将": yue_jiang,
        "占时": shi_chen,
        "日柱": f"{ri_gan}{ri_zhi}",
        "天地盘": tiandi_pan,
        "课体": san_chuan.get("课体", ""),
        "四课": sike_strs,
        "四课简写": "、".join(sike_strs),
        "三传": chuan_list,
        "三传天将": [tianjiang_map.get(c, "") for c in chuan_list],
        "三传带天将": " → ".join(chuan_with_tj),
        "禄马贵": lu_ma_gui,
        "禄马贵简写": f"禄{lu_ma_gui.get('禄','')}、马{lu_ma_gui.get('驿马','')}、贵{guiren_str}"
    }


def format_paipan_reference(engine_result: dict) -> str:
    """将引擎排盘格式化为prompt注入文本"""
    yuejiang = engine_result["月将"]
    shichen = engine_result["占时"]
    rizhu = engine_result["日柱"]
    keti = engine_result["课体"]
    sike_str = engine_result["四课简写"]
    sanchuan_str = engine_result["三传带天将"]
    lmg_str = engine_result["禄马贵简写"]

    return (
        "【排盘参考】（由计算引擎提供，保证正确）：\n"
        f"  日柱：{rizhu}  月将：{yuejiang}  占时：{shichen}\n"
        f"  课体：{keti}\n"
        f"  四课：{sike_str}\n"
        f"  三传：{sanchuan_str}\n"
        f"  禄马贵：{lmg_str}"
    )


def try_extract_paipan_params(case: dict) -> dict:
    """从案例数据中提取排盘参数"""
    case_id = case.get("id", "")
    if case_id in PAIPAN_OVERRIDES:
        return dict(PAIPAN_OVERRIDES[case_id])
    raw_text = case.get("raw_text", "")
    text = raw_text + (case.get("original_prediction", "") or "")
    params = {}
    rg = re.search(r'([甲乙丙丁戊己庚辛壬癸])([子丑寅卯辰巳午未申酉戌亥])日', text)
    if rg:
        params["ri_gan"] = rg.group(1)
        params["ri_zhi"] = rg.group(2)
    yj = re.search(r'([子丑寅卯辰巳午未申酉戌亥])将', text)
    if yj:
        params["yue_jiang"] = yj.group(1)
    sc = re.search(r'([子丑寅卯辰巳午未申酉戌亥])时', text)
    if sc:
        params["shi_chen"] = sc.group(1)
    if all(k in params for k in ["ri_gan", "ri_zhi", "yue_jiang", "shi_chen"]):
        return params
    return None


def get_engine_paipan(case: dict) -> dict:
    """双阶段入口：提取参数 → 引擎计算 → 返回结构化结果"""
    params = try_extract_paipan_params(case)
    if not params:
        return None
    try:
        engine_result = run_engine_paipan(params)
        ref_text = format_paipan_reference(engine_result)
        return {
            "params": params,
            "engine_result": engine_result,
            "reference_text": ref_text
        }
    except Exception as e:
        print(f"  [排盘引擎] {case.get('id','')} 计算失败: {e}")
        return None
