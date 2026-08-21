# -*- coding: utf-8 -*-
"""
六壬综合判断引擎 — 第三层 CBR 检索 + 壬归寻原 + 辨证五轴融合

====================================================================
设计哲学（为什么不用线性加权求和）
--------------------------------------------------------------------
六壬的本质是「一个贯通的判断故事」，不是 17 个独立判断题相加。
当前 liuren_20d_engine 的「各维度 ±分 再求和」会丢失三件事：
  1. 交互：旬空在初传为凶、在末传为「事终成」，求和把它们等同了
  2. 体用：课体/用神是「君」，神煞是「佐使」，求和时权重相同
  3. 叙事：维度之间要「讲一个连贯的道理」，而非各自打分

本模块用三层结构替代线性求和：

  ┌─ Layer 3a: CaseLibrary (CBR 检索)
  │     按 (课体, 三传, 用神, 日干) 从 data/ 检索最相似的古例/股例
  │     → 产出「裁决锚」：在这个课体下，历史上怎么判、谁主导
  │
  ├─ Layer 3b: DialecticalAxes (辨证五轴)
  │     把判断建模成 5 组矛盾张力（有符号、可解释）：
  │       动静 / 刚柔 / 主客 / 虚实 / 始终
  │     → 不直接给趋势，只给「张力态势」
  │
  └─ Layer 3c: XunyuanSynthesizer (壬归·寻原)
        立极 → 取用 → 辨向 → 察变 → 归一
        用检索到的课例逻辑「裁决」五轴冲突，输出唯一综合判断

关键点：辨证五轴不是事后附录，而是寻原的「输入张力」；
        课例检索结果用来「定夺」哪个轴在该课体下主导。
====================================================================
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Any, Tuple, Optional

# ----------------------------------------------------------------------
# 基础常量
# ----------------------------------------------------------------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")

# ----------------------------------------------------------------------
# 应期引擎懒加载（避免循环依赖）
# ----------------------------------------------------------------------
_yingqi_mod = None


def _load_yingqi():
    """延迟导入 engine.yingqi_engine，仅在首次调用应期接线时加载。"""
    global _yingqi_mod
    if _yingqi_mod is None:
        try:
            import importlib
            if BASE not in __import__("sys").path:
                __import__("sys").path.insert(0, BASE)
            _yingqi_mod = importlib.import_module("engine.yingqi_engine")
        except Exception:
            _yingqi_mod = False  # 标记不可用，避免反复 import 失败
    return _yingqi_mod if _yingqi_mod is not False else None

WX: Dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}
GAN_WX: Dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
    "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
# 我生（食伤）
WX_SHENG: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 我克（财）
WX_KE: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 天将刚柔属性
GANG_TJ = {"白虎", "玄武", "勾陈", "螣蛇", "朱雀"}      # 刚（凶煞、主动荡）
ROU_TJ = {"贵人", "青龙", "六合", "太阴", "天后"}        # 柔（吉神、主安稳）

# 六亲刚柔
GANG_LQ = {"官鬼", "七杀"}                              # 刚（克我，压力）
ROU_LQ = {"父母", "妻财"}                               # 柔（生我/养我）

# 旺衰 → 强弱权重（用于虚实轴）
WANG_SHUAI_W: Dict[str, float] = {
    "长生": 1.0, "沐浴": 0.6, "冠带": 0.7, "临官": 0.9, "帝旺": 1.0,
    "衰": 0.3, "病": 0.1, "死": -0.4, "墓": -0.6, "绝": -0.8,
    "胎": -0.2, "养": 0.0,
}

# 课体 → 动静偏置（壬归·课义）。伏吟/返吟/八专等静体，贼克/遥克/昴星等动体
# 课体名去后缀，与 CBR 索引格式对齐（索引存"铸印""六仪"等无后缀名）
STATIC_KETI = {"伏吟", "返吟", "八专", "冬蛇掩目", "度厄", "六纯"}
ACTIVE_KETI = {"元首", "重审", "涉害", "遥克", "昴星", "别责", "知一", "察微", "绝嗣", "赘婿", "乱首"}


# ======================================================================
# Layer 3a: CaseLibrary — CBR 检索
# ======================================================================
class CaseLibrary:
    """CBR 案例检索库。

    优先使用 cbr_retrieval 的 747 案索引（断案疏正 218 + 壬占汇选 529），
    6 维加权相似度（占类/课格Jaccard/毕法Jaccard/传变/发用五行/神煞）。
    旧 231 案简单匹配保留为 fallback。
    """

    def __init__(self):
        self.cases: List[Dict[str, Any]] = []          # 旧格式（fallback）
        self._cbr_cases: List[Dict] = []                # cbr_retrieval 747 案
        self._cbr_loaded = False
        self._vkb = None                                # VectorKnowledgeBase 文本通道
        self._vkb_loaded = False
        self._load()
        self._load_cbr()
        self._load_vector_index()

    def _load(self) -> None:
        # 1) 大六壬数征案例（224 条古例）
        try:
            with open(os.path.join(DATA_DIR, "daliuren_shuzheng_cases.json"),
                      "r", encoding="utf-8") as f:
                for c in json.load(f):
                    self.cases.append(self._norm_shuzheng(c))
        except Exception:
            pass
        # 2) 股票训练案例（7 条股例）
        try:
            with open(os.path.join(DATA_DIR, "stock_training_cases.json"),
                      "r", encoding="utf-8") as f:
                for c in json.load(f):
                    self.cases.append(self._norm_stock(c))
        except Exception:
            pass

    @staticmethod
    def _split_keti(keti: str) -> List[str]:
        """拆分课体字符串，去掉'课'/'格'后缀，与 CBR 索引格式对齐。
        索引端存储如 ['铸印','六仪','连珠']（无后缀），查询端需同样去后缀。"""
        if not keti:
            return []
        out = []
        for t in keti.replace("，", ",").replace("、", ",").split(","):
            t = t.strip()
            # 去掉"课"或"格"后缀，与CBR索引格式对齐
            for suffix in ('课', '格'):
                if t.endswith(suffix) and len(t) > 1:
                    t = t[:-1]
                    break
            if t:
                out.append(t)
        return out

    @staticmethod
    def _norm_shuzheng(c: Dict) -> Dict:
        ke_ti = c.get("ke_ti", "") or ""
        sc = c.get("sanchuan", [])
        if isinstance(sc, list):
            sanchuan = [str(x).strip() for x in sc if str(x).strip() in WX]
        elif isinstance(sc, str):
            sanchuan = [x for x in sc if x in WX]
        else:
            sanchuan = []
        interp = c.get("interpretation", "") or ""
        return {
            "source": "数征", "name": c.get("name", ""), "ke_ti": ke_ti,
            "keti_tokens": CaseLibrary._split_keti(ke_ti),
            "sanchuan": sanchuan, "ri_gan": c.get("ri_gan", ""),
            "ri_zhi": c.get("ri_zhi", ""),
            "interpretation": interp,
            "sanchuan_interpretation": c.get("sanchuan_interpretation", "") or "",
            "yingqi": c.get("yingqi", "") or "",
            "question": c.get("question", "") or "",
        }

    @staticmethod
    def _norm_stock(c: Dict) -> Dict:
        sc = c.get("sanchuan", {})
        if isinstance(sc, dict):
            sanchuan = []
            for k in ("first", "second", "third"):
                v = str(sc.get(k, ""))
                # "白虎+金" → 取天将名 "白虎"（用于天将匹配时另存）
                tj = v.split("+")[0].strip()
                sanchuan.append(tj)
        else:
            sanchuan = []
        parts = []
        if c.get("liuqin_analysis"):
            parts.append(str(c.get("liuqin_analysis")))
        if c.get("tianjiang_analysis"):
            parts.append(str(c.get("tianjiang_analysis")))
        if c.get("jingi_analysis"):
            parts.append(str(c.get("jingi_analysis")))
        verdict = f"趋势:{c.get('trend_prediction','')} 实际:{c.get('actual_trend','')} 对错:{c.get('is_correct','')}"
        return {
            "source": "股例", "name": c.get("stock_name", ""),
            "ke_ti": str(c.get("keti", "")),
            "keti_tokens": CaseLibrary._split_keti(str(c.get("keti", ""))),
            "sanchuan": sanchuan, "ri_gan": "", "ri_zhi": "",
            "interpretation": verdict + " | " + " ".join(parts),
            "sanchuan_interpretation": "", "yingqi": "",
            "question": c.get("title", "") or "",
        }

    def _load_cbr(self) -> None:
        """从 cbr_retrieval 加载 747 案特征向量索引。"""
        try:
            from engine.cbr_retrieval import _load_cases as cbr_load
            self._cbr_cases = cbr_load()
            self._cbr_loaded = len(self._cbr_cases) > 0
        except Exception:
            self._cbr_loaded = False

    def _load_vector_index(self) -> None:
        """加载 VectorKnowledgeBase n-gram 文本索引（747 案断语）。"""
        try:
            from engine.vector_knowledge_base import VectorKnowledgeBase
            DATA = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), 'data')
            idx_file = os.path.join(DATA, 'vector_store', 'cbr_vector_index.json')
            if os.path.exists(idx_file):
                vkb = VectorKnowledgeBase(persist_dir=os.path.join(DATA, 'vector_store'))
                if vkb.load(idx_file):
                    self._vkb = vkb
                    self._vkb_loaded = len(vkb.documents) > 0
        except Exception:
            self._vkb_loaded = False

    def _text_search(self, query_text: str, top_k: int = 5) -> Dict[str, float]:
        """文本语义检索通道：返回 {case_id: text_similarity}。"""
        if not self._vkb_loaded or not query_text or len(query_text) < 2:
            return {}
        try:
            results = self._vkb.query(query_text, top_k=top_k)
            return {r['case'].get('id', ''): r['similarity']
                    for r in results if r.get('similarity', 0) > 0.01}
        except Exception:
            return {}

    def retrieve(self, keti: str, sanchuan: List[str], yong_shen: str = "",
                 ri_gan: str = "", top_k: int = 3, category: str = "",
                 full_data: Dict = None) -> List[Tuple[int, Dict, List[str]]]:
        """返回 [(score, case, reasons), ...] 按相似度降序。

        优先走 cbr_retrieval 6 维相似度（747 案）；失败时回退旧 4 因子匹配。
        """
        # ── 优先：cbr_retrieval 747 案 6 维检索 ──
        if self._cbr_loaded and sanchuan:
            try:
                return self._retrieve_cbr(keti, sanchuan, yong_shen, ri_gan,
                                          top_k, category, full_data)
            except Exception:
                pass  # 降级到旧逻辑

        # ── fallback：旧 231 案 4 因子匹配 ──
        return self._retrieve_legacy(keti, sanchuan, yong_shen, ri_gan, top_k)

    def _retrieve_cbr(self, keti: str, sanchuan: List[str], yong_shen: str,
                      ri_gan: str, top_k: int, category: str,
                      full_data: Dict = None) -> List[Tuple[int, Dict, List[str]]]:
        """双通道融合检索：cbr_retrieval 6 维结构分 + VectorKB n-gram 文本分。"""
        from engine.cbr_retrieval import retrieve as cbr_retrieve, similarity as cbr_sim
        from engine.knowledge_features import relation, WX

        # 构建查询特征向量
        chu = sanchuan[0] if sanchuan else ''
        q_vec = {
            'zhanlei': category or '',
            'fayong': chu,
            'fayong_wuxing': WX.get(chu, '') if chu else '',
            'ji_sha_count': 0,
            'xiong_sha_count': 0,
        }
        # 2026-08-21 修复：神煞计数与索引端同口径（build_shensha），
        # 原硬编码 0 导致打分端 |0-cj|+|0-cx| 系统性惩罚神煞多的案例
        try:
            from engine.build_feature_vectors import build_shensha
            _fd = full_data or {}
            _lm = _fd.get('lunar_month') or _fd.get('农历月') or 0
            _nz = _fd.get('nian_zhi') or ''
            if not _nz:
                _bi0 = _fd.get('basic_info') or {}
                _nz = _bi0.get('nian_zhi') or _bi0.get('年支') or ''
            _sike = _fd.get('sike') or _fd.get('四课') or []
            _ss = build_shensha(ri_gan, ri_zhi, _lm, _nz, sanchuan, _sike)
            if _ss:
                q_vec['ji_sha_count'] = int(_ss.get('吉神数', 0) or 0)
                q_vec['xiong_sha_count'] = int(_ss.get('凶煞数', 0) or 0)
        except Exception:
            pass
        if chu and ri_gan:
            q_vec['fayong_ri_gan'] = relation(chu, ri_gan)['relation']
        # 传变
        if len(sanchuan) >= 3:
            order = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
            try:
                idx = [order.index(x) for x in sanchuan[:3]]
                if idx[0]+1 == idx[1] and idx[1]+1 == idx[2]:
                    q_vec['chuan_bian'] = '进茹'
                elif idx[0]-1 == idx[1] and idx[1]-1 == idx[2]:
                    q_vec['chuan_bian'] = '退茹'
                else:
                    q_vec['chuan_bian'] = '乱传'
            except Exception:
                q_vec['chuan_bian'] = ''

        # 尝试从 analysis 提取毕法赋命中
        bifa_list = []
        if full_data:
            analysis = full_data.get("analysis", {})
            if isinstance(analysis, dict):
                bf = analysis.get("bifa", {})
                if isinstance(bf, dict):
                    for d in bf.get("断法", []):
                        if isinstance(d, dict):
                            bifa_list.append((d.get("法句", ""), d.get("分类", "")))

        # 2026-08-21 修复：查询端补齐变格列表（索引端 features.bianjie 一直有数据，
        # 打分端课格维度现按 keti+变格联合 Jaccard 计算）
        bianjie_list = []
        if full_data:
            _an = full_data.get("analysis", {})
            if isinstance(_an, dict):
                _bj = _an.get("bianjie", {})
                if isinstance(_bj, dict):
                    bianjie_list = [str(x) for x in _bj.get("匹配变格", []) if x]
        q_feat = {
            'keti': CaseLibrary._split_keti(keti),
            'bifa': bifa_list,
            'bianjie': bianjie_list,
        }

        # 通道1：cbr_retrieval 6 维结构检索
        matches = cbr_retrieve(q_vec, q_feat, cases=self._cbr_cases, top_k=top_k * 2)

        # 通道2：VectorKB n-gram 文本检索
        query_text = ''
        if full_data:
            query_text = (full_data.get('question', '') or
                         full_data.get('description', '') or
                         full_data.get('query_text', ''))
        # 若无显式查询文本，用占类+课体+三传构造
        if not query_text:
            query_text = f"{category} {keti} {''.join(sanchuan)}".strip()
        text_scores = self._text_search(query_text, top_k=top_k * 2) if query_text else {}

        # ── 融合评分 ──
        # 结构分: 0-100 (cbr_retrieval.similarity)
        # 文本分: 0-1 (VectorKB cosine) → 加权为 0-30 的 bonus
        # 最终: final = struct_score + text_bonus
        TEXT_BONUS_MAX = 30.0
        scored_map = {}  # case_id → (final_score, match_dict, reasons)

        for m in matches:
            cid = m.get('case_id', '')
            struct_s = m.get('similarity', 0)
            text_s = text_scores.get(cid, 0)
            text_bonus = min(text_s, 1.0) * TEXT_BONUS_MAX
            final_s = struct_s + text_bonus

            case_dict = {
                'source': '汇选' if m.get('source') == 'Corpus_A' else '数征',
                'name': cid,
                'interpretation': m.get('duanyu', '') or '',
                'sanchuan': m.get('sanchuan', []),
                'ri_gan': (m.get('day_ganzhi', '') or '')[:1],
                'ri_zhi': (m.get('day_ganzhi', '') or '')[1:2] if len(m.get('day_ganzhi', '')) > 1 else '',
                'ke_ti': '、'.join(m.get('keti', [])),
                'keti_tokens': m.get('keti', []),
                'question': m.get('zhanlei', ''),
                'label': m.get('label', ''),
                'sanchuan_interpretation': '',
                'yingqi': '、'.join(m.get('yingqi', [])) if m.get('yingqi') else '',
            }
            reasons = []
            if m.get('zhanlei') and category and m['zhanlei'] == category:
                reasons.append("占类同")
            if m.get('keti') and q_feat['keti']:
                common = set(m['keti']) & set(q_feat['keti'])
                if common:
                    reasons.append(f"课体同({','.join(common)})")
            if m.get('chuan_bian') and q_vec.get('chuan_bian') and m['chuan_bian'] == q_vec['chuan_bian']:
                reasons.append(f"传变同({m['chuan_bian']})")
            if text_bonus > 5:
                reasons.append(f"断语相似({text_s:.2f})")
            if not reasons:
                reasons.append("综合相似")
            scored_map[cid] = (final_s, case_dict, reasons)

        # 补充：仅在文本通道命中但不在结构通道的案例
        for cid, text_s in text_scores.items():
            if cid in scored_map:
                continue
            # 从 _cbr_cases 或 _vkb 找原始案例
            c = next((x for x in self._cbr_cases if x.get('case_id') == cid), None)
            if not c:
                # 从 vkb.documents 查
                c = next((d for d in self._vkb.documents if d.get('id') == cid), None)
            if not c:
                continue
            text_bonus = min(text_s, 1.0) * TEXT_BONUS_MAX
            if text_bonus < 5:
                continue
            case_dict = {
                'source': '汇选' if c.get('source') == 'Corpus_A' else '数征',
                'name': cid,
                'interpretation': (c.get('duanyu', '') or c.get('duanyu', ''))[:500],
                'sanchuan': c.get('sanchuan', []),
                'ri_gan': (c.get('day_ganzhi', '') or '')[:1],
                'ri_zhi': (c.get('day_ganzhi', '') or '')[1:2] if len(c.get('day_ganzhi', '')) > 1 else '',
                'ke_ti': '、'.join(c.get('features', {}).get('keti', [])),
                'question': c.get('zhanlei', ''),
                'label': c.get('label', ''),
                'sanchuan_interpretation': '',
                'yingqi': '',
            }
            scored_map[cid] = (text_bonus, case_dict, [f"断语高度相似({text_s:.2f})"])

        # 按融合分排序，取 top_k
        out = sorted(scored_map.values(), key=lambda x: -x[0])[:top_k]
        return out

    def _retrieve_legacy(self, keti: str, sanchuan: List[str], yong_shen: str,
                         ri_gan: str, top_k: int) -> List[Tuple[int, Dict, List[str]]]:
        """旧 4 因子 fallback：课体+3/三传+2/位/发用+2/日干+1。"""
        q_tokens = set(CaseLibrary._split_keti(keti))
        scored: List[Tuple[int, Dict, List[str]]] = []
        for c in self.cases:
            score = 0
            reasons: List[str] = []
            # 课体匹配（最重要）
            if q_tokens & set(c["keti_tokens"]):
                score += 3
                reasons.append("课体同")
            # 三传逐位匹配
            if sanchuan and c["sanchuan"]:
                same = sum(1 for a, b in zip(sanchuan, c["sanchuan"]) if a == b)
                if same > 0:
                    score += same * 2
                    reasons.append(f"三传{same}位同")
            # 发用（初传）= 用神
            if yong_shen and c["sanchuan"] and c["sanchuan"][0] == yong_shen:
                score += 2
                reasons.append("发用同")
            # 日干匹配
            if ri_gan and c["ri_gan"] == ri_gan:
                score += 1
                reasons.append("日干同")
            if score > 0:
                scored.append((score, c, reasons))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]


# ======================================================================
# Layer 3b: DialecticalAxes — 辨证五轴
# ======================================================================
class DialecticalAxes:
    """把判断拆成 5 组矛盾张力，每组给一个有符号的态势（不直接判趋势）。"""

    @staticmethod
    def compute(analysis: Dict, full_data: Dict) -> Dict[str, Dict]:
        axes: Dict[str, Dict] = {}

        sanchuan = full_data.get("san_chuan") or full_data.get("sanchuan") or []
        if sanchuan and isinstance(sanchuan[0], dict):
            sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]
        kong = analysis.get("kong_info", {}) if isinstance(analysis, dict) else {}
        rels = analysis.get("relationships", []) if isinstance(analysis, dict) else []
        wang = analysis.get("wangshuai", []) if isinstance(analysis, dict) else []
        liuqin = analysis.get("liuqin", []) if isinstance(analysis, dict) else []
        tj = analysis.get("tianjiang", {}) if isinstance(analysis, dict) else {}
        sike = analysis.get("sike_qi", {}) if isinstance(analysis, dict) else {}
        keti = full_data.get("keti", "") or ""

        # --- 轴1：动静（动=刑冲克战；静=墓绝空休/伏吟反吟）---
        dong = 0
        ev: List[str] = []
        for r in rels:
            if isinstance(r, dict):
                if r.get("六冲") or r.get("三刑"):
                    dong += 1
                    ev.append("见刑冲")
                elif r.get("六合"):
                    dong -= 1
                    ev.append("见六合")
        if isinstance(kong, dict):
            kc = sum(1 for v in kong.values() if v)
            dong -= kc
            if kc:
                ev.append(f"空亡{kc}传→静")
        if any(t in STATIC_KETI for t in CaseLibrary._split_keti(keti)):
            dong -= 2
            ev.append("伏吟/反吟→静体")
        axes["动静"] = {
            "signed": dong,
            "dir": "动" if dong > 0 else ("静" if dong < 0 else "平"),
            "evidence": "、".join(ev) or "无明显动静",
        }

        # --- 轴2：刚柔（刚=官鬼白虎；柔=父母青龙）---
        gang = 0
        ev = []
        for lq in liuqin:
            if isinstance(lq, dict):
                name = lq.get("六亲", "")
                if name in GANG_LQ:
                    gang += 1
                    ev.append(f"{lq.get('地支','')}官鬼(刚)")
                elif name in ROU_LQ:
                    gang -= 1
                    ev.append(f"{lq.get('地支','')}{name}(柔)")
        for chuan in ("初传", "中传", "末传"):
            t = tj.get(chuan, "") if isinstance(tj, dict) else ""
            if t in GANG_TJ:
                gang += 1
                ev.append(f"{chuan}{t}(刚)")
            elif t in ROU_TJ:
                gang -= 1
                ev.append(f"{chuan}{t}(柔)")
        # 八杀凶煞折入刚柔（煞气重=刚/凶）
        ba = analysis.get("ba_sha", {}) if isinstance(analysis, dict) else {}
        if isinstance(ba, dict):
            ba_score = ba.get("评分", 0) or 0
            if ba_score < 0:
                gang += 1
                ev.append(f"八杀凶({ba_score}分)→刚")
            elif ba_score > 0:
                gang -= 1
                ev.append(f"八杀吉({ba_score}分)→柔")
        axes["刚柔"] = {
            "signed": gang,
            "dir": "刚" if gang > 0 else ("柔" if gang < 0 else "平"),
            "evidence": "、".join(ev) or "刚柔相参",
        }

        # --- 轴3：主客（干=我/股市为体；支=事/彼为用）---
        # 用四课关系判断干支受生受克态势（去重，同信号只计一次）
        zhu = 0
        ev = []
        seen = set()
        if isinstance(sike, dict):
            sq = sike.get("四课关系", [])
            if isinstance(sq, list):
                for r in sq:
                    if isinstance(r, dict):
                        desc = str(r.get("描述", "")) + str(r.get("类型", ""))
                        sig = None
                        if ("干" in desc and ("生" in desc or "旺" in desc)) or \
                           ("支" in desc and ("克" in desc or "墓" in desc or "绝" in desc)):
                            sig = "干强"
                        elif ("支" in desc and ("生" in desc or "旺" in desc)) or \
                             ("干" in desc and ("克" in desc or "墓" in desc or "绝" in desc)):
                            sig = "支强"
                        if sig and sig not in seen:
                            seen.add(sig)
                            if sig == "干强":
                                zhu += 1
                                ev.append("干受生/支受克→主强")
                            else:
                                zhu -= 1
                                ev.append("支受生/干受克→客强")
        axes["主客"] = {
            "signed": zhu,
            "dir": "主强" if zhu > 0 else ("客强" if zhu < 0 else "均势"),
            "evidence": "、".join(ev) or "干支关系未显",
        }

        # --- 轴4：虚实（实=现传临旺；虚=空亡陷没）---
        xu = 0
        ev = []
        # 空亡 → 虚
        if isinstance(kong, dict):
            kc = sum(1 for v in kong.values() if v)
            xu -= kc
            if kc:
                ev.append(f"{kc}传落空→虚")
        # 旺衰：取三传旺衰均值
        if sanchuan and wang:
            wmap = {w.get("地支"): w.get("旺衰", "") for w in wang if isinstance(w, dict)}
            vals = [WANG_SHUAI_W.get(wmap.get(z, ""), 0.0) for z in sanchuan if z in wmap]
            if vals:
                avg = sum(vals) / len(vals)
                if avg > 0.3:
                    xu += 1
                    ev.append("三传偏旺→实")
                elif avg < -0.2:
                    xu -= 1
                    ev.append("三传偏衰→虚")
        axes["虚实"] = {
            "signed": xu,
            "dir": "实" if xu > 0 else ("虚" if xu < 0 else "平"),
            "evidence": "、".join(ev) or "虚实相参",
        }

        # --- 轴5：始终（初传=机，末传=果；气之流转方向）---
        shi = 0
        ev = []
        zhijiu = analysis.get("sanchuan_zhijiu", {}) if isinstance(analysis, dict) else {}
        if isinstance(zhijiu, dict):
            qq = str(zhijiu.get("气之趋势", ""))
            szh = str(zhijiu.get("始终吉凶", ""))
            if "先难后易" in szh or "初凶末吉" in szh or "先凶后吉" in qq:
                shi += 1
                ev.append("初凶末吉")
            elif "先易后难" in szh or "初吉末凶" in szh or "先吉后凶" in qq:
                shi -= 1
                ev.append("初吉末凶")
        # 若三传旺衰递增 → 气进（始终向好）
        if sanchuan and wang:
            wmap = {w.get("地支"): w.get("旺衰", "") for w in wang if isinstance(w, dict)}
            seq = [WANG_SHUAI_W.get(wmap.get(z, ""), 0.0) for z in sanchuan if z in wmap]
            if len(seq) >= 2:
                if seq[-1] > seq[0] + 0.2:
                    shi += 1
                    ev.append("气由初传向末传渐旺")
                elif seq[-1] < seq[0] - 0.2:
                    shi -= 1
                    ev.append("气由初传向末传渐衰")
        axes["始终"] = {
            "signed": shi,
            "dir": "进" if shi > 0 else ("退" if shi < 0 else "滞"),
            "evidence": "、".join(ev) or "始终未显",
        }

        return axes


# ======================================================================
# Layer 3c: XunyuanSynthesizer — 壬归·寻原
# ======================================================================
class XunyuanSynthesizer:
    """
    壬归寻原五步：
        立极（干为股市/体，支为事/用）
        取用（选定用神）
        辨向（用神对我之生克）
        察变（三传初→末之气流转 = 始终轴）
        归一（五轴 + 课例裁决 → 唯一判断）

    规则库 XUNYUAN_RULES 可扩展：每条 rule 含 match(ctx) 与 effect(state)。
    """

    # 壬归寻原规则库（可在此增删）
    RULES: List[Dict] = [
        {
            "name": "干支皆受生·利外不利内",
            "match": lambda c: c["gan_shang_sheng"] and c["zhi_shang_sheng"],
            "effect": lambda s: s.__setitem__("score", s["score"] - 1)
            or s["evidence"].append("干支皆受上神来生，利外不利内（利彼不利我）"),
        },
        {
            "name": "干受生支受克·我吉彼凶",
            "match": lambda c: c["gan_shang_sheng"] and c["zhi_shang_ke"],
            "effect": lambda s: s.__setitem__("score", s["score"] + 1)
            or s["evidence"].append("干受生支受克，我吉彼凶，持股有利"),
        },
        {
            "name": "末传生干·终能就我",
            "match": lambda c: c["mo_sheng_gan"],
            "effect": lambda s: s.__setitem__("score", s["score"] + 1)
            or s["evidence"].append("末传生干，事终能就我，先难后易"),
        },
        {
            "name": "发用克末传·事由外起",
            "match": lambda c: c["chu_ke_mo"],
            "effect": lambda s: s.__setitem__("score", s["score"] - 1)
            or s["evidence"].append("初传克末传，事由外起，被动受制"),
        },
        {
            "name": "伏吟·天地同位宜静",
            "match": lambda c: c["is_fuyin"],
            "effect": lambda s: s["evidence"].append("伏吟天地同位，事有停滞，宜静不宜动，反弹力度有限"),
        },
        {
            "name": "用神落空·其利不实",
            "match": lambda c: c["yong_kong"],
            "effect": lambda s: s.__setitem__("score", s["score"] - 1)
            or s["evidence"].append("用神落空亡，其利不实，防虚涨"),
        },
    ]

    @staticmethod
    def _relation(gan_wx: str, other_wx: str) -> str:
        """返回 other 对 干(我) 的关系。"""
        if other_wx == gan_wx:
            return "比和"
        if WX_SHENG[gan_wx] == other_wx:
            return "我生"      # 我生=泄
        if WX_KE[gan_wx] == other_wx:
            return "我克"      # 我克=财
        if WX_SHENG[other_wx] == gan_wx:
            return "生我"      # 生我=助
        if WX_KE[other_wx] == gan_wx:
            return "克我"      # 克我=压
        return "比和"

    def synthesize(self, analysis: Dict, full_data: Dict,
                   axes: Dict[str, Dict], cases: List[Tuple[int, Dict, List[str]]]) -> Dict:
        rizhu = full_data.get("rizhu", "") or ""
        ri_gan = rizhu[:1]
        gan_wx = GAN_WX.get(ri_gan, "金")

        yong = analysis.get("yong_shen", {}) if isinstance(analysis, dict) else {}
        yong_zhi = yong.get("用神", "") if isinstance(yong, dict) else ""

        sanchuan = full_data.get("san_chuan") or full_data.get("sanchuan") or []
        if sanchuan and isinstance(sanchuan[0], dict):
            sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]

        # 取用：用神为空时回退到初传(发用) —— 六壬常规
        if not yong_zhi and sanchuan:
            yong_zhi = sanchuan[0]
        yong_wx = WX.get(yong_zhi, "金")
        direction = self._relation(gan_wx, yong_wx)

        # ---- 立极 / 取用 / 辨向 / 察变 → 构造 ctx（供规则匹配）----
        keti = full_data.get("keti", "") or ""
        is_fuyin = any(t in ("伏吟",) for t in CaseLibrary._split_keti(keti))

        # 四课关系：干上/支上受生受克
        sike = analysis.get("sike_qi", {}) if isinstance(analysis, dict) else {}
        gan_shang_sheng = gan_shang_ke = zhi_shang_sheng = zhi_shang_ke = False
        if isinstance(sike, dict):
            for r in sike.get("四课关系", []):
                if isinstance(r, dict):
                    desc = str(r.get("描述", "")) + str(r.get("类型", ""))
                    if "干" in desc:
                        if "生" in desc or "旺" in desc:
                            gan_shang_sheng = True
                        if "克" in desc or "墓" in desc or "绝" in desc:
                            gan_shang_ke = True
                    if "支" in desc:
                        if "生" in desc or "旺" in desc:
                            zhi_shang_sheng = True
                        if "克" in desc or "墓" in desc or "绝" in desc:
                            zhi_shang_ke = True

        # 末传生干？
        mo_sheng_gan = False
        if len(sanchuan) >= 3:
            mo_wx = WX.get(sanchuan[-1], "")
            mo_sheng_gan = (WX_SHENG[mo_wx] == gan_wx)
        # 初传克末传？
        chu_ke_mo = False
        if len(sanchuan) >= 2:
            chu_wx = WX.get(sanchuan[0], "")
            mo_wx = WX.get(sanchuan[-1], "")
            chu_ke_mo = (WX_KE[chu_wx] == mo_wx)
        # 用神落空？
        kong = analysis.get("kong_info", {}) if isinstance(analysis, dict) else {}
        yong_kong = bool(kong) and bool(kong.get("初传"))  # 发用=初传（六壬术语：用神落空看发用是否空）

        ctx = {
            "gan_shang_sheng": gan_shang_sheng, "gan_shang_ke": gan_shang_ke,
            "zhi_shang_sheng": zhi_shang_sheng, "zhi_shang_ke": zhi_shang_ke,
            "mo_sheng_gan": mo_sheng_gan, "chu_ke_mo": chu_ke_mo,
            "is_fuyin": is_fuyin, "yong_kong": yong_kong,
        }

        # ---- 归一：从「用神辨向」起步，融入五轴张力 ----
        state = {"score": 0.0, "evidence": []}
        # 用神辨向（辨向）
        if direction == "生我":
            state["score"] += 2
            state["evidence"].append(f"用神{yong_zhi}({yong_wx})生干({gan_wx})，主得外力之助")
        elif direction == "克我":
            state["score"] -= 2
            state["evidence"].append(f"用神{yong_zhi}({yong_wx})克干({gan_wx})，主受外力压制")
        elif direction == "我克":
            state["score"] += 1
            state["evidence"].append(f"用神{yong_zhi}({yong_wx})为财，主有可得之利")
        elif direction == "我生":
            state["score"] -= 1
            state["evidence"].append(f"用神{yong_zhi}({yong_wx})泄我，主耗散")
        else:
            state["evidence"].append(f"用神{yong_zhi}与干比和，事主反复")

        # 融入五轴张力（主客/虚实/始终 直接入分；动静/刚柔 影响幅度与表述）
        ax = axes
        if ax["主客"]["signed"] > 0:
            state["score"] += 1
            state["evidence"].append("主强客弱，我方占优")
        elif ax["主客"]["signed"] < 0:
            state["score"] -= 1
            state["evidence"].append("客强主弱，事多不由我")
        if ax["虚实"]["signed"] < 0:
            state["score"] -= 1
            state["evidence"].append("气偏虚（空亡/衰），其利不实")
        elif ax["虚实"]["signed"] > 0:
            state["score"] += 0.5
            state["evidence"].append("气偏实（临旺），其势可据")
        if ax["始终"]["signed"] > 0:
            state["score"] += 1
            state["evidence"].append("初凶末吉，气之流转向优")
        elif ax["始终"]["signed"] < 0:
            state["score"] -= 1
            state["evidence"].append("初吉末凶，盛极而衰")

        # 动静 / 刚柔 → 幅度与表述（极端刚柔才入分，框架内非线性硬加）
        if ax["动静"]["dir"] == "静":
            state["evidence"].append("动静偏静，行情迟滞、缺乏催化")
        if ax["刚柔"]["dir"] == "刚":
            state["evidence"].append("刚煞汇聚，波动剧烈、易现恐慌")
            if ax["刚柔"]["signed"] >= 2:
                state["score"] -= 1
                state["evidence"].append("煞气过重（刚≥2），行情凶险")
        elif ax["刚柔"]["dir"] == "柔":
            state["evidence"].append("柔神相济，走势温和、易得支撑")
            if ax["刚柔"]["signed"] <= -2:
                state["score"] += 0.5
                state["evidence"].append("柔神得位，易获支撑")

        # 天乙贵神状态（叙事+失位则助力弱）
        gui = analysis.get("guishen_jixiong", {}) if isinstance(analysis, dict) else {}
        if isinstance(gui, dict):
            tb = str(gui.get("天乙状态", ""))
            if tb:
                if any(k in tb for k in ("害", "凶", "囚", "空")):
                    state["score"] -= 0.5
                    state["evidence"].append(f"{tb}→贵神失位，外力助力弱")
                else:
                    state["evidence"].append(f"{tb}")

        # ---- 课例裁决（CBR 锚）：用检索到的相似课例定夺冲突 ----
        anchor_text = ""
        if cases:
            top_score, top_case, reasons = cases[0]
            anchor_text = f"引《{top_case['name']}》[{top_case['source']}]（相似度{top_score}）：{top_case['interpretation'][:120]}"
            state["evidence"].append("【课例裁决】" + anchor_text)
            # 课例对「主客」轴的修正：若古例明言「利宅不利人/利外不利内」，
            # 对股市映射为「利持股者(我)不利追高者(客)」→ 主强
            interp = top_case["interpretation"]
            if ("利" in interp and "不利" in interp):
                if "内" in interp or "人" in interp:
                    # 利外不利内 → 对我(内/持股)不利
                    state["score"] -= 0.5
                    state["evidence"].append("古例『利外不利内』，映射股市：利出局不利持仓")
                elif "宅" in interp and "人" in interp:
                    state["score"] -= 0.5
                    state["evidence"].append("古例『利宅不利人』，映射股市：利兑现不利恋战")

        # ---- 壬归寻原规则库裁决 ----
        for rule in self.RULES:
            try:
                if rule["match"](ctx):
                    rule["effect"](state)
            except Exception:
                pass

        # ---- 归一 → 趋势 ----
        sc = state["score"]
        if sc > 1.0:
            trend = "涨"
        elif sc < -1.0:
            trend = "跌"
        else:
            trend = "震荡"
        # 伏吟特殊：即便偏多也以震荡为主（天地不动）
        if is_fuyin and trend == "涨":
            trend = "震荡"
            state["evidence"].append("伏吟天地不动，虽偏多仍以震荡定局")

        confidence = min(0.95, 0.45 + abs(sc) * 0.09 + (cases[0][0] if cases else 0) * 0.02)

        # 总断：一句贯通（把辨证态势 + 课例 + 规则收束为一句）
        zongduan = self._make_zongduan(trend, axes, direction, yong_zhi, anchor_text)

        return {
            "trend": trend,
            "score": round(sc, 2),
            "confidence": round(confidence, 2),
            "zongduan": zongduan,
            "axes": axes,
            "direction": direction,
            "yong_shen": yong_zhi,
            "evidence": state["evidence"],
            "retrieved_cases": [
                {"name": c[1]["name"], "source": c[1]["source"],
                 "score": c[0], "reason": "、".join(c[2]),
                 "interpretation": c[1]["interpretation"][:160]}
                for c in cases
            ],
        }

    @staticmethod
    def _make_zongduan(trend: str, axes: Dict, direction: str,
                       yong_zhi: str, anchor: str) -> str:
        ax_desc = "，".join(f"{k}{v['dir']}" for k, v in axes.items())
        base = f"综合判断【{trend}】：用神{yong_zhi}与干{direction}；"
        base += f"辨证态势——{ax_desc}。"
        if anchor:
            base += f" 援引古例定夺冲突。"
        return base


# ======================================================================
# 编排器：HolisticSynthesizer
# ======================================================================
class HolisticSynthesizer:
    """对外入口：输入完整预测 dict（含 analysis / san_chuan / keti / rizhu），
    输出综合判断。不修改原评分，作为独立附加维度。"""

    def __init__(self):
        self.lib = CaseLibrary()
        self.xunyuan = XunyuanSynthesizer()

    def analyze(self, full_data: Dict) -> Dict:
        analysis = full_data.get("analysis", {})
        if not isinstance(analysis, dict):
            analysis = {}
        keti = full_data.get("keti", "") or ""
        sanchuan = full_data.get("san_chuan") or full_data.get("sanchuan") or []
        if sanchuan and isinstance(sanchuan[0], dict):
            sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]
        yong = analysis.get("yong_shen", {}) if isinstance(analysis, dict) else {}
        yong_zhi = yong.get("用神", "") if isinstance(yong, dict) else ""
        rizhu = full_data.get("rizhu", "") or ""
        ri_gan = rizhu[:1]

        # Layer 3a
        category = str(full_data.get("category", "") or full_data.get("question_type", "") or "")
        cases = self.lib.retrieve(keti, sanchuan, yong_zhi, ri_gan, top_k=3,
                                  category=category, full_data=full_data)
        # Layer 3b
        axes = DialecticalAxes.compute(analysis, full_data)
        # Layer 3c
        result = self.xunyuan.synthesize(analysis, full_data, axes, cases)
        # Layer 3d — 应期引擎接线：把七法应期判断并入综合结果
        result["yingqi"] = self._compute_yingqi(full_data, analysis, sanchuan, ri_gan, rizhu, yong_zhi)
        result["_meta"] = {
            "total_cases": len(self.lib._cbr_cases) if self.lib._cbr_loaded else len(self.lib.cases),
            "cbr_source": "cbr_retrieval(747案)" if self.lib._cbr_loaded else "legacy(231案)",
            "vector_kb": "loaded" if self.lib._vkb_loaded else "not_loaded",
            "retrieval_mode": "dual_channel" if (self.lib._cbr_loaded and self.lib._vkb_loaded) else "struct_only",
            "keti": keti, "sanchuan": sanchuan, "yong_shen": yong_zhi,
            "yingqi_methods": len(result.get("yingqi", {}).get("candidates", [])),
        }
        return result

    @staticmethod
    def _compute_yingqi(full_data: Dict, analysis: Dict, sanchuan: List[str],
                        ri_gan: str, rizhu: str, yong_zhi: str) -> Dict:
        """从 full_data/analysis 提取参数，调用 yingqi_engine.judge_yingqi()。

        容错式：拿不到的字段就留空，由 judge_yingqi 自行降级 confidence。"""
        mod = _load_yingqi()
        if not mod:
            return {"available": False, "reason": "yingqi_engine 未加载"}

        ri_zhi = (rizhu[1:] if len(rizhu) >= 2 else "") or full_data.get("ri_zhi", "") or ""
        ganzhi = rizhu or full_data.get("ganzhi", "") or ""

        # 干上神 / 支上神：从 sike_qi 推断，没有就空
        sike = analysis.get("sike_qi", {}) if isinstance(analysis, dict) else {}
        gan_shang = ""
        zhi_shang = ""
        if isinstance(sike, dict):
            gan_shang = str(sike.get("gan_shang", "") or sike.get("干上神", "") or "")
            zhi_shang = str(sike.get("zhi_shang", "") or sike.get("支上神", "") or "")

        # 旬空：kong_info 是 dict，可能有"初传"/"中传"/"末传"键，提取所有非空地支
        kong = analysis.get("kong_info", {}) if isinstance(analysis, dict) else {}
        kongwang: List[str] = []
        if isinstance(kong, dict):
            for v in kong.values():
                if isinstance(v, str) and len(v) == 1:
                    kongwang.append(v)
                elif isinstance(v, list):
                    kongwang.extend([x for x in v if isinstance(x, str) and len(x) == 1])

        # 天将：tianjiang 可能是 dict {地支: 天将} 或 {初/中/末: 天将}
        tj = analysis.get("tianjiang", {}) if isinstance(analysis, dict) else {}
        tianjiang: Optional[Dict[str, str]] = tj if isinstance(tj, dict) and tj else None

        # season（用于旺相休囚）：日支推断不到时让 yingqi_engine 内部推断
        season = str(analysis.get("season", "") or full_data.get("season", "") or "")

        # 占事类别
        category = str(full_data.get("category", "") or full_data.get("question_type", "") or "")

        # 用神位置：在 sanchuan 中索引
        yong_pos = ""
        if yong_zhi and yong_zhi in sanchuan:
            idx = sanchuan.index(yong_zhi)
            yong_pos = ["初传", "中传", "末传"][idx] if idx < 3 else ""

        try:
            return mod.judge_yingqi(
                ri_gan=ri_gan,
                sanchuan=sanchuan,
                ri_zhi=ri_zhi,
                ganzhi=ganzhi,
                gan_shang=gan_shang,
                zhi_shang=zhi_shang,
                yong_shen=yong_zhi,
                yong_shen_pos=yong_pos,
                kongwang=kongwang or None,
                tianjiang=tianjiang,
                season=season,
                category=category,
            )
        except Exception as e:
            return {"available": False, "reason": f"judge_yingqi 调用失败: {e}"}


# 模块级便捷函数
_synth = None


def holistic_judge(full_data: Dict) -> Dict:
    global _synth
    if _synth is None:
        _synth = HolisticSynthesizer()
    return _synth.analyze(full_data)


if __name__ == "__main__":
    import sys
    # 自测：从 stock_predictions.json 读取第一条做演示
    p = os.path.join(BASE, "_memory", "stock_predictions.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        for d in data[:3]:
            r = holistic_judge(d)
            print(f"\n=== {d.get('category')} | {d.get('keti')} ===")
            print(f"趋势: {r['trend']} | 分: {r['score']} | 置信: {r['confidence']}")
            print(f"总断: {r['zongduan']}")
            print("辨证五轴:")
            for k, v in r["axes"].items():
                print(f"  {k}: {v['dir']} ({v['signed']:+d}) — {v['evidence']}")
            print("引例:", r["retrieved_cases"][0]["name"] if r["retrieved_cases"] else "无")
    else:
        print("未找到 stock_predictions.json")
