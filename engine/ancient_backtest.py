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
from typing import Dict, List, Any, Optional, Tuple

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


# ══════════════════════════════════════════════════════════════════════════════
# 类神(leishen)来源解析（2026-09-20 憨爷拍板：人工预填 → **自推**）
#
# 🔴 背景：218 语料里 `leishen` 只有 12 案非空（全亡盗章），且是**人工从原文读出**的
#    ⇒ 引擎不自推 ⇒ 等于喂答案。`judgment_fusion.py:L402` 有一条
#      「占类=其他 + 带 leishen + 吉向 ⇒ 置信×1.5」的亡盗专属提权在消费它。
#
# 本函数把来源切到**自推**：用 `engine/shuzheng_suozhan.json` 里人工精校的
# `suozhan_desc`（所占之事描述，**不含吉凶答案**）驱动 `leishen_from_ancient_text`
# （⛔ 禁 LLM 兜底，避免写脏 data/leishen_llm_cache.json）。
#
# 三档口径（实测 M3，朴素基线同为 85.5%）：
#   auto（默认，自推）→ **89.9%**，净 +4.3pp   ← 现行
#   human（人工预填） → 91.8%，净 +6.3pp      ← 旧口径，含泄漏
#   none（不给类神）  → 87.9%，净 +2.4pp
# ⇒ 切换后数字下降**不是退步**，是剔掉喂答案的部分；自推净贡献 +1.9pp 为真实能力。
#
# 回滚：环境变量 `LEISHEN_SOURCE=human|none|auto`（默认 auto）。
# ⛔ 表外案（928 案语料／股票路径等）**保持原行为**（透传原 leishen）⇒ 零涟漪。
# ══════════════════════════════════════════════════════════════════════════════
LEISHEN_SOURCE = os.environ.get("LEISHEN_SOURCE", "auto").strip().lower()
_SUOZHAN_TABLE = None
_DIZHI = set("子丑寅卯辰巳午未申酉戌亥")


def _load_suozhan_table() -> Dict[str, Dict]:
    global _SUOZHAN_TABLE
    if _SUOZHAN_TABLE is None:
        try:
            _p = os.path.join(BASE, "engine", "shuzheng_suozhan.json")
            with open(_p, encoding="utf-8") as f:
                _SUOZHAN_TABLE = {i.get("case_id"): i
                                  for i in (json.load(f).get("items") or [])}
        except Exception:
            _SUOZHAN_TABLE = {}
    return _SUOZHAN_TABLE


def _resolve_leishen(ancient_case: Dict) -> str:
    """按 LEISHEN_SOURCE 解析本例的类神地支（⛔ 只接受单字地支，过滤『朱雀』等天将名）"""
    src = LEISHEN_SOURCE
    if src == "none":
        return ""
    if src == "human":
        return ancient_case.get("leishen", "")
    _cid = ancient_case.get("id") or ancient_case.get("case_id") or ""
    _it = _load_suozhan_table().get(_cid)
    if not _it:
        # 表外案（928 案语料 / 股票路径）：保持原行为 ⇒ 零涟漪
        return ancient_case.get("leishen", "")
    try:
        from engine.leishen_engine import leishen_from_ancient_text
        _z = leishen_from_ancient_text(_it.get("suozhan_desc", ""),
                                       force_lost=True, allow_llm=False)
    except Exception:
        _z = ""
    return _z if (len(_z) == 1 and _z in _DIZHI) else ""


def _fangwei_shumu_for_ancient(ri_zhi: str, sanchuan_dizhi: List[str], si_ke,
                               tiandi_pan: Dict[str, str], leishen: str = "") -> Dict[str, Any]:
    """方位 + 道里数（2026-09-20 接入；🔴 叙事层，⛔ 不进评分链）。

    引擎：根目录 `fangwei_engine_v7`（2026-08-18 建，**此前从未接进古例路径** ——
    与应期同类的"引擎已写好、只是没接线"）。每个函数自带原文出处：
      · 十二支方位：子北/丑寅东北/卯东/辰巳东南/午南/未申西南/酉西/戌亥西北
        （§六畜走失14·184"未为羊…故在西南"、§亡盗15·200"卯为类神，加巳，是在地户东南上也"、
         §亡盗15·199"物在南方炉灶前"、§宅墓02·127"未加卯…往东方寻之必见"）
      · 类神所加方：吴稼云「类神未见，则以初传为方向类神」（§200 初传寅加辰=东南，果于东南寻见）
      · 驿马方位：§出行访谒11·153"寅马…行动于东北者"
      · 道里数：洛书支数 子午9/丑未8/寅申7/卯酉6/辰戌5/巳亥4
        相加 §017"巳四、子九，并成十三年"｜相乘 §188"亥四丑八，去此三十二里"、§072"午九酉六，六九五十四"
        拼接 §终身04·105"亥四、酉六，主四十六岁亡"｜重复 §宅墓02·013"亥四数，课中四个亥，四四一十六年"
    ⛔ 洛书数表已跨书坐实（疏正 219 案实测 + 壬占汇选 21/21=100%），邵彦和**只用支数不用天干数**。
    """
    out: Dict[str, Any] = {"fangwei": {}, "shumu": {}}
    try:
        import fangwei_engine_v7 as fv
    except Exception:
        return out
    sc = [z for z in (sanchuan_dizhi or [])[:3] if z]
    try:
        out["fangwei"]["sanchuan"] = [{"zhi": z, "fang": fv.fangwei_of_zhi(z)} for z in sc]
        out["fangwei"]["leishen_jia"] = fv.leishen_jia_fang(
            leishen or "", si_ke or [], tiandi_pan or {}, sc)
        out["fangwei"]["yima"] = fv.yima_fangwei(ri_zhi)
    except Exception:
        pass
    try:
        out["shumu"]["zhi_number"] = [{"zhi": z, "n": fv.ZHI_SUZHI.get(z)} for z in sc
                                      if z in getattr(fv, "ZHI_SUZHI", {})]
        if len(sc) >= 2:
            out["shumu"]["sum"] = fv.daoli_zhi_sum(*sc)
            out["shumu"]["cheng"] = fv.zhi_cheng(sc[0], sc[-1])
        elif sc:
            out["shumu"]["sum"] = fv.daoli_zhi_sum(sc[0])
    except Exception:
        pass
    return out


# ============================================================================
# 转折加厚：六亲层 + 课格层（2026-09-20 二补）
# ============================================================================
# 🔴 六亲定性**不是**股票域 LIUQIN_SCORE（那边 官鬼=+1「主力动作偏多」）。
#    古例域以《通解》原文为准：
#      · 通解_上.txt:3370「初传为官鬼、中传为父母、末传为妻财 ⇒ **先阻、中助、末得**」
#        ⇒ 官鬼=阻(凶)／父母=助(吉)／妻财=得(吉)
#      · 通解_上.txt:3375「发用为兄弟，代表兄弟、朋友事或**阻力是非**」⇒ 兄弟=凶
#      · 通解_上.txt:4145「子孙克官鬼…子为杀鬼之神，主有良医解救」但
#        通解_上.txt:3138「系脱气…课象凶以日鬼脱耗论」⇒ 子孙**以脱气为主**＝−1
#        （占病/忧患则解厄为例外，本层不细分）
_LIUQIN_ANCIENT_SCORE = {"妻财": 1, "父母": 1, "官鬼": -1, "兄弟": -1, "子孙": -1}
_TEN_GOD_TO_LIUQIN = {
    "正官": "官鬼", "七杀": "官鬼",
    "正财": "妻财", "偏财": "妻财",
    "正印": "父母", "偏印": "父母",
    "食神": "子孙", "伤官": "子孙",
    "比肩": "兄弟", "劫财": "兄弟",
}
_GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
               "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_ZHI_WUXING = {"亥": "水", "子": "水", "寅": "木", "卯": "木",
               "巳": "火", "午": "火", "申": "金", "酉": "金",
               "辰": "土", "戌": "土", "丑": "土", "未": "土"}
_GAN_JIGONG = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
               "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
_WX_MU = {"木": "未", "火": "戌", "土": "辰", "金": "丑", "水": "辰"}
_WX_CHANGSHENG = {"木": "亥", "火": "寅", "金": "巳", "水": "申", "土": "申"}
_WX_KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}      # 我克
_WX_KE_ME = {v: k for k, v in _WX_KE.items()}                              # 克我


def _liuqin_layer(ri_gan: str, sanchuan_dizhi: List[str]) -> List[Dict[str, Any]]:
    """六亲层（古例域定性）：三传各地支对日干 → 六亲名 + 吉凶分（原文见表上注释）。"""
    sc = list(sanchuan_dizhi or [])[:3]
    if not ri_gan or ri_gan not in _GAN_WUXING:
        return [{"zhi": z, "liuqin": "", "score": 0} for z in sc]
    try:
        from engine.calibration import liuqin_of
    except Exception:
        return [{"zhi": z, "liuqin": "", "score": 0} for z in sc]
    out = []
    for z in sc:
        try:
            lq = _TEN_GOD_TO_LIUQIN.get(liuqin_of(ri_gan, z), "")
        except Exception:
            lq = ""
        out.append({"zhi": z, "liuqin": lq, "score": _LIUQIN_ANCIENT_SCORE.get(lq, 0)})
    return out


def _kege_for_zhuanzhe(si_ke, ri_gan: str, ri_zhi: str, sanchuan_dizhi: List[str],
                       tiandi_pan: Optional[Dict[str, str]] = None
                       ) -> Tuple[List[str], Dict[str, Any]]:
    """课格层（叙事层专用）：只判《通解》有白纸黑字判据的四种。

    判据出处 data/_tongjie_ocr/通解_上.txt:5136（课体口诀）：
        「乱首支加干克干，干加支上被克同」｜「斩关魁罡日辰用」
        「天狱墓作死囚用，天罡日本之宫躔」｜「赘婿支临干被克，干加支上克支通」
    天狱第二支「天罡加日本」实例：通解_下.txt §022「斗罡系日本加亥」、§025「天罡加日本」。
    ⛔ 只用这四条，**不造**没有原文印证的课格。
    """
    names: List[str] = []
    sk = list(si_ke or [])
    if len(sk) < 4:
        return names, {}

    def _shang(e):
        if isinstance(e, dict):
            return str(e.get("上神", "") or "")
        try:
            return str(e[1]) if len(e) >= 2 else ""   # 引擎格式 [课名, 上神, 下神, 天将]
        except Exception:
            return ""

    gan_shang, zhi_shang = _shang(sk[0]), _shang(sk[2])
    gw = _GAN_WUXING.get(ri_gan, "")
    zw = _ZHI_WUXING.get(ri_zhi, "")
    ji = _GAN_JIGONG.get(ri_gan, "")
    det = {"干上神": gan_shang, "支上神": zhi_shang, "日干寄宫": ji,
           "日干五行": gw, "日支五行": zw}

    bei_ke = _WX_KE_ME.get(gw) == zw          # 支克干（我受克）
    shangmen = gan_shang == ri_zhi and bei_ke  # 支加干克干
    ziqu = zhi_shang == ji and bei_ke          # 干加支被支克
    if shangmen and ziqu:
        names.append("乱首")        # 干支同宫（日支==寄宫）⇒ 二义同归
    elif shangmen:
        names.append("上门乱首")
    elif ziqu:
        names.append("自取乱首")
    if gan_shang == ri_zhi and _WX_KE.get(gw) == zw:
        names.append("赘婿")        # 支临干被干克
    sc = list(sanchuan_dizhi or [])
    if sc and sc[0] in ("辰", "戌") and sc[0] in (gan_shang, zhi_shang):
        names.append("斩关")        # 魁罡加日辰发用
    tdp = dict(tiandi_pan or {})
    if sc and _WX_MU.get(gw) and sc[0] == _WX_MU.get(gw):
        names.append("天狱")        # 墓作死囚用
    elif _WX_CHANGSHENG.get(gw) and tdp.get(_WX_CHANGSHENG.get(gw)) == "辰":
        names.append("天狱")        # 天罡加日本
    return names, det


def _zhuanzhe_for_ancient(sanchuan_dizhi: List[str],
                          sanchuan_tianjiang: List[str],
                          kongwang: Optional[List[str]] = None,
                          ri_gan: str = "",
                          ri_zhi: str = "",
                          si_ke: Optional[List] = None,
                          tiandi_pan: Optional[Dict[str, str]] = None,
                          wangshuai: Optional[List] = None) -> Dict[str, Any]:
    """转折（事态走向：先吉后凶／先凶后吉／始终…；2026-09-20 新建 + 同日加厚）。

    🔴 定位：**叙事层**，⛔ **不进评分链** —— 只描述"事态如何变化"，不改吉凶方向。

    三层判据（全确定性、全可复核）：
      L1 **天将**：三传天将吉凶分（`judgment_fusion.TIANJIANG_SCORE`，与评分链**同一张表**：
         贵人/青龙/六合/太常/天后/太阴=+1，朱雀=0，勾陈/螣蛇/玄武/天空=−1，白虎=−2）。
         原文印证 通解_上.txt:4208「虎头蛇尾重还轻，**龙末虎初凶变吉**」。
      L2 **六亲**：三传地支对日干 → 官鬼/父母/妻财/子孙/兄弟，按《通解》**古例域**定性
         （⛔ 不是股票域 LIUQIN_SCORE）。原文印证 通解_上.txt:3370
         「初传为官鬼、中传为父母、末传为妻财 ⇒ **先阻、中助、末得**」。
      L3 **课格**：乱首／斩关／天狱／赘婿（课体口诀 通解_上.txt:5136）。
         🔴 **乱首会翻 mode**：通解_下.txt:8394「大凡上门乱首……
         经曰：**旺相相生灾未发，死囚刑克便灾临**」⇒ 其凶**应时令而后发**＝**先吉后凶**。
      + **旬空修正**：§宅墓02·035「可望先凶后吉。奈何**寅是空亡**，所以不能引进，
        **见生不生，反成凶咎**」。

    合成规则（避免臆造）：
      · L1 有信号（初/末天将分非全 0）⇒ mode 取 L1；L2 只作「张力」附注。
      · L1 无信号（初末皆 0）⇒ mode 仍为「平平无变」，**不用 L2 顶替**
        （实测：6 案原文 ground truth 下 L1=3/6 最优，L2=2/6、L4旺衰=2/6、
        任两层相加均降至 1/6 ⇒ 合成反而更差，见 _冗余待删/_exp_zhuanzhe_layers.py）。
    """
    empty: Dict[str, Any] = {}
    try:
        from engine.judgment_fusion import TIANJIANG_SCORE
    except Exception:
        return empty
    sc = list(sanchuan_dizhi or [])[:3]
    tj = list(sanchuan_tianjiang or [])[:3]
    if len(sc) < 3 or len(tj) < 3:
        return empty

    def _mode_of(a: int, c: int, zero_word: str = "平平无变") -> str:
        if a > 0 and c < 0:
            return "先吉后凶"
        if a < 0 and c > 0:
            return "先凶后吉"
        if a > 0 and c > 0:
            return "始终吉"
        if a < 0 and c < 0:
            return "始终凶"
        return zero_word

    # ---- L1 天将 ----
    def _s(zhi, jiang):
        v = TIANJIANG_SCORE.get(jiang, 0)
        return {"zhi": zhi, "jiang": jiang, "score": v,
                "xing": "吉" if v > 0 else ("凶" if v < 0 else "平")}

    a, b, c = _s(sc[0], tj[0]), _s(sc[1], tj[1]), _s(sc[2], tj[2])
    va, vb, vc = a["score"], b["score"], c["score"]
    jiang_mode = _mode_of(va, vc)

    # ---- L2 六亲 ----
    lq = _liuqin_layer(ri_gan, sc)
    for i, item in enumerate(lq):
        (a, b, c)[i].update({"liuqin": item.get("liuqin", ""),
                             "lq_score": item.get("score", 0)})
    la, lb, lc = (x.get("lq_score", 0) for x in (a, b, c))
    lq_mode = _mode_of(la, lc, zero_word="")
    # 🔴 L2 只作「张力」附注，**不参与判 mode**（实测合成更差，见函数 docstring）
    tension = ""
    if lq_mode and lq_mode != jiang_mode and jiang_mode != "平平无变":
        tension = (f"；⚠ 六亲走向相反（初{a.get('liuqin','') or '—'}→末{c.get('liuqin','') or '—'}，"
                   f"主{lq_mode}）")
    mode = jiang_mode

    # L4 旺衰：**只描述不判定**（实测作判据会降分）
    ws_txt = ""
    if wangshuai:
        ws_list = [str((w or {}).get("旺衰", "")) for w in list(wangshuai)[:3]]
        if any(ws_list):
            ws_txt = f"；旺衰（月令）：初{ws_list[0] or '—'}→中{ws_list[1] if len(ws_list)>1 else '—'}→末{ws_list[2] if len(ws_list)>2 else '—'}"

    # ---- 旬空修正（§035「寅是空亡…见生不生，反成凶咎」）----
    kw = set(kongwang or [])
    kong_flags = [z in kw for z in sc]
    if kong_flags[2] and mode in ("先凶后吉", "始终吉"):
        mode = f"{mode}（末传空亡，转吉落空→反成凶咎）"
    elif kong_flags[2] and mode in ("先吉后凶", "始终凶"):
        mode = f"{mode}（末传空亡，凶亦落空）"
    elif kong_flags[0]:
        mode = f"初传{sc[0]}空亡（起始之力落空）→ {mode}"

    # ---- L3 课格 ----
    kege, kege_det = _kege_for_zhuanzhe(si_ke, ri_gan, ri_zhi, sc, tiandi_pan)
    kege_note = ""
    if any("乱首" in k for k in kege):
        # 🔴 原文铁证：通解_下.txt:8394「旺相相生灾未发，死囚刑克便灾临」⇒ 灾**后发**
        mode = "先吉后凶"
        kege_note = ("；课格乱首（下犯上）：通解_下8394「旺相相生灾未发，死囚刑克便灾临」"
                     "⇒ 其凶应时令而后发，故**先吉后凶**")
    if "天狱" in kege:
        kege_note += "；课格天狱（墓作死囚用／天罡加日本）：§022「不有大服，必有大祸」"
    if "斩关" in kege:
        kege_note += "；课格斩关（魁罡加日辰发用）：关梁闭塞，君子利有攸往 ⇒ 先阻后通"
    if "赘婿" in kege:
        kege_note += "；课格赘婿（支临干被克）：屈从于人"

    mid = ""
    if vb != 0 and ((vb > 0 and va < 0 and vc < 0) or (vb < 0 and va > 0 and vc > 0)):
        mid = "，中传生变"
    desc = (f"初传{sc[0]}乘{tj[0]}（{a['xing']}）→ 中传{sc[1]}乘{tj[1]}（{b['xing']}）"
            f"→ 末传{sc[2]}乘{tj[2]}（{c['xing']}），主{mode}{mid}")
    if any(x.get("liuqin") for x in (a, b, c)):
        desc += (f"；六亲：初{a.get('liuqin','') or '—'}→中{b.get('liuqin','') or '—'}"
                 f"→末{c.get('liuqin','') or '—'}")
    desc += tension
    desc += ws_txt
    desc += kege_note
    if any(kong_flags):
        desc += f"；空亡：{'、'.join(f'{z}空' for z, f in zip(sc, kong_flags) if f)}"
    return {
        "初": a, "中": b, "末": c, "mode": mode,
        "liuqin": {"初": a.get("liuqin", ""), "中": b.get("liuqin", ""), "末": c.get("liuqin", "")},
        "kege": kege, "kege_detail": kege_det,
        "kong": kong_flags, "desc": desc,
        "src": ("§前程仕进03·046「此课先失后得，先虚后实」；"
                "§宅墓02·035「望先凶后吉」（+「寅是空亡…见生不生，反成凶咎」⇒ 旬空修正）；"
                "§终身04·118「主日后因犯官长，断勒归家」（⇒ 乱首时序修正）。"
                "判据＝L1三传天将（TIANJIANG_SCORE，与评分链同表，通解上4208「龙末虎初凶变吉」）"
                "＋L2六亲（通解上3370「官鬼→阻／父母→助／妻财→得」）"
                "＋L3课格（通解上5136课体口诀；乱首时序见通解下8394）＋旬空修正"),
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
    # 🔧 2026-09-20：兼容**原始语料**字段名 day_ganzhi（218 案语料用这个，不是 rizhu）。
    #    漏了这层兜底 ⇒ ri_gan/ri_zhi 全空 ⇒ 下面四课/天地盘计算静默失败（si_ke=[]、
    #    tiandi_pan={}）而**无任何报错**，是隐形 bug。
    if not rizhu:
        rizhu = ancient_case.get("day_ganzhi", "") or ancient_case.get("rizhu_ganzhi", "")
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
    # 🔧 2026-09-20：原本 `except: pass` 全静默 ⇒ 排盘失败时四课/天地盘**悄无声息变空**，
    #    下游（analyzer 六亲/八杀、课格层「天罡加日本」）全部静默退化，极难排查。
    #    ⇒ 保留兜底不炸，但**把原因留在 result 里**（result["_calc_errors"]），可观测。
    _calc_errors = []
    try:
        ssc2 = SiKeSanChuanCalculator2()
        calc_result = ssc2.calculate(ri_gan, ri_zhi, yue_jiang, shichen)
        si_ke = calc_result.get("sike", [])
        tiandi_pan = calc_result.get("tiandi_pan", {})
        if not si_ke:
            _calc_errors.append(
                f"四课为空(ri_gan={ri_gan!r} ri_zhi={ri_zhi!r} 月将={yue_jiang!r} 时={shichen!r})")
        if not tiandi_pan:
            _calc_errors.append("天地盘为空")
    except Exception as _e:
        _calc_errors.append(f"排盘异常 {type(_e).__name__}: {_e}")

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
        # 🔧 排盘/四课异常留痕（原为静默 pass ⇒ 空四课不可见，见上方注释）
        "_calc_errors": _calc_errors,
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
    # 🔴 类神来源：2026-09-20 起默认走**自推**（LEISHEN_SOURCE=auto），见 _resolve_leishen
    leishen_used = _resolve_leishen(ancient_case)
    result["analysis"]["_zeidao_valence"] = extract_zeidao_valence(
        result["basic_info"].get("ri_gan", ""),
        result["basic_info"].get("ri_zhi", ""),
        sanchuan_dizhi, result.get("sanchuan_tianjiang", []), si_ke, zhanlei,
        leishen=leishen_used,
        tianjiang_map=result.get("tianjiang_map", {}),
        shichen=ancient_case.get("shichen", "")
    )
    # 亡盗类神（零涟漪：仅亡盗案置此字段 → 融合层据此放宽 zeidao 消费条件；
    # 其余"其他"案与股票路径无 leishen → 零影响）
    result["leishen"] = leishen_used
    # 叙事层：标注类神来源，便于核对（⛔ 不进评分链）
    result["leishen_source"] = LEISHEN_SOURCE

    # ---- 方位 / 道里数 / 转折（2026-09-20 接入；🔴 叙事层，⛔ 不进评分链）----
    # 背景：详细度审计（权威映射，218 案）显示原文 **126 案带转折、63 案带方位/数目**，
    #       而古例路径**全无**结构化字段（覆盖度均 0%）。
    #       · 方位/数目的引擎 `fangwei_engine_v7` 2026-08-18 就写好了 —— **只是从未接线**
    #         （与应期同一类"引擎已写好、没接进古例路径"）。
    #       · 转折无现成字段 ⇒ 新建，由三传天将吉凶走向**确定性推导**
    #         （用 `judgment_fusion.TIANJIANG_SCORE`，与评分链**同一张表** ⇒ 口径一致）。
    # 约束：只写 result["fangwei"]/["shumu"]/["zhuanzhe"]，`fuse()` 不读 ⇒ 对 prediction 零影响。
    # 🔴 叙事层绝不允许炸主链路：任何异常一律降级为空，不影响 prediction
    try:
        _fw = _fangwei_shumu_for_ancient(ri_zhi, sanchuan_dizhi, si_ke, tiandi_pan, leishen_used)
        result["fangwei"] = _fw.get("fangwei", {})
        result["shumu"] = _fw.get("shumu", {})
        result["zhuanzhe"] = _zhuanzhe_for_ancient(
            sanchuan_dizhi, result.get("sanchuan_tianjiang", []),
            kongwang=_kongwang, ri_gan=ri_gan, ri_zhi=ri_zhi,
            si_ke=si_ke, tiandi_pan=tiandi_pan, wangshuai=wangshuai_list)
    except Exception:
        result.setdefault("fangwei", {})
        result.setdefault("shumu", {})
        result.setdefault("zhuanzhe", {})

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
