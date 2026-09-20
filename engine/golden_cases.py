#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
黄金案例验证集 (Golden Cases)
用于评估不同层级 AI 推理（规则/模板/AI）的质量

核心功能：
1. 存储经过验证的典型案例（含排盘、课体、吉凶、推理链）
2. 作为 "真相" (Ground Truth) 对比不同引擎的输出
3. 确保降级/蒸馏后的推理质量不下降
"""

import json
import os
from typing import Dict, List, Any

class GoldenCaseSet:
    """黄金案例集合"""
    
    def __init__(self):
        self.golden_file = self._get_golden_file()
        self.golden_cases = self._load_golden_cases()
        
    def _get_golden_file(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "data", "golden_cases.json")
    
    def _load_golden_cases(self) -> List[Dict]:
        """加载黄金案例"""
        if os.path.exists(self.golden_file):
            try:
                with open(self.golden_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载黄金案例失败: {e}")
        return self._create_default_golden_cases()
    
    def _create_default_golden_cases(self) -> List[Dict]:
        """创建默认黄金案例（从现有数据中提取典型）"""
        cases = []
        
        # 1. 尝试从股票训练案例中提取
        stock_cases_file = os.path.join(
            os.path.dirname(self.golden_file), "stock_training_cases.json"
        )
        if os.path.exists(stock_cases_file):
            try:
                with open(stock_cases_file, 'r', encoding='utf-8') as f:
                    stock_cases = json.load(f)
                # 筛选高置信度、已验证的案例
                for case in stock_cases:
                    if case.get('is_correct') and case.get('confidence') == 'high':
                        golden_case = self._convert_to_golden_format(case)
                        if golden_case:
                            cases.append(golden_case)
            except Exception as e:
                print(f"从股票案例提取失败: {e}")
        
        # 2. 添加一些经典案例作为补充
        classic_cases = self._get_classic_cases()
        cases.extend(classic_cases)
        
        # 保存并返回
        if cases:
            self._save_golden_cases(cases)
            
        return cases
    
    def _convert_to_golden_format(self, case: Dict) -> Dict:
        """将训练案例转换为黄金格式"""
        return {
            "id": case.get('id', ''),
            "title": case.get('title', ''),
            "zhanshi": "求财" if case.get('stock_code') else '其他',
            "source": case.get('source', ''),
            "ground_truth": {
                "keti": case.get('keti', ''),
                "jixiong": "吉" if case.get('trend_prediction') in ['涨', '先涨后跌'] else "凶",
                "sanchuan": case.get('sanchuan', {}),
                "key_signals": [
                    case.get('liuqin_analysis', ''),
                    case.get('tianjiang_analysis', '')
                ]
            },
            "verification": {
                "is_correct": case.get('is_correct', False),
                "actual_result": case.get('actual_result', ''),
                "confidence": case.get('confidence', '')
            }
        }
    
    def _get_classic_cases(self) -> List[Dict]:
        """获取经典案例（人工精选）"""
        return [
            {
                "id": "GOLDEN-001",
                "title": "求财类-白虎发用主暴跌",
                "zhanshi": "求财",
                "source": "训练案例 CASE-STOCK-002",
                "ground_truth": {
                    "keti": "弹射",
                    "jixiong": "凶",
                    "sanchuan": {"first": "白虎+金", "second": "玄武+水", "third": "勾陈+土"},
                    "key_signals": ["白虎临官鬼主暴跌", "玄武主暗流", "勾陈主筑底"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "赤峰黄金从42元跌至35元",
                    "confidence": "high"
                }
            },
            {
                "id": "GOLDEN-002",
                "title": "求财类-子孙旺相主发财",
                "zhanshi": "求财",
                "source": "刘文元案例",
                "ground_truth": {
                    "keti": "",
                    "jixiong": "吉",
                    "sanchuan": {"first": "巳（子孙+白虎）"},
                    "key_signals": ["巳火为子孙财源", "旺相生财", "项目与火电金属相关"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "投资门房电气焊，半年内发大财",
                    "confidence": "high"
                }
            },
            {
                "id": "GOLDEN-003",
                "title": "疾病类-朱雀临身主发热",
                "zhanshi": "疾病",
                "source": "经典六壬案例",
                "ground_truth": {
                    "keti": "涉害",
                    "jixiong": "凶",
                    "sanchuan": {"first": "朱雀+巳", "second": "太常+未"},
                    "key_signals": ["朱雀主口舌发热", "巳火旺相", "需防炎症"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "高热不退，后确诊肺炎",
                    "confidence": "high"
                }
            },
            {
                "id": "GOLDEN-004",
                "title": "婚姻类-六合临妻主良缘",
                "zhanshi": "婚姻",
                "source": "经典六壬案例",
                "ground_truth": {
                    "keti": "六合",
                    "jixiong": "吉",
                    "sanchuan": {"first": "六合+卯", "second": "青龙+寅"},
                    "key_signals": ["六合主婚姻和合", "青龙主喜庆", "卯木为桃花"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "当年结婚，婚姻美满",
                    "confidence": "high"
                }
            },
            {
                "id": "GOLDEN-005",
                "title": "出行类-驿马临用主速行",
                "zhanshi": "出行",
                "source": "经典六壬案例",
                "ground_truth": {
                    "keti": "元首",
                    "jixiong": "吉",
                    "sanchuan": {"first": "驿马+申", "second": "青龙+寅"},
                    "key_signals": ["驿马主动", "申为道路", "出行顺利"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "如期出发，平安到达",
                    "confidence": "high"
                }
            },
            {
                "id": "GOLDEN-006",
                "title": "官讼类-白虎临官主胜诉",
                "zhanshi": "官讼",
                "source": "经典六壬案例",
                "ground_truth": {
                    "keti": "重审",
                    "jixiong": "吉",
                    "sanchuan": {"first": "白虎+申", "second": "贵人+丑"},
                    "key_signals": ["白虎主武力", "贵人主帮助", "胜诉有望"]
                },
                "verification": {
                    "is_correct": True,
                    "actual_result": "最终胜诉",
                    "confidence": "high"
                }
            }
        ]
    
    def _save_golden_cases(self, cases: List[Dict]):
        """保存黄金案例"""
        try:
            os.makedirs(os.path.dirname(self.golden_file), exist_ok=True)
            with open(self.golden_file, 'w', encoding='utf-8') as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
            print(f"✅ 黄金案例已保存: {self.golden_file} ({len(cases)} 个案例)")
        except Exception as e:
            print(f"❌ 保存黄金案例失败: {e}")
    
    def get_all_cases(self) -> List[Dict]:
        """获取所有黄金案例"""
        return self.golden_cases
    
    def get_case_by_id(self, case_id: str) -> Dict:
        """按ID获取案例"""
        for case in self.golden_cases:
            if case.get('id') == case_id:
                return case
        return None
    
    def get_cases_by_zhanshi(self, zhanshi: str) -> List[Dict]:
        """按占事类型获取案例"""
        return [c for c in self.golden_cases if c.get('zhanshi') == zhanshi]
    
    def validate_result(self, case_id: str, predicted_result: Dict) -> Dict:
        """
        验证预测结果与黄金案例的符合度
        
        参数：
            case_id: 黄金案例ID
            predicted_result: 预测结果 {keti, jixiong, analysis}
            
        返回：
            验证结果 {score, matches, details}
        """
        golden_case = self.get_case_by_id(case_id)
        if not golden_case:
            return {"error": f"案例 {case_id} 不存在"}
        
        ground_truth = golden_case['ground_truth']
        matches = {
            "keti_match": predicted_result.get('keti') == ground_truth['keti'],
            "jixiong_match": predicted_result.get('jixiong') == ground_truth['jixiong'],
        }
        
        # 计算匹配分数
        total_checks = len(matches)
        matched_count = sum(1 for v in matches.values() if v)
        score = matched_count / total_checks if total_checks > 0 else 0
        
        return {
            "case_id": case_id,
            "score": score,
            "matches": matches,
            "predicted": predicted_result,
            "ground_truth": ground_truth
        }

# 单例模式
_instance = None

def get_golden_cases() -> GoldenCaseSet:
    """获取黄金案例单例"""
    global _instance
    if _instance is None:
        _instance = GoldenCaseSet()
    return _instance

# 测试
if __name__ == "__main__":
    golden = get_golden_cases()
    print(f"\n📊 黄金案例集状态：")
    print(f"   案例总数: {len(golden.get_all_cases())}")
    
    cases_by_type = {}
    for case in golden.get_all_cases():
        zhanshi = case.get('zhanshi', '未知')
        cases_by_type[zhanshi] = cases_by_type.get(zhanshi, 0) + 1
    
    print(f"\n   按占事类型分布:")
    for zhanshi, count in sorted(cases_by_type.items(), key=lambda x: -x[1]):
        print(f"     - {zhanshi}: {count} 个")
    
    # 测试验证
    test_case = golden.get_all_cases()[0]
    result = golden.validate_result(test_case['id'], {
        'keti': test_case['ground_truth']['keti'],
        'jixiong': test_case['ground_truth']['jixiong']
    })
    print(f"\n✅ 验证测试: {test_case['title']}")
    print(f"   匹配分数: {result['score']:.0%}")
