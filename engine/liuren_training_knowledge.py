#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬训练结果知识库
基于第8轮224案例训练结果构建

功能：
1. 按占事分类存储训练案例
2. 存储类象特征和判断规律
3. 支持快速查询类似案例
4. 支持新增案例追加训练
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from engine.vector_knowledge_base import VectorKnowledgeBase


class LiuRenTrainingKnowledge:
    """大六壬训练结果知识库类"""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.training_results_file = os.path.join(base_dir, "224案例GLM4第十轮训练结果_1_224.json")
        self.original_cases_file = os.path.join(base_dir, "extracted_cases_v2_20260416_172701.json")
        self.stock_cases_file = os.path.join(base_dir, "data", "stock_training_cases.json")
        self.knowledge_base = self._build_knowledge_base()
        self.vector_kb = VectorKnowledgeBase(
            persist_dir=os.path.join(base_dir, "data", "vector_store")
        )
        self._build_vector_index()

    def _build_vector_index(self):
        """构建向量索引，支持语义搜索"""
        if not self.vector_kb.load():
            all_cases = []
            for cat, cases in self.knowledge_base.get("占事分类", {}).items():
                for case in cases:
                    enriched = dict(case)
                    enriched["占事"] = cat
                    all_cases.append(enriched)
            if all_cases:
                self.vector_kb.add_documents(all_cases)
                self.vector_kb.save()

    def _rebuild_vector_index(self):
        """重建向量索引（当知识库变更时调用）"""
        all_cases = []
        for cat, cases in self.knowledge_base.get("占事分类", {}).items():
            for case in cases:
                enriched = dict(case)
                enriched["占事"] = cat
                all_cases.append(enriched)
        if all_cases:
            self.vector_kb = VectorKnowledgeBase(
                persist_dir=os.path.dirname(
                    self.vector_kb.persist_dir
                ) if hasattr(self.vector_kb, 'persist_dir') else None
            )
            self.vector_kb.add_documents(all_cases)
            self.vector_kb.save()

    def _build_knowledge_base(self) -> Dict:
        """构建知识库"""
        if not os.path.exists(self.training_results_file):
            kb = self._create_empty_knowledge_base()
        else:
            with open(self.training_results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            original_cases = {}
            if os.path.exists(self.original_cases_file):
                with open(self.original_cases_file, 'r', encoding='utf-8') as f:
                    original = json.load(f)
                    for case in original:
                        original_cases[case.get('id', '')] = case

            kb = {
                "元数据": {
                    "总案例数": len(results),
                    "训练轮次": 10,
                    "构建时间": self._get_timestamp()
                },
                "占事分类": self._categorize_by_zhanshi(results, original_cases),
                "课体分类": self._categorize_by_tiandui(results),
                "关键词规律": self._extract_keyword_patterns(results),
                "类象规则": self._extract_leixiang_rules(results)
            }

        stock_cases = self._load_stock_cases()
        if stock_cases:
            if "占事分类" not in kb:
                kb["占事分类"] = {}
            kb["占事分类"]["stock"] = stock_cases
            kb["元数据"]["总案例数"] = kb["元数据"].get("总案例数", 0) + len(stock_cases)
            kb["元数据"]["股票案例数"] = len(stock_cases)
            kb["元数据"]["构建时间"] = self._get_timestamp()

        return kb

    def _load_stock_cases(self) -> List[Dict]:
        """加载股票训练案例"""
        if not os.path.exists(self.stock_cases_file):
            print(f"股票案例文件不存在: {self.stock_cases_file}")
            return []

        try:
            with open(self.stock_cases_file, 'r', encoding='utf-8') as f:
                raw_cases = json.load(f)

            formatted_cases = []
            for case in raw_cases:
                formatted_cases.append({
                    "id": case.get("id", ""),
                    "原文": case.get("raw_text", ""),
                    "实际事情": case.get("actual_result", ""),
                    "预测事情": case.get("original_prediction", ""),
                    "类象特征": self._extract_leixiang_features(case.get("original_prediction", "")),
                    "stock_code": case.get("stock_code", ""),
                    "stock_name": case.get("stock_name", ""),
                    "trend_prediction": case.get("trend_prediction", ""),
                    "is_correct": case.get("is_correct", False),
                    "liuqin_analysis": case.get("liuqin_analysis", ""),
                    "tianjiang_analysis": case.get("tianjiang_analysis", "")
                })

            return formatted_cases
        except Exception as e:
            print(f"加载股票案例失败: {e}")
            return []

    def _create_empty_knowledge_base(self) -> Dict:
        """创建空知识库"""
        return {
            "元数据": {
                "总案例数": 0,
                "训练轮次": 0,
                "构建时间": self._get_timestamp()
            },
            "占事分类": {},
            "课体分类": {},
            "关键词规律": {},
            "类象规则": {}
        }

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _extract_zhanshi_from_id(self, case_id: str) -> str:
        """从案例ID中提取占事类型"""
        if not case_id:
            return "未知"

        patterns = [
            (r'CASE-天时-\d+', '天时'),
            (r'CASE-流年-\d+', '流年'),
            (r'CASE-终身-\d+', '终身'),
            (r'CASE-婚姻-\d+', '婚姻'),
            (r'CASE-官讼-\d+', '官讼'),
            (r'CASE-疾病-\d+', '疾病'),
            (r'CASE-出行-\d+', '出行'),
            (r'CASE-求财-\d+', '求财'),
            (r'CASE-行人-\d+', '行人'),
            (r'CASE-失物-\d+', '失物'),
            (r'CASE-田宅-\d+', '田宅'),
            (r'CASE-考试-\d+', '考试'),
            (r'CASE-交易-\d+', '交易'),
            (r'CASE-经营-\d+', '经营'),
            (r'CASE-开业-\d+', '开业'),
            (r'CASE-安葬-\d+', '安葬'),
            (r'CASE-STOCK-\d+', 'stock'),
            (r'CASE-股票-\d+', 'stock'),
            (r'CASE-其他-\d+', '其他'),
        ]

        for pattern, zhanshi in patterns:
            if re.match(pattern, case_id):
                return zhanshi

        return "未知"

    def _categorize_by_zhanshi(self, results: List[Dict], original_cases: Dict) -> Dict:
        """按占事分类"""
        categories = defaultdict(list)

        for result in results:
            case_id = result.get('id', '')
            zhanshi = self._extract_zhanshi_from_id(case_id)

            if zhanshi == "未知":
                raw_text = result.get('原文', '')
                if not raw_text and case_id in original_cases:
                    raw_text = original_cases[case_id].get('raw_text', '')
                if raw_text:
                    zhanshi = self._guess_zhanshi(raw_text)

            if zhanshi == "未知":
                zhanshi = "其他"

            original = original_cases.get(case_id, {})

            categories[zhanshi].append({
                "id": case_id,
                "原文": result.get('原文', '') or original.get('raw_text', ''),
                "实际事情": result.get('实际事情', '') or original.get('original_prediction', ''),
                "预测事情": result.get('预测事情', ''),
                "类象特征": self._extract_leixiang_features(result.get('预测事情', ''))
            })

        return dict(categories)

    def _guess_zhanshi(self, raw_text: str) -> str:
        """根据原文猜测占事类型"""
        if not raw_text:
            return "未知"

        keywords_map = {
            "天时": ["天", "雨", "雪", "晴", "风", "寒", "暖", "节气", "气候"],
            "流年": ["流年", "一年", "今年", "年来", "运势", "年命"],
            "终身": ["终身", "一生", "毕生", "平生", "此生", "性命"],
            "婚姻": ["婚", "嫁", "娶", "妻", "夫", "姻缘", "配偶"],
            "官讼": ["官", "讼", "告", "判", "罪", "刑", "牢", "官司"],
            "疾病": ["病", "疾", "医", "药", "身体", "恙", "恙"],
            "出行": ["行", "出", "往", "去", "动", "旅", "往", "程"],
            "求财": ["财", "利", "富", "钱", "银", "生意", "盈利"],
            "stock": ["股票", "股市", "基金", "投资", "A股", "大盘", "涨停", "跌停", "K线", "主力", "庄家", "散户", "券商", "牛市", "熊市", "仓位"],
            "行人": ["人", "来", "归", "回", "至", "到", "人归"],
            "失物": ["失", "丢", "寻", "找", "物", "遗", "失物"],
            "田宅": ["宅", "屋", "居", "住", "田", "庄", "家", "居所"],
            "考试": ["考", "试", "学", "考", "中", "第", "科", "科举"]
        }

        for category, kws in keywords_map.items():
            for kw in kws:
                if kw in raw_text:
                    return category

        return "其他"

    def _extract_leixiang_features(self, prediction: str) -> Dict:
        """提取类象特征"""
        features = {
            "涉及地支": [],
            "涉及神将": [],
            "吉凶判断": "未明",
            "关键类象": []
        }

        dizhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        shenjiang_list = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙', '天空', '白虎', '太常', '玄武', '太阴', '天后']

        if prediction:
            for dz in dizhi_list:
                if dz in prediction:
                    features["涉及地支"].append(dz)

            for sj in shenjiang_list:
                if sj in prediction:
                    features["涉及神将"].append(sj)

            if any(kw in prediction for kw in ['吉', '利', '好', '顺', '成', '得', '喜']):
                features["吉凶判断"] = "吉"
            elif any(kw in prediction for kw in ['凶', '危', '败', '破', '损', '失', '死', '丧']):
                features["吉凶判断"] = "凶"
            else:
                features["吉凶判断"] = "中性"

        return features

    def _categorize_by_tiandui(self, results: List[Dict]) -> Dict:
        """按天三大抵分类"""
        tiandui_map = defaultdict(list)

        for result in results:
            prediction = result.get('预测事情', '')
            tiandui = self._detect_tiandui(prediction)
            tiandui_map[tiandui].append({
                "id": result.get('id', ''),
                "占事": self._extract_zhanshi_from_id(result.get('id', '')),
                "实际事情": result.get('实际事情', ''),
                "预测事情": result.get('预测事情', '')
            })

        return dict(tiandui_map)

    def _detect_tiandui(self, prediction: str) -> str:
        """检测课体"""
        if not prediction:
            return "未确定"

        tiandui_keywords = {
            "元首课": ["一上克下", "尊卑有序", "事顺利成"],
            "重审课": ["一下克上", "审而后用", "谨慎行事"],
            "知一课": ["比用", "相近", "相同"],
            "涉害课": ["涉害", "深浅", "先后"],
            "遥克课": ["遥克", "日遥", "克应"],
            "昴星课": ["昴星", "四课无克", "俯仰"],
            "别责课": ["别责", "四课不全", "补救"],
            "八专课": ["八专", "干支同位", "逆顺"],
            "伏吟课": ["伏吟", "星月将", "不动"],
            "反吟课": ["反吟", "冲", "变动"],
            "三光课": ["三光", "日辰用神", "旺相"],
            "三阳课": ["三阳", "天乙顺", "阳气"],
            "三奇课": ["三奇", "甲戊庚", "奇仪"],
            "润下课": ["润下", "水局", "流动"],
            "稼穑课": ["稼穑", "土局", "稳重"],
            "从革课": ["从革", "金局", "变革"],
            "曲直课": ["曲直", "木局", "生发"],
            "炎上课": ["炎上", "火局", "向上"]
        }

        for tiandui, keywords in tiandui_keywords.items():
            for kw in keywords:
                if kw in prediction:
                    return tiandui

        return "其他课体"

    def _extract_keyword_patterns(self, results: List[Dict]) -> Dict:
        """提取关键词规律"""
        patterns = {
            "吉判断": [],
            "凶判断": [],
            "事情类型": []
        }

        for result in results:
            prediction = result.get('预测事情', '')
            actual = result.get('实际事情', '')

            if not prediction or not actual:
                continue

            if any(kw in actual for kw in ['吉', '利', '好', '顺']):
                patterns["吉判断"].append({
                    "预测": prediction[:100],
                    "实际": actual[:100]
                })

            if any(kw in actual for kw in ['凶', '危', '败', '破']):
                patterns["凶判断"].append({
                    "预测": prediction[:100],
                    "实际": actual[:100]
                })

        return patterns

    def _extract_leixiang_rules(self, results: List[Dict]) -> Dict:
        """提取类象规则"""
        rules = {}

        for result in results:
            prediction = result.get('预测事情', '')
            if not prediction or '三传' not in prediction:
                continue

            rules[result.get('id', '')] = {
                "原文": result.get('原文', '')[:100],
                "预测": prediction
            }

        return rules

    def query_by_zhanshi(self, zhanshi: str) -> List[Dict]:
        """根据占事类型查询案例"""
        categories = self.knowledge_base.get("占事分类", {})
        return categories.get(zhanshi, [])

    def query_similar_cases(self, raw_text: str = None, zhanshi: str = None, limit: int = 10) -> List[Dict]:
        """查询类似案例 - 使用向量语义搜索为主，关键词搜索为备选

        Args:
            raw_text: 查询原文（用于语义搜索）
            zhanshi: 占事类型过滤
            limit: 返回数量
        """
        if raw_text and self.vector_kb.documents:
            vector_results = self.vector_kb.query(
                query_text=raw_text,
                top_k=limit,
                zhanshi_filter=zhanshi
            )
            if vector_results:
                return [r["case"] for r in vector_results]

        if zhanshi:
            cases = self.query_by_zhanshi(zhanshi)
        elif raw_text:
            guessed_type = self._guess_zhanshi(raw_text)
            if guessed_type != "未知":
                cases = self.query_by_zhanshi(guessed_type)
            else:
                all_cases = []
                for cat_cases in self.knowledge_base.get("占事分类", {}).values():
                    all_cases.extend(cat_cases)
                cases = all_cases
        else:
            all_cases = []
            for cat_cases in self.knowledge_base.get("占事分类", {}).values():
                all_cases.extend(cat_cases)
            cases = all_cases

        return cases[:limit]

    def get_judgment_rules(self, zhanshi: str) -> Dict:
        """获取判断规则"""
        categories = self.knowledge_base.get("占事分类", {})
        if zhanshi not in categories:
            return {}

        cases = categories[zhanshi]
        rules = {
            "典型特征": [],
            "常见类象": defaultdict(int),
            "吉凶规律": {"吉": 0, "凶": 0, "中性": 0}
        }

        for case in cases:
            features = case.get("类象特征", {})
            if features.get("吉凶判断"):
                rules["吉凶规律"][features["吉凶判断"]] += 1

            for dz in features.get("涉及地支", []):
                rules["常见类象"][dz] += 1

            for sj in features.get("涉及神将", []):
                rules["常见类象"][sj] += 1

        rules["常见类象"] = dict(rules["常见类象"])
        return rules

    def add_new_case(self, case_data: Dict):
        """追加新案例"""
        new_case = {
            "id": case_data.get('id', f"NEW-{self._get_timestamp()}"),
            "占事": case_data.get('占事', '未知'),
            "原文": case_data.get('原文', ''),
            "实际事情": case_data.get('实际事情', ''),
            "预测事情": case_data.get('预测事情', ''),
            "训练轮次": "新增"
        }

        if os.path.exists(self.training_results_file):
            with open(self.training_results_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        else:
            existing = []

        existing.append(new_case)

        with open(self.training_results_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        self.knowledge_base = self._build_knowledge_base()
        self._rebuild_vector_index()

    def get_all_categories(self) -> List[str]:
        """获取所有占事分类"""
        return list(self.knowledge_base.get("占事分类", {}).keys())

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        meta = self.knowledge_base.get("元数据", {})
        categories = self.knowledge_base.get("占事分类", {})

        stats = {
            "总案例数": meta.get("总案例数", 0),
            "训练轮次": meta.get("训练轮次", 0),
            "占事类型数": len(categories),
            "各类型案例数": {},
            "向量检索": self.vector_kb.get_statistics()
        }

        for cat, cases in categories.items():
            stats["各类型案例数"][cat] = len(cases)

        return stats


def save_training_knowledge():
    """保存知识库到文件"""
    knowledge = LiuRenTrainingKnowledge()
    output_file = "训练结果知识库.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge.knowledge_base, f, ensure_ascii=False, indent=2)

    print(f"知识库已保存到: {output_file}")
    return knowledge


if __name__ == "__main__":
    kb = save_training_knowledge()
    stats = kb.get_statistics()
    print("\n=== 知识库统计 ===")
    print(f"总案例数: {stats['总案例数']}")
    print(f"训练轮次: {stats['训练轮次']}")
    print(f"占事类型数: {stats['占事类型数']}")
    print("\n各类型案例数:")
    for cat, count in sorted(stats["各类型案例数"].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
