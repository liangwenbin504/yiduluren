# -*- coding: utf-8 -*-
"""
六壬知识点特征工程 — knowledge_features
====================================================================
把每条课例自动派生为「训练系统可学习」的结构化特征，覆盖：

  ● 四组关系（用户重点）
      干上神↔发用 / 支上神↔发用 / 日干↔发用 / 支↔发用
      日干↔支上神(交车) / 支↔干上神(交车)
  ● 理气：旺衰、十二长生、空亡、月将、进气退气
  ● 类象：天将刚柔向量、神煞命中
  ● 课体：课名 + 等级 + 历史准确率（由训练库给）
  ● 毕法赋：从关系/空亡推导的关键法（交车相合/相克/相刑/相冲/用神空）
  ● 三传结构：发用五行、初中末生克流向、进茹/退茹
  ● 神将组合：初传天将 + 发用地支

输出分三层：
  features['relations']     四组关系（人类可读）
  features['liqi']          理气
  features['leixiang']      类象
  features['keti']          课体
  features['bifa']          毕法赋推导
  features['sanchuan']      三传结构
  features['shenjiang']     神将组合
  features['vector']        扁平特征向量（供 unified_trainer 消费/学习）

本模块不依赖重量级引擎，纯确定性计算；任意一步失败都降级为空，绝不让预测链路崩溃。
"""

from __future__ import annotations
import os
import json
from typing import Dict, List, Any, Optional

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")

# ───────────── 五行 / 干支基础 ─────────────
WX: Dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}
GAN_WX: Dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土",
    "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
SHENG: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

LIU_HE = {  # 地支六合
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午",
}
CHONG = {  # 六冲
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}
HAI = {  # 六害
    "子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉",
}
XING_PAIRS = {  # 三刑（无序对）
    frozenset(("寅", "巳")), frozenset(("巳", "申")), frozenset(("寅", "申")),
    frozenset(("丑", "戌")), frozenset(("戌", "未")), frozenset(("丑", "未")),
    frozenset(("子", "卯")),
    frozenset(("辰", "辰")), frozenset(("午", "午")),
    frozenset(("酉", "酉")), frozenset(("亥", "亥")),
}
GAN_HE = {  # 天干五合
    "甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛", "辛": "丙",
    "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊",
}
# 关系 → 有符号分值（以「对『我/干』是否有利」为基准的通用编码）
REL_SIGN = {
    "生我": 1.0, "我生": -0.5, "克我": -1.0, "我克": 0.5, "比和": 0.0,
    "六合": 0.5, "六冲": -1.0, "六害": -0.5, "三刑": -1.0, "天干合": 0.5, "无": 0.0,
}

# 天将刚柔类象
GANG_TJ = {"白虎", "玄武", "勾陈", "螣蛇", "朱雀"}
ROU_TJ = {"贵人", "青龙", "六合", "太阴", "天后"}
TIANJIANG_NAME = {  # 取天将名（去"+\金"等后缀）
    "贵人": "贵人", "青龙": "青龙", "六合": "六合", "太常": "太常", "朱雀": "朱雀",
    "白虎": "白虎", "玄武": "玄武", "太阴": "太阴", "天后": "天后", "螣蛇": "螣蛇",
    "勾陈": "勾陈", "天空": "天空",
}
# 关键神煞（吉 / 凶 分类）
JI_SHA = {"天德", "月德", "天喜", "天赦", "驿马", "日禄", "文昌", "禄神", "日贵", "天乙贵人", "日马"}
XIONG_SHA = {"劫煞", "灾煞", "羊刃", "桃花", "孤辰", "寡宿", "丧门", "吊客", "病符", "岁破", "月破", "日破", "日害"}
# 旺衰 → 强弱权重
WANG_W = {"长生": 1.0, "沐浴": 0.6, "冠带": 0.7, "临官": 0.9, "帝旺": 1.0,
          "衰": 0.3, "病": 0.1, "死": -0.4, "墓": -0.6, "绝": -0.8, "胎": -0.2, "养": 0.0}
WANG_GRADE = {"旺": 1.0, "相": 0.6, "休": -0.3, "囚": -0.6, "死": -0.8}


def _wx_of(token: str) -> str:
    return GAN_WX.get(token, WX.get(token, ""))


def _is_gan(token: str) -> bool:
    return token in GAN_WX


def relation(a: str, b: str) -> Dict[str, Any]:
    """返回 a 对 b 的关系（以 a 为参照的通用生克编码）。
    返回 {relation, signed}。a/b 可为天干或地支。"""
    if not a or not b or a == b:
        return {"relation": "比和" if a == b else "无", "signed": 0.0 if a == b else 0.0}
    wa, wb = _wx_of(a), _wx_of(b)
    # 五行生克（两边都有五行时）
    if wa and wb:
        if SHENG[wa] == wb:
            return {"relation": "我生", "signed": REL_SIGN["我生"]}
        if SHENG[wb] == wa:
            return {"relation": "生我", "signed": REL_SIGN["生我"]}
        if KE[wa] == wb:
            return {"relation": "我克", "signed": REL_SIGN["我克"]}
        if KE[wb] == wa:
            return {"relation": "克我", "signed": REL_SIGN["克我"]}
        if wa == wb:
            return {"relation": "比和", "signed": 0.0}
    # 合 / 刑 / 冲 / 害（地支之间用六合；天干+地支用天干五合）
    if a in GAN_WX or b in GAN_WX:
        # 有一方是天干：检查天干五合
        if a in GAN_HE and GAN_HE.get(a) == b:
            return {"relation": "天干合", "signed": REL_SIGN["天干合"]}
        if b in GAN_HE and GAN_HE.get(b) == a:
            return {"relation": "天干合", "signed": REL_SIGN["天干合"]}
    else:
        # 双方皆地支
        if LIU_HE.get(a) == b:
            return {"relation": "六合", "signed": REL_SIGN["六合"]}
        if CHONG.get(a) == b:
            return {"relation": "六冲", "signed": REL_SIGN["六冲"]}
        if HAI.get(a) == b:
            return {"relation": "六害", "signed": REL_SIGN["六害"]}
        if frozenset((a, b)) in XING_PAIRS:
            return {"relation": "三刑", "signed": REL_SIGN["三刑"]}
    return {"relation": "无", "signed": 0.0}


def _clean_tj(s: str) -> str:
    """取天将名（去 '+\金' 等）。"""
    if not s:
        return ""
    s = str(s).split("+")[0].strip().split("(")[0].strip()
    return TIANJIANG_NAME.get(s, s)


def extract_knowledge_features(entry: Dict) -> Dict[str, Any]:
    """从一条预测 entry 派生全部知识点特征。失败降级为空字典。"""
    out: Dict[str, Any] = {
        "relations": {}, "liqi": {}, "leixiang": {},
        "keti": {}, "bifa": {}, "sanchuan": {}, "shenjiang": {}, "vector": {},
    }
    try:
        rizhu = entry.get("rizhu", "") or ""
        ri_gan = rizhu[:1]
        ri_zhi = rizhu[1:2]
        keti = entry.get("keti", "") or ""
        sanchuan = entry.get("san_chuan") or entry.get("sanchuan") or []
        if isinstance(sanchuan, list) and sanchuan and isinstance(sanchuan[0], dict):
            sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]
        sanchuan = [str(z).strip() for z in sanchuan if str(z).strip()]

        analysis = entry.get("analysis", {}) or {}
        if not isinstance(analysis, dict):
            analysis = {}

        # 四课：sike[0]=第一课(干上神,日干)；sike[2]=第三课(支上神,日支)
        sike = entry.get("sike", []) or []
        gan_shang = zhi_shang = ""
        if isinstance(sike, list) and len(sike) >= 4:
            try:
                if isinstance(sike[0], (list, tuple)) and len(sike[0]) >= 2:
                    gan_shang = str(sike[0][1])
                if isinstance(sike[2], (list, tuple)) and len(sike[2]) >= 2:
                    zhi_shang = str(sike[2][1])
            except Exception:
                pass

        # 发用（初传）
        yong = sanchuan[0] if sanchuan else ""
        yong_from_analysis = analysis.get("yong_shen", {}).get("用神", "") if isinstance(analysis.get("yong_shen"), dict) else ""
        yong = yong or yong_from_analysis

        # ───── 1) 四组关系 ─────
        rel_pairs = {
            "干上神_发用": (gan_shang, yong),
            "支上神_发用": (zhi_shang, yong),
            "日干_发用": (ri_gan, yong),
            "支_发用": (ri_zhi, yong),
            "日干_支上神": (ri_gan, zhi_shang),   # 交车③
            "支_干上神": (ri_zhi, gan_shang),      # 交车④
        }
        for name, (a, b) in rel_pairs.items():
            if a and b:
                r = relation(a, b)
                out["relations"][name] = {
                    "a": a, "b": b,
                    "relation": r["relation"], "signed": r["signed"],
                }

        # ───── 2) 理气 ─────
        liqi: Dict[str, Any] = {}
        # 用神旺衰（取自 analysis.yong_shen.旺衰 或 wangshuai 列表）
        yong_ws = analysis.get("yong_shen", {}).get("旺衰", "") if isinstance(analysis.get("yong_shen"), dict) else ""
        if not yong_ws and sanchuan:
            wang = analysis.get("wangshuai", []) or []
            for w in wang:
                if isinstance(w, dict) and w.get("地支") == yong:
                    yong_ws = w.get("旺衰", "")
                    break
        liqi["用神旺衰"] = yong_ws
        liqi["用神旺衰分"] = WANG_GRADE.get(yong_ws, 0.0) if yong_ws in WANG_GRADE else WANG_W.get(yong_ws, 0.0)
        # 空亡（初/中/末传）
        kong = analysis.get("kong_info", {}) or {}
        kong_hits = [k for k, v in kong.items() if v] if isinstance(kong, dict) else []
        liqi["空亡传"] = kong_hits
        liqi["空亡数"] = len(kong_hits)
        liqi["旬空"] = analysis.get("xun_kong", []) or []
        liqi["月将"] = entry.get("yue_jiang", "")
        # 进气退气：初中末传旺衰序列趋势
        if sanchuan:
            wmap = {w.get("地支"): w.get("旺衰", "") for w in (analysis.get("wangshuai", []) or []) if isinstance(w, dict)}
            seq = [WANG_GRADE.get(wmap.get(z, ""), WANG_W.get(wmap.get(z, ""), 0.0)) for z in sanchuan if z in wmap]
            if len(seq) >= 2:
                if seq[-1] > seq[0] + 0.2:
                    liqi["气之流转"] = "进气(初→末渐旺)"
                elif seq[-1] < seq[0] - 0.2:
                    liqi["气之流转"] = "退气(初→末渐衰)"
                else:
                    liqi["气之流转"] = "平气"
            else:
                liqi["气之流转"] = "平气"
        out["liqi"] = liqi

        # ───── 3) 类象 ─────
        leixiang: Dict[str, Any] = {}
        tj = analysis.get("tianjiang", {}) or {}
        tj_names = []
        for chuan in ("初传", "中传", "末传"):
            t = _clean_tj(tj.get(chuan, "")) if isinstance(tj, dict) else ""
            if t:
                tj_names.append(t)
        leixiang["三传天将"] = tj_names
        gang_n = sum(1 for t in tj_names if t in GANG_TJ)
        rou_n = sum(1 for t in tj_names if t in ROU_TJ)
        leixiang["刚煞数"] = gang_n
        leixiang["柔神数"] = rou_n
        leixiang["刚柔净额"] = rou_n - gang_n   # >0 柔主，<0 刚主
        # 神煞命中
        sha = analysis.get("shen_sha", {}) or {}
        ji_hit, xiong_hit = [], []
        if isinstance(sha, dict):
            for k in sha.keys():
                if k in JI_SHA:
                    ji_hit.append(k)
                elif k in XIONG_SHA:
                    xiong_hit.append(k)
        leixiang["吉神"] = ji_hit
        leixiang["凶煞"] = xiong_hit
        leixiang["吉神数"] = len(ji_hit)
        leixiang["凶煞数"] = len(xiong_hit)
        out["leixiang"] = leixiang

        # ───── 4) 课体 ─────
        keti_dy = analysis.get("keti_duanyu", {}) or {}
        out["keti"] = {
            "name": keti,
            "level": keti_dy.get("level") or keti_dy.get("等级", ""),
            "duanyu": keti_dy.get("duanyu") or keti_dy.get("断语", ""),
        }

        # ───── 5) 毕法赋（由关系/空亡推导的关键法）─────
        bifa: Dict[str, Any] = {}
        r = out["relations"]
        # 交车相合/相克/相刑/相冲
        jiaoche = []
        if r.get("日干_支上神", {}).get("relation") in ("天干合", "六合"):
            jiaoche.append("交车相合(干与支上神合)")
        if r.get("支_干上神", {}).get("relation") in ("六合",):
            jiaoche.append("交车相合(支与干上神合)")
        if r.get("日干_支上神", {}).get("relation") == "克我":
            jiaoche.append("交车相克(干被支上神克)")
        if r.get("支_干上神", {}).get("relation") == "克我":
            jiaoche.append("交车相克(支被干上神克)")
        if r.get("日干_支上神", {}).get("relation") == "三刑":
            jiaoche.append("交车相刑")
        if r.get("日干_支上神", {}).get("relation") == "六冲":
            jiaoche.append("交车相冲")
        if r.get("支_干上神", {}).get("relation") == "六冲":
            jiaoche.append("交车相冲")
        bifa["交车"] = jiaoche
        # 用神空亡（画饼）
        if "初传" in liqi.get("空亡传", []):
            bifa["用神空"] = "初传(发用)落空，凡事不实"
        # 全备/不备（四课缺失）
        bifa["课格提示"] = []
        if "遥克" in (entry.get("fayong", "") or "") or "昴星" in (entry.get("fayong", "") or ""):
            bifa["课格提示"].append("遥克/昴星·事由外动")
        out["bifa"] = bifa

        # ───── 6) 三传结构 ─────
        sc: Dict[str, Any] = {}
        sc["发用"] = yong
        sc["发用五行"] = WX.get(yong, "")
        if len(sanchuan) >= 3:
            c, z, m = sanchuan[0], sanchuan[1], sanchuan[2]
            sc["初中末"] = sanchuan
            sc["初克中"] = relation(c, z)["relation"]
            sc["中克末"] = relation(z, m)["relation"]
            sc["初克末"] = relation(c, m)["relation"]
            # 进茹/退茹（连续顺/逆）
            order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
            try:
                idxs = [order.index(x) for x in sanchuan[:3]]
                if idxs[0] + 1 == idxs[1] and idxs[1] + 1 == idxs[2]:
                    sc["传变"] = "进茹(气进)"
                elif idxs[0] - 1 == idxs[1] and idxs[1] - 1 == idxs[2]:
                    sc["传变"] = "退茹(气退)"
                else:
                    sc["传变"] = "乱传"
            except Exception:
                sc["传变"] = "未知"
        out["sanchuan"] = sc

        # ───── 7) 神将组合 ─────
        out["shenjiang"] = {
            "初传天将": tj_names[0] if tj_names else "",
            "发用地支": yong,
            "组合": f"{tj_names[0] if tj_names else '?'}+{yong}" if yong else "",
        }

        # ───── 8) 扁平特征向量（供训练系统消费/学习）─────
        vec: Dict[str, Any] = {}
        for name, info in out["relations"].items():
            vec[f"rel_{name}"] = info["relation"]
            vec[f"rel_{name}_signed"] = info["signed"]
        vec["yong_wangshuai"] = liqi.get("用神旺衰", "")
        vec["kong_count"] = liqi.get("空亡数", 0)
        vec["qi_flow"] = liqi.get("气之流转", "")
        vec["gang_net"] = leixiang.get("刚柔净额", 0)
        vec["ji_sha_count"] = leixiang.get("吉神数", 0)
        vec["xiong_sha_count"] = leixiang.get("凶煞数", 0)
        vec["keti"] = keti
        vec["keti_level"] = out["keti"].get("level", "")
        vec["bifa_jiaoche"] = "|".join(bifa.get("交车", []))
        vec["yong_kong"] = 1 if bifa.get("用神空") else 0
        vec["chuan_bian"] = sc.get("传变", "")
        vec["chu_ke_zhong"] = sc.get("初克中", "")
        out["vector"] = vec

    except Exception:
        # 绝不让特征工程拖垮预测链路
        pass
    return out


def _has_knowledge_signal(kf: Dict) -> bool:
    """是否产出任一可用于权重反哺的维度信号。

    纯量化/ML 记录往往不含六壬原始字段（日柱/四课/三传/旺衰），extract 后只剩
    空壳；这种情况不应写回 knowledge_features，否则会让 Step1 合格样本数虚高却
    学不到任何维度。仅在真正存在关系/理气/类象/毕法/三传信号时才算有效。
    """
    if not isinstance(kf, dict):
        return False
    if kf.get("relations"):
        return True
    liqi = kf.get("liqi", {}) or {}
    if liqi.get("用神旺衰"):
        return True
    if liqi.get("空亡数"):
        return True
    lx = kf.get("leixiang", {}) or {}
    if lx.get("刚柔净额") not in (0, None):
        return True
    if (kf.get("bifa", {}) or {}).get("交车"):
        return True
    if (kf.get("sanchuan", {}) or {}).get("传变"):
        return True
    return False


def extract_for_backfill(entry: Dict) -> Optional[Dict]:
    """回填专用入口：萃取知识点特征，无可用信号则返回 None（不污染合格样本判定）。

    供 stock_result_check / quant_predictor / tianji_harness 三个结算步在标记
    status=completed 时调用，仅在含六壬维度信号时才返回特征字典。
    """
    kf = extract_knowledge_features(entry)
    if _has_knowledge_signal(kf):
        return kf
    return None


# 模块级便捷函数
def get_features(entry: Dict) -> Dict[str, Any]:
    return extract_knowledge_features(entry)


if __name__ == "__main__":
    import sys
    p = os.path.join(BASE, "_memory", "stock_predictions.json")
    if os.path.exists(p):
        data = json.load(open(p, encoding="utf-8"))
        e = data[0]
        feats = extract_knowledge_features(e)
        print(json.dumps(feats, ensure_ascii=False, indent=2))
