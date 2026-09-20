# -*- coding: utf-8 -*-
"""
混合推理引擎 — llm_judge（确定性引擎 + 本地 Ollama DeepSeek 裁决叙事）
====================================================================
设计（治「仪表盘推理生硬别扭」的根）：
  六壬计算仍由确定性引擎保证（可验证、可复现）；
  本地 DeepSeek 只负责「把证据讲成有说服力的辩证判断」，
  专治规则拼接式的生硬，并受「证据契约」约束防幻觉。

数据流：
  确定性分析 + knowledge_features + CBR古案例 + 训练先验
        └─> 结构化证据包(evidence bundle, JSON)
              └─> 本地 Ollama glm4:9b 提示词(严格证据契约)
                    └─> Ollama 输出「综合判断」叙事(JSON)
                          └─> grounding校验(只能用语包/案例里的事实)
                                └─> 落库 + 仪表盘渲染

降级：Ollama 不可用 / 超时 / 解析失败 → 自动回退到规则综合判断(holistic_synthesis)，仪表盘永不崩。

调用通道：本地 Ollama（HTTP /api/chat，stdlib urllib，零额外依赖）。
模型默认 glm4:9b（实测中文叙事与 JSON 契约最优，见下文 OLLAMA_MODEL 注释）。
"""

from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 保证既可作为包内模块（被 repredict_today 从项目根导入），也可直接 `python engine/llm_judge.py` 运行
if BASE not in sys.path:
    sys.path.insert(0, BASE)
DATA_DIR = os.path.join(BASE, "data")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
# 实测(2026-08-24, RTX4060Ti 16G): glm4:9b 在本任务 8s 完整输出合法JSON且叙事连贯；
# qwen3:14b 因 num_predict=700 输出被截断致 JSON 损坏, 且速度最慢(37s)。
# 故默认用 glm4:9b（中文叙事最优）；可经 OLLAMA_MODEL 覆盖。
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "glm4:9b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# 复用既有模块
try:
    from engine.knowledge_features import extract_knowledge_features
except Exception:  # pragma: no cover
    def extract_knowledge_features(e): return {}

try:
    from engine.holistic_synthesis import HolisticSynthesizer, DialecticalAxes
except Exception:  # pragma: no cover
    HolisticSynthesizer = None
    DialecticalAxes = None

try:
    from unified_trainer import get_trainer
except Exception:  # pragma: no cover
    def get_trainer(): return None


# ======================================================================
# 1) 结构化证据包
# ======================================================================
def build_evidence_bundle(full_data: Dict, kf: Dict, cases: List, trainer) -> Dict:
    """把确定性产物汇编成 LLM 可消费的紧凑证据包（只含事实，不含判断）。"""
    keti = full_data.get("keti", "") or ""
    sanchuan = full_data.get("san_chuan") or full_data.get("sanchuan") or []
    if isinstance(sanchuan, list) and sanchuan and isinstance(sanchuan[0], dict):
        sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]
    sanchuan = [str(z) for z in sanchuan if str(z)]
    tj = (full_data.get("analysis", {}) or {}).get("tianjiang", {}) or {}
    tj_list = [tj.get(c, "") for c in ("初传", "中传", "末传")] if isinstance(tj, dict) else []

    bundle: Dict[str, Any] = {
        "课体": {"名": keti, "等级": (kf.get("keti", {}) or {}).get("level", ""),
                  "断语": (kf.get("keti", {}) or {}).get("duanyu", "")},
        "三传": {"地支": sanchuan, "天将": tj_list,
                  "发用": sanchuan[0] if sanchuan else ""},
        "四组关系": kf.get("relations", {}),
        "理气": kf.get("liqi", {}),
        "类象": kf.get("leixiang", {}),
        "毕法赋推导": kf.get("bifa", {}),
        "三传结构": kf.get("sanchuan", {}),
        "神将组合": kf.get("shenjiang", {}),
    }

    # 辨证五轴态势（供 LLM 融汇，不预设结论）
    if DialecticalAxes is not None:
        try:
            axes = DialecticalAxes.compute(full_data.get("analysis", {}), full_data)
            bundle["辨证五轴态势"] = {
                k: f"{k}{v['dir']}（{v['evidence']}）" for k, v in axes.items()
            }
        except Exception:
            pass

    # 检索古例/股例（CBR 裁决锚）
    if cases:
        bundle["援引课例"] = [
            {"名": c[1].get("name", ""), "源": c[1].get("source", ""),
             "相似度": c[0], "理由": "、".join(c[2]),
             "要旨": str(c[1].get("interpretation", ""))[:140]}
            for c in cases[:3]
        ]

    # 训练先验（多维统计量）
    if trainer is not None:
        try:
            cat = full_data.get("category", "") or full_data.get("target", "")
            w = trainer.get_category_weight(cat)
            fi_score, fi_reasons = trainer.get_knowledge_feature_impact(kf)
            bundle["训练先验"] = {
                "类别准确率权重": round(w, 2),
                "知识点修正分": fi_score,
                "修正理由": fi_reasons[:6],
            }
        except Exception:
            pass

    return bundle


# ======================================================================
# 2) 本地 Ollama 调用（stdlib，零依赖）
# ======================================================================
def call_ollama(system_prompt: str, user_prompt: str,
                 model: str = OLLAMA_MODEL, timeout: int = OLLAMA_TIMEOUT) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 700, "top_p": 0.9},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("message", {}).get("content", "")


# ======================================================================
# 3) 提示词（证据契约）
# ======================================================================
SYSTEM_PROMPT = (
    "你是六壬（大六壬）宗师级推命师，深通《壬归》『立极→取用→辨向→察变→归一』之法，"
    "与『辨证五轴』（动静、刚柔、主客、虚实、始终）之辩证。\n"
    "你的任务：基于求测者这一课【证据包】中的事实，做出一段连贯、有说服力的综合判断，"
    "像面对真实求测者当面论断，而非罗列条目。\n"
    "严格约束（防幻觉）：\n"
    "  1. 只能使用【证据包】里给出的课体、三传、发用、四组关系、理气、类象、毕法赋、援引课例；"
    "不得编造任何课体、神煞、用神、天将或课例。\n"
    "  2. 必须将『辨证五轴态势』融会进叙述，说明各轴如何彼此制衡、最终归一。\n"
    "  3. 若【援引课例】存在，须引用其要旨来定夺矛盾；若为空则不引用。\n"
    "  4. 输出严格 JSON，字段如下，不得输出 JSON 以外的解释文字。"
)

USER_TEMPLATE = (
    "【证据包】\n{evi}\n\n"
    "请基于上述证据，输出严格 JSON（不要任何额外文字）：\n"
    "{{\n"
    "  \"trend\": \"涨\"|\"跌\"|\"震荡\",\n"
    "  \"confidence\": 0.0到1.0之间的小数,\n"
    "  \"zongduan\": \"一句贯通的总断（含趋势与核心依据）\",\n"
    "  \"narrative\": \"一段连贯的综合判断（融入辨证五轴与课例援引，像当面论断，忌清单式罗列）\",\n"
    "  \"axes_narrative\": \"对动静/刚柔/主客/虚实/始终五轴各自的辩证说明（一句一轴）\"\n"
    "}}"
)


def _extract_json(text: str) -> Optional[Dict]:
    """从模型输出中容忍式提取第一个 JSON 对象。"""
    if not text:
        return None
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        return json.loads(text[s:e + 1])
    except Exception:
        return None


def _ground_check(parsed: Dict, bundle: Dict) -> bool:
    """校验 LLM 输出是否被证据约束（防幻觉的最低门槛）。"""
    if not isinstance(parsed, dict):
        return False
    if parsed.get("trend") not in ("涨", "跌", "震荡"):
        return False
    try:
        cf = float(parsed.get("confidence", -1))
        if not (0.0 <= cf <= 1.0):
            return False
    except Exception:
        return False
    nar = str(parsed.get("narrative", "")) + str(parsed.get("zongduan", ""))
    if len(nar) < 20:
        return False
    # 必须引用证据包中的课体或发用，防止凭空杜撰
    keti = (bundle.get("课体", {}) or {}).get("名", "")
    yong = (bundle.get("三传", {}) or {}).get("发用", "")
    if keti and keti not in nar and yong and yong not in nar:
        return False
    return True


# ======================================================================
# 4) 编排：综合裁决
# ======================================================================
def deepseek_synthesize(full_data: Dict, rule_verdict: Optional[Dict] = None,
                        model: str = OLLAMA_MODEL) -> Dict:
    """
    混合推理主入口。返回：
      {
        "llm_verdict": {trend, confidence, zongduan, narrative, axes_narrative, evidence_used},
        "model": model,
        "degraded": False/True,
        "degrade_reason": "...",
        "evidence_bundle": {...}
      }
    degraded=True 时 llm_verdict 回退为 rule_verdict（规则综合判断）。
    """
    result: Dict[str, Any] = {"model": model, "degraded": False, "degrade_reason": "",
                              "llm_verdict": {}, "evidence_bundle": {}}

    # 1) 知识点特征
    try:
        kf = extract_knowledge_features(full_data)
    except Exception:
        kf = {}

    # 2) CBR 检索
    cases: List = []
    try:
        if HolisticSynthesizer is not None:
            lib = HolisticSynthesizer().lib
            sanchuan = full_data.get("san_chuan") or full_data.get("sanchuan") or []
            if isinstance(sanchuan, list) and sanchuan and isinstance(sanchuan[0], dict):
                sanchuan = [s.get("地支", s.get("zhi", "")) for s in sanchuan]
            yong = (full_data.get("analysis", {}) or {}).get("yong_shen", {}).get("用神", "") \
                if isinstance((full_data.get("analysis", {}) or {}).get("yong_shen"), dict) else ""
            rizhu = full_data.get("rizhu", "") or ""
            cases = lib.retrieve(full_data.get("keti", ""), sanchuan, yong, rizhu[:1], top_k=3)
    except Exception:
        cases = []

    # 3) 训练器
    trainer = None
    try:
        trainer = get_trainer()
    except Exception:
        trainer = None

    # 4) 证据包
    bundle = build_evidence_bundle(full_data, kf, cases, trainer)
    result["evidence_bundle"] = bundle

    # 5) 调本地 DeepSeek
    try:
        user_prompt = USER_TEMPLATE.format(evi=json.dumps(bundle, ensure_ascii=False, indent=1))
        raw = call_ollama(SYSTEM_PROMPT, user_prompt, model=model)
        parsed = _extract_json(raw)
        if not parsed or not _ground_check(parsed, bundle):
            raise ValueError(f"LLM 输出未通过证据契约校验 (raw={raw[:120]})")
        result["llm_verdict"] = {
            "trend": parsed.get("trend"),
            "confidence": float(parsed.get("confidence", 0.5)),
            "zongduan": str(parsed.get("zongduan", "")),
            "narrative": str(parsed.get("narrative", "")),
            "axes_narrative": str(parsed.get("axes_narrative", "")),
            "evidence_used": {
                "relations": list((kf.get("relations") or {}).keys()),
                "bifa": (kf.get("bifa") or {}).get("交车", []),
                "cases": [c[1].get("name", "") for c in cases[:3]],
            },
        }
    except Exception as e:
        # 降级到规则综合判断（注意：必须复制为新 dict，绝不能把 rule_verdict 自身赋回自身，否则形成循环引用）
        result["degraded"] = True
        result["degrade_reason"] = str(e)[:160]
        if rule_verdict and isinstance(rule_verdict, dict) and "error" not in rule_verdict:
            result["llm_verdict"] = {
                "trend": rule_verdict.get("trend"),
                "confidence": rule_verdict.get("confidence", 0.5),
                "zongduan": rule_verdict.get("zongduan", "（已降级为规则综合判断）"),
                "narrative": "",
                "axes_narrative": "",
                "evidence_used": {},
                "rule_axes": rule_verdict.get("axes"),
                "rule_evidence": rule_verdict.get("evidence"),
            }
        else:
            result["llm_verdict"] = {
                "trend": (full_data.get("trend_prediction") or "震荡"),
                "confidence": 0.5,
                "zongduan": "（本地模型不可用，已降级为规则综合判断）",
                "narrative": "",
                "axes_narrative": "",
                "evidence_used": {},
            }

    return result


# 模块级便捷函数
_llm = None


def llm_judge(full_data: Dict, rule_verdict: Optional[Dict] = None,
              model: str = OLLAMA_MODEL) -> Dict:
    return deepseek_synthesize(full_data, rule_verdict=rule_verdict, model=model)


if __name__ == "__main__":
    p = os.path.join(BASE, "_memory", "stock_predictions.json")
    if os.path.exists(p):
        data = json.load(open(p, encoding="utf-8"))
        out = deepseek_synthesize(data[0])
        print(json.dumps(out, ensure_ascii=False, indent=2))
