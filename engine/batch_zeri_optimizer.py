#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量择日优化器 (Batch Zeri Optimizer)
======================================
在 3/5/10 年时间范围内，为每山选出最优日课。

三阶段漏斗策略：
  Phase 1 (斗首快筛): 预计算全量四柱 → 斗首评分 → 每山保留 TOP-N
  Phase 2 (到山到向):  对候选计算天地盘 → 到山到向加分 → 每山保留 TOP-M
  Phase 3 (完整六壬):  对候选计算三传 → 拱格/活禄马 → 最终排名输出

时间复杂度估算（10年=3652天）：
  Phase 1: 3652天 × 12时辰 × 24山 = 1,051,776 次 O(1) 检查 → ~3秒
  Phase 2: 500候选/山 × 24山 = 12,000 次天地盘 → ~2秒
  Phase 3: 50候选/山 × 24山 = 1,200 次三传 → ~10秒
  总计: ~15秒（10年范围）
"""

import json, os, time, sys, heapq
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field, asdict

# 添加项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.sizhu_engine import get_sizhu, get_day_ganzhi, get_hour_ganzhi, get_year_ganzhi, get_month_ganzhi
from engine.yidu_liuren_yaojue import (
    SHAN_JIA_MAP, XIANG_SHOU, ZHI_LIST, LU, get_yima, JIGONG,
    get_doushou_class, get_yuanchen_gans,
    check_sizhu_tou_yuanchen, check_liuxiang_liuti,
    check_sanyuan_sanwu_yilian, check_jixiong_position,
    check_all_gong_patterns, check_huoma_huolu,
    check_chaotian_ge, check_guiyuan_ge, check_luowen_ge,
    check_longde_ke, check_lu_daoshan_daoxiang,
    check_ma_daoshan_daoxiang, check_guiren_daoshan_daoxiang,
    check_buyuan_methods, SHAN_DOUSHO, analyze_yidu_full, score_doushou_liuxiang,
)
from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen, arrange_tiandi_pan
from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
from engine.daliuren_64ke_rules import keti_tier
from engine.gui_ren_engine import GuiRenCalculator
# ═══ 【2026-09-12 憨爷「按你的建议操作」】类神吉应排序梯次（吉>平>凶）═══
#   与生产 `/api/zeri/batch` **同源**（`engine/zeri_batch_sort.py`，单一真源）。
#   根因：批量 total_score 99.5% 恒=100 → 类神吉应被淹没、`zeri_type` 实质失效。
#   插位：`triple_key` 中 **`he`（日月合朔）之后、`pri`（首选档）之前**；默认排序路径同置 rank_score 之前。
#   env `ZERI_TYPE_TIER=0` → 恒中性 1，逐位回退零回归。
from engine.zeri_batch_sort import type_tier_rank as _type_tier_rank

# ═══ 【2026-09-11 憨爷四次拍板「按原著来」】原著三者定位（张九仪《仪度六壬选日要诀》）═══
#   斗首＝基础 ／ 六壬＝主旨（最重要）／ 演禽＝支节。
#   原文铁证：斗首「**第三章标题**：仪度六壬日课以炉传斗首日课为基础」；
#            六壬「**第二章**：必用六壬内禄马贵人到山到向，以为之主（注解『这是最重要的』）」；
#            演禽「**全书无专章**、词频仅 8（第十一章『演禽窃要…要择徒而授』）」。词频 六壬277｜斗首111｜演禽8。
#   → 演禽（支节）**退出首选档硬门槛**、**退出「短板」**、**降为末位旁证**。
#   ZERI_YUANZHU=0 回退旧口径（演禽作首选档硬门槛 + 决胜层首位 + 计入短板），供 A/B 对照。
YUANZHU = os.environ.get('ZERI_YUANZHU', '1') == '1'
#   斗首＝**基础**（原著「**先**看某山某向…俱用斗首取法…**次**取本山本向禄马贵人」）
#   → 斗首不过基础门槛者**出局**（与生产内核 `_build_zeri_candidate` 的 `斗首<50→None` 同口径）。
#   🔴 env 键统一为 `ZERI_DOUSHO_MIN`（与脚本 `_zeri_marriage_final.py`、课单 HTML 同名，一参数一名）。
#   ZERI_DOUSHO_MIN=0 关闭该门槛；ZERI_YUANZHU=0 亦回退不设门槛（保持旧行为）。
DOUSHO_MIN = float(os.environ.get('ZERI_DOUSHO_MIN', '50'))
from data.斗首择日规则 import DIZHI, GUIREN

# 12时辰
SHICHEN_LIST = list(DIZHI)

# 所有24山
ALL_MOUNTAINS = list(SHAN_JIA_MAP.keys())


@dataclass
class Candidate:
    """日课候选"""
    date_str: str           # '2026-07-15'
    shichen: str            # '巳'
    mountain: str           # '壬'
    nian_gan: str = ''
    nian_zhi: str = ''
    yue_gan: str = ''
    yue_zhi: str = ''
    ri_gan: str = ''
    ri_zhi: str = ''
    shi_gan: str = ''
    shi_zhi: str = ''
    
    # Phase 1 评分
    score_phase1: float = 0
    doushou_details: dict = field(default_factory=dict)
    
    # Phase 2 评分
    score_phase2: float = 0
    daoshan_details: dict = field(default_factory=dict)
    tiandi_pan: dict = None
    
    # Phase 3 评分
    score_phase3: float = 0
    gong_patterns: list = field(default_factory=list)
    huoma_details: dict = field(default_factory=dict)
    advanced_patterns: dict = field(default_factory=dict)
    buyuan_details: dict = field(default_factory=dict)
    # 统一口径拆解项（来自 analyze_yidu_full，三项之和 = total_score，供前端展示）
    yidu_liuxiang: float = 0   # 斗首加分（六想增量 + 三元三武 + 凶在外吉在内）
    yidu_daoshan: float = 0    # 禄马贵人到山到向权威骨架（luma_base）
    yidu_liuren: float = 0     # 六壬课格加分（拱格+活禄马+高级格+补元）
    yidu_result: dict = field(default_factory=dict)
    total_score: float = 0
    grade: str = ''
    # 斗首凶在日时(内)一票否决（2026-08-31 统一口径）：一定不能用，Phase3 直接淘汰
    vetoed: bool = False
    # 三煞方硬性禁忌（2026-09-05）：年支三合对冲方位，四柱地支落入=犯，Phase3 直接淘汰
    san_sha_hit: bool = False
    san_sha_level: str = ''

    # 精度禄马贵人最终分（含课体修正；2026-08-25 加权 6:4 融入排序）
    precision_score: float = 0   # = 禄马贵人到山到向基础 + 课体±修正
    precision_base: float = 0    # 禄马贵人到山到向基础分（合格依据）
    precision_keti: float = 0    # 课体±修正（十三吉课加分/凶课减分）
    rank_score: float = 0        # 排序键 = 综合分×0.6 + 精度最终分×0.4

    # 三传信息
    sanchuan: dict = None

    # 【2026-09-06 三维顶格择日】斗首/演禽/六壬·禄马贵人 各自独立原始分（与 /api/zeri/batch 同源）
    doushou_score: float = 0
    yanqin_score: float = 0
    liuren_score: float = 0
    triple_min: float = 0         # 三维最低分（均衡度/顶格度）
    triple_top: bool = False      # 三维均≥85 = 顶格课
    triple_100: bool = False      # 【2026-09-07 用户新档】三维均=100（斗首/演禽/六壬全满分）最高档
    fa_chuan_ok: bool = False     # 禄马贵人发三传达标（三传禄马贵 ≥2；2026-09-06 铁律硬闸）
    fa_chuan_count: int = 0       # 禄马贵发传数量（0-3，排序用精确值；2026-09-06 分层漏斗）
    pillar_count: int = 0         # 年月日时四柱禄马贵到山到向合格柱数（0-4；2026-09-06 分层漏斗）
    pillar_ymr_ok: bool = False   # 【2026-09-06 用户补充规则】年+月+日禄马贵人"到山到向"达成
                                  #   = 三通道任一：①直接到山到向 ②三传互禄互贵 ③拱禄拱贵拱马(至山向)
                                  #   时柱到向仅作优先项（4柱>3柱），不设硬闸。
    hulu_hugui_ok: bool = False   # 通道②：互禄互贵格命中（禄贵跨柱互成，含坐山禄贵交叉）
    gong_daoshan_ok: bool = False # 通道③：拱禄拱贵拱马命中（check_gong_pillars 已强制拱至山/向）
    doushou_tier: str = ''        # 斗首课格档（2026-09-06 用户方法论分层漏斗）：
                                  #   S=第一吉课/四元/四武  A=三元一武/三元/三武/破鬼把门  B=透元辰/透武财  C=其他
    yanqin_ok: bool = False       # 演禽得时且得地（原 2026-09-06 硬门槛：日禽得时+日禽泊宫吉/中吉）
                                  #   🔴 2026-09-11 憨爷拍板「按原著来」：演禽＝支节 → **不再是硬门槛**，
                                  #   仅作末位旁证（triple_key 最后一位）与展示。ZERI_YUANZHU=0 回退旧口径。
    yanqin_result: dict = field(default_factory=dict)  # 演禽完整分析（供展示得时得地细节）
    riyue_hesu: str = ''          # 【2026-09-07 用户规则】日月合朔类型：'合塑'/'对望'/''（合塑到山向为最优先）
    jike_hits: int = 0            # 十三吉课命中数（2026-09-06：十三吉课为档内择优项）
    dingge: bool = False          # 【2026-09-06 用户拍板新口径】顶格 = 年/月/日/时四柱禄马贵人
                                  #   全到山或到向（pillar_count==4）且 发在三传（sanchuan_qualified）
                                  #   且 三维各≥85；十三吉课（jike_hits）降为档内择优，不再硬闸。

    @property
    def leishen_tier(self) -> int:
        """择日类型类神吉应梯次（吉 2 > 平 1 > 凶 0；2026-09-12「按你的建议」根本解）。

        与生产 `/api/zeri/batch` 同源（`engine/zeri_batch_sort.type_tier_rank`）：
        修「total_score 99.5% 恒=100 → 类神吉应被淹没 → zeri_type 实质失效」。
        `ZERI_TYPE_TIER=0` → 恒 **1（中性）**，逐位回退旧口径（零回归）。
        """
        return _type_tier_rank(
            {'leishen_detail': (self.yidu_result or {}).get('leishen_detail') or {}})

    @property
    def triple_key(self) -> tuple:
        """分层漏斗排序键（2026-09-06 用户方法论 + 降级规则）：
        0. 【用户新规则首选档】六壬顶格(发传≥2+到向≥3+六壬≥85) 且 斗首次顶格(≥80) 且 演禽得时得地
           —— 全三维顶格课天然满足此档且排最前；选不到全顶格时优先出这类课。
        1. 斗首课格档（S第一吉/四元/四武 > A三元一武/三元/三武/破鬼把门 > B透元辰/武财 > C）
        2. 禄马贵到山到向合格柱数（4>3>2>1>0，降序）
        3. 禄马贵发传数量（3>2>1>0，降序；≥2为硬闸）
        4. 十三吉课命中数（择优，降序）
        5. 顶格标签（到向4+发传2+三维85）→ 三维全100 → 全85
        6. 演禽分（决胜层）→ 三维最低分 → 三维和 → 综合分

        【2026-09-11 憨爷拍板「按原著来」· 原著三者定位】YUANZHU=1（默认）时按层级重排：
          斗首＝**基础**（仍保留 ≥80 次顶格门槛，不改）／ 六壬＝**主旨**（发传·到向·六壬分，主序）
          ／ 演禽＝**支节** → ① **退出首选档硬门槛**（原 pri 含 yanqin_ok，已移除）
          ② **退出「短板」**（最低分只比 斗首 与 六壬）③ **降为末位旁证**（原为决胜层首位）。
        ZERI_YUANZHU=0 回退旧口径，供 A/B 对照。

        【2026-09-12 憨爷「按你的建议操作」· 类神吉应梯次】`T = self.leishen_tier`（吉2>平1>凶0）
          插在 **`he`（日月合朔）之后、`pri`（首选档）之前** → `(he, T, pri_flag, ...)`：
          保留 09-07 拍板的「日月合朔最优先」；使**类神吉应优先于首选档/斗首六壬维度的细分**，
          与生产 `/api/zeri/batch` 口径一致（凶应不再越级）。`ZERI_TYPE_TIER=0` → T 恒 1（中性）回退。"""
        d, y, l = self.doushou_score or 0, self.yanqin_score or 0, self.liuren_score or 0
        mn = min(d, y, l)
        # 【2026-09-11 原著口径】演禽（支节）退出「短板」：最低分只比 斗首（基础）与 六壬（主旨）
        mn_zb = min(d, l)
        # 注意：排序处 sort(key=triple_key, reverse=True) —— key 一律用"越大越好"的正分量
        ymr = int(self.pillar_ymr_ok)          # 年月日三柱到向（顶格必备）优先于总柱数
        pc = int(self.pillar_count or 0)
        fc = int(self.fa_chuan_count or 0)
        jh = int(self.jike_hits or 0)
        # 【2026-09-11 憨爷拍板】课体三档：2=十三吉课 > 1=平课(含涉害) > 0=凶课；
        #   置于 jike_hits 之前（十三吉课档先于命中数；平课不再被课经「凶」字压到底）。
        kt = keti_tier(((self.sanchuan or {}).get('课体') or ''))
        # 【用户新规则】六壬顶格（年月日到向 + 发传≥2 + 六壬≥85）＋斗首次顶格＋演禽硬门槛
        lr_ding = int(self.fa_chuan_count >= 2 and self.pillar_ymr_ok and l >= 85)
        ds_ci = int(d >= 80)
        # 【2026-09-11 原著口径】演禽退出首选档硬门槛（斗首＝基础、六壬＝主旨，二者定档）
        _yq_gate = True if YUANZHU else self.yanqin_ok
        pri = int(bool(lr_ding and ds_ci and _yq_gate))
        tier_rank = {'S': 6, 'A': 5, 'B': 4, 'C': 3}.get(self.doushou_tier, 2)
        t100 = int(self.triple_100)            # 三维全100（2026-09-07 用户新档，最高优先）
        # 【2026-09-07 用户规则】日月合朔最优先：合塑到山向=2 > 日月对望=1 > 无=0（置于排序最前）
        he = 2 if self.riyue_hesu == '合塑' else (1 if self.riyue_hesu == '对望' else 0)
        dg = int(self.dingge)
        # 【2026-09-12 类神吉应梯次】吉2 > 平1 > 凶0；env ZERI_TYPE_TIER=0 → 恒 1（中性）
        #   插在 he（日月合朔）之后、pri（首选档）之前 —— 详见本属性 docstring。
        T = self.leishen_tier
        if YUANZHU:
            # 【原著口径】演禽（支节）降至**末位旁证**：短板只比 斗首·六壬，和只取 斗首+六壬，演禽分殿最后
            if pri:
                return (he, T, 1, t100, ymr, pc, fc, round(l, 1), kt, jh, tier_rank, dg,
                        round(mn_zb, 1), round(d + l, 1), self.total_score or 0, round(y, 1))
            return (he, T, 0, tier_rank, t100, ymr, pc, fc, kt, jh, dg,
                    round(mn_zb, 1), round(d + l, 1), self.total_score or 0, round(y, 1))
        if pri:
            # 首选档（用户规则：优先六壬顶格，斗首仅过次顶格门槛）：日月合朔 > 三维全100 > 年月日到向
            return (he, T, 1, t100, ymr, pc, fc, round(l, 1), kt, jh, tier_rank, dg,
                    round(y, 1), round(mn, 1), round(d + y + l, 1), self.total_score or 0)
        # 非首选档：日月合朔 > 课格档 > 三维全100 > 年月日到向 > 总柱数 > 发传 > 课体三档 > 吉课 > …
        return (he, T, 0, tier_rank, t100, ymr, pc, fc, kt, jh, dg,
                round(y, 1), round(mn, 1), round(d + y + l, 1), self.total_score or 0)
    
    def to_dict(self) -> dict:
        """精简输出（去除冗余）"""
        return {
            'date': self.date_str,
            'shichen': self.shichen,
            'mountain': self.mountain,
            'sizhu': f'{self.nian_gan}{self.nian_zhi} {self.yue_gan}{self.yue_zhi} {self.ri_gan}{self.ri_zhi} {self.shi_gan}{self.shi_zhi}',
            'total_score': round(self.total_score, 1),
            'grade': self.grade,
            'phase1_score': round(self.score_phase1, 1),
            'phase2_score': round(self.score_phase2, 1),
            'phase3_score': round(self.score_phase3, 1),
            'rank_score': round(self.rank_score, 1),
            'precision_score': round(self.precision_score, 1),
            'precision_base': round(self.precision_base, 1),
            'precision_keti': round(self.precision_keti, 1),
            'doushou_classes': self.doushou_details.get('classes', {}),
            'yuanchen': self.doushou_details.get('yuanchen_ok', False),
            'sanyuan_grade': self.doushou_details.get('sanyuan_grade', ''),
            'gong_count': len([p for p in self.gong_patterns if p.get('matched')]),
            'gong_names': [p['name'] for p in self.gong_patterns if p.get('matched')],
            'huoma_count': self.huoma_details.get('count', 0),
            'daoshan_count': self.daoshan_details.get('total_count', 0),
            'vetoed': self.vetoed,
            'san_sha_hit': self.san_sha_hit,
            'san_sha_level': self.san_sha_level,
            # 2026-09-06 三维顶格择日：斗首/演禽/六壬独立分 + 顶格标记
            'doushou_score': round(self.doushou_score, 1),
            'yanqin_score': round(self.yanqin_score, 1),
            'liuren_score': round(self.liuren_score, 1),
            'triple_min': round(self.triple_min, 1),
            'triple_top': self.triple_top,
            'triple_100': self.triple_100,
            'riyue_hesu': self.riyue_hesu,
            'fa_chuan_ok': self.fa_chuan_ok,
            'fa_chuan_count': self.fa_chuan_count,
            'pillar_count': self.pillar_count,
            'pillar_ymr_ok': self.pillar_ymr_ok,
            'hulu_hugui_ok': self.hulu_hugui_ok,
            'gong_daoshan_ok': self.gong_daoshan_ok,
            'doushou_tier': self.doushou_tier,
            'yanqin_ok': self.yanqin_ok,
            'jike_hits': self.jike_hits,
            'dingge': self.dingge,
            # 【2026-09-11 留痕】原著三者定位生效标志（1=斗首基础/六壬主旨/演禽支节·末位旁证）
            'yuanzhu_mode': YUANZHU,
            # 择日类型类神吉应（2026-09-06 方案A-L3：{end,narr,leishen}，前端叙事/徽标用）
            'leishen_detail': (self.yidu_result or {}).get('leishen_detail', {}) or {},
        }


class BatchZeriOptimizer:
    """
    批量择日优化器
    三阶段漏斗筛选 + 最终排名
    """
    
    def __init__(self, start_date: date, end_date: date,
                 mountains: List[str] = None,
                 phase1_top: int = 500,
                 phase2_top: int = 50,
                 phase3_top: int = 20,
                 verbose: bool = True,
                 ben_ming: str = None, ben_ming_gan: str = None,
                 ben_ming2: str = None, ben_ming2_gan: str = None,
                 zeri_type: str = '',
                 top_triple: bool = False,
                 auto_extend: bool = False,
                 min_top: int = 5,
                 max_years: int = 30):
        """
        参数:
            start_date: 起始日期
            end_date: 结束日期
            mountains: 要分析的24山列表（默认全部）
            phase1_top: Phase1 每山保留候选数
            phase2_top: Phase2 每山保留候选数
            phase3_top: Phase3 每山最终输出数
            verbose: 是否输出进度
            ben_ming: 祭主（福主）本命地支（2026-09-05 起影响本命贵人/作禄作马加分）
            ben_ming_gan: 祭主（福主）本命天干（判定命禄用，可缺省）
            ben_ming2: 第二命主本命地支（2026-09-11 双命主；婚嫁＝女命，与本命各计一次）
            ben_ming2_gan: 第二命主本命天干（判定命禄用，可缺省）
            zeri_type: 择日类型（2026-09-06 方案A-L3：作灶/提车/安门…类神吉应微调，空则跳过）
            top_triple: 顶格择日（2026-09-06 用户口径）：排序键改三维顶格度
                       （先斗首/演禽/六壬全100 → 全≥85 → 最低分大 → 三维和高）
            auto_extend: 窗口顺延（2026-09-06）：默认90天起步，每山候选不足 min_top 时
                       自动 +90 天续扫，直到凑齐或达 max_years（用户口径"一直往后推"）
            min_top: 每山至少保留候选数（auto_extend 停窗条件）
            max_years: 顺延年数上限（默认30年保护，防失控长跑）
        """
        self.start_date = start_date
        self.end_date = end_date
        self.mountains = mountains or ALL_MOUNTAINS
        self.phase1_top = phase1_top
        self.phase2_top = phase2_top
        self.phase3_top = phase3_top
        self.verbose = verbose
        self.ben_ming = ben_ming
        self.ben_ming_gan = ben_ming_gan
        self.ben_ming2 = ben_ming2
        self.ben_ming2_gan = ben_ming2_gan
        self.zeri_type = zeri_type or ''
        self.top_triple = top_triple
        self.auto_extend = auto_extend
        self.min_top = min_top
        self.max_years = max_years
        
        # 预计算缓存
        self._sizhu_cache: Dict[str, dict] = {}  # key: "YYYY-MM-DD"
        self._luma_engine = DaLiuRenLuMaGuiRen()
        self._tiandi_pan_cache: Dict[str, dict] = {}  # key: "月将_时辰"
        
        # 统计
        self.stats = {
            'days': 0, 'phase1_checked': 0, 'phase2_checked': 0, 'phase3_checked': 0,
            'phase1_candidates': 0, 'phase2_candidates': 0, 'phase3_candidates': 0,
        }
    
    def _log(self, msg: str):
        if self.verbose:
            print(msg)
    
    # ═══════════════════════════════════════════════
    # 预计算：全日期范围四柱
    # ═══════════════════════════════════════════════
    
    def precompute_sizhu(self):
        """预计算整个日期范围内所有四柱（年/月/日）"""
        self._log(f'\n[预计算] 计算 {self.start_date} ~ {self.end_date} 四柱...')
        t0 = time.time()
        
        current = self.start_date
        while current <= self.end_date:
            key = current.strftime('%Y-%m-%d')
            sizhu = get_sizhu(current.year, current.month, current.day, '子')
            self._sizhu_cache[key] = {
                'nian_gan': sizhu['年柱'][0],
                'nian_zhi': sizhu['年柱'][1],
                'yue_gan': sizhu['月柱'][0],
                'yue_zhi': sizhu['月柱'][1],
                'ri_gan': sizhu['日柱'][0],
                'ri_zhi': sizhu['日柱'][1],
            }
            current += timedelta(days=1)
        
        elapsed = time.time() - t0
        self.stats['days'] = len(self._sizhu_cache)
        self._log(f'[预计算] 完成 {self.stats["days"]} 天，耗时 {elapsed:.1f}s')
    
    # ═══════════════════════════════════════════════
    # Phase 1: 斗首快筛
    # ═══════════════════════════════════════════════
    
    def _score_phase1(self, nian_gan: str, nian_zhi: str,
                       yue_gan: str, yue_zhi: str,
                       ri_gan: str, ri_zhi: str,
                       shi_gan: str, shi_zhi: str,
                       mountain: str) -> Tuple[float, dict]:
        """
        Phase 1 快筛：与单课权威评分 analyze_yidu_full 的 A 段（斗首六想）同口径。
        仅用 O(1) 斗首规则，不做六壬；最终排名以 Phase 3 的 analyze_yidu_full 分为准。
        （去掉原自研「元辰±」「贪破在六相」扣分，避免误杀权威高分课）
        """
        year_pillar = nian_gan + nian_zhi
        month_pillar = yue_gan + yue_zhi
        day_pillar = ri_gan + ri_zhi
        hour_pillar = shi_gan + shi_zhi

        # 六想评分（与权威分析一致的基础分）
        liuxiang = score_doushou_liuxiang(year_pillar, month_pillar, day_pillar, hour_pillar, mountain)
        score = liuxiang['score']

        # 斗首类别 + 三元三武一廉
        classes = {
            '年': get_doushou_class(mountain, year_pillar),
            '月': get_doushou_class(mountain, month_pillar),
            '日': get_doushou_class(mountain, day_pillar),
            '时': get_doushou_class(mountain, hour_pillar),
        }
        sanyuan = check_sanyuan_sanwu_yilian(
            classes['年'], classes['月'], classes['日'], classes['时']
        )
        if sanyuan.get('is_first_jike'):
            score += 15
        elif sanyuan.get('grade'):
            score += 8

        # 凶吉内外
        jixiong = check_jixiong_position(classes)
        score += jixiong['score']

        # 元辰仅作合格性记录（不参与快筛分，与权威评分口径一致）
        yuanchen_ok = check_sizhu_tou_yuanchen(
            year_pillar, month_pillar, day_pillar, hour_pillar, mountain
        ).get('has_yuanchen', False)
        # 【2026-09-06 分层漏斗·斗首课格档】S=第一吉/四元/四武  A=三元一武/三元/三武/破鬼把门
        #   B=透元辰或透武财  C=其他。破鬼把门=破鬼独居年干（check_sanyuan_sanwu_yilian 已判 has_xiong 豁免）。
        _grade = sanyuan.get('grade', '') or ''
        wu_tou = any(c == '武财' for c in classes.values())
        if _grade in ('第一吉课', '四元大吉', '四武大吉'):
            tier = 'S'
        elif _grade in ('破鬼把门', '三元一武大吉', '三元格局', '三武格局'):
            tier = 'A'
        elif yuanchen_ok or wu_tou:
            tier = 'B'
        else:
            tier = 'C'

        details = {
            'classes': classes,
            'sanyuan_grade': sanyuan.get('grade', ''),
            'liuxiang_score': liuxiang['score'],
            'yuanchen_ok': yuanchen_ok,
            'doushou_tier': tier,
        }
        return max(20, min(100, score)), details
    
    def run_phase1(self) -> Dict[str, List[Candidate]]:
        """
        Phase 1: 遍历所有日期×时辰×山，斗首评分后保留每山TOP-N
        """
        self._log(f'\n[Phase 1] 斗首快筛: {len(self._sizhu_cache)}天 × 12时辰 × {len(self.mountains)}山')
        self._log(f'[Phase 1] 预计检查 {len(self._sizhu_cache) * 12 * len(self.mountains):,} 次')
        t0 = time.time()
        
        # 每山保留TOP candidate
        mountain_candidates: Dict[str, List[Candidate]] = {
            m: [] for m in self.mountains
        }
        
        checked = 0
        # 【2026-09-06 分层漏斗·日层资格预筛】对每山预取"元辰干∪武财干"集合（寅山=丁壬∪甲己…），
        #   年月日三干无一落入 → 该山整日 12 时辰跳过（×12 省算力，等价"只找元辰/武财日"）。
        _shan_ygwc = {m: (
            set(get_yuanchen_gans(m)),
            {g for g in '甲乙丙丁戊己庚辛壬癸' if get_doushou_class(m, g + '子') == '武财'},
        ) for m in self.mountains}
        for date_key, sizhu in self._sizhu_cache.items():
            nian_gan = sizhu['nian_gan']
            nian_zhi = sizhu['nian_zhi']
            yue_gan = sizhu['yue_gan']
            yue_zhi = sizhu['yue_zhi']
            ri_gan = sizhu['ri_gan']
            ri_zhi = sizhu['ri_zhi']
            
            # 日干日支不变，但时柱随时辰变
            _ydy3 = [int(x) for x in date_key.split('-')]
            for shichen in SHICHEN_LIST:
                # 【2026-09-06 交节时刻切分修复】年/月柱按时辰重算：
                #   交节当日交节时刻之前的时辰仍属旧年/旧月（旧逻辑按公历日0点整体错判新月）。
                try:
                    _yg_ = get_year_ganzhi(_ydy3[0], _ydy3[1], _ydy3[2], shichen)
                    _mg_ = get_month_ganzhi(_ydy3[0], _ydy3[1], _ydy3[2], shichen)
                    nian_gan, nian_zhi = _yg_
                    yue_gan, yue_zhi = _mg_
                except Exception:
                    pass  # 失败保底：沿用天级缓存年/月柱
                shi_gan, shi_zhi = get_hour_ganzhi(ri_gan, shichen)
                
                for mountain in self.mountains:
                    _yg, _wg = _shan_ygwc[mountain]
                    if not ({nian_gan, yue_gan, ri_gan} & (_yg | _wg)):
                        continue  # 年月日无一元辰/武财干 → 该山今日全部时辰跳过
                    checked += 1
                    score, details = self._score_phase1(
                        nian_gan, nian_zhi, yue_gan, yue_zhi,
                        ri_gan, ri_zhi, shi_gan, shi_zhi, mountain
                    )
                    
                    # 阈值过滤：至少 35 分才考虑
                    if score < 35:
                        continue
                    
                    cand = Candidate(
                        date_str=date_key,
                        shichen=shichen,
                        mountain=mountain,
                        nian_gan=nian_gan, nian_zhi=nian_zhi,
                        yue_gan=yue_gan, yue_zhi=yue_zhi,
                        ri_gan=ri_gan, ri_zhi=ri_zhi,
                        shi_gan=shi_gan, shi_zhi=shi_zhi,
                        score_phase1=score,
                        doushou_details=details,
                        doushou_tier=(details or {}).get('doushou_tier', ''),
                    )
                    
                    # 每山保留TOP-N：heapq 最小堆存 (-score,序,cand)，取前 p1_top 高分（240年窗口必经）
                    heap = mountain_candidates[mountain]
                    _entry = (-score, checked, cand)
                    if len(heap) < self.phase1_top:
                        heapq.heappush(heap, _entry)
                    elif _entry < heap[0]:
                        heapq.heapreplace(heap, _entry)
        
        # 还原按 score_phase1 降序（与原 append+sort 输出语义一致）
        for m in mountain_candidates:
            mountain_candidates[m] = [c for _, _, c in
                                      sorted(mountain_candidates[m], key=lambda e: -e[0])]
        
        self.stats['phase1_checked'] = checked
        elapsed = time.time() - t0
        
        total_candidates = sum(len(v) for v in mountain_candidates.values())
        self.stats['phase1_candidates'] = total_candidates
        
        self._log(f'[Phase 1] 完成: 检查{checked:,}次, 保留{total_candidates:,}候选, 耗时{elapsed:.1f}s')
        for m in sorted(mountain_candidates.keys())[:5]:
            c = mountain_candidates[m]
            if c:
                top_score = c[0].score_phase1
                self._log(f'  {m}山: {len(c)}候选, 最高分 {top_score}')
        
        return mountain_candidates
    
    # ═══════════════════════════════════════════════
    # Phase 2: 天地盘 + 到山到向
    # ═══════════════════════════════════════════════
    
    def _score_phase2(self, cand: Candidate) -> Tuple[float, dict]:
        """
        Phase 2 评分：天地盘 + 到山到向
        满分 20 分
        """
        score = 0
        details = {}
        
        # 计算月将（按《大六壬通解》节气中气，2026-08-15 憨爷指正：原按地支月错误）
        _yd = cand.date_str.split('-')
        yuejiang = self._luma_engine.get_yuejiang_by_date(int(_yd[0]), int(_yd[1]), int(_yd[2]))
        tiandi_pan = arrange_tiandi_pan(yuejiang, cand.shichen)
        cand.tiandi_pan = tiandi_pan
        
        shan_jia = SHAN_JIA_MAP.get(cand.mountain, '')
        xiang_shou = XIANG_SHOU.get(cand.mountain, shan_jia)
        
        # 到山到向
        lu_zhi = LU.get(cand.ri_gan, '')
        ma_zhi = get_yima(cand.ri_zhi)
        guiren_zhi = list(GUIREN.get(cand.ri_gan, []))
        
        lu_dsdx = check_lu_daoshan_daoxiang(lu_zhi, shan_jia, xiang_shou)
        ma_dsdx = check_ma_daoshan_daoxiang(ma_zhi, shan_jia, xiang_shou)
        guiren_dsdx = check_guiren_daoshan_daoxiang(guiren_zhi, shan_jia, xiang_shou)
        
        dsdx_count = sum([lu_dsdx['is_daoshan_daoxiang'],
                          ma_dsdx['is_daoshan_daoxiang'],
                          guiren_dsdx['is_daoshan_daoxiang']])
        
        details = {
            'lu': lu_dsdx, 'ma': ma_dsdx, 'guiren': guiren_dsdx,
            'total_count': dsdx_count,
        }
        
        # 到山到向得分: 每项+5, 全中+5 bonus
        score += dsdx_count * 5
        if dsdx_count >= 2:
            score += 5  # bonus
        
        # 朝天格/归垣格 (Phase 2能判断)
        chaotian = check_chaotian_ge(tiandi_pan, cand.ri_gan, guiren_zhi)
        guiyuan = check_guiyuan_ge(tiandi_pan, cand.ri_zhi, guiren_zhi)
        if chaotian['matched']:
            score += 5
            details['chaotian'] = True
        if guiyuan['matched']:
            score += 3
            details['guiyuan'] = True
        
        return min(20, score), details
    
    def run_phase2(self, mountain_candidates: Dict[str, List[Candidate]]) -> Dict[str, List[Candidate]]:
        """
        Phase 2: 对Phase1候选计算天地盘+到山到向，每山保留TOP
        """
        self._log(f'\n[Phase 2] 到山到向分析: {sum(len(v) for v in mountain_candidates.values()):,}候选')
        t0 = time.time()
        
        checked = 0
        for mountain, candidates in mountain_candidates.items():
            for cand in candidates:
                checked += 1
                score, details = self._score_phase2(cand)
                cand.score_phase2 = score
                cand.daoshan_details = details
                # 累计分数
                cand.total_score = cand.score_phase1 + cand.score_phase2
            
            # 按总分开排序，保留TOP
            candidates.sort(key=lambda c: c.total_score, reverse=True)
            if len(candidates) > self.phase2_top:
                del candidates[self.phase2_top:]
        
        self.stats['phase2_checked'] = checked
        elapsed = time.time() - t0
        total_candidates = sum(len(v) for v in mountain_candidates.values())
        self.stats['phase2_candidates'] = total_candidates
        
        self._log(f'[Phase 2] 完成: 检查{checked:,}候选, 保留{total_candidates:,}, 耗时{elapsed:.1f}s')
        
        return mountain_candidates
    
    # ═══════════════════════════════════════════════
    # Phase 3: 完整六壬 (三传 + 拱格 + 活禄马)
    # ═══════════════════════════════════════════════
    
    def _score_phase3(self, cand: Candidate) -> Tuple[float, dict]:
        """
        Phase 3 评分：完整六壬分析（与单课 /api/zeri/analyze 同口径）
        —— 改用 sike_sanchuan_engine 起课（修双引擎），直接调用权威函数
           analyze_yidu_full 取最终评分（与单课详情完全一致，统一口径）。
        返回: (total_score, yidu_result_dict)
        """
        try:
            calc = SiKeSanChuanCalculator2()
            _yd = cand.date_str.split('-')
            yuejiang = self._luma_engine.get_yuejiang_by_date(int(_yd[0]), int(_yd[1]), int(_yd[2]))
            tdp = calc.get_tiandi_pan(yuejiang, cand.shichen)
            cand.tiandi_pan = tdp

            # 四课三传（统一引擎）
            sike = calc.qi_sike(cand.ri_gan, cand.ri_zhi, tdp)
            sc = calc.fa_sanchuan(sike, cand.ri_gan, cand.ri_zhi, tdp)
            # 【2026-09-06 修复】fa_sanchuan 键为 初传/中传/末传（'三传' 键不存在），
            #   原用 sc.get('三传', []) 致 chuan_list 恒空 → 候选三传全空 →
            #   类神吉应恒"不入传平" + 活禄马/禄马发传等加分全失效
            chuan_list = sc.get('三传', []) or [
                sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')]
            sanchuan = {
                '初传': chuan_list[0] if len(chuan_list) > 0 else '',
                '中传': chuan_list[1] if len(chuan_list) > 1 else '',
                '末传': chuan_list[2] if len(chuan_list) > 2 else '',
                '课体': sc.get('课体', ''),
            }
            cand.sanchuan = sanchuan

            # 天将映射（用于龙德课等，与单课同口径）
            _tj_map = GuiRenCalculator().arrange_gui_ren_pan(
                cand.ri_gan, {'天地对应': tdp}, cand.shichen)
            tianjiang_map = _tj_map.get('天将映射', {})

            # 权威评分（与单课 /api/zeri/analyze 完全一致的引擎 + 公式 + 评级线）
            yidu = analyze_yidu_full(
                shan=cand.mountain,
                year_pillar=cand.nian_gan + cand.nian_zhi,
                month_pillar=cand.yue_gan + cand.yue_zhi,
                day_pillar=cand.ri_gan + cand.ri_zhi,
                hour_pillar=cand.shi_gan + cand.shi_zhi,
                ri_gan=cand.ri_gan,
                ri_zhi=cand.ri_zhi,
                sanchuan=sanchuan,
                tiandi_pan=tdp,
                tianjiang_map=tianjiang_map,
                yue_jiang=yuejiang,
                nian_zhi=cand.nian_zhi,
                shichen=cand.shichen,
                ke_ti=sanchuan.get('课体', '') or None,
                year=int(_yd[0]), month=int(_yd[1]), day=int(_yd[2]),
                ben_ming=self.ben_ming,
                ben_ming_gan=self.ben_ming_gan,
                ben_ming2=self.ben_ming2,
                ben_ming2_gan=self.ben_ming2_gan,
                # 2026-09-06 方案A-L3：择日类型类神吉应（与单课同口径；空则跳过）
                zeri_type=self.zeri_type,
            )

            # 挂接结果
            cand.gong_patterns = yidu.get('gong_patterns', [])
            cand.daoshan_details = yidu.get('daoshan_daoxiang', {})
            cand.huoma_details = yidu.get('huoma_huolu', {})
            cand.buyuan_details = yidu.get('buyuan', {})
            cand.advanced_patterns = yidu.get('advanced_patterns', {})
            cand.yidu_result = yidu

            # 拆解三项（供前端"斗首+到向+六壬"展示，三项之和 = total；2026-08-31 统一口径）
            cand.yidu_liuxiang = float(yidu.get('doushou_bonus', 0))   # 斗首加分（六想增量+三元三武+凶外吉内）
            cand.yidu_daoshan = float(yidu.get('luma_base', 0))        # 禄马贵人到山到向权威骨架
            cand.yidu_liuren = float(yidu['total_score'] - cand.yidu_liuxiang - cand.yidu_daoshan)  # 六壬拱/活禄马/高级/补元

            # 精度禄马贵人最终分（含课体修正）——加权 6:4 融入排序（2026-08-25）
            try:
                _yd = cand.date_str.split('-')
                # 【2026-09-05 日期传参健壮化】原位置参数传 int(_yd[0..2])（依赖参数顺序脆弱），
                #   改关键字显式传 year/month/day，与 analyze_full_with_sanchuan 日期参数明确对应。
                _p = self._luma_engine.analyze_full_with_sanchuan(
                    cand.mountain, cand.shichen,
                    cand.nian_gan, cand.nian_zhi,
                    cand.yue_gan, cand.yue_zhi,
                    cand.ri_gan, cand.ri_zhi,
                    cand.shi_gan, cand.shi_zhi,
                    sanchuan=cand.sanchuan,
                    year=int(_yd[0]), month=int(_yd[1]), day=int(_yd[2]),
                ).get('precision', {})
                cand.precision_score = float(_p.get('precision_score', 0))
                cand.precision_base = float(_p.get('base_score', cand.precision_score))
                cand.precision_keti = float(_p.get('keti_score', 0))
            except Exception:
                cand.precision_score = cand.precision_base = cand.precision_keti = 0.0

            # 【2026-09-06 三维顶格】斗首/演禽/六壬·禄马贵人 独立原始分（与 /api/zeri/batch 同源）
            #   顶格排序与"全100/全85"判定依赖三者；任一失败该维记 0（拖低 triple_top 不误杀）。
            try:
                from engine.douhou_analyzer import DouhouKegeAnalyzer as _DHA
                _szd = {'年柱': cand.nian_gan + cand.nian_zhi, '月柱': cand.yue_gan + cand.yue_zhi,
                        '日柱': cand.ri_gan + cand.ri_zhi, '时柱': cand.shi_gan + cand.shi_zhi}
                cand.doushou_score = float(_DHA().analyze_kege(cand.mountain, _szd).get('综合评分', 0) or 0)
            except Exception:
                cand.doushou_score = 0.0
            try:
                from engine.yanqin_analyzer import YanQinAnalyzer as _YQA
                _szd2 = {'年柱': cand.nian_gan + cand.nian_zhi, '月柱': cand.yue_gan + cand.yue_zhi,
                         '日柱': cand.ri_gan + cand.ri_zhi, '时柱': cand.shi_gan + cand.shi_zhi}
                cand.yanqin_result = _YQA().analyze_yanqin_with_calendar(
                    _szd2, int(_yd[0]), int(_yd[1]), int(_yd[2]))
                cand.yanqin_score = float(cand.yanqin_result.get('综合评分', 0) or 0)
                # 【2026-09-06 用户规则·演禽硬门槛】得时（格局=日禽得时）且 得地（日禽泊宫吉/中吉）
                _ge = cand.yanqin_result.get('格局判定', []) or []
                _deshi = any(str(g.get('格局名称', '')) == '日禽得时' for g in _ge)
                _po = cand.yanqin_result.get('泊宫', {}) or {}
                _dedi = str((_po.get('日禽') or {}).get('吉凶', '')) in ('吉', '中吉')
                cand.yanqin_ok = bool(_deshi and _dedi)
            except Exception:
                cand.yanqin_score = 0.0
                cand.yanqin_ok = False
            try:
                _lr3 = self._luma_engine.calculate_new_score(
                    cand.mountain, cand.shichen, cand.nian_gan, cand.nian_zhi,
                    cand.yue_gan, cand.yue_zhi, cand.ri_gan, cand.ri_zhi,
                    cand.shi_gan, cand.shi_zhi,
                    sanchuan=cand.sanchuan, ke_ti_list=None, yuejiang=yuejiang,
                    # 【2026-09-07】日月合朔真实天文需公历日期（朔/望取自 sxtwl 农历日）
                    year=int(cand.date_str.split('-')[0]), month=int(cand.date_str.split('-')[1]),
                    day=int(cand.date_str.split('-')[2]))
                cand.liuren_score = float(_lr3.get('final_score', 0) or 0)
            except Exception:
                cand.liuren_score = 0.0
            cand.triple_min = min(cand.doushou_score, cand.yanqin_score, cand.liuren_score)
            cand.triple_top = cand.triple_min >= 85
            # 【2026-09-07 用户新档】三维全=100（斗首/演禽/六壬全满分）最高档
            cand.triple_100 = bool(cand.doushou_score >= 100 and cand.yanqin_score >= 100
                                   and cand.liuren_score >= 100)
            # 【2026-09-07 用户规则】日月合朔（合塑到山向/对望）：取 calculate_new_score 输出；排序最优先
            try:
                cand.riyue_hesu = str((_lr3 or {}).get('riyue_hesu_type') or '')
            except Exception:
                cand.riyue_hesu = ''
            # 【2026-09-06 分层漏斗排序字段】发传数（硬闸 ≥2，**年月日**禄马贵口径）+ 到向合格柱数
            #   （用户拍板：年月日禄马贵人未发三传不合次格课 → 发传<2 直接淘汰，不排最后凑数；
            #    时柱禄马贵人仅作优先项，不计入发传硬闸）
            try:
                _lmg_cnt = self._luma_engine.check_ymr_sanchuan_luma_guiren_count(
                    cand.sanchuan, cand.nian_gan, cand.nian_zhi,
                    cand.yue_gan, cand.yue_zhi, cand.ri_gan, cand.ri_zhi,
                    tdp, cand.shichen)
            except Exception:
                _lmg_cnt = 0
            cand.fa_chuan_count = int(_lmg_cnt or 0)
            cand.fa_chuan_ok = cand.fa_chuan_count >= 2
            cand.pillar_count = int((_lr3 or {}).get('pillar_qualified_count', 0) or 0)
            # 【2026-09-06 用户补充规则】顶格必备=年+月+日禄马贵人"到山到向"，三通道任一达成：
            #   A.严格直达（禄马贵加临后正好落山家/向首，不含三合次吉——2026-09-07 用户拍板）
            #   B.三传互禄互贵  C.拱禄拱贵拱马(至山向)。
            #   （时柱到向仅作优先项，不设硬闸）
            try:
                _sja = SHAN_JIA_MAP.get(cand.mountain, '')
                _xsh = XIANG_SHOU.get(cand.mountain, _sja)
                # 【2026-09-07 严格直达口径】check_single_pillar 的 lu_to_shan/xiang、ma_to_shan/xiang、
                #   guiren_to_shan/xiang（不含 sanhe）逐柱判"该柱禄马贵至少一者直达山向"。
                def _pillar_strict(g, z):
                    _sp = self._luma_engine.check_single_pillar(
                        g, z, tdp, cand.shichen, _sja, _xsh, '')
                    return bool((_sp.get('lu_to_shan') or _sp.get('lu_to_xiang') or
                                 _sp.get('ma_to_shan') or _sp.get('ma_to_xiang') or
                                 _sp.get('guiren_to_shan') or _sp.get('guiren_to_xiang')))
                _direct_ok = all(
                    _pillar_strict(g, z)
                    for g, z in ((cand.nian_gan, cand.nian_zhi),
                                 (cand.yue_gan, cand.yue_zhi),
                                 (cand.ri_gan, cand.ri_zhi)))
                # 通道B：互禄互贵（禄贵跨柱互成；含坐山贵人/坐山禄交叉通道）
                try:
                    _hh = self._luma_engine.check_hulu_hugui(
                        cand.nian_gan, cand.yue_gan, cand.ri_gan,
                        self.ben_ming_gan, cand.mountain, cand.yue_zhi)
                    cand.hulu_hugui_ok = bool(_hh.get('is_mutual_lu_gui'))
                except Exception:
                    cand.hulu_hugui_ok = False
                # 通道C：拱禄拱贵拱马（check_gong_pillars 内置"拱至山家/向首"收紧）
                try:
                    _gp = self._luma_engine.check_gong_pillars(
                        cand.nian_gan, cand.nian_zhi,
                        cand.yue_gan, cand.yue_zhi,
                        cand.ri_gan, cand.ri_zhi,
                        cand.shi_gan, cand.shi_zhi,
                        ben_ming=self.ben_ming, mountain=cand.mountain)
                    cand.gong_daoshan_ok = bool(_gp.get('has_gong'))
                except Exception:
                    cand.gong_daoshan_ok = False
                cand.pillar_ymr_ok = bool(_direct_ok or cand.hulu_hugui_ok or cand.gong_daoshan_ok)
            except Exception:
                cand.pillar_ymr_ok = False
            # 【2026-09-06 十三吉课降为档内择优】jike_hits 取自 analyze 的 luma_detail.keti_adjust
            _kd = ((yidu or {}).get('luma_detail') or {}).get('keti_adjust') or {}
            cand.jike_hits = int(_kd.get('jike_hits', 0) or 0)
            # 【2026-09-07 用户拍板：真顶格=演禽得时得地】顶格口径（用户拍板+补充）=
            #   年/月/日三柱均到山到向 AND 发在三传≥2 AND 三维各≥85 AND 演禽得时且得地（yanqin_ok）；
            #   时柱到向仅作优先项（4柱>3柱）；十三吉课交由 triple_key 档内择优。
            # 【2026-09-11 憨爷拍板「按原著来」】演禽＝支节 → 退出顶格硬门槛、退出「短板」；
            #   顶格只由 斗首（基础）与 六壬（主旨）之最低分界定。ZERI_YUANZHU=0 回退旧口径。
            _mn_zb = min(cand.doushou_score, cand.liuren_score) if YUANZHU else cand.triple_min
            _yq_gate = True if YUANZHU else cand.yanqin_ok
            cand.dingge = bool(_lmg_cnt >= 2 and cand.pillar_ymr_ok
                               and _mn_zb >= 85 and _yq_gate)

            return yidu['total_score'], yidu
        except Exception as e:
            cand.gong_patterns = []
            cand.daoshan_details = {}
            cand.huoma_details = {}
            cand.yidu_liuxiang = cand.yidu_daoshan = cand.yidu_liuren = 0
            cand.precision_score = cand.precision_base = cand.precision_keti = 0.0
            cand.yidu_result = {'error': str(e)}
            return 0.0, {'error': str(e)}
    
    def run_phase3(self, mountain_candidates: Dict[str, List[Candidate]]) -> Dict[str, List[Candidate]]:
        """
        Phase 3: 对Phase2候选计算完整六壬，最终排名
        """
        total = sum(len(v) for v in mountain_candidates.values())
        self._log(f'\n[Phase 3] 完整六壬分析: {total:,}候选（三传计算较慢）')
        t0 = time.time()
        
        checked = 0
        for mountain, candidates in mountain_candidates.items():
            for cand in candidates:
                checked += 1
                try:
                    yidu_total, yidu = self._score_phase3(cand)
                except Exception as e:
                    yidu_total, yidu = 0.0, {'error': str(e)}

                # 统一口径：综合分 = 权威 analyze_yidu_full 分（与单课一致，含斗首/拱/到向/补元）
                cand.total_score = yidu_total
                cand.grade = yidu.get('grade', '不宜')
                # 斗首凶在日时(内)一票否决（2026-08-31 统一口径）：一定不能用，稍后直接淘汰
                cand.vetoed = bool(yidu.get('vetoed', False))
                # 三煞方硬性禁忌（2026-09-05）：犯三煞一票淘汰（不参与排名）
                _ss = yidu.get('san_sha', {}) or {}
                cand.san_sha_hit = bool(_ss.get('hit', False))
                cand.san_sha_level = str(_ss.get('level', ''))
                # 排序键 = 综合分×0.6 + 精度最终分(含课体修正)×0.4（2026-08-25 用户拍板 6:4）
                cand.rank_score = round(yidu_total * 0.6 + cand.precision_score * 0.4, 2)
                # 前端"斗首/到向/六壬"三项展示（来自 yidu 拆解，三项之和 = total）
                cand.score_phase1 = cand.yidu_liuxiang
                cand.score_phase2 = cand.yidu_daoshan
                cand.score_phase3 = cand.yidu_liuren
            
            # 【2026-08-31 统一口径】斗首凶在日时(内)一票否决：一定不能用，直接淘汰该候选
            # 【2026-09-05】三煞方硬性禁忌（"日课不可犯"）：犯三煞同样直接淘汰
            # 【2026-09-06 用户拍板】年月日禄马贵人未发三传（<2）不合次格课 → 一并淘汰
            # 【2026-09-11 憨爷拍板「按原著来」】斗首＝**基础** → 不过基础门槛（默认 <50）者**出局**。
            #   原著「**先**看某山某向…俱用斗首取法…**次**取本山本向禄马贵人」＋
            #   生产内核 `_build_zeri_candidate` 已有同口径快筛 `斗首<50→None`。
            #   ZERI_DOUSHO_MIN=0 或 ZERI_YUANZHU=0 时不设此门槛（保持旧行为）。
            def _pass_dousho(c):
                if not YUANZHU or DOUSHO_MIN <= 0:
                    return True
                return float(c.doushou_score or 0) >= DOUSHO_MIN
            candidates[:] = [c for c in candidates
                             if not c.vetoed and not c.san_sha_hit and c.fa_chuan_ok
                             and _pass_dousho(c)]
            # 排序：默认按综合×0.6+精度×0.4；top_triple（2026-09-06）改按三维顶格度
            #   （先斗首/演禽/六壬全100 → 全≥85 → 最低分大 → 三维和高 → 综合高）
            # 【2026-09-12 类神吉应梯次】默认路径亦置**类神梯次于 `rank_score` 之前**
            #   （与生产 `/api/zeri/batch` 同源：禄马贵人首键之后、斗首六壬加权分之前）；
            #   `ZERI_TYPE_TIER=0` → 梯次恒 1 → 与旧口径**逐位一致**（零回归）。
            #   top_triple 路径已由 `triple_key` 内含 T，无需重复。
            if self.top_triple:
                candidates.sort(key=lambda c: c.triple_key, reverse=True)
            else:
                candidates.sort(key=lambda c: (c.leishen_tier, c.rank_score), reverse=True)
            if len(candidates) > self.phase3_top:
                del candidates[self.phase3_top:]
        
        self.stats['phase3_checked'] = checked
        elapsed = time.time() - t0
        total_candidates = sum(len(v) for v in mountain_candidates.values())
        self.stats['phase3_candidates'] = total_candidates
        
        self._log(f'[Phase 3] 完成: 检查{checked:,}候选, 保留{total_candidates:,}, 耗时{elapsed:.1f}s')
        
        return mountain_candidates
    
    # ═══════════════════════════════════════════════
    # 主流程 + 结果导出
    # ═══════════════════════════════════════════════
    
    def optimize(self) -> Dict[str, List[Candidate]]:
        """
        完整三阶段优化流程。
        返回: {mountain: [Candidate, ...]}
        auto_extend=True（2026-09-06 用户口径"一直往后推"）：从 start_date 起 90 天窗口，
        每山候选 < min_top 或尚无顶格课(三维≥85)时，自动 +90 天续扫至 max_years 上限，
        直到凑齐；排序始终按顶格度/triple_key（top_triple=True 时）。
        """
        if self.auto_extend:
            return self._optimize_extended()
        return self._optimize_window(self.start_date, self.end_date)

    def _optimize_window(self, start_date: date, end_date: date) -> Dict[str, List[Candidate]]:
        """单窗口三阶段优化（抽出供分段循环复用）。"""
        # 同步 self 日期（顺延模式下 end_date 可能为 None，precompute/run_phase* 均读 self）
        self.start_date = start_date
        self.end_date = end_date
        # 【2026-09-06 分段独立】清空 sizhu 缓存：precompute_sizhu 不清缓存会把历史段
        #   全量重扫 → 跨段最优课在每段重复入池（曾致 TOP 同课重复9次）
        self._sizhu_cache = {}
        t_start = time.time()
        self._log('=' * 60)
        self._log(f'批量择日优化: {start_date} ~ {end_date}')
        self._log(f'范围: {(end_date - start_date).days + 1} 天（窗口累计）')
        self._log(f'目标: {len(self.mountains)} 山')
        self._log('=' * 60)

        # Phase 1（增量预计算：`precompute_sizhu` 已按 start~end 全量建缓存，窗口只扩不缩）
        self.precompute_sizhu()
        results = self.run_phase1()

        # Phase 2
        results = self.run_phase2(results)

        # Phase 3
        results = self.run_phase3(results)

        elapsed = time.time() - t_start
        self._log(f'\n{"=" * 60}')
        self._log(f'优化完成！总耗时 {elapsed:.1f}s ({elapsed/60:.1f}分钟)')
        self._log(f'Phase1: {self.stats["phase1_checked"]:,}次检查 → {self.stats["phase1_candidates"]}候选')
        self._log(f'Phase2: {self.stats["phase2_checked"]:,}次分析 → {self.stats["phase2_candidates"]}候选')
        self._log(f'Phase3: {self.stats["phase3_checked"]:,}次深度分析 → {self.stats["phase3_candidates"]}最终')

        # 打印每山TOP摘要
        self._log(f'\n每山最优课摘要:')
        self._log(f'{">" * 80}')
        for mountain in sorted(results.keys()):
            cands = results[mountain]
            if not cands:
                self._log(f'  {mountain}山: 无合格候选')
                continue
            xiang = SHAN_JIA_MAP.get(mountain, '')
            self._log(f'\n🏔 {mountain}山(坐{mountain}向{xiang}):')
            for i, c in enumerate(cands[:3]):
                self._log(f'  #{i+1} {c.date_str} {c.shichen}时 | '
                         f'{c.nian_gan}{c.nian_zhi}.{c.yue_gan}{c.yue_zhi}.{c.ri_gan}{c.ri_zhi}.{c.shi_gan}{c.shi_zhi}'
                         + (f' | 斗首{c.doushou_score:.0f}/演禽{c.yanqin_score:.0f}/六壬{c.liuren_score:.0f}'
                            + (' ★顶格' if c.triple_top else '')) if self.top_triple else '')
                gong_count = len([p for p in c.gong_patterns if p.get('matched', False)])
                huo_count = c.huoma_details.get('count', 0) if hasattr(c.huoma_details, 'get') else 0
                dsdx_count = c.daoshan_details.get('total_count', 0) if hasattr(c.daoshan_details, 'get') else 0
                self._log(f'       排序{c.rank_score:.1f} | 综合{c.total_score:.1f} [{c.grade}] | '
                         f'斗首{c.score_phase1:.0f}+到向{c.score_phase2:.0f}+六壬{c.score_phase3:.0f} | '
                         f'精度{c.precision_score:.0f}(基础{c.precision_base:.0f}课体{c.precision_keti:+.0f}) | '
                         f'拱{gong_count}活{huo_count}到{dsdx_count}')

        return results

    def _optimize_extended(self, segment_years: int = 30) -> Dict[str, List[Candidate]]:
        """【2026-09-06 用户方案：分段跑，30年为一段，一段内找到即不用找，找不到才往下一段】
        分段执行 optimize 单窗口（每段独立内存），跨段只保留每山全局最优 TOP：
        停段条件：每山已出现 dingge（三铁律足+三维≥85）→ 立即停；
        否则记录该段最高档（★上等→○良 递补）继续下一段，全部扫完（max_years 上限）取全局最高。"""
        seg_days = int(365.25 * max(segment_years, 1))
        max_end = self.start_date + timedelta(days=int(365.25 * self.max_years))
        global_pool: Dict[str, List[Candidate]] = {m: [] for m in self.mountains}
        _orig_start = self.start_date
        seg_start = self.start_date
        rounds = 0
        self._log(f'\n⚡ 分段顶格顺延：{segment_years}年/段，砰到每山 ◆顶格 即停，总上限 {self.max_years} 年')
        while True:
            rounds += 1
            seg_end = min(seg_start + timedelta(days=seg_days - 1), max_end)
            self._log(f'\n── 第 {rounds} 段：{seg_start} ~ {seg_end}（{segment_years}年）──')
            for k in ('days', 'phase1_candidates', 'phase2_candidates', 'phase3_candidates',
                      'phase1_checked', 'phase2_checked', 'phase3_checked'):
                self.stats[k] = 0
            # 单段完整跑（段间独立内存；_optimize_window 已清 sizhu 缓存）
            _seg = self._optimize_window(seg_start, seg_end)
            # 合并到全局池：按 (日期,时辰) 去重 + triple_key 取 TOP
            seen = set()
            for m in self.mountains:
                pool = []
                for c in global_pool[m] + list(_seg.get(m, [])):
                    if not c.fa_chuan_ok:
                        continue  # 【2026-09-06】发传<2 不合次格课，跨段亦剔除
                    key = (c.date_str, c.shichen)
                    if key in seen:
                        continue
                    seen.add(key)
                    pool.append(c)
                pool.sort(key=lambda c: c.triple_key, reverse=True)
                global_pool[m] = pool[:max(self.phase3_top * 2, 20)]
            # 停段：每山都存在 ◆顶格（dingge）
            all_dingge = all(any(c.dingge for c in global_pool[m]) for m in self.mountains)
            if all_dingge:
                self._log('\n✅ 各山均已出现 ◆顶格（三铁律+三维≥85），停止搜索')
                break
            if seg_end >= max_end:
                self._log(f'\n⚠️ 已达 {self.max_years} 年上限（{rounds} 段），取全局最高档课')
                break
            seg_start = seg_end + timedelta(days=1)
        # 输出：各山取全局 TOP（按顶格分级）；start_date 还原为最初起点
        self.start_date = _orig_start
        self.end_date = min(seg_end, max_end)
        return {m: global_pool[m][:self.phase3_top] for m in self.mountains}
    
    def export_results(self, results: Dict[str, List[Candidate]],
                       output_path: str = None) -> str:
        """导出结果为JSON文件"""
        if output_path is None:
            d1 = self.start_date.strftime('%Y%m%d')
            d2 = self.end_date.strftime('%Y%m%d')
            output_path = os.path.join(PROJECT_ROOT, 'data', f'zeri_optimize_{d1}_{d2}.json')
        
        output = {
            'meta': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'days': self.stats['days'],
                'mountains': len(self.mountains),
                'elapsed_stats': self.stats,
            },
            'results': {}
        }
        
        for mountain, candidates in results.items():
            output['results'][mountain] = [c.to_dict() for c in candidates]
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        self._log(f'\n结果已导出: {output_path}')
        return output_path


# ═══════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════

def optimize_for_years(years: int = 3,
                        start_year: int = None,
                        mountains: List[str] = None,
                        phase1_top: int = 500,
                        phase2_top: int = 50,
                        phase3_top: int = 20,
                        output_path: str = None,
                        zeri_type: str = '',
                        top_triple: bool = False,
                        auto_extend: bool = False,
                        min_top: int = 5,
                        max_years: int = 30) -> str:
    """
    便捷函数：优化N年择日

    参数:
        years: 年数 (3/5/10)
        start_year: 起始年份（默认从今天开始）
        mountains: 山列表（默认全部24山）
        phase1/2/3_top: 各阶段保留数
        output_path: 输出文件路径
        zeri_type: 择日类型（2026-09-06 方案A-L3：类神吉应微调，空则跳过）
        top_triple: 顶格择日（斗首/演禽/六壬三维顶格度排序）
        auto_extend: 窗口顺延（一直往后推至全100/收敛/max_years）

    返回: 输出JSON路径
    """
    from datetime import date
    
    if start_year is None:
        start = date.today()
    else:
        start = date(start_year, 1, 1)
    
    end = date(start.year + years - 1, 12, 31)
    
    optimizer = BatchZeriOptimizer(
        start_date=start,
        end_date=end,
        mountains=mountains,
        phase1_top=phase1_top,
        phase2_top=phase2_top,
        phase3_top=phase3_top,
        verbose=True,
        zeri_type=zeri_type,
        top_triple=top_triple, auto_extend=auto_extend,
        min_top=min_top, max_years=max_years,
    )
    
    results = optimizer.optimize()
    return optimizer.export_results(results, output_path)


# ═══════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量择日优化器')
    parser.add_argument('--years', type=int, default=3, help='年数 (默认3)')
    parser.add_argument('--start', type=str, default=None, help='起始日期 YYYY-MM-DD')
    parser.add_argument('--mountains', type=str, default=None, help='山列表，逗号分隔 (默认全部)')
    parser.add_argument('--p1', type=int, default=500, help='Phase1每山保留数')
    parser.add_argument('--p2', type=int, default=50, help='Phase2每山保留数')
    parser.add_argument('--p3', type=int, default=20, help='Phase3每山输出数')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    parser.add_argument('--zeri-type', type=str, default='', help='择日类型（作灶/提车/安门…类神吉应微调）')
    parser.add_argument('--top-triple', action='store_true', help='顶格择日：按斗首/演禽/六壬三维顶格度排序')
    parser.add_argument('--auto-extend', action='store_true', help='窗口顺延：90天起，每山不足 min-top 自动往后推')
    parser.add_argument('--min-top', type=int, default=5, help='每山至少保留候选数（auto-extend 停窗条件）')
    parser.add_argument('--max-years', type=int, default=30, help='顺延年数上限（默认30）')
    parser.add_argument('--segment-years', type=int, default=30, help='分段年数（默认30年一段，段内找到顶格即停）')
    
    args = parser.parse_args()
    
    mountains = None
    if args.mountains:
        mountains = [m.strip() for m in args.mountains.split(',')]
    
    if args.start:
        start_date = date.fromisoformat(args.start)
        end_date = date(start_date.year + args.years - 1, 12, 31)
        optimizer = BatchZeriOptimizer(
            start_date=start_date, end_date=end_date,
            mountains=mountains,
            phase1_top=args.p1, phase2_top=args.p2, phase3_top=args.p3,
            zeri_type=args.zeri_type,
            top_triple=args.top_triple, auto_extend=args.auto_extend,
            min_top=args.min_top, max_years=args.max_years,
        )
        results = optimizer.optimize()
        optimizer.export_results(results, args.output)
    else:
        output = optimize_for_years(
            years=args.years,
            mountains=mountains,
            phase1_top=args.p1, phase2_top=args.p2, phase3_top=args.p3,
            output_path=args.output,
            zeri_type=args.zeri_type,
            top_triple=args.top_triple, auto_extend=args.auto_extend,
            min_top=args.min_top, max_years=args.max_years,
        )
        print(f'\nDone → {output}')
