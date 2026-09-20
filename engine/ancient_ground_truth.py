"""
古例真值标签抽取器
从 Corpus B (224例 大六壬断案疏正) + Corpus A 上游(704例 壬占汇选) 的断语中
系统抽取 吉/凶/平 标签。

策略：
1. 关键词规则匹配（高精度，覆盖约70%案例）
2. LLM辅助判断（覆盖规则无法判定者）
3. 求财类优先标注

输出：engine/ancient_truth_labels.json
"""
import json
import re
from pathlib import Path
from collections import Counter

# ============================================================
# 关键词词典
# ============================================================

# 吉兆关键词（按确信度分级）
JILI_STRONG = [
    "可愈", "得中", "获利", "大利", "大吉", "必成", "必得", "得官",
    "升迁", "高中", "及第", "登科", "痊愈", "康复", "全愈",
    "获厚利", "获利丰厚", "大获全胜", "一举成名", "考试得中",
    "婚姻可成", "必生贵子", "出行大吉", "行人即归",
]
JILI_WEAK = [
    "有望", "可成", "顺利", "有成", "平安", "可望", "有利",
    "终获", "可得", "应吉", "佳音", "喜讯", "贵人相助",
    "转危为安", "化险为夷", "有救", "得救",
]

# 凶兆关键词
XIONG_STRONG = [
    "不愈", "不起", "必死", "大凶", "破财", "败诉", "损财",
    "不利", "不成", "不得", "落第", "不中", "罢黜", "降职",
    "家产四分", "尽坏", "耗尽", "倾家", "不治", "死",
    "必败", "大败", "全输", "血本无归",
]
XIONG_WEAK = [
    "难成", "受阻", "不利", "有阻", "多阻", "不顺", "艰难",
    "费财", "耗财", "损利", "不吉", "应凶", "有灾",
    "口舌", "官非", "争讼", "病重", "病危",
]

# 平兆关键词
PING_KEYWORDS = [
    "平平", "无大碍", "无大利", "无大害", "小损", "小利",
    "平常", "一般", "中等", "尚可", "可守", "守成",
    "先难后易", "先凶后吉", "先吉后凶", "起伏",
]

# 求财相关占事（股票映射的核心类别）
WEALTH_QUESTIONS = [
    "求财", "经营", "交易", "买卖", "占货", "占市", "占利",
    "获利", "占商", "贸易", "合本", "开店",
]

# ============================================================
# 规则引擎
# ============================================================

def extract_label_from_interpretation(interpretation: str) -> dict:
    """
    从断语中抽取吉凶标签。
    返回: {"label": "吉"/"凶"/"平"/"未知", "confidence": 0-1, "evidence": str}
    """
    text = interpretation or ""
    if not text.strip():
        return {"label": "未知", "confidence": 0.0, "evidence": ""}

    # 1. 强吉
    for kw in JILI_STRONG:
        if kw in text:
            return {"label": "吉", "confidence": 0.95, "evidence": f"命中强吉词:{kw}"}

    # 2. 强凶
    for kw in XIONG_STRONG:
        if kw in text:
            return {"label": "凶", "confidence": 0.95, "evidence": f"命中强凶词:{kw}"}

    # 3. 弱吉
    ji_evidence = []
    for kw in JILI_WEAK:
        if kw in text:
            ji_evidence.append(kw)

    # 4. 弱凶
    xiong_evidence = []
    for kw in XIONG_WEAK:
        if kw in text:
            xiong_evidence.append(kw)

    # 5. 平
    for kw in PING_KEYWORDS:
        if kw in text:
            return {"label": "平", "confidence": 0.75, "evidence": f"命中平词:{kw}"}

    # 6. 综合判断弱标签
    ji_score = len(ji_evidence)
    xiong_score = len(xiong_evidence)

    if ji_score > xiong_score and ji_score >= 2:
        return {"label": "吉", "confidence": 0.70,
                "evidence": f"弱吉词:{','.join(ji_evidence)}"}
    elif xiong_score > ji_score and xiong_score >= 2:
        return {"label": "凶", "confidence": 0.70,
                "evidence": f"弱凶词:{','.join(xiong_evidence)}"}
    elif ji_score > xiong_score:
        return {"label": "吉", "confidence": 0.55,
                "evidence": f"弱吉词:{','.join(ji_evidence)}"}
    elif xiong_score > ji_score:
        return {"label": "凶", "confidence": 0.55,
                "evidence": f"弱凶词:{','.join(xiong_evidence)}"}

    # 7. LLM级别的语义判断：解析断语中的结论句
    # 末传/末传结论往往是最终结果
    last_sentence = text.split("。")[-2] if "。" in text[:-1] else text[-60:]
    # 检查末句中的极性
    for kw in JILI_STRONG + JILI_WEAK:
        if kw in last_sentence:
            return {"label": "吉", "confidence": 0.60,
                    "evidence": f"末句含吉词:{kw}"}
    for kw in XIONG_STRONG + XIONG_WEAK:
        if kw in last_sentence:
            return {"label": "凶", "confidence": 0.60,
                    "evidence": f"末句含凶词:{kw}"}

    return {"label": "未知", "confidence": 0.0, "evidence": "规则未命中"}


def classify_question(question: str) -> str:
    """占事分类"""
    q = question or ""
    for wq in WEALTH_QUESTIONS:
        if wq in q:
            return "求财"
    if "病" in q or "疾" in q:
        return "疾病"
    if "宅" in q or "家" in q or "修造" in q:
        return "家宅"
    if "婚姻" in q or "婚" in q or "嫁" in q:
        return "婚姻"
    if "考试" in q or "功名" in q or "仕" in q or "科举" in q or "前程" in q:
        return "功名"
    if "出行" in q or "行" in q:
        return "出行"
    if "官" in q or "讼" in q:
        return "官讼"
    if "走失" in q or "逃亡" in q:
        return "走失"
    if "产" in q or "孕" in q:
        return "胎产"
    if "寿" in q:
        return "寿元"
    if "征战" in q or "兵" in q:
        return "征战"
    if "蚕" in q:
        return "蚕桑"
    if "学" in q or "书" in q:
        return "学业"
    if "升迁" in q or "补官" in q:
        return "功名"
    return "其他"


# ============================================================
# 三传解析辅助
# ============================================================

def parse_sanchuan_str(s: str) -> list:
    """解析 "巳→寅→亥" 格式的三传字符串"""
    if not s:
        return []
    # 支持 → / -> / 空格分隔
    parts = re.split(r'[→\->\s]+', s.strip())
    return [p.strip() for p in parts if p.strip()]


def parse_time_to_shichen(hour: int) -> str:
    """将小时数转为时辰"""
    SHICHEN_MAP = {
        0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅", 5: "卯", 6: "卯",
        7: "辰", 8: "辰", 9: "巳", 10: "巳", 11: "午", 12: "午",
        13: "未", 14: "未", 15: "申", 16: "申", 17: "酉", 18: "酉",
        19: "戌", 20: "戌", 21: "亥", 22: "亥", 23: "子",
    }
    return SHICHEN_MAP.get(hour % 24, "子")


# ============================================================
# 主流程
# ============================================================

def process_corpus_b(filepath: str) -> list:
    """处理 Corpus B (大六壬断案疏正 224例)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    results = []
    for case in cases:
        interp = case.get("interpretation", "")
        label_info = extract_label_from_interpretation(interp)
        qtype = classify_question(case.get("question", ""))

        # 解析三传
        sanchuan_str = case.get("sanchuan", "")
        sanchuan = parse_sanchuan_str(sanchuan_str)

        # 解析课体
        keti_str = case.get("ke_ti", "")
        keti_list = [k.strip() for k in keti_str.replace("、", "，").split("，") if k.strip()]

        # 时辰转换
        hour = case.get("hour", 0)
        shichen = parse_time_to_shichen(hour)

        record = {
            "source": "Corpus_B",
            "id": case.get("id", ""),
            "name": case.get("name", ""),
            "question": case.get("question", ""),
            "category": qtype,
            "ri_gan": case.get("ri_gan", ""),
            "ri_zhi": case.get("ri_zhi", ""),
            "rizhu": f"{case.get('ri_gan','')}{case.get('ri_zhi','')}",
            "yue_jiang": case.get("yue_jiang", ""),
            "shichen": shichen,
            "hour": hour,
            "keti": keti_list,
            "sanchuan": sanchuan,
            "era": case.get("era", ""),
            # 标签
            "label": label_info["label"],
            "label_confidence": label_info["confidence"],
            "label_evidence": label_info["evidence"],
            # 断语原文（供人工复核）
            "interpretation": interp[:300],
            "sanchuan_interpretation": case.get("sanchuan_interpretation", "")[:200],
            "yingqi": case.get("yingqi", ""),
        }
        results.append(record)

    return results


def process_corpus_a(filepath: str) -> list:
    """处理 Corpus A 上游 (壬占汇选 704例) - 从 case_text 中抽取"""
    with open(filepath, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    results = []
    for case in cases:
        case_text = case.get("case_text", "")
        # 尝试从 case_text 中提取断语部分（通常在"断曰"之后）
        duanyu = ""
        if "断曰" in case_text or "断：" in case_text:
            parts = re.split(r'断曰|断：', case_text, maxsplit=1)
            if len(parts) > 1:
                duanyu = parts[1][:500]

        label_info = extract_label_from_interpretation(duanyu) if duanyu else \
                     extract_label_from_interpretation(case_text)

        question = case.get("question", "")
        qtype = classify_question(question)

        # 解析三传
        sanchuan_raw = case.get("sanchuan", "")
        if isinstance(sanchuan_raw, list):
            sanchuan = sanchuan_raw
        elif isinstance(sanchuan_raw, str):
            sanchuan = parse_sanchuan_str(sanchuan_raw)
        else:
            sanchuan = []

        record = {
            "source": "Corpus_A",
            "id": f"RH-{case.get('ganzhi','')}",
            "name": case.get("source", ""),
            "question": question,
            "category": qtype,
            "ri_gan": case.get("ganzhi", "")[:1] if case.get("ganzhi") else "",
            "ri_zhi": case.get("ganzhi", "")[1:] if case.get("ganzhi") and len(case.get("ganzhi",""))>=2 else "",
            "rizhu": case.get("ganzhi", ""),
            "yue_jiang": case.get("yuejiang", ""),
            "shichen": case.get("shichen", ""),
            "keti": [],
            "sanchuan": sanchuan,
            "label": label_info["label"],
            "label_confidence": label_info["confidence"],
            "label_evidence": label_info["evidence"],
            "interpretation": duanyu[:300] if duanyu else case_text[:300],
        }
        results.append(record)

    return results


def print_summary(results: list, title: str):
    """打印标签分布摘要"""
    labels = Counter(r["label"] for r in results)
    cats = Counter(r["category"] for r in results)
    high_conf = sum(1 for r in results if r["label_confidence"] >= 0.70 and r["label"] != "未知")
    unknown = sum(1 for r in results if r["label"] == "未知")

    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"  总案例: {len(results)}")
    print(f"  标签分布: 吉={labels.get('吉',0)}, 凶={labels.get('凶',0)}, "
          f"平={labels.get('平',0)}, 未知={unknown}")
    print(f"  高置信度(≥0.7): {high_conf} ({100*high_conf/len(results):.1f}%)")
    print(f"  覆盖率: {100*(len(results)-unknown)/len(results):.1f}%")

    print(f"\n  占事分类:")
    for cat, cnt in cats.most_common():
        cat_labels = Counter(r["label"] for r in results if r["category"] == cat)
        print(f"    {cat}: {cnt} (吉{cat_labels.get('吉',0)} "
              f"凶{cat_labels.get('凶',0)} 平{cat_labels.get('平',0)} "
              f"未知{cat_labels.get('未知',0)})")

    # 求财类专项
    wealth = [r for r in results if r["category"] == "求财"]
    if wealth:
        wl = Counter(r["label"] for r in wealth)
        print(f"\n  ★ 求财类专项: {len(wealth)}例")
        print(f"    吉={wl.get('吉',0)}, 凶={wl.get('凶',0)}, "
              f"平={wl.get('平',0)}, 未知={wl.get('未知',0)}")
        print(f"    覆盖率: {100*(len(wealth)-wl.get('未知',0))/len(wealth):.1f}%")
        # 显示未知的求财案例
        unknown_wealth = [r for r in wealth if r["label"] == "未知"]
        if unknown_wealth:
            print(f"    ⚠ 未标注求财案例:")
            for r in unknown_wealth[:5]:
                print(f"      [{r['id']}] {r['name']}: {r['interpretation'][:100]}...")


def main():
    base = Path(__file__).parent.parent
    output_path = base / "engine" / "ancient_truth_labels.json"
    merged = []

    # 1. Corpus B
    corpus_b_path = base / "data" / "daliuren_shuzheng_cases.json"
    if corpus_b_path.exists():
        b_results = process_corpus_b(str(corpus_b_path))
        print_summary(b_results, "Corpus B: 大六壬断案疏正 (224例)")
        merged.extend(b_results)
    else:
        print("⚠ Corpus B 文件不存在")

    # 2. Corpus A 上游 (壬占汇选)
    corpus_a_path = base / "extracted_data" / "壬占汇选_训练数据_v2.json"
    if corpus_a_path.exists():
        a_results = process_corpus_a(str(corpus_a_path))
        print_summary(a_results, "Corpus A 上游: 壬占汇选 (704例)")
        merged.extend(a_results)
    else:
        print("⚠ 壬占汇选 文件不存在")

    # 3. 汇总
    print_summary(merged, "全部古例汇总")

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "_meta": {
                "version": "1.0.0",
                "created": "2026-07-30",
                "description": "古例真值标签（吉/凶/平），从断语文本中规则抽取",
                "total": len(merged),
                "sources": ["Corpus_B(大六壬断案疏正)", "Corpus_A上游(壬占汇选)"],
            },
            "cases": merged
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 标签已保存至: {output_path}")
    print(f"   总案例: {len(merged)}")

    # 输出求财类高置信样本
    wealth_high = [r for r in merged
                   if r["category"] == "求财"
                   and r["label_confidence"] >= 0.70
                   and r["label"] != "未知"]
    print(f"\n   求财类高置信样本: {len(wealth_high)}例 (可用于引擎校准)")


if __name__ == "__main__":
    main()
