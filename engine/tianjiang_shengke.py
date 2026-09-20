# -*- coding: utf-8 -*-
"""天将生克层（将 × 日干）：《通解》上卷 L2567／L2568「天将生克规则」的落地。

原文（`data/_tongjie_ocr/通解_上.txt`，L＝分卷行号）：
  · **L2566**「以课之【天盘】起贵神之例，【地盘】定顺逆之序」⇒ 天将骑在**天盘**上。
  · **L2567 天将五行性质规定**：「凡壬课吉凶系于天将，五行虽各有所属，而用者**专取天盘乘神决之**。
    如贵人属土，若**乘**亥子则属水矣，生克皆以水论。」
  · **L2568 天将生克规则**：「**生日为吉，虽凶将亦为吉；克日为凶，虽吉将亦为凶**，紧要不离『生』『克』二字。
    **吉将喜生扶，忌克制；凶将反此**。更察**乘神所加盘之神**，生克、旺相休囚，喜则宜旺相，忌则宜休囚也。」

🔴🔴 **乘 ≠ 临（本文件的核心口径 · 搞反则全错）**
  | 术语 | 所指 | 数据位置 | 用途 |
  |---|---|---|---|
  | **乘**（乘神） | 天将所骑的【**天盘**】之支（十二神） | `tianjiang_map` 的**键** | **定五行 → 与日干生克（本层判 side）** |
  | **临**（所加盘之神） | 乘神所落脚的【**地盘**】之宫 | `tiandi_pan` 反查（{地盘:天盘} ⇒ {天盘:地盘}） | L2568 第二级（**仅展示 · 本轮不判 side**） |
  铁证 **L8619**（指掌赋注）：「玄武**所乘之神**临戊地…从**地盘**之戌／从**天盘**之卯」。
  旁证 **L3251**：「**将**克**神**、**神**克**方**为外战；**方**克**神**、**神**克**将**为内战」（将＝天将｜神＝天盘｜方＝地盘）。

⚠️ **旧实现之误（2026-09-16 憨爷定案）**：原用 `TJ_WX`（**将之本五行**：贵人恒土／白虎恒金）
   —— **既非乘亦非临** ⇒ 判读全错。量化（1440 组）：**关系 77.8%／吉凶 62.8% 不同**。

⇒ 本层＝把 L2567／L2568 的「将 × **乘神** × 日干」规则，**扩到课中出现的全部将**。
   既有系统只把它用到「干上神」一处（`liuqin_engine.liuqin_judge` → `liuqin_struct` → 应人列），
   本层按 L2568「**凡**壬课吉凶系于天将」覆盖**全部**（`_skip_pos` 跳过干上以防重复呈现）。

⛔ 边界（守「不可推广」与「单源」两道红线）：
  · **「比和」不判吉凶** —— 《通解》L2575「比和吉」出自**贵人章（单将）**，非全局规则，
    故只标关系、**不下 side**（宁缺勿滥）。
  · 断语复用《东方朔射覆秘诀》卷之二「贵神主客六亲论」**60 条表**（单一真源，不另造）。
  · 本层**纯展示、不进评分链**；**不覆盖、不改动**既有 `side`（逐宫断语）。
  · ⚠️ 两套体系的「取向」可能相反：L2568 看**谁克谁**，东方朔断语看**得财/受损**
    （如「日克为财妻半富」）⇒ 前端**分别呈现**、`system_note` 明示互不覆盖。
"""
from typing import Dict

# ── 吉将／凶将（与 engine.kege_shensha.JI_JIANG / XIONG_JIANG 一致；闸口有「两表一致」断言防漂移）──
JI_JIANG = ('贵人', '青龙', '六合', '太常', '天后', '太阴')
XIONG_JIANG = ('螣蛇', '朱雀', '勾陈', '天空', '白虎', '玄武')

# ── 五行表与断语表：**单一真源＝项目根 `liuqin_engine.py`**（东方朔卷之二），此处只引用不复制 ──
#   ⚠️ `engine/` 下另有**同名** `liuqin_engine.py`（内容不同：只有 LiuQinCalculator 类，无 GAN_WX/LIUQIN/ZHI_WX）
#   ⇒ ⛔ 不能只靠 `import liuqin_engine`（结果取决于 sys.path 顺序）—— 先试常规 import 并**校验表存在**，
#      不通过则按**文件路径**显式加载项目根真源（与 sys.path 顺序解耦）。
def _load_tables():
    try:
        import liuqin_engine as _m
        if (hasattr(_m, 'GAN_WX') and hasattr(_m, 'LIUQIN')
                and hasattr(_m, 'ZHI_WX') and hasattr(_m, 'TJ_WX')):
            return _m
    except Exception:
        pass
    import importlib.util as _iu
    import os as _os
    _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                       'liuqin_engine.py')
    if not _os.path.exists(_p):
        raise ImportError('tianjiang_shengke: 未找到项目根 liuqin_engine.py（五行/断语单一真源）')
    _spec = _iu.spec_from_file_location('_liuqin_tables_src', _p)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    if not (hasattr(_mod, 'GAN_WX') and hasattr(_mod, 'ZHI_WX')
            and hasattr(_mod, 'TJ_WX') and hasattr(_mod, 'LIUQIN')):
        raise ImportError('tianjiang_shengke: liuqin_engine 缺少 GAN_WX/ZHI_WX/TJ_WX/LIUQIN 表')
    return _mod


_T = _load_tables()
GAN_WX, TJ_WX, ZHI_WX = _T.GAN_WX, _T.TJ_WX, _T.ZHI_WX
WX_SHENG, WX_KE, LIUQIN = _T.WX_SHENG, _T.WX_KE, _T.LIUQIN

# ── L2568 吉凶规则表：关系 × 将类 → side ──
#   「生日为吉，虽凶将亦为吉」⇒ 生日 不分将类皆吉
#   「克日为凶，虽吉将亦为凶」⇒ 克日 不分将类皆凶
#   「吉将喜生扶，忌克制；凶将反此」⇒ 日生（我生之＝洩）／日克（我克之＝制）
#   「比和」⛔ 全局无据（L2575 仅贵人章）⇒ '' 不判
_JIXIONG = {
    '生日': {'吉将': '吉', '凶将': '吉'},
    '克日': {'吉将': '凶', '凶将': '凶'},
    '日生': {'吉将': '吉', '凶将': '凶'},
    '日克': {'吉将': '凶', '凶将': '吉'},
    '比和': {'吉将': '',  '凶将': ''},
}

# 关系标签（🔴 主语一律写「乘神」——五行取自乘神，非将之本五行）
REL_LABEL = {
    '生日': '乘神生日干（生我者·恩）',
    '克日': '乘神克日干（克我者·伤）',
    '日生': '日干生乘神（我生之·脱）',
    '日克': '日干克乘神（我克之·制）',
    '比和': '乘神与日干比和（同气）',
}

SRC = '《通解》上卷十二将释义「天将五行性质规定／天将生克规则」（L2566／L2567／L2568）'
DUANYU_SRC = '《东方朔射覆秘诀》卷之二「贵神主客六亲论」'   # 断语单一真源（表在项目根 liuqin_engine.py）


def jiang_lei(jiang: str) -> str:
    """将类：吉将／凶将（不在两表者返回空）。"""
    if jiang in JI_JIANG:
        return '吉将'
    if jiang in XIONG_JIANG:
        return '凶将'
    return ''


def cheng_wx_of(cheng_zhi: str) -> str:
    """**乘神**（天盘支）的五行 —— L2567「专取天盘乘神决之」。"""
    return ZHI_WX.get(cheng_zhi, '')


def ben_wx_of(jiang: str) -> str:
    """将之**本**五行（仅供对照展示，⛔ **不参与生克判定**）。"""
    return TJ_WX.get(jiang, '')


# 兼容别名（旧名 = 将本五行；保留以免外部脚本断裂，语义见 docstring）
def jiang_wx_of(jiang: str) -> str:
    """⚠️ 将之**本**五行 —— 已**不用于**生克判定（L2567 取乘神）。新码请用 `cheng_wx_of`。"""
    return TJ_WX.get(jiang, '')


def gan_wx_of(ri_gan: str) -> str:
    return GAN_WX.get(ri_gan, '')


def rel_of(ri_gan: str, jiang: str, cheng_zhi: str) -> str:
    """关系判定：**日干** × **乘神**（天盘支）五行。
    比和／生日／克日／日生／日克（判序与 `liuqin_judge` 一致）。
    ⛔ `jiang` 只在缺 `cheng_zhi` 时回落用；正常路径不读它的五行。"""
    gwx = GAN_WX.get(ri_gan, '')
    wx = ZHI_WX.get(cheng_zhi, '') if cheng_zhi else TJ_WX.get(jiang, '')
    if not gwx or not wx:
        return ''
    if wx == gwx:
        return '比和'
    if WX_SHENG.get(wx) == gwx:
        return '生日'
    if WX_KE.get(wx) == gwx:
        return '克日'
    if WX_SHENG.get(gwx) == wx:
        return '日生'
    return '日克'


def suo_jia_of(tiandi_pan, cheng_zhi: str) -> str:
    """**乘神所加之地盘宫**（＝「临」）—— L2568「更察**乘神所加盘之神**」。
    `tiandi_pan` 契约为 **{地盘: 天盘}**；本函数反查「天盘＝cheng_zhi 的那个地盘」。
    ⛔ 与本层判 side 无关，仅供展示/追溯（乘 ≠ 临）。"""
    if not isinstance(tiandi_pan, dict) or not cheng_zhi:
        return ''
    for _d, _t in tiandi_pan.items():
        if _t == cheng_zhi:
            return _d
    return ''


def shengke_of(ri_gan: str, jiang: str, cheng_zhi: str) -> Dict[str, str]:
    """单将判定。返回 {jiang, cheng_zhi, cheng_wx, ben_wx, rel, rel_label, side, lei, note, src}
    （缺数据返回 {}）。🔴 五行取**乘神**（L2567），`ben_wx` 仅对照。"""
    _rel = rel_of(ri_gan, jiang, cheng_zhi)
    if not _rel:
        return {}
    _lei = jiang_lei(jiang)
    _side = _JIXIONG.get(_rel, {}).get(_lei, '')
    return {
        'jiang': jiang,
        'cheng_zhi': cheng_zhi,
        'cheng_wx': ZHI_WX.get(cheng_zhi, '') if cheng_zhi else '',
        'ben_wx': TJ_WX.get(jiang, ''),
        'rel': _rel,
        'rel_label': REL_LABEL.get(_rel, ''),
        'side': _side,
        'lei': _lei,
        'note': (LIUQIN.get(jiang) or {}).get(_rel, ''),
        'src': SRC,
    }


# ═══════════════ L2568 末句：喜忌 × 旺衰 的强度调节（2026-09-17） ═══════════════
# 原文（`data/_tongjie_ocr/通解_上.txt` L2568）：
#   「更察乘神所加盘之神，生克、旺相休囚，喜则宜旺相，忌则宜休囚也。」
# 口径：
#   · 「喜／忌」＝前文生克所定的吉凶（吉＝喜、凶＝忌）；
#   · 「旺相／休囚」＝**乘神所加盘之神**（＝所临地盘宫，「临」）之**月令旺衰**；
#     原文只言「旺相」「休囚」两档 ⇒ 旺/相 → 旺相，休/囚/死 → 休囚（⛔ 不细分五档，原文未及）。
#
# 🔴🔴 落地形态＝**正交强度标注，⛔ 不进评分链**。理由＝**量化实证否决**（2026-09-17）：
#   探针 `_冗余待删/_quant_xjws_sep.py` 在 34 吉案 / 172 凶案 上做**分离度检验**，
#   两种「喜/忌」口径 × 两个特征**全部无分离度**：
#     生克 side：喜×旺相 +1.1pp ／ 忌×休囚 +7.3pp；
#     宫位断语 side：喜×旺相 −0.7pp ／ 忌×休囚 −3.3pp（后两者**方向还是反的**）。
#   单因子方向准确率 31.4%（基线）／38.6%（加旺衰）—— 远低于「永远猜凶」的 83.1%。
#   ⚠️ 初版 δ1 曾显示 +7.2pp「提升」，实为**类间偏置**而非信号
#      —— 印证 SOP「百分比提升 ≠ 方案正确」。
#   ⇒ 按 SOP 第 0 步「单一特征无分离度 ⇒ 不做评分层」，本条**只做叙事强度标注**。
XIJI_SRC = ('《通解》上卷十二将释义「天将生克规则」L2568'
            '「更察乘神所加盘之神…喜则宜旺相，忌则宜休囚也」')

_XI_WANG = ('旺', '相')
_XI_SHUAI = ('休', '囚', '死')

XIJI_TIAOJIE = {
    ('吉', '旺相'): '喜而旺相·其吉力厚',
    ('吉', '休囚'): '喜而休囚·其吉力薄',
    ('凶', '旺相'): '忌而旺相·其凶尤甚',
    ('凶', '休囚'): '忌而休囚·其凶可减',
}


def xi_ji_band(ws: str) -> str:
    """月令旺衰五档 → 原文二分「旺相／休囚」（原文只言此两档）。"""
    if ws in _XI_WANG:
        return '旺相'
    if ws in _XI_SHUAI:
        return '休囚'
    return ''


def xiji_of(side: str, ws: str) -> str:
    """L2568 末句强度判语。⛔ side 空判（比和）或旺衰缺失 ⇒ 返回 ''（原文未及，不臆造）。"""
    return XIJI_TIAOJIE.get((side, xi_ji_band(ws)), '')
