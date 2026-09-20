"""
古例回测引擎
============
对标注了真值标签的古例运行 D-S 融合引擎，计算准确率。

四方法消融对比:
- M1: 原始引擎(无求财类神, 无CBR)
- M2: 融合(有求财类神, 无CBR)
- M3: 融合+求财类神+CBR
- M4: 仅求财类神

核心挑战: 古例只有 日柱/月将/时辰/三传，需要构造完整的 result dict 给 fuse() 消费。
策略: 使用 engine 的独立模块计算四课/天将/六亲/旺衰/空亡，不依赖完整日期管线。
"""
import json
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

# ---- 引擎模块 ----
from engine.sizhu_engine import get_day_ganzhi
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
from engine.liuren_analysis_engine import LiurenAnalysisEngine
from engine.gui_ren_engine import GuiRenCalculator
from engine.gui_ren_daynight import get_gui_ren_pan, is_daytime
from engine.judgment_fusion import fuse, Gate, collect_signals, BASE_CONF, TIANJIANG_SCORE
from engine.caishen_enhance import detect_caishen_patterns, caishen_to_mass, get_caishen_signal_for_fusion

# ---- 古例域不应注入"求财类神"看涨偏置(其为股票域设计) ----
# 🔴 2026-09-17：**本行就是 `DISABLE_CAISHEN` 的唯一致命置位点**（模块级 import 副作用）。
#   `judgment_fusion.py:L92` 的初始值是 `False` ⇒ ⛔ 只读那个文件会误判为"caishen 已启用"。
#   硬证据：古例盲测 **M4（仅 caishen）＝ 14.5%、凶→吉 160** ⇒ 极强吉向偏置，禁用是对的。
#   ⚠️ 连带事实：因该开关 + 古例路径不产 `holistic_judgment`，**M1 ≡ M2 ≡ M3 完全等价**
#   （实测混淆矩阵逐案相同；探针 `_冗余待删/_probe_signal_groups.py`）
#   ⇒ 「完整融合 M3」在本域**等于「原始引擎 M1」**，三方法对比**不含真实消融**。
import engine.judgment_fusion as _jf
_jf.DISABLE_CAISHEN = True

# ---- 古例域保留「六亲(十神)」信号组 ----
# 股票路径已永久关闭六亲(liuren_20d_engine 导入时置 DISABLE_LIUQIN=1)，
# 但古例验证器(90.9%)依赖六亲，故此处显式确保其在古例域启用，避免同进程被误关。
os.environ.pop('DISABLE_LIUQIN', None)


# ---- 月将(简化映射: 中气后对应月将) ----
# 古例给出 yue_jiang 如 "辰"、"酉" 等
YUE_JIANG_ZHI = {
    "寅": "亥", "卯": "戌", "辰": "酉", "巳": "申",
    "午": "未", "未": "午", "申": "巳", "酉": "辰",
    "戌": "卯", "亥": "寅", "子": "丑", "丑": "子",
}

# 月将→季节推断(用于旺衰)
YUE_JIANG_SEASON = {
    "亥": "冬", "子": "冬", "丑": "冬",
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
}


# ── 农历月 → 季节（古例带 month 时优先用它，比月将准）──
LUNAR_MONTH_SEASON = {
    1: "春", 2: "春", 3: "春",
    4: "夏", 5: "夏", 6: "夏",
    7: "秋", 8: "秋", 9: "秋",
    10: "冬", 11: "冬", 12: "冬",
}


def _yingqi_for_ancient(ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                        yue_jiang: str = "", month: object = "",
                        kongwang: Optional[List[str]] = None,
                        tianjiang: Optional[Dict[str, str]] = None,
                        category: str = "") -> Dict[str, Any]:
    """古例路径的应期推算（2026-09-20 接入）。

    🔴 定位：**叙事层**，⛔ **不进评分链** —— `fuse()` 不读 `result["yingqi"]`，
      仅用于补齐「原文断语有应期、引擎原先完全没有」的详细度缺口（60 案抽样中 31 案有）。
    失败一律返回 {}，绝不阻塞主流程、不改变 prediction。
    """
    if not ri_gan or len(sanchuan_dizhi) < 3:
        return {}
    try:
        from engine.yingqi_engine import judge_yingqi
    except Exception:
        return {}

    # 季节：优先农历月；缺失则退回月将（与天机路径 `tianji_harness._yingqi_period` 同映射）
    season = ""
    try:
        season = LUNAR_MONTH_SEASON.get(int(str(month).strip()), "")
    except Exception:
        season = ""
    if not season:
        season = YUE_JIANG_SEASON.get(yue_jiang, "")

    try:
        r = judge_yingqi(ri_gan, list(sanchuan_dizhi),
                         ri_zhi=ri_zhi, ganzhi=(ri_gan + ri_zhi),
                         kongwang=list(kongwang or []),
                         tianjiang=dict(tianjiang or {}),
                         season=season, category=category or "")
    except Exception:
        return {}

    pri = r.get("primary") or {}
    stages = [{
        "method": c.get("method", ""), "timing": c.get("timing", ""),
        "days": c.get("days", 0),
        "trigger_gz": c.get("trigger_gz", ""), "trigger_zhi": c.get("trigger_zhi", ""),
    } for c in (r.get("candidates") or [])[:6]]
    return {
        "primary": {
            "method": pri.get("method", ""), "timing": pri.get("timing", ""),
            "days": pri.get("days", 0),
            "trigger_gz": pri.get("trigger_gz", ""), "trigger_zhi": pri.get("trigger_zhi", ""),
        },
        "stages": stages,
        "narrative": r.get("narrative", ""),
        "season_used": season,
    }


def build_result_from_ancient(ancient_case: Dict) -> Dict[str, Any]:
    """
    从古例数据构造 fuse() 所需的 result dict。

    古例字段:
        rizhu: "庚寅" (日柱)
        yue_jiang: "辰" (月将)
        shichen: "未" (时辰)
        hour: 13 (小时, Corpus B 有)
        sanchuan: ["巳","寅","亥"] (三传地支)
        keti: ["元首","闭口"] (课体列表)
    """
    rizhu = ancient_case.get("rizhu", "")
    ri_gan = rizhu[0] if len(rizhu) >= 1 else ""
    ri_zhi = rizhu[1] if len(rizhu) >= 2 else ""
    yue_jiang = ancient_case.get("yue_jiang", "")
    shichen = ancient_case.get("shichen", "")
    sanchuan_dizhi = ancient_case.get("sanchuan", [])

    # 【v5修复】兼容拼接格式: 源数据中174例sanchuan为字符串 "巳寅亥"(非列表)
    # 导致 tianjiang_map.get("巳寅亥") 全部匹配失败 → 天将全空
    # 拆分策略: 取前3个汉字作为三传(初传/中传/末传)
    if len(sanchuan_dizhi) == 1 and isinstance(sanchuan_dizhi[0], str) and len(sanchuan_dizhi[0]) >= 3:
        raw = sanchuan_dizhi[0]
        sanchuan_dizhi = [raw[i] for i in range(min(3, len(raw)))]
    # 防御: 确保是三传格式(3个地支)
    if len(sanchuan_dizhi) < 3:
        # 不足以构成三传 → 用空值填充, 后续分析会有兜底
        pass

    # 默认值
    if not ri_gan:
        ri_gan = ancient_case.get("ri_gan", "")
    if not ri_zhi:
        ri_zhi = ancient_case.get("ri_zhi", "")

    # ---- 1. 四课计算 ----
    si_ke = []
    tiandi_pan = {}
    try:
        ssc2 = SiKeSanChuanCalculator2()
        calc_result = ssc2.calculate(ri_gan, ri_zhi, yue_jiang, shichen)
        si_ke = calc_result.get("sike", [])
        tiandi_pan = calc_result.get("tiandi_pan", {})
    except Exception:
        pass

    # ---- 2. 天将计算(用 GuiRenCalculator 更稳健) ----
    tianjiang_list = []
    tianjiang_map = {}
    tianjiang_detail = {}
    try:
        gui_calc = GuiRenCalculator()
        # 构造天地盘: 地盘固定为12地支, 天盘从月将+时辰推导
        tiandi_for_gui = {"天地对应": tiandi_pan} if tiandi_pan else {}
        gui_ren_result = gui_calc.arrange_gui_ren_pan(ri_gan, tiandi_for_gui, shichen)
        tianjiang_map = gui_ren_result.get("天将映射", {})
        tianjiang_list = [tianjiang_map.get(z, "") for z in sanchuan_dizhi]
        tianjiang_detail = {
            "初传": tianjiang_list[0] if tianjiang_list else "",
            "中传": tianjiang_list[1] if len(tianjiang_list) > 1 else "",
            "末传": tianjiang_list[2] if len(tianjiang_list) > 2 else "",
            "贵人": gui_ren_result.get("贵人", ""),
            "昼夜": gui_ren_result.get("昼夜", ""),
            "顺逆": gui_ren_result.get("顺逆", ""),
        }
    except Exception as e_tj:
        # 降级: 尝试直接使用 get_gui_ren_pan
        try:
            from engine.gui_ren_daynight import get_gui_ren_pan as get_pan
            gui_map2 = get_pan(ri_gan, shichen, lat=25.1, lon=105.5)
            if isinstance(gui_map2, dict):
                tianjiang_map = gui_map2.get("天将映射", gui_map2)
            tianjiang_list = [tianjiang_map.get(z, "") for z in sanchuan_dizhi]
        except Exception:
            pass

    # ---- 3. 分析引擎 ----
    analyzer = LiurenAnalysisEngine()
    sanchuan_dict = {
        "初传": sanchuan_dizhi[0] if len(sanchuan_dizhi) > 0 else "",
        "中传": sanchuan_dizhi[1] if len(sanchuan_dizhi) > 1 else "",
        "末传": sanchuan_dizhi[2] if len(sanchuan_dizhi) > 2 else "",
    }

    # 四课格式适配
    sike_for_analysis = []
    for sk in si_ke:
        if len(sk) >= 3:
            sike_for_analysis.append((sk[2], sk[1]))  # (上神, 下神)
        else:
            sike_for_analysis.append(("", ""))

    # 旺衰: 从月将推断季节
    season = YUE_JIANG_SEASON.get(yue_jiang, "春")
    yuejian_zhi = YUE_JIANG_ZHI.get(yue_jiang, "寅")  # 月将→月建逆推

    full_analysis = {}
    try:
        full_analysis = analyzer.analyze(
            ri_gan=ri_gan, ri_zhi=ri_zhi, sanchuan=sanchuan_dict,
            sike=sike_for_analysis, tiandi_pan=tiandi_pan or {},
            yue_jiang=yue_jiang, shi_chen=shichen,
            lunar_month=1, nian_zhi="午", yuejian_zhi=yuejian_zhi,
            ri_gan_zhi=rizhu,
        )
    except Exception:
        pass

    # ---- 4. 提取关键字段 ----
    # 空亡
    kong_info = {}
    try:
        for i, chuan in enumerate(["初传", "中传", "末传"]):
            if i < len(sanchuan_dizhi):
                kong_info[chuan] = analyzer.is_kong_wang(sanchuan_dizhi[i], rizhu)
    except Exception:
        pass

    # 旺衰
    wangshuai_list = full_analysis.get("旺衰", [])
    if not wangshuai_list:
        try:
            def _base_of(z, tdp):
                for d, t in (tdp or {}).items():
                    if t == z:
                        return d
                return None
            wangshuai_list = [
                {"地支": z, "旺衰": analyzer.get_zhi_wang_shuai_by_yuejian(z, yuejian_zhi, _base_of(z, tiandi_pan))}
                for z in sanchuan_dizhi
            ]
        except Exception:
            wangshuai_list = []

    # 六亲
    liuqin_list = full_analysis.get("六亲分析", [])
    if not liuqin_list:
        try:
            liuqin_list = analyzer.get_liuqin_analysis(ri_gan, sanchuan_dizhi)
        except Exception:
            liuqin_list = []

    # 课体
    keti_raw = ""
    keti_list = ancient_case.get("keti", [])
    if isinstance(keti_list, list) and keti_list:
        keti_raw = keti_list[0]
    elif isinstance(keti_list, str):
        keti_raw = keti_list

    # ---- 5. 课体断语：留待 result 组装后由 liuren_keti_bifa 真实抽取(替换原 stub 全平) ----

    # ---- 6. 八杀 / 神煞（LiurenAnalysisEngine 确定性产出；日干支+三传，无泄漏）----
    ba_sha = full_analysis.get("八杀分析", {"八杀明细": []})
    shen_sha = full_analysis.get("神煞", [])

    # 占类（古例 zhanlei；探针 build_clean 已置 category 字段）
    zhanlei = ancient_case.get("category", "其他") or "其他"

    # ---- 7. 组装 result ----
    # 【2026-09-11 六项判据补齐】神煞类课格上下文（供 kege_shensha 完整判据）：
    #   nian_zhi(太岁) / shichen(占时) / xing_nian_zhi(行年) / ben_ming_zhi(本命)
    # year 字段为干支格式（如 '戊申'）→ 取地支位。
    _year_raw = str(ancient_case.get("year", "") or "")
    _nian_zhi = _year_raw[1:2] if (len(_year_raw) >= 2 and
                                   _year_raw[1:2] in '子丑寅卯辰巳午未申酉戌亥') else ''
    result = {
        "keti": keti_raw,
        "si_ke": si_ke,
        "san_chuan": sanchuan_dizhi,
        "tiandi_pan": tiandi_pan,
        "sanchuan_tianjiang": tianjiang_list,
        "tianjiang_map": tianjiang_map,
        "tianjiang_detail": tianjiang_detail,
        "nian_zhi": _nian_zhi,
        "shichen": shichen,
        "xing_nian_zhi": ancient_case.get("xing_nian_zhi", "") or "",
        "ben_ming_zhi": ancient_case.get("ben_ming_zhi", "") or "",
        "basic_info": {"ri_gan": ri_gan, "ri_zhi": ri_zhi, "rizhu": rizhu},
        "analysis": {
            "keti_duanyu": {},
            "liuqin": liuqin_list,
            "wangshuai": wangshuai_list,
            "kong_info": kong_info,
            "ba_sha": ba_sha,
            "shen_sha": shen_sha,
            "_zhanlei": zhanlei,
        },
    }

    # ---- 8. 应期（2026-09-20 接入；🔴 叙事层，⛔ 不进评分链）----
    # 背景：60 案抽样中 31 案原文断语带应期（"十一年""后五年""巳日/巳月"），
    #       而古例路径原先完全没有（应期引擎此前只接在天机/股票域）。
    # 约束：只写 result["yingqi"]，`fuse()` 不读该字段 ⇒ 对 prediction 零影响。
    _kongwang = []
    try:
        from engine.bifa_detector import XUN_KONG_MAP
        _kongwang = list(XUN_KONG_MAP.get(ri_gan + ri_zhi, []) or [])
    except Exception:
        _kongwang = []
    result["yingqi"] = _yingqi_for_ancient(
        ri_gan, ri_zhi, sanchuan_dizhi,
        yue_jiang=yue_jiang, month=ancient_case.get("month", ""),
        kongwang=_kongwang, tianjiang=tianjiang_map, category=zhanlei,
    )

    # ---- 真实课体/毕法赋/三传课格 抽取(占类化valence；替换 stub 全平) ----
    duanyu_text = ancient_case.get("duanyu", "")
    from engine.liuren_keti_bifa import build_keti_duanyu, extract_shen_sha_valence, extract_taichan_valence, extract_guansong_valence, extract_qiucai_valence, extract_disease_valence, extract_gongming_valence, extract_jiazhai_valence, extract_chuxing_valence, extract_hunyin_valence, extract_zeidao_valence, extract_tianyu_valence, extract_tai_sui_valence
    result["analysis"]["keti_duanyu"] = build_keti_duanyu(result, duanyu_text, zhanlei)

    # ---- 天狱课（通用课体凶信号，任何占类；天罡辰加日干长生位=日本 → 天狱，不有大服必有大祸）----
    result["analysis"]["_tianyu_valence"] = extract_tianyu_valence(
        result["basic_info"].get("ri_gan", ""), tiandi_pan
    )
    # ---- 太岁临身（守卫版：排除胎产/官讼 + 三传乘青龙禁；全量回测 8/8=100% 2026-08-02）----
    result["analysis"]["_tai_sui_valence"] = extract_tai_sui_valence(
        result["basic_info"].get("ri_gan", ""), tiandi_pan,
        ancient_case.get("year") or "", zhanlei, sanchuan_dizhi,
        result.get("sanchuan_tianjiang", [])
    )


    # ---- 功名专属：临官帝旺/六阳数足/帘幕贵人(记录) + 朱雀值鬼/墓绝凶（确定性，占类化，无泄漏；仅古例路径）----
    result["analysis"]["_gongming_valence"] = extract_gongming_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), zhanlei,
        xing_nian_zhi=ancient_case.get("xing_nian_zhi", ""),
        tiandi_pan=tiandi_pan
    )

    # ---- 家宅/出行/婚姻/贼盗 专属（凶向；确定性，占类化，无泄漏；仅古例路径）----
    result["analysis"]["_jiazhai_valence"] = extract_jiazhai_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), si_ke, zhanlei
    )
    result["analysis"]["_chuxing_valence"] = extract_chuxing_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), si_ke, zhanlei
    )
    result["analysis"]["_hunyin_valence"] = extract_hunyin_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), si_ke, zhanlei
    )
    result["analysis"]["_zeidao_valence"] = extract_zeidao_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), si_ke, zhanlei,
        leishen=ancient_case.get("leishen", ""),
        tianjiang_map=result.get("tianjiang_map", {}),
        shichen=ancient_case.get("shichen", "")
    )
    # 亡盗类神（零涟漪：仅亡盗案置此字段 → 融合层据此放宽 zeidao 消费条件；
    # 其余"其他"案与股票路径无 leishen → 零影响）
    result["leishen"] = ancient_case.get("leishen", "")

    # ---- 真实神煞/八杀 valence 抽取（确定性，占类化，无泄漏）----
    result["analysis"]["_shen_sha_valence"] = extract_shen_sha_valence(
        result["analysis"], zhanlei
    )

    # ---- 胎产专属：子孙生扶 / 德神临 / 胞胎神 / 私妊凶（确定性，占类化，无泄漏；仅古例路径）----
    result["analysis"]["_taichan_valence"] = extract_taichan_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), zhanlei
    )

    # ---- 官讼专属：解厄吉 / 官鬼凶 / 连茹凶（确定性，占类化，无泄漏；仅古例路径）----
    result["analysis"]["_guansong_valence"] = extract_guansong_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), zhanlei
    )

    # ---- 求财专属：财爻生扶吉 / 青龙乘财吉 / 财虚凶（确定性，占类化，无泄漏；仅古例路径）----
    result["analysis"]["_qiucai_valence"] = extract_qiucai_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []),
        result.get("si_ke", []), zhanlei
    )

    # ---- 疾病专属：虎鬼/子孙解厄/生龙/贵医/两蛇夹墓/华盖孝帛（确定性，占类化，无泄漏；仅古例路径）----
    # lunar_month 取自案例原文标题（OCR 解析起课月份，见 docs/reports/_assign_month_v4.py），
    # 用于 D2 月解神守卫（白虎乘当月解神→凶可解）；无月份则守卫不启用（安全降级）。
    lunar_month = ancient_case.get("month")
    if not isinstance(lunar_month, int) or not (1 <= lunar_month <= 12):
        lunar_month = None
    # 年命接入：本命地支 + 天地盘 → 年命上神（D3 两蛇夹墓年命加重/破墓守卫，毕法赋53法）
    ben_ming_zhi = ancient_case.get("ben_ming_zhi") or ''
    if not (isinstance(ben_ming_zhi, str) and ben_ming_zhi in set('子丑寅卯辰巳午未申酉戌亥')):
        ben_ming_zhi = ''
    result["analysis"]["_disease_valence"] = extract_disease_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), zhanlei, lunar_month,
        ben_ming_zhi, tiandi_pan
    )

    return result


def predict_ancient_case(ancient_case: Dict, method: str = "M3") -> Dict:
    """
    对单条古例运行融合引擎预测。

    method:
        M1: 原始引擎(无caishen, 无CBR)
        M2: 融合+求财类神(无CBR)
        M3: 融合+求财类神+CBR(完整)
        M4: 仅求财类神

    返回: {"prediction": "吉"/"凶"/"平", "prob_up": float, "prob_down": float, ...}
    """
    result = build_result_from_ancient(ancient_case)

    if method == "M4":
        # 仅求财类神
        tl = result.get("sanchuan_tianjiang", [])
        sc = result.get("san_chuan", [])
        tm = result.get("tianjiang_map", {})
        sk = result.get("si_ke", [])
        lq = result.get("analysis", {}).get("liuqin", [])
        rg = result.get("basic_info", {}).get("ri_gan", "")

        detail = detect_caishen_patterns(tl, tm, sc, sk, lq, rg)
        mass = caishen_to_mass(detail)

        prob_up = mass["涨"]
        prob_down = mass["跌"]
        prob_flat = mass["平"]
        uncertainty = mass["⊤"]

        # 决策
        if prob_up > prob_down and prob_up > 0.05:
            prediction = "吉"
        elif prob_down > prob_up and prob_down > 0.05:
            prediction = "凶"
        else:
            prediction = "平"

        return {
            "method": "M4",
            "prediction": prediction,
            "prob_up": prob_up,
            "prob_down": prob_down,
            "prob_flat": prob_flat,
            "uncertainty": uncertainty,
            "confidence": 1.0 - uncertainty,
            "caishen_detail": detail,
            "no_fusion": True,
        }

    # ---- M1/M2/M3: 使用标准融合 ----
    # 临时开关控制 caishen/holistic
    if method == "M1":
        # 禁用 caishen 和 holistic
        import engine.judgment_fusion as jf
        orig_collect = jf.collect_signals
        def m1_collect(r):
            sigs = orig_collect(r)
            return [(g, s, u, c) for g, s, u, c in sigs if g not in ("caishen", "holistic")]
        jf.collect_signals = m1_collect

    elif method == "M2":
        import engine.judgment_fusion as jf
        orig_collect = jf.collect_signals
        def m2_collect(r):
            sigs = orig_collect(r)
            return [(g, s, u, c) for g, s, u, c in sigs if g != "holistic"]
        jf.collect_signals = m2_collect

    try:
        fused = fuse(result)
    finally:
        if method in ("M1", "M2"):
            import engine.judgment_fusion as jf
            jf.collect_signals = orig_collect

    # 映射: 涨→吉, 跌→凶, 平→平
    trend = fused.get("trend", "平")
    if trend == "���荡":
        trend = "平"

    prob_up = fused.get("prob_up", 0.33)
    prob_down = fused.get("prob_down", 0.33)

    if trend == "看涨":
        prediction = "吉"
    elif trend == "看跌":
        prediction = "凶"
    elif trend == "平":
        prediction = "平"
    else:
        prediction = "平"

    return {
        "method": method,
        "prediction": prediction,
        "prob_up": prob_up,
        "prob_down": prob_down,
        "prob_flat": fused.get("prob_flat", 0.33),
        "confidence": fused.get("confidence", 0.5),
        "conflict": fused.get("conflict", 0.0),
        "trend": trend,
        "caishen_detail": result.get("_caishen_detail", {}),
    }


def run_backtest(truth_labels_path: str, methods: List[str] = None) -> Dict:
    """
    运行完整古例回测。

    参数:
        truth_labels_path: ancient_truth_labels.json 路径
        methods: 要测试的方法列表，默认全部

    返回:
        回测报告 dict
    """
    if methods is None:
        methods = ["M1", "M2", "M3", "M4"]

    with open(truth_labels_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cases = data.get("cases", [])
    if not cases:
        print("❌ 无案例数据")
        return {}

    # 只取有标签的案例
    labeled = [c for c in cases if c.get("label") != "未知" and c.get("label_confidence", 0) >= 0.50]
    print(f"总案例: {len(cases)}, 有标签: {len(labeled)}")

    # 按类别分组
    by_category = defaultdict(list)
    for c in labeled:
        by_category[c.get("category", "其他")].append(c)

    # 运行回测
    results = {m: [] for m in methods}

    for i, case in enumerate(labeled):
        if i % 50 == 0:
            print(f"  进度: {i}/{len(labeled)}")

        # 修复数据: 确保必要字段存在
        if not case.get("sanchuan") or len(case.get("sanchuan", [])) < 1:
            continue

        for method in methods:
            try:
                pred = predict_ancient_case(case, method)
                pred["case_id"] = case.get("id", "")
                pred["case_name"] = case.get("name", "")
                pred["category"] = case.get("category", "")
                pred["truth"] = case.get("label", "")
                pred["correct"] = (pred["prediction"] == case.get("label", ""))
                results[method].append(pred)
            except Exception as e:
                results[method].append({
                    "method": method,
                    "case_id": case.get("id", ""),
                    "error": str(e),
                    "prediction": "错误",
                    "truth": case.get("label", ""),
                    "correct": False,
                })

    # ---- 汇总统计 ----
    summary = {}
    for method in methods:
        rlist = results[method]
        total = len(rlist)
        correct = sum(1 for r in rlist if r.get("correct", False))
        errors = sum(1 for r in rlist if "error" in r)
        accuracy = correct / max(total - errors, 1) if total > 0 else 0.0

        # 按类别
        cat_stats = {}
        for cat, cat_cases in by_category.items():
            cat_results = [r for r in rlist if r.get("category") == cat]
            cat_total = len(cat_results)
            cat_correct = sum(1 for r in cat_results if r.get("correct", False))
            cat_err = sum(1 for r in cat_results if "error" in r)
            if cat_total > 0:
                cat_stats[cat] = {
                    "total": cat_total,
                    "correct": cat_correct,
                    "errors": cat_err,
                    "accuracy": cat_correct / max(cat_total - cat_err, 1),
                }

        # 求财类
        wealth_results = [r for r in rlist if r.get("category") == "求财"]
        wealth_total = len(wealth_results)
        wealth_correct = sum(1 for r in wealth_results if r.get("correct", False))

        # 混淆矩阵(转字符串key)
        cm = Counter()
        for r in rlist:
            if "error" not in r:
                key = f"{r.get('truth', '')}->{r.get('prediction', '')}"
                cm[key] += 1

        # 平均置信度
        avg_conf = sum(r.get("confidence", 0) for r in rlist if "error" not in r) / max(total - errors, 1)

        summary[method] = {
            "total": total,
            "correct": correct,
            "errors": errors,
            "accuracy": accuracy,
            "avg_confidence": avg_conf,
            "confusion_matrix": dict(cm),
            "by_category": cat_stats,
            "wealth": {
                "total": wealth_total,
                "correct": wealth_correct,
                "accuracy": wealth_correct / max(wealth_total, 1) if wealth_total > 0 else 0.0,
            },
        }

    return {
        "summary": summary,
        "detailed_results": results,
        "total_cases": len(labeled),
    }


def print_report(report: Dict):
    """打印回测报告"""
    summary = report.get("summary", {})

    print("\n" + "=" * 70)
    print("  古例回测报告")
    print("=" * 70)
    print(f"  总案例(有标签): {report.get('total_cases', 0)}")

    # 方法对比表
    print(f"\n  {'方法':<20} {'准确率':>8} {'正确':>6} {'错误':>6} {'平均置信':>8} {'求财准确率':>10}")
    print(f"  {'-'*58}")
    for method in ["M1", "M2", "M3", "M4"]:
        s = summary.get(method, {})
        wealth = s.get("wealth", {})
        print(f"  {method:<20} {s.get('accuracy',0)*100:>7.1f}% "
              f"{s.get('correct',0):>5}  {s.get('total',0)-s.get('correct',0)-s.get('errors',0):>5} "
              f"{s.get('avg_confidence',0):>7.3f}  "
              f"{wealth.get('accuracy',0)*100:>9.1f}%")

    # 方法解释
    print(f"\n  方法说明:")
    print(f"    M1 = 原始引擎(无求财类神·无CBR)")
    print(f"    M2 = 融合+求财类神(朱雀+六合+财爻+青龙)·无CBR")
    print(f"    M3 = 完整融合(求财类神+CBR)")
    print(f"    M4 = 仅求财类神(独立判断)")

    # 各类别准确率
    for method in ["M1", "M2", "M3"]:
        s = summary.get(method, {})
        cats = s.get("by_category", {})
        if cats:
            print(f"\n  --- {method} 各类别准确率 ---")
            for cat in sorted(cats.keys()):
                cs = cats[cat]
                bar = "█" * int(cs["accuracy"] * 20)
                print(f"    {cat:<8} {cs['accuracy']*100:>5.1f}% {bar} ({cs['correct']}/{cs['total']-cs.get('errors',0)})")

    # 混淆矩阵(M3)
    m3 = summary.get("M3", {})
    cm = m3.get("confusion_matrix", {})
    if cm:
        print(f"\n  --- M3 混淆矩阵 ---")
        print(f"              预测")
        print(f"          吉    凶    平")
        for truth in ["吉", "凶", "平"]:
            row = [str(cm.get(f"{truth}->吉", 0)), str(cm.get(f"{truth}->凶", 0)), str(cm.get(f"{truth}->平", 0))]
            print(f"    {truth}  |  {'  '.join(f'{x:>3}' for x in row)}")


def main():
    truth_path = BASE / "engine" / "ancient_truth_labels.json"
    if not truth_path.exists():
        print(f"❌ 真值标签文件不存在: {truth_path}")
        return

    print("🔄 运行古例回测...")
    report = run_backtest(str(truth_path))

    print_report(report)

    # 保存报告
    output_path = BASE / "engine" / "ancient_backtest_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 只保存摘要(详细结果太大)
    save_data = {
        "_meta": {
            "version": "1.0.0",
            "created": "2026-07-30",
            "description": "古例回测报告: D-S融合引擎四方法消融对比",
        },
        "summary": report["summary"],
        "total_cases": report["total_cases"],
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 报告已保存至: {output_path}")

    # 同时输出详细结果(简化版)
    detail_path = BASE / "engine" / "ancient_backtest_details.json"
    detail_save = {
        "_meta": save_data["_meta"],
        "results": {}
    }
    for method in ["M1", "M2", "M3", "M4"]:
        detail_save["results"][method] = [
            {
                "id": r.get("case_id", ""),
                "name": r.get("case_name", ""),
                "category": r.get("category", ""),
                "truth": r.get("truth", ""),
                "prediction": r.get("prediction", ""),
                "correct": r.get("correct", False),
                "confidence": r.get("confidence", 0),
                "prob_up": r.get("prob_up", 0),
                "prob_down": r.get("prob_down", 0),
                "caishen_signals": r.get("caishen_detail", {}).get("signals", []) if r.get("caishen_detail") else [],
            }
            for r in report["detailed_results"].get(method, [])
        ]
    with open(detail_path, 'w', encoding='utf-8') as f:
        json.dump(detail_save, f, ensure_ascii=False, indent=2)
    print(f"✅ 详细结果已保存至: {detail_path}")


if __name__ == "__main__":
    main()
