# -*- coding: utf-8 -*-
"""
六壬「应期」引擎 v1.0（2026-08-21）
====================================================================
应期 = 占事兑现之期。本引擎基于七法判定应期长短与触发地支：

  法1. 三传应期法   —— 三传结构（递克/长生墓/合住冲日/相冲合日/回环）
  法2. 类神应期法   —— 类神临初/中/末传定速迟，不入传待冲合日
  法3. 神煞应期法   —— 日德日禄、驿马、墓神、天喜临传
  法4. 旺相休囚法   —— 旺相速 / 休囚迟 / 死绝无期
  法5. 干支结构法   —— 闭口卦冲破、金日逢丁、人宅受脱、干传支末传当令
  法6. 旬空特殊法   —— 空亡填实/冲空/刑害化解
  法7. 占事专用法   —— 取自《断案》20 类占事的专用应期条目

数据来源：
  · data/knowledge_应期_完整规则.json（21 条，YQ_xxx 编号）
  · engine/duanan_knowledge_base.py（20 类占事的应期条目）
  · engine/leishen_engine.py（类神判法）
  · engine/kege_atoms.py / bifa_detector.py（基础常量）

输出：
  {
    'primary': {'method':..., 'timing':速/中/迟/无期, 'days':int,
                'trigger_zhi':..., 'desc':..., 'rule_ids':[...]},
    'candidates': [同上 dict,...],
    'matched_rules': [YQ_xxx,...],
    'narrative': '...综合应期叙述...',
    'confidence': high/medium/low
  }

约定 days：速=1~3、中=7~15、迟=30+、无期=0
====================================================================
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional, Tuple, Any

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# ── 复用 bifa_detector 已有常量（不重复造轮子）──
from engine.bifa_detector import (
    WUXING, GAN_WUXING, ZHI_WUXING,
    LU_SHEN, GAN_JIGONG,
    CHANG_SHENG as GAN_CS, MU as GAN_MU, JUE as GAN_JUE, TAI_SHEN as GAN_TAI, BAI as GAN_BAI,
    WX_CHANG_SHENG, WX_TAI_SHUANG, WX_SI_SHUANG,
    DIZHI_ORDER, DIZHI_INDEX,
    LIUHE, LIUHAI, LIUCHONG, SANXING, SANHE_JU,
    YUEJIANG_SEASON, SEASON_WANG,
    TIANJIANG_WUXING, TIANJIANG_BENJIA,
    YIMA, GUIREN_MAP, WUXING_MU,
    XUN_KONG_MAP, XUN_SHOU, XUN_WEI, XUN_DING,
)

# ── 应期专用补充常量 ──
# 日德（甲己德在寅、乙庚德在申、丙辛德在巳、丁壬德在亥、戊癸德在巳）
RI_DE = {'甲': '寅', '己': '寅', '乙': '申', '庚': '申',
         '丙': '巳', '辛': '巳', '丁': '亥', '壬': '亥',
         '戊': '巳', '癸': '巳'}

# 天喜（春戌、夏丑、秋辰、冬未）
TIAN_XI = {'春': '戌', '夏': '丑', '秋': '辰', '冬': '未'}

# 五行旺位（当令地支）
WX_WANG_ZHI = {'木': {'寅', '卯'}, '火': {'巳', '午'},
               '金': {'申', '酉'}, '水': {'亥', '子'},
               '土': {'辰', '戌', '丑', '未'}}

# 三合局冲位（合住→冲日方动）：申子辰合冲午、亥卯未合冲酉、寅午戌合冲子、巳酉丑合冲卯
SANHE_CHONG = {'申子辰': '午', '亥卯未': '酉', '寅午戌': '子', '巳酉丑': '卯'}

# 三合局合位（相冲→合日方住）：申子辰冲→合丑、亥卯未冲→合午、寅午戌冲→合未、巳酉丑冲→合辰
SANHE_HE = {'申子辰': '丑', '亥卯未': '午', '寅午戌': '未', '巳酉丑': '辰'}

# 季节→五行休囚（克季节旺者为囚，季节旺所克为死）
SEASON_XIU = {'春': '金', '夏': '水', '秋': '木', '冬': '火'}  # 囚
SEASON_SI = {'春': '土', '夏': '金', '秋': '木', '冬': '火'}   # 死

# ── 加载应期规则知识库 ──
_YQ_RULES_PATH = os.path.join(BASE, 'data', 'knowledge_应期_完整规则.json')
_yq_rules = None


def _load_yq_rules():
    global _yq_rules
    if _yq_rules is None:
        try:
            import json
            with open(_YQ_RULES_PATH, 'r', encoding='utf-8') as f:
                _yq_rules = json.load(f)
        except Exception:
            _yq_rules = {'rules': []}
    return _yq_rules


# ══════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════

def _wx(z: str) -> str:
    """取天干/地支五行"""
    return GAN_WUXING.get(z, '') or ZHI_WUXING.get(z, '')


def _ke(a: str, b: str) -> bool:
    """a 五行克 b 五行"""
    return {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}.get(_wx(a), '') == _wx(b)


def _sheng(a: str, b: str) -> bool:
    """a 五行生 b 五行"""
    return {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(_wx(a), '') == _wx(b)


def _is_kong(z: str, kongwang) -> bool:
    return z in set(kongwang or [])


def _chong_zhi(z: str) -> str:
    return LIUCHONG.get(z, '')


def _he_zhi(z: str) -> str:
    return LIUHE.get(z, '')


def _xing_zhi(z: str) -> str:
    """三刑之支（被z所刑者）；自刑返回自身"""
    return SANXING.get(z, '')


def _is_yang(z: str) -> bool:
    return z in set('子寅辰午申戌')


def _season_of(ri_zhi: str) -> str:
    """从日支粗推季节（用于旺相休囚参考；精确应取月建，但占日有日支粗判可用）"""
    if ri_zhi in {'寅', '卯', '辰'}:
        return '春'
    if ri_zhi in {'巳', '午', '未'}:
        return '夏'
    if ri_zhi in {'申', '酉', '戌'}:
        return '秋'
    return '冬'


def _wx_state(z: str, season: str) -> str:
    """取 z 在 season 下的十二长生状态（旺/相/休/囚/死 简化版）"""
    wx = _wx(z)
    if not wx or not season:
        return ''
    wang_wx = SEASON_WANG.get(season, '')
    if wx == wang_wx:
        return '旺'
    sheng_wx = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(wang_wx, '')
    if wx == sheng_wx:
        return '相'
    if wx == SEASON_XIU.get(season, ''):
        return '休'
    if wx == SEASON_SI.get(season, ''):
        return '死'
    # 囚 = 克旺者
    ke_wang = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}.get(wang_wx, '')
    if wx == ke_wang:
        return '囚'
    return ''


def _days_from_timing(timing: str) -> int:
    return {'速': 3, '中': 12, '迟': 45, '无期': 0}.get(timing, 0)


# ══════════════════════════════════════════════════════════════
# 法1: 三传应期法
# ══════════════════════════════════════════════════════════════

def _m1_sanchuan(ri_gan: str, sanchuan: List[str]) -> List[dict]:
    sc = list(sanchuan or [])
    if len(sc) < 3 or not ri_gan:
        return []
    ch, zh, mo = sc[0], sc[1], sc[2]
    out: List[dict] = []

    # 【2026-09-08 审计修复 BUG-A】《断案》第一心法：三传本支即应期支。
    #   三传之支"动"即为应期信号，应于该支值日/值月/值年。
    #   （例：三传亥→寅→巳 → 应期在亥/寅/巳月日；原文"巳月得中，亥月放榜"）
    #   优先级最高（排在递克/长生墓等结构法之前），作为三传应期的默认主干。
    #   末传为事之终局，权重最高；初传次之；中传再次——各列候选，由主应期选举统一排序。
    tri_zhi = sc[0:3]
    for _i, _z in enumerate(tri_zhi):
        _pos = ('初传', '中传', '末传')[_i]
        _timing = ('速', '中', '迟')[_i]
        _days = (3, 12, 30)[_i]
        out.append({
            'method': f'三传本支({_pos})',
            'timing': _timing,
            'days': _days,
            'trigger_zhi': _z,
            'desc': f'三传{_pos}{_z}为应期之支（《断案》三传本支即应期），应于{_z}日/月当令之时',
            'rule_ids': ['YQ_00(三传本支)'],
        })

    # YQ_01: 三传递克 → 事败，应期在末传克日时
    if _ke(ch, zh) and _ke(zh, mo) and _ke(mo, ri_gan):
        trig = mo  # 末传克日
        out.append({
            'method': '三传递克',
            'timing': '迟',
            'days': 45,
            'trigger_zhi': mo,
            'desc': f'三传{ch}-{zh}-{mo}递克，末传{mo}克日干{ri_gan}，事败于{mo}日当令之时',
            'rule_ids': ['YQ_01'],
        })

    # YQ_02: 初长生末墓 → 先易后难，应期在末传墓神被冲/填实
    cs_gan = GAN_CS.get(ri_gan, '')
    mu_gan = GAN_MU.get(ri_gan, '')
    if ch == cs_gan and mo == mu_gan:
        trig = _chong_zhi(mo)
        out.append({
            'method': '初长末墓',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': trig or mo,
            'desc': f'初传{ch}（{ri_gan}长生）末传{mo}（{ri_gan}墓），先易后难，应期在{trig}日冲墓或{mo}日填实',
            'rule_ids': ['YQ_02'],
        })

    # YQ_02 反：初墓末长生 → 先难后易，应期在末传长生当令
    if ch == mu_gan and mo == cs_gan:
        out.append({
            'method': '初墓末长生',
            'timing': '中',
            'days': 15,
            'trigger_zhi': mo,
            'desc': f'初传{ch}（墓）末传{mo}（长生），先难后易，应期在{mo}日当令之时',
            'rule_ids': ['YQ_02'],
        })

    # YQ_03: 三传合住 → 冲日方动（与三传合局相冲的地支）
    sanhe_key = _detect_sanhe(sc)
    if sanhe_key:
        chong = SANHE_CHONG.get(sanhe_key, '')
        if chong:
            out.append({
                'method': '三传合住',
                'timing': '中',
                'days': 12,
                'trigger_zhi': chong,
                'desc': f'三传{sanhe_key}合局，事情被合住，待{chong}日冲合方动',
                'rule_ids': ['YQ_03'],
            })

    # YQ_03 反：三传相冲 → 冲则动、应在冲支本身当令（【2026-09-08 审计修复 BUG-B】
    #   ①判据收紧：须三传呈结构性相冲（两两对应冲：子午/寅申/巳亥等连环冲），
    #     任一对冲即判的过宽判定会产生大面积误报（午寅子/卯子酉等错判）；
    #   ②方向修正：相冲主动，应期在冲神值日/值月（传统断案"冲则动，应在冲支"），
    #     原实现反向取"合位方住"，语义与断案相反。）
    #   结构性相冲判定：三传互为冲对（如 [子, 午, X] 或 [寅, 申, 戌] 首中相冲等）
    if not sanhe_key:
        # 找出全部相冲对
        chong_pairs = []
        for i in range(3):
            for j in range(i + 1, 3):
                if _chong_zhi(sc[i]) == sc[j]:
                    chong_pairs.append((sc[i], sc[j]))
        if len(chong_pairs) >= 2:
            # 至少两对相冲 → 三传整体呈冲局（连环冲或双冲）
            _chong_z = sorted({z for p in chong_pairs for z in p})
            for _z in _chong_z:
                out.append({
                    'method': '三传相冲',
                    'timing': '中',
                    'days': 12,
                    'trigger_zhi': _z,
                    'desc': f'三传{sc}互冲（{"、".join("-".join(p) for p in chong_pairs)}），冲则动，应于冲神{"、".join(_chong_z)}值日/月当令之时',
                    'rule_ids': ['YQ_03'],
                })

    # YQ_05: 回环格 → 传不离课，反复拖延
    # 简化判定：三传与四课重叠 ≥2（这里仅用三传自检：是否有两支相同）
    if len(set(sc)) < 3:
        out.append({
            'method': '回环格',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': '',
            'desc': '三传支重复，回环格，事反复拖延，应期较长',
            'rule_ids': ['YQ_05'],
        })

    return out


def _detect_sanhe(sc: List[str]) -> str:
    """检测三传是否构成三合局，返回局名（如'申子辰'）或''"""
    s = set(sc)
    for ju in ['申子辰', '亥卯未', '寅午戌', '巳酉丑']:
        if set(ju) == s:
            return ju
    return ''


# ══════════════════════════════════════════════════════════════
# 法2: 类神应期法
# ══════════════════════════════════════════════════════════════

def _m2_leishen(leishen: str, sanchuan: List[str]) -> List[dict]:
    if not leishen or not sanchuan:
        return []
    sc = list(sanchuan)
    out: List[dict] = []
    pos = ''
    for i, z in enumerate(sc):
        if z == leishen:
            pos = ('初传', '中传', '末传')[i]
            break

    if pos == '初传':
        out.append({
            'method': '类神临初传',
            'timing': '速',
            'days': 3,
            'trigger_zhi': leishen,
            'desc': f'类神{leishen}现于初传（发用），应期速，{leishen}日当令之时',
            'rule_ids': ['YQ_05(类神)'],
        })
    elif pos == '中传':
        out.append({
            'method': '类神临中传',
            'timing': '中',
            'days': 12,
            'trigger_zhi': leishen,
            'desc': f'类神{leishen}现于中传，应期中，{leishen}日当令之时',
            'rule_ids': ['YQ_05(类神)'],
        })
    elif pos == '末传':
        out.append({
            'method': '类神临末传',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': leishen,
            'desc': f'类神{leishen}现于末传，应期迟，{leishen}日当令之时',
            'rule_ids': ['YQ_05(类神)'],
        })
    else:
        # 类神不入传 → 待冲合之日
        ch = _chong_zhi(leishen)
        he = _he_zhi(leishen)
        out.append({
            'method': '类神不入传',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': ch or he or leishen,
            'desc': f'类神{leishen}不入传，待{ch}日冲开或{he}日合住之时方应',
            'rule_ids': ['YQ_05(类神)'],
        })
    return out


# ══════════════════════════════════════════════════════════════
# 法3: 神煞应期法
# ══════════════════════════════════════════════════════════════

def _m3_shensha(ri_gan: str, sanchuan: List[str], season: str) -> List[dict]:
    if not ri_gan or not sanchuan:
        return []
    sc = list(sanchuan)
    out: List[dict] = []

    # YQ_001: 日德日禄临传
    de = RI_DE.get(ri_gan, '')
    lu = LU_SHEN.get(ri_gan, '')
    for i, z in enumerate(sc):
        pos = ('初传', '中传', '末传')[i]
        if z == de:
            timing = {'初传': '速', '中传': '中', '末传': '迟'}[pos]
            out.append({
                'method': f'日德临{pos}',
                'timing': timing,
                'days': _days_from_timing(timing),
                'trigger_zhi': z,
                'desc': f'日德{de}临{pos}，应期在{z}日或{z}时',
                'rule_ids': ['YQ_001'],
            })
        if z == lu:
            timing = {'初传': '速', '中传': '中', '末传': '迟'}[pos]
            out.append({
                'method': f'日禄临{pos}',
                'timing': timing,
                'days': _days_from_timing(timing),
                'trigger_zhi': z,
                'desc': f'日禄{lu}临{pos}，应期在{z}日或{z}时',
                'rule_ids': ['YQ_001'],
            })

    # YQ_002: 驿马临传 → 主速
    # 注：驿马按日支算，调用方应传 yima_zhi；此处从参数外补
    # 此处仅当日禄/德；驿马由 judge_yingqi 主函数注入
    return out


def _m3_yima_in_sc(yima_zhi: str, sanchuan: List[str]) -> Optional[dict]:
    """驿马临三传 → 主速（独立函数，因需日支算马）"""
    if not yima_zhi or not sanchuan:
        return None
    sc = list(sanchuan)
    for i, z in enumerate(sc):
        if z == yima_zhi:
            pos = ('初传', '中传', '末传')[i]
            timing = {'初传': '速', '中传': '中', '末传': '迟'}[pos]
            return {
                'method': f'驿马临{pos}',
                'timing': timing,
                'days': _days_from_timing(timing),
                'trigger_zhi': yima_zhi,
                'desc': f'驿马{yima_zhi}临{pos}，主速，应期在{yima_zhi}日或{yima_zhi}时',
                'rule_ids': ['YQ_002'],
            }
    return None


def _m3_mu_shen(leishen: str, sanchuan: List[str]) -> Optional[dict]:
    """YQ_003: 墓神临三传 → 应期在墓神被冲或当旺之时"""
    if not leishen or not sanchuan:
        return None
    wx_ls = _wx(leishen)
    if not wx_ls:
        return None
    mu = WUXING_MU.get(wx_ls, '')
    if not mu:
        return None
    sc = list(sanchuan)
    for i, z in enumerate(sc):
        if z == mu:
            pos = ('初传', '中传', '末传')[i]
            chong = _chong_zhi(mu)
            timing = {'初传': '速', '中传': '中', '末传': '迟'}[pos]
            return {
                'method': f'墓神临{pos}',
                'timing': timing,
                'days': _days_from_timing(timing),
                'trigger_zhi': chong or mu,
                'desc': f'墓神{mu}临{pos}，主终结，应期在{chong}日冲墓或{mu}月当旺',
                'rule_ids': ['YQ_003'],
            }
    return None


def _m3_tianxi(season: str, sanchuan: List[str]) -> Optional[dict]:
    """YQ_004: 天喜临三传 → 主喜庆，应期在天喜所临地支时间"""
    if not season or not sanchuan:
        return None
    tx = TIAN_XI.get(season, '')
    if not tx:
        return None
    sc = list(sanchuan)
    for i, z in enumerate(sc):
        if z == tx:
            pos = ('初传', '中传', '末传')[i]
            return {
                'method': f'天喜临{pos}',
                'timing': '中',
                'days': 12,
                'trigger_zhi': tx,
                'desc': f'天喜{tx}临{pos}，主喜庆，应期在{tx}日或{tx}时',
                'rule_ids': ['YQ_004'],
            }
    return None


# ══════════════════════════════════════════════════════════════
# 法4: 旺相休囚法
# ══════════════════════════════════════════════════════════════

def _m4_wangxiu(leishen: str, yong_shen: str, season: str) -> Optional[dict]:
    """YQ_04: 类神/用神旺相速、休囚迟、死绝无期"""
    z = leishen or yong_shen
    if not z or not season:
        return None
    state = _wx_state(z, season)
    if not state:
        return None
    if state == '旺' or state == '相':
        return {
            'method': f'类神{state}',
            'timing': '速',
            'days': 3,
            'trigger_zhi': z,
            'desc': f'类神/用神{z}在{season}季{state}，应期速，{z}日当令之时',
            'rule_ids': ['YQ_04(旺休)'],
        }
    if state == '休':
        return {
            'method': f'类神{state}',
            'timing': '中',
            'days': 12,
            'trigger_zhi': z,
            'desc': f'类神/用神{z}在{season}季休，应期中，需待{z}日当令之时',
            'rule_ids': ['YQ_04(旺休)'],
        }
    if state == '囚':
        return {
            'method': f'类神{state}',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': z,
            'desc': f'类神/用神{z}在{season}季囚，应期迟，需待{z}日当令或冲克囚神之时',
            'rule_ids': ['YQ_04(旺休)'],
        }
    if state == '死':
        return {
            'method': f'类神{state}',
            'timing': '无期',
            'days': 0,
            'trigger_zhi': '',
            'desc': f'类神/用神{z}在{season}季死，事情难以发生或应期极远',
            'rule_ids': ['YQ_04(旺休)'],
        }
    return None


# ══════════════════════════════════════════════════════════════
# 法5: 干支结构法
# ══════════════════════════════════════════════════════════════

def _m5_bikou(ganzhi: str, sanchuan: List[str]) -> Optional[dict]:
    """YQ_02(实战): 闭口卦（旬尾加旬首）→ 冲破之时"""
    if not ganzhi or not sanchuan:
        return None
    xun_shou = XUN_SHOU.get(ganzhi, '')
    xun_wei = XUN_WEI.get(ganzhi, '')
    if not xun_shou or not xun_wei:
        return None
    sc = list(sanchuan)
    # 旬尾加旬首：初传=旬尾、中传或末传=旬首，或反之
    if (sc[0] == xun_wei[-1] and xun_shou[-1] in sc[1:]) or \
       (sc[0] == xun_shou[-1] and xun_wei[-1] in sc[1:]):
        chong = _chong_zhi(xun_shou[-1]) or _chong_zhi(xun_wei[-1])
        return {
            'method': '闭口卦',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': chong,
            'desc': f'闭口卦（旬尾{xun_wei[-1]}加旬首{xun_shou[-1]}），主信息闭塞，应期在{chong}日冲破闭口之时',
            'rule_ids': ['YQ_02(闭口)'],
        }
    return None


def _m5_jin_ri_feng_ding(ri_gan: str, sanchuan: List[str]) -> Optional[dict]:
    """YQ_04(实战)/YQ_02(综合): 金日逢丁凶祸动 → 丁神当令或填实之日"""
    if not ri_gan or not sanchuan:
        return None
    if ri_gan not in ('庚', '辛'):
        return None
    xun = XUN_SHOU.get('', '')  # 需 ganzhi；这里退化为按三传查丁神
    # 按日干支旬算丁神
    # 此函数需 ganzhi 才能准确算 XUN_DING；故接收 ganzhi 的话另算
    # 这里简化：三传中出现"丁"对应地支即为丁神
    # （丁神地支：甲子旬卯、甲戌旬丑、甲申旬亥、甲午旬酉、甲辰旬未、甲寅旬巳）
    # 用 ri_gan 仅作"金日"判定；丁神具体值由主函数注入
    return None


def _m5_jin_ding_ext(ganzhi: str, sanchuan: List[str]) -> Optional[dict]:
    """金日逢丁（扩展版，需日干支）"""
    if not ganzhi or not sanchuan:
        return None
    ri_gan = ganzhi[0]
    if ri_gan not in ('庚', '辛'):
        return None
    xun = XUN_SHOU.get(ganzhi, '')
    if not xun:
        return None
    ding_zhi = XUN_DING.get(xun, '')
    if not ding_zhi:
        return None
    sc = list(sanchuan)
    if ding_zhi in sc:
        return {
            'method': '金日逢丁',
            'timing': '速',
            'days': 3,
            'trigger_zhi': ding_zhi,
            'desc': f'金日{ri_gan}见丁神{ding_zhi}，主凶祸变动，应期在{ding_zhi}日当令或填实之时',
            'rule_ids': ['YQ_04(金日逢丁)', 'YQ_02(综合)'],
        }
    return None


def _m5_renzhai_tuotuo(ri_gan: str, ri_zhi: str, gan_shang: str, zhi_shang: str) -> Optional[dict]:
    """YQ_03(综合): 人宅受脱（干支互脱）→ 脱气之神被填实/合住"""
    if not all([ri_gan, ri_zhi, gan_shang, zhi_shang]):
        return None
    # 干上神脱日干：干上神生？否，应为"干上神泄日干"（日干生干上神）
    gan_tuo = _sheng(ri_gan, gan_shang)  # ri_gan 生 gan_shang → gan_shang 脱 ri_gan
    zhi_tuo = _sheng(ri_zhi, zhi_shang)
    if gan_tuo and zhi_tuo:
        # 脱气之神 = 干上神 + 支上神
        # 应期：脱气之神被填实（土）或合住
        tuoshen = gan_shang
        he = _he_zhi(tuoshen)
        return {
            'method': '人宅受脱',
            'timing': '中',
            'days': 12,
            'trigger_zhi': he or tuoshen,
            'desc': f'干支互脱（{ri_gan}生{gan_shang}、{ri_zhi}生{zhi_shang}），损耗难拔，应期在{he or tuoshen}日合住脱气之时',
            'rule_ids': ['YQ_03(人宅受脱)'],
        }
    return None


def _m5_gan_chuan_zhi(sanchuan: List[str], gan_shang: str, zhi_shang: str) -> Optional[dict]:
    """YQ_04(综合): 干传支 → 末传当令填实"""
    if not sanchuan or not gan_shang or not zhi_shang:
        return None
    sc = list(sanchuan)
    # 三传从干（干上神起）传至支（支上神）→ 末传为支相关
    if sc[0] == gan_shang and sc[-1] == zhi_shang:
        return {
            'method': '干传支',
            'timing': '迟',
            'days': 30,
            'trigger_zhi': sc[-1],
            'desc': f'三传从干{gan_shang}传至支{zhi_shang}，外部影响内部，应期在末传{sc[-1]}当令填实之时',
            'rule_ids': ['YQ_04(干传支)'],
        }
    return None


# ══════════════════════════════════════════════════════════════
# 法6: 旬空特殊法
# ══════════════════════════════════════════════════════════════

def _m6_xunkong(leishen: str, yong_shen: str, sanchuan: List[str],
                kongwang, season: str) -> List[dict]:
    out: List[dict] = []
    kw = set(kongwang or [])
    if not kw:
        return out
    sc = list(sanchuan or [])
    targets = set()
    if leishen:
        targets.add(leishen)
    if yong_shen:
        targets.add(yong_shen)
    targets.update(sc)

    for z in targets:
        if z in kw:
            chong = _chong_zhi(z)
            # YQ_005: 空亡填实（该地支出现之日）或冲空（与空亡相冲的地支出现之日）
            out.append({
                'method': '旬空填实',
                'timing': '中',
                'days': 12,
                'trigger_zhi': z,
                'desc': f'用神/类神{z}临旬空，主虚而不实，应期在{z}日填实或{chong}日冲空之时',
                'rule_ids': ['YQ_005(旬空)'],
            })

    # 刑害化解（三传见刑害 → 待合神化解）
    for z in sc:
        xing_target = _xing_zhi(z)
        if xing_target and xing_target in sc and z != xing_target:
            he = _he_zhi(z)
            if he:
                out.append({
                    'method': '刑害化解',
                    'timing': '中',
                    'days': 12,
                    'trigger_zhi': he,
                    'desc': f'三传见刑（{z}刑{xing_target}），主拖延阻碍，应期在{he}日合神化解之时',
                    'rule_ids': ['YQ_05(刑害)'],
                })
    return out


# ══════════════════════════════════════════════════════════════
# 法7: 占事专用应期
# ══════════════════════════════════════════════════════════════

# 占事→应期专用判法关键字（基于 duanan_knowledge_base 20 类占事的应期条目）
CATEGORY_YQ_RULES = {
    '求财': [
        ('财爻合日为得财之日', 'he_yong_shen', '速'),
        ('末传之合神上神亦为得财之期', 'he_mo', '中'),
        ('财爻旺相见青龙主速', 'wang_xiang_qinglong', '速'),
    ],
    '婚姻': [
        ('三传生日媒言亦实', 'san_chuan_sheng_ri', '速'),
        ('日生三传强成终久不偕', 'ri_sheng_san_chuan', '迟'),
    ],
    '胎产': [
        ('妻行年上神长生者为受孕之月', 'sheng_zhang_yue', '中'),
        ('月之长生为受胎之日', 'yue_cs', '中'),
        ('日之长生为受胎之时', 'ri_cs', '速'),
    ],
    '疾病': [
        ('甲乙日用水神为瘥期', 'jia_yi_water', '中'),
        ('用金神为死期', 'jin_dead', '迟'),
        ('无阳气三日内死', 'no_yang_3day', '速'),
    ],
    '行人': [
        ('三传先虚后实行人来归', 'xu_shi_lai', '中'),
        ('日干见墓发用行人此日还', 'ri_gan_mo', '中'),
        ('申发用则巳日有信', 'shen_yong_si_xin', '速'),
    ],
    '盗贼': [
        ('勾陈克盗神及克日鬼者即为获盗日期', 'gou_chen_ke', '中'),
    ],
    '出行': [
        ('月将加时视所往之方上见何神决之', 'yuejiang_shi', '中'),
    ],
    '官讼': [
        ('行年到亥子上见父母 → 有服（丧事）', 'xing_hai_parent', '迟'),
        ('太岁入宅克宅 → 经官判断', 'tai_sui_kzhai', '迟'),
    ],
    '前程': [
        ('青龙去日干几位便知是几年迁转', 'qinglong_ri_gan', '迟'),
        ('青龙乘神所生为迁日', 'qinglong_sheng', '中'),
    ],
    '宅墓': [
        ('卯数六不出六年', 'mao_six', '迟'),
    ],
}


def _m7_category(category: str, ri_gan: str, sanchuan: List[str],
                 yong_shen: str, gan_shang: str = '', zhi_shang: str = '') -> List[dict]:
    """占事专用应期：调用方传入占事类型，按 duanan_knowledge_base 的条目给出专用判法"""
    if not category or not sanchuan:
        return []
    sc = list(sanchuan)
    out: List[dict] = []
    rules = CATEGORY_YQ_RULES.get(category, [])

    for desc, key, timing in rules:
        trig = ''
        days = _days_from_timing(timing)

        # 求财：财爻合日为得财之日
        if key == 'he_yong_shen' and yong_shen:
            trig = _he_zhi(yong_shen) or yong_shen
        elif key == 'he_mo':
            trig = _he_zhi(sc[-1]) if sc else ''
        elif key == 'wang_xiang_qinglong' and yong_shen:
            trig = yong_shen
        elif key == 'san_chuan_sheng_ri':
            if all(_sheng(z, ri_gan) for z in sc if z):
                trig = sc[-1] if sc else ''
            else:
                continue
        elif key == 'ri_sheng_san_chuan':
            if all(_sheng(ri_gan, z) for z in sc if z):
                trig = sc[-1] if sc else ''
            else:
                continue
        elif key == 'ri_cs':
            cs = GAN_CS.get(ri_gan, '')
            if cs:
                trig = cs
            else:
                continue
        elif key == 'jia_yi_water':
            if ri_gan in ('甲', '乙'):
                water_set = {'亥', '子'}
                w_in_sc = [z for z in sc if z in water_set]
                if w_in_sc:
                    trig = w_in_sc[0]
                else:
                    continue
            else:
                continue
        elif key == 'jin_dead':
            jin_set = {'申', '酉'}
            j_in_sc = [z for z in sc if z in jin_set]
            if j_in_sc:
                trig = j_in_sc[0]
            else:
                continue
        elif key == 'shen_yong_si_xin':
            if sc and sc[0] == '申':
                trig = '巳'
            else:
                continue
        elif key == 'ri_gan_mo':
            mo = GAN_MU.get(ri_gan, '')
            if mo and mo in sc:
                trig = mo
            else:
                continue
        elif key == 'qinglong_sheng':
            # 简化：青龙乘神 = 财爻，所生为迁日 → 取末传五行所生
            if sc:
                mo_wx = _wx(sc[-1])
                sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}.get(mo_wx, '')
                if sheng:
                    zhi_of_sheng = next((z for z in DIZHI_ORDER if _wx(z) == sheng), '')
                    if zhi_of_sheng:
                        trig = zhi_of_sheng
                    else:
                        continue
                else:
                    continue
            else:
                continue

        out.append({
            'method': f'[{category}专用] {desc}',
            'timing': timing,
            'days': days,
            'trigger_zhi': trig,
            'desc': desc + (f'，应期在{trig}日' if trig else '，应期按占事专用法判定'),
            'rule_ids': [f'YQ_{category}_专用'],
        })

    return out


# ══════════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════════

def judge_yingqi(
    ri_gan: str,
    sanchuan: List[str],
    *,
    ri_zhi: str = '',
    ganzhi: str = '',
    gan_shang: str = '',
    zhi_shang: str = '',
    yong_shen: str = '',
    yong_shen_pos: str = '',
    leishen: str = '',
    kongwang: Optional[List[str]] = None,
    tianjiang: Optional[Dict[str, str]] = None,
    season: str = '',
    category: str = '',
) -> dict:
    """六壬应期综合判断引擎（七法合一）

    参数：
      ri_gan: 日干（甲乙…）
      sanchuan: 三传地支 [初传, 中传, 末传]
      ri_zhi: 日支
      ganzhi: 日干支（如"甲子"，用于旬空/旬首/旬丁判定）
      gan_shang/zhi_shang: 干上神、支上神
      yong_shen: 用神地支
      yong_shen_pos: 用神在三传的位置（初传/中传/末传）
      leishen: 类神地支（占失物/六畜等）
      kongwang: 旬空地支列表（如 ['戌','亥']）
      tianjiang: 天将映射 {初传:.., 中传:.., 末传:..} 或 {地支:天将}
      season: 春夏秋冬（用于旺相休囚）
      category: 占事类型（求财/婚姻/疾病/行人/盗贼/前程/宅墓/官讼/出行/胎产…）

    返回：
      {
        'primary': 主应期 dict（method/timing/days/trigger_zhi/desc/rule_ids）,
        'candidates': 全部候选应期 list,
        'matched_rules': 命中的 YQ_xxx 规则编号集合,
        'narrative': 综合叙述,
        'confidence': high/medium/low
      }
    """
    kongwang = list(kongwang or [])
    if not season:
        season = _season_of(ri_zhi) if ri_zhi else ''
    yima_zhi = YIMA.get(ri_zhi, '') if ri_zhi else ''
    if not ganzhi and ri_gan and ri_zhi:
        ganzhi = ri_gan + ri_zhi

    candidates: List[dict] = []

    # ── 法1: 三传应期 ──
    candidates.extend(_m1_sanchuan(ri_gan, sanchuan))

    # ── 法2: 类神应期 ──
    ls = leishen or yong_shen
    candidates.extend(_m2_leishen(ls, sanchuan))

    # ── 法3: 神煞应期 ──
    candidates.extend(_m3_shensha(ri_gan, sanchuan, season))
    yima_r = _m3_yima_in_sc(yima_zhi, sanchuan)
    if yima_r:
        candidates.append(yima_r)
    mu_r = _m3_mu_shen(ls, sanchuan)
    if mu_r:
        candidates.append(mu_r)
    tx_r = _m3_tianxi(season, sanchuan)
    if tx_r:
        candidates.append(tx_r)

    # ── 法4: 旺相休囚 ──
    wx_r = _m4_wangxiu(leishen, yong_shen, season)
    if wx_r:
        candidates.append(wx_r)

    # ── 法5: 干支结构 ──
    bk_r = _m5_bikou(ganzhi, sanchuan)
    if bk_r:
        candidates.append(bk_r)
    jd_r = _m5_jin_ding_ext(ganzhi, sanchuan)
    if jd_r:
        candidates.append(jd_r)
    rz_r = _m5_renzhai_tuotuo(ri_gan, ri_zhi, gan_shang, zhi_shang)
    if rz_r:
        candidates.append(rz_r)
    gz_r = _m5_gan_chuan_zhi(sanchuan, gan_shang, zhi_shang)
    if gz_r:
        candidates.append(gz_r)

    # ── 法6: 旬空特殊 ──
    candidates.extend(_m6_xunkong(leishen, yong_shen, sanchuan, kongwang, season))

    # ── 法7: 占事专用 ──
    if category:
        candidates.extend(_m7_category(category, ri_gan, sanchuan, yong_shen, gan_shang, zhi_shang))

    # ── 主应期选举 ──
    # 优先级：占事专用 > 类神/神煞 > 三传/干支 > 旺相休囚
    # 同优先级内：timing 速 > 中 > 迟 > 无期（days 升序）
    priority = {
        '专用': 0,
        # 三传本支应期是《断案》默认主干，应优先于日德/日禄等神煞（2026-09-08 BUG-A）
        '三传本支': 1,
        '类神': 1, '日德': 1, '日禄': 1, '驿马': 1, '墓神': 1, '天喜': 1,
        '三传': 2, '闭口': 2, '金日逢丁': 2, '人宅受脱': 2, '干传支': 2,
        '旬空': 3, '刑害': 3,
        '类神旺': 4,
    }
    timing_rank = {'速': 0, '中': 1, '迟': 2, '无期': 3}

    def _priority_of(cand: dict) -> int:
        m = cand.get('method', '')
        for k, p in priority.items():
            if k in m:
                return p
        return 5

    candidates.sort(key=lambda c: (_priority_of(c), timing_rank.get(c.get('timing', ''), 4)))

    matched_rules = set()
    for c in candidates:
        for rid in c.get('rule_ids', []):
            matched_rules.add(rid)

    primary = candidates[0] if candidates else {
        'method': '无明确应期信号',
        'timing': '无期',
        'days': 0,
        'trigger_zhi': '',
        'desc': '课传无显著应期触发条件，需结合占事类别与三传综合判断',
        'rule_ids': [],
    }

    # ── 综合叙述 ──
    narr_parts = []
    if primary.get('trigger_zhi'):
        narr_parts.append(f"主应期：{primary['method']}（{primary['timing']}，约{primary['days']}日，触发地支{primary['trigger_zhi']}）")
    else:
        narr_parts.append(f"主应期：{primary['method']}（{primary['timing']}）")
    if len(candidates) > 1:
        sec = candidates[1]
        narr_parts.append(f"次选：{sec['method']}（{sec['timing']}，{sec.get('trigger_zhi','-')}）")
    if len(candidates) > 2:
        narr_parts.append(f"共命中{len(candidates)}种应期法")

    # ── 置信度 ──
    if len(matched_rules) >= 3:
        confidence = 'high'
    elif len(matched_rules) >= 1:
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'primary': primary,
        'candidates': candidates,
        'matched_rules': sorted(matched_rules),
        'narrative': '；'.join(narr_parts),
        'confidence': confidence,
    }


# ══════════════════════════════════════════════════════════════
# 自检（真实课例回放）
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('=' * 60)
    print('应期引擎自检')
    print('=' * 60)

    # 课例1: 甲子日 三传 戌申午（递克，事败）
    # 戌土 → 申金 → 午火克甲木（递克到底，事败）
    r = judge_yingqi('甲', ['戌', '申', '午'],
                     ri_zhi='子', ganzhi='甲子',
                     gan_shang='戌', zhi_shang='申',
                     yong_shen='午', yong_shen_pos='末传',
                     kongwang=['戌', '亥'], season='冬')
    print(f'\n[课例1] 甲子日 戌申午递克')
    print(f'  主应期: {r["primary"]["method"]} | {r["primary"]["timing"]} | {r["primary"]["days"]}日 | {r["primary"]["trigger_zhi"]}')
    print(f'  命中规则: {r["matched_rules"]}')
    print(f'  叙述: {r["narrative"]}')

    # 课例2: 庚辰日 三传 子申辰（三合水局，合住冲日方动）
    r = judge_yingqi('庚', ['子', '申', '辰'],
                     ri_zhi='辰', ganzhi='庚辰',
                     gan_shang='子', zhi_shang='申',
                     yong_shen='子', yong_shen_pos='初传',
                     kongwang=['戌', '亥'], season='春')
    print(f'\n[课例2] 庚辰日 子申辰三合水局')
    print(f'  主应期: {r["primary"]["method"]} | {r["primary"]["timing"]} | {r["primary"]["days"]}日 | {r["primary"]["trigger_zhi"]}')
    print(f'  命中规则: {r["matched_rules"]}')
    print(f'  叙述: {r["narrative"]}')

    # 课例3: 丁亥日 求财 三传 寅卯辰（财爻旺相，应期速）
    r = judge_yingqi('丁', ['寅', '卯', '辰'],
                     ri_zhi='亥', ganzhi='丁亥',
                     gan_shang='寅', zhi_shang='卯',
                     yong_shen='寅', yong_shen_pos='初传',
                     leishen='寅', kongwang=['戌', '亥'],
                     season='春', category='求财')
    print(f'\n[课例3] 丁亥日 寅卯辰 求财')
    print(f'  主应期: {r["primary"]["method"]} | {r["primary"]["timing"]} | {r["primary"]["days"]}日 | {r["primary"]["trigger_zhi"]}')
    print(f'  命中规则: {r["matched_rules"]}')
    print(f'  叙述: {r["narrative"]}')

    # 课例4: 辛巳日 疾病 三传 酉丑巳（金局，金日逢丁）
    # 辛在甲戌旬，丁神=丑
    r = judge_yingqi('辛', ['酉', '丑', '巳'],
                     ri_zhi='巳', ganzhi='辛巳',
                     gan_shang='酉', zhi_shang='丑',
                     yong_shen='酉', kongwang=['申', '酉'],
                     season='夏', category='疾病')
    print(f'\n[课例4] 辛巳日 酉丑巳 疾病')
    print(f'  主应期: {r["primary"]["method"]} | {r["primary"]["timing"]} | {r["primary"]["days"]}日 | {r["primary"]["trigger_zhi"]}')
    print(f'  命中规则: {r["matched_rules"]}')
    print(f'  叙述: {r["narrative"]}')

    # 课例5: 戊午日 失物 三传 巳酉丑（金局），类神=酉（金器/银）
    r = judge_yingqi('戊', ['巳', '酉', '丑'],
                     ri_zhi='午', ganzhi='戊午',
                     gan_shang='巳', zhi_shang='酉',
                     leishen='酉', yong_shen='酉',
                     kongwang=['子', '丑'], season='夏',
                     category='盗贼')
    print(f'\n[课例5] 戊午日 巳酉丑 失物(银)')
    print(f'  主应期: {r["primary"]["method"]} | {r["primary"]["timing"]} | {r["primary"]["days"]}日 | {r["primary"]["trigger_zhi"]}')
    print(f'  命中规则: {r["matched_rules"]}')
    print(f'  叙述: {r["narrative"]}')

    print('\n' + '=' * 60)
    print('自检完成。')
