#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能分层决策引擎 (Smart Judge) — 调度中心

定位：
- 第1层（规则）→ 第2层（模板/便宜AI）→ 第3层（高级AI）的调度器
- 根据案例复杂度动态选择最优引擎
- 在保证质量的前提下，最小化成本

决策逻辑：
1. 如果规则引擎能高置信度解决 → 直接返回（0成本）
2. 如果是常见占事类型 → 用模板引擎 + glm-4-flash（低成本）
3. 如果是复杂/边界案例 → 升级到 glm-5.3-flash（高成本）
4. 所有结果经过质量验证
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from enum import Enum

# 确保可以导入项目模块
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class EngineLevel(Enum):
    """引擎层级"""
    RULE = 1        # 规则引擎层
    TEMPLATE = 2    # 模板引擎层 (glm-4-flash)
    AI = 3          # AI引擎层 (glm-5.3-flash)
    TRAINING = 4    # 训练/蒸馏层 (glm-5.3-pro)


class SmartJudge:
    """智能分层决策引擎"""
    
    # 规则引擎高置信度阈值
    RULE_HIGH_CONFIDENCE = 0.85
    
    # 模板引擎低置信度阈值（低于此值升级到AI）
    TEMPLATE_LOW_CONFIDENCE = 0.4
    
    # 模板引擎适用的占事类型
    TEMPLATE_SUITABLE_ZANSHI = {
        "求财", "婚姻", "疾病", "出行", "官讼", "功名", 
        "家宅", "胎产", "贼盗", "失物", "交易", "经营", 
        "开业", "安葬", "流年", "终身", "杂占", "其他",
        "股票预测", "大盘预测", "个股预测"  # 股票预测专用类型
    }
    
    # 股票预测专用类型（会触发股票规则引擎）
    STOCK_ZANSHI_TYPES = {"股票预测", "大盘预测", "个股预测", "求财"}
    
    # 【P8 2026-09-06】特殊课型确定性规则：golden 24 条验证过的"发用天将"模式，
    #   由规则层直接判定（0成本），避免模板层(glm-4-flash)固有心智误判。
    #   发用天将数组按三传顺序，首元素=初传（发用）所乘天将。
    #   原则：只收录 golden 已验证、判据无歧义的模式（防误伤）。
    #   (占事, 发用天将, 课体包含词(可空), 吉凶, 置信, 说明)
    SPECIAL_RULE = [
        ("官讼", "白虎", "", "吉", 0.90, "白虎临官主胜诉（官鬼得势）"),
        ("疾病", "青龙", "", "吉", 0.90, "青龙临身主生机康复"),
        ("疾病", "天后", "", "吉", 0.85, "天后主身心恢复"),
        ("疾病", "白虎", "", "凶", 0.90, "白虎临身主大病/肺疾"),
        ("疾病", "朱雀", "", "凶", 0.80, "朱雀主发热口舌炎症"),
        ("求财", "玄武", "", "凶", 0.85, "玄武主出货/盗贼破财"),
        ("求财", "青龙", "", "吉", 0.85, "青龙临身主得财/大涨"),
        # 勾陈=横盘仅限伏吟课成立（GOLDEN-011 伏吟+勾陈=平）；
        # 反例 CASE-STOCK-002/GOLDEN-001 弹射格勾陈发用=暴跌后筑底凶 → 必须课体限定
        ("求财", "勾陈", "伏吟", "平", 0.80, "伏吟课+勾陈主横盘停滞/等待突破"),
        ("婚姻", "六合", "", "吉", 0.90, "六合临身主良缘"),
        ("婚姻", "天后", "", "吉", 0.90, "天后临身主恩爱"),
        ("婚姻", "螣蛇", "", "凶", 0.85, "螣蛇主口舌反复"),
        ("出行", "白虎", "", "凶", 0.85, "白虎主路有阻/意外"),
        ("出行", "贵人", "", "吉", 0.90, "贵人临身主顺利"),
        ("功名", "青龙", "", "吉", 0.90, "青龙临身主高中/功成"),
        ("功名", "玄武", "", "凶", 0.85, "玄武主落榜/失意"),
        ("家宅", "六合", "", "吉", 0.90, "六合主家庭和睦"),
        # 【2026-09-06 P10 全量回测下沉】Corpus_A(壬占汇选) 实测：
        #   家宅+勾陈 3/3 真值凶（模板层被误判吉3条）；勾陈主田宅争斗/迁延扦格，家宅见之不安——干净可下沉
        ("家宅", "勾陈", "", "凶", 0.85, "勾陈主田宅争斗/迟滞，家宅见之不安"),
        #   家宅+太常 4/4 真值凶（模板层被误判吉2条）；太常为孝帛之神，主丧服忧戚，家宅见之不利——干净可下沉
        ("家宅", "太常", "", "凶", 0.80, "太常为孝帛之神主丧服忧戚，家宅见之不利"),
    ]
    # 特殊课型规则触发阈值（低于 RULE_HIGH_CONFIDENCE 但高于模板层）
    SPECIAL_HIGH_CONFIDENCE = 0.75
    
    def __init__(self):
        self._init_engines()
        self.decision_log = []  # 决策日志
        self.distill_engine = None  # 蒸馏引擎
        self.template_updater = None  # 模板更新器
        self._init_distillation()
        
    def _init_engines(self):
        """初始化各层引擎"""
        # 第1层：Phase C v4 数据驱动混合规则引擎（首选，准确率 85.1%）
        self.hybrid_rule_engine = None
        self.hybrid_rule_engine_available = False
        
        # 第1.1层：旧规则引擎（fallback）
        self.rule_engine = None
        self.rule_engine_available = False
        
        # 第1.5层：股票专用规则引擎（用于股票预测场景）
        self.stock_rule_engine = None
        self.stock_rule_engine_available = False
        self.realtime_engine = None
        try:
            from engine.stock_rule_engine import StockRuleEngine
            # 尝试导入实时行情引擎
            try:
                from engine.realtime_market_data import create_realtime_engine
                self.realtime_engine = create_realtime_engine()
                print("📡 实时行情引擎已创建")
            except Exception:
                pass
            
            self.stock_rule_engine = StockRuleEngine(realtime_engine=self.realtime_engine)
            self.stock_rule_engine_available = True
            print("📈 股票规则引擎已初始化")
        except Exception as e:
            print(f"⚠️ 股票规则引擎初始化失败: {e}")
        
        # 第2层：模板引擎
        try:
            from engine.template_engine import get_template_engine
            self.template_engine = get_template_engine()
            self.template_engine_available = True
        except Exception as e:
            print(f"⚠️ 模板引擎初始化失败: {e}")
            self.template_engine = None
            self.template_engine_available = False
        
        # 第3层：AI引擎（延迟导入，只在需要时加载）
        self.ai_engine = None
        self.ai_engine_available = False
    
    def _init_distillation(self):
        """初始化蒸馏引擎"""
        try:
            from engine.distillation_engine import DistillationEngine, TemplateUpdater
            self.distill_engine = DistillationEngine()
            self.template_updater = TemplateUpdater(self.distill_engine)
            print("🧠 蒸馏引擎已初始化")
        except Exception as e:
            print(f"⚠️ 蒸馏引擎初始化失败: {e}")
            self.distill_engine = None
            self.template_updater = None
        
    def _ensure_rule_engine(self):
        """确保规则引擎已加载（优先 Phase C v4 混合引擎）"""
        # 优先尝试 Phase C v4 数据驱动混合规则引擎
        if self.hybrid_rule_engine is None:
            try:
                from engine.hybrid_rule_engine import HybridRuleEngine
                self.hybrid_rule_engine = HybridRuleEngine.get_instance()
                self.hybrid_rule_engine_available = self.hybrid_rule_engine.is_available()
                if self.hybrid_rule_engine_available:
                    info = self.hybrid_rule_engine.get_info()
                    print(f"🧠 Phase C v4 混合规则引擎已加载 (权重{info['global_keti_count']+info['global_special_count']}项, 救应{info['jiuying_rules_count']}条, 准确率{info['phase_c_v4_accuracy']:.1f}%)")
            except Exception as e:
                print(f"⚠️ Phase C v4 混合规则引擎加载失败: {e}")
                self.hybrid_rule_engine_available = False
        
        if self.hybrid_rule_engine_available:
            return True
        
        # Fallback: 旧 generate_zhanshi_duanyu 规则引擎
        if self.rule_engine is None:
            try:
                from engine.zhanshi_duanyu_patched11 import generate_zhanshi_duanyu
                self.rule_engine = generate_zhanshi_duanyu
                self.rule_engine_available = True
                print("📜 旧规则引擎已加载 (fallback)")
            except Exception as e:
                print(f"⚠️ 旧规则引擎加载失败: {e}")
                self.rule_engine_available = False
        
        return self.rule_engine_available or self.hybrid_rule_engine_available
    
    def _ensure_ai_engine(self):
        """确保AI引擎已加载

        【2026-09-06 BUG-FIX】必须 use_smart_engine=False：
        LiuRenAIJudge 默认 use_smart_engine=True 会在内部 _init_smart_engine 再建一个
        SmartJudge；当模板层置信不足时新 SmartJudge 又走到 AI 层 → 再建 LiuRenAIJudge
        → 无限递归（maximum recursion depth exceeded）。
        此处 AI 层应直接调用原始 glm-5.3-flash 引擎，不再回环分层调度。
        """
        if self.ai_engine is None:
            try:
                from engine.liuren_ai_judge import LiuRenAIJudge
                self.ai_engine = LiuRenAIJudge(use_smart_engine=False)
                self.ai_engine_available = True
            except Exception as e:
                print(f"⚠️ AI引擎加载失败: {e}")
                self.ai_engine_available = False
        return self.ai_engine_available
    
    def judge(self, paipan_result: Dict, zhanshi: str = None, 
              stock_code: str = None, force_level: EngineLevel = None) -> Dict:
        """
        执行分层决策
        
        参数：
            paipan_result: 排盘结果
            zhanshi: 占事类型
            stock_code: 股票代码（如需）
            force_level: 强制使用某层引擎（用于测试）
            
        返回：
            {
                "success": bool,
                "result": Dict,
                "engine_used": EngineLevel,
                "confidence": float,
                "cost_estimate": str,
                "decision_path": List[Dict],
                "error": str
            }
        """
        decision_path = []
        
        # 如果指定了强制层级
        if force_level:
            return self._execute_at_level(force_level, paipan_result, zhanshi, 
                                          stock_code, decision_path)
        
        # 第0层：股票预测专用路径（优先使用股票规则引擎）
        if zhanshi and zhanshi in self.STOCK_ZANSHI_TYPES:
            stock_result = self._try_stock_engine(paipan_result, zhanshi, 
                                                   stock_code, decision_path)
            # 仅当股票引擎给出真实信号（置信度>0.5 且分数偏离中性基线 0.5）才短路；
            # 否则（课体/三传/天将/六亲全未收录的中性输出）继续走混合 RULE 判定，
            # 避免 0.5 基线 stock 结果抢走求财等占事的 RULE 判定权
            stock_score = stock_result.get('score', 0.5) if stock_result else None
            if (stock_result 
                    and stock_result.get('confidence', 0) > 0.5
                    and stock_score is not None and abs(stock_score - 0.5) > 0.01):
                return self._format_response(stock_result, EngineLevel.RULE, 
                                            decision_path)
        
        # 第1层：尝试规则引擎
        rule_result = self._try_rule_engine(paipan_result, zhanshi, decision_path)
        if rule_result and rule_result.get('confidence', 0) >= self.RULE_HIGH_CONFIDENCE:
            return self._format_response(rule_result, EngineLevel.RULE, decision_path)
        
        # 第1.5层：特殊课型确定性规则（P8 2026-09-06）
        # golden 验证过的"发用天将"模式（官讼白虎胜诉/疾病青龙康复/求财玄武凶等），
        # 规则层直接判定，规避模板层 glm-4-flash 固有心智误判
        special_result = self._try_special_rule_engine(paipan_result, zhanshi, decision_path)
        if special_result and special_result.get('confidence', 0) >= self.SPECIAL_HIGH_CONFIDENCE:
            return self._format_response(special_result, EngineLevel.RULE, decision_path)
        
        # 第2层：尝试模板引擎
        if zhanshi and zhanshi in self.TEMPLATE_SUITABLE_ZANSHI:
            template_result = self._try_template_engine(paipan_result, zhanshi,
                                                          decision_path)
            if template_result and template_result.get('confidence', 0) >= self.TEMPLATE_LOW_CONFIDENCE:
                # 模板引擎返回值来自 result['result']（含 overall_jixiong 字段）+ confidence
                tpl_jx = template_result.get('overall_jixiong', '') or template_result.get('jixiong', '')
                # 【2026-09-06 第2项】模板判"吉"升级 AI 复核（乐观偏置拦截）：
                #   全量回测 Corpus_A 实测 模板判吉准确率仅 38%（72条中45条真凶被误判吉），
                #   而判凶准确率 78% 可信；glm-4-flash 有"发用吉将即判吉"的乐观心智，
                #   无法用课体/天将特征切分（真凶/真吉特征分布重叠），只能升级 AI 层复核
                if tpl_jx and '吉' in str(tpl_jx) and '凶' not in str(tpl_jx):
                    decision_path.append({
                        "level": EngineLevel.TEMPLATE.name,
                        "result": f"模板判吉 {tpl_jx}（38%置信度），乐观偏置风险，升级AI层复核"
                    })
                    ai_result = self._try_ai_engine(paipan_result, zhanshi, stock_code, decision_path)
                    if ai_result:
                        return self._format_response(ai_result, EngineLevel.AI, decision_path)
                    # AI 复核失败 → 回退模板原判（保守保留模板结论）
                    decision_path.append({
                        "level": EngineLevel.AI.name,
                        "result": "AI复核不可用，回退模板原判"
                    })
                return self._format_response(template_result, EngineLevel.TEMPLATE,
                                            decision_path)
        
        # 第3层：升级到AI引擎
        ai_result = self._try_ai_engine(paipan_result, zhanshi, stock_code, decision_path)
        if ai_result:
            return self._format_response(ai_result, EngineLevel.AI, decision_path)
        
        # 所有引擎都失败
        return self._format_response(
            {"error": "所有引擎均无法处理此案例"}, 
            None, 
            decision_path,
            success=False
        )
    
    def _try_stock_engine(self, paipan_result: Dict, zhanshi: str,
                          stock_code: str, decision_path: list) -> Optional[Dict]:
        """尝试股票专用规则引擎"""
        decision_path.append({
            "level": "STOCK_RULE",
            "action": "尝试股票专用规则引擎"
        })
        
        if not self.stock_rule_engine_available:
            decision_path.append({
                "level": "STOCK_RULE",
                "result": "股票规则引擎不可用，跳过"
            })
            return None
        
        # 提取排盘数据
        paipan_data = self._extract_paipan_data_for_stock(paipan_result)
        
        # 计算股票五行（用于实时行情调整）
        stock_wuxing = ""
        if stock_code:
            paipan_data['stock_code'] = stock_code
            try:
                from engine.stock_templates import (
                    get_code_dizhi, infer_industry_wuxing, 
                    get_stock_leixiang
                )
                code_info = get_code_dizhi(stock_code)
                paipan_data.update(code_info)
                
                # 获取股票五行
                stock_info = get_stock_leixiang(stock_code)
                if stock_info:
                    stock_wuxing = stock_info.get('wuxing', '')
                else:
                    stock_wuxing = infer_industry_wuxing('', '')
                    
            except Exception:
                pass
        
        # 初始化实时行情引擎（如果可用且未初始化）
        if self.realtime_engine and hasattr(self.realtime_engine, '_initialized'):
            if not self.realtime_engine._initialized:
                try:
                    self.realtime_engine.initialize()
                except Exception:
                    pass
        
        decision_path.append({
            "level": "STOCK_RULE",
            "action": f"执行股票规则引擎分析 (占事: {zhanshi}, 五行: {stock_wuxing})"
        })
        
        try:
            result = self.stock_rule_engine.evaluate(paipan_data, stock_wuxing=stock_wuxing)
            
            if result:
                confidence = result.get('confidence', 0)
                
                decision_path.append({
                    "level": "STOCK_RULE",
                    "result": f"股票规则引擎完成，置信度: {confidence:.0%}，趋势: {result.get('trend', '未知')}"
                })
                
                # 添加股票专属字段
                result['engine_type'] = 'stock_rule_engine'
                result['stock_specific'] = True
                
                return result
                
        except Exception as e:
            decision_path.append({
                "level": "STOCK_RULE",
                "error": str(e)
            })
            print(f"⚠️ 股票规则引擎执行失败: {e}")
        
        return None
    
    def _extract_paipan_data_for_stock(self, paipan_result: Dict) -> Dict:
        """从排盘结果中提取股票引擎需要的数据"""
        # 兼容多种格式
        keti = (paipan_result.get('课体', '') or 
                paipan_result.get('keti', ''))
        # 兼容 list 格式（壬占汇选 {keti:[...]}）：转中文逗号连接字符串，
        # 避免 KETI_STOCK_RULES.get(list) 抛 unhashable type: 'list'
        if isinstance(keti, list):
            keti = '，'.join(str(k).strip() for k in keti if str(k).strip())
        elif keti is None:
            keti = ''
        tianjiang = (paipan_result.get('天将', '') or
                     paipan_result.get('tianjiang', ''))
        sanchuan = (paipan_result.get('三传', {}) or
                    paipan_result.get('sanchuan', {}))
        # 天将：兼容 list（古例 ['六合','朱雀','螣蛇']）→ 逗号连接字符串，
        # 避免 stock_rule_engine._evaluate_tianjiang 调用 .split() 抛 'list' object has no attribute 'split'
        if isinstance(tianjiang, (list, tuple)):
            tianjiang = ','.join(str(t).strip() for t in tianjiang if str(t).strip())
        elif isinstance(tianjiang, dict):
            tianjiang = ','.join(str(v).strip() for v in tianjiang.values() if str(v).strip())
        elif tianjiang is None:
            tianjiang = ''
        # 三传：list（古例 ['申','午']）→ dict {first/second/third}
        if isinstance(sanchuan, (list, tuple)):
            _sc_list = [str(s).strip() for s in sanchuan if str(s).strip()]
            sanchuan = {
                'first': _sc_list[0] if len(_sc_list) > 0 else '',
                'second': _sc_list[1] if len(_sc_list) > 1 else '',
                'third': _sc_list[2] if len(_sc_list) > 2 else '',
            }
        elif sanchuan is None:
            sanchuan = {}
        wuxing = (paipan_result.get('五行分析', '') or 
                  paipan_result.get('wuxing_analysis', '') or '')
        day_gan = (paipan_result.get('日干', '') or 
                   paipan_result.get('day_gan', ''))
        shen_wangshuai = (paipan_result.get('身强身弱', '') or 
                          paipan_result.get('shen_wangshuai', ''))
        liuqin = (paipan_result.get('六亲分析', '') or 
                  paipan_result.get('liuqin', '') or '')
        sike = (paipan_result.get('四课加临', '') or 
                paipan_result.get('sike', '') or '')
        
        return {
            'keti': keti,
            'sanchuan': sanchuan,
            'tianjiang': tianjiang,
            'wuxing': wuxing,
            'day_gan': day_gan,
            'shen_wangshuai': shen_wangshuai,
            'liuqin': liuqin,
            'sike': sike,
        }
    
    def _try_rule_engine(self, paipan_result: Dict, zhanshi: str, 
                         decision_path: list) -> Optional[Dict]:
        """尝试规则引擎（优先 Phase C v4 混合引擎）"""
        decision_path.append({
            "level": EngineLevel.RULE.name,
            "action": "尝试加载规则引擎"
        })
        
        if not self._ensure_rule_engine():
            decision_path.append({
                "level": EngineLevel.RULE.name,
                "result": "规则引擎不可用，跳过"
            })
            return None
        
        # 优先用 Phase C v4 混合引擎
        if self.hybrid_rule_engine_available:
            try:
                decision_path.append({
                    "level": EngineLevel.RULE.name,
                    "action": "执行 Phase C v4 数据驱动规则引擎"
                })
                
                result = self.hybrid_rule_engine.judge(
                    paipan_result=paipan_result,
                    zhanshi=zhanshi
                )
                
                if result and result.get('success'):
                    # 混合引擎自带置信度，直接用
                    confidence = result.get('confidence', 0.5)
                    
                    decision_path.append({
                        "level": EngineLevel.RULE.name,
                        "result": f"Phase C v4 完成: {result.get('verdict','?')} (score={result.get('score',0):+.1f}, conf={confidence:.0%})"
                    })
                    
                    return {
                        **result,
                        "confidence": confidence
                    }
            except Exception as e:
                decision_path.append({
                    "level": EngineLevel.RULE.name,
                    "error": f"Phase C v4 异常: {str(e)}，尝试 fallback"
                })
        
        # Fallback: 旧规则引擎
        if self.rule_engine_available:
            try:
                decision_path.append({
                    "level": EngineLevel.RULE.name,
                    "action": "执行旧规则引擎"
                })
                
                result = self.rule_engine(
                    paipan_result=paipan_result,
                    zhanshi=zhanshi
                )
                
                if result and isinstance(result, dict):
                    confidence = self._calculate_rule_confidence(result)
                    
                    decision_path.append({
                        "level": EngineLevel.RULE.name,
                        "result": f"旧规则引擎完成，置信度: {confidence:.0%}"
                    })
                    
                    return {
                        **result,
                        "confidence": confidence
                    }
                    
            except Exception as e:
                decision_path.append({
                    "level": EngineLevel.RULE.name,
                    "error": str(e)
                })
        
        return None
    
    def _try_special_rule_engine(self, paipan_result: Dict, zhanshi: str,
                                 decision_path: list) -> Optional[Dict]:
        """
        特殊课型确定性规则（P8 2026-09-06）
        
        golden 24 条验证过的"发用天将"模式，由规则层直接判定（0成本）：
        - 官讼白虎=胜诉吉、疾病青龙/天后=康复吉、疾病白虎/朱雀=凶
        - 求财玄武=凶、求财青龙=吉、求财勾陈=平
        - 婚姻六合/天后=吉、螣蛇=凶；出行白虎=凶、贵人=吉
        - 功名青龙=吉、玄武=凶；家宅六合=吉
        
        规避模板层 glm-4-flash 固有心智误判（白虎=凶一刀切/疾病保守等）。
        """
        decision_path.append({
            "level": "SPECIAL_RULE",
            "action": "尝试特殊课型确定性规则"
        })
        
        if not zhanshi:
            decision_path.append({
                "level": "SPECIAL_RULE",
                "result": "无占事类型，跳过"
            })
            return None
        
        try:
            # 提取发用（初传）所乘天将
            tianjiang = (paipan_result.get('天将', '') or
                         paipan_result.get('tianjiang', ''))
            if isinstance(tianjiang, (list, tuple)):
                first_tj = str(tianjiang[0]).strip() if tianjiang else ''
            else:
                first_tj = str(tianjiang or '').strip()
            import re as _re
            m = _re.findall(r'[\u4e00-\u9fa5]{2}', first_tj)
            fn = m[0] if m else ''
            if not fn:
                decision_path.append({
                    "level": "SPECIAL_RULE",
                    "result": "无发用天将信息，跳过"
                })
                return None
            
            for zs, tj, keti_need, jx, conf, desc in self.SPECIAL_RULE:
                if zhanshi == zs and fn == tj:
                    # 课体条件（若有）：课体名须包含指定词才命中（如"求财勾陈"仅伏吟课成立）
                    if keti_need:
                        keti = (paipan_result.get('课体', '') or
                                paipan_result.get('keti', '') or '')
                        if keti_need not in str(keti):
                            continue
                    decision_path.append({
                        "level": "SPECIAL_RULE",
                        "result": f"{desc} → {jx} (conf={conf:.0%})"
                    })
                    return {
                        'jixiong': jx,
                        'verdict': desc,
                        'confidence': conf,
                        'special_rule': desc,
                        'engine_type': 'special_rule_engine'
                    }
        except Exception as e:
            decision_path.append({
                "level": "SPECIAL_RULE",
                "error": str(e)
            })
        
        return None
    
    def _calculate_rule_confidence(self, rule_result: Dict) -> float:
        """计算规则引擎的置信度"""
        # 简单逻辑：如果有详细的断语和毕法分析，置信度高
        score = 0.5  # 基础分
        
        # 如果有毕法赋命中
        if rule_result.get('bifa_rules') and len(rule_result['bifa_rules']) > 0:
            score += 0.15
        
        # 如果有类神分析
        if rule_result.get('leishen_analysis'):
            score += 0.15
        
        # 如果有具体断语
        if rule_result.get('duanyu') and len(rule_result['duanyu']) > 50:
            score += 0.1
        
        # 如果有应期判断
        if rule_result.get('yingqi'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _try_template_engine(self, paipan_result: Dict, zhanshi: str,
                             decision_path: list) -> Optional[Dict]:
        """尝试模板引擎"""
        decision_path.append({
            "level": EngineLevel.TEMPLATE.name,
            "action": "尝试加载模板引擎"
        })
        
        if not self.template_engine_available:
            decision_path.append({
                "level": EngineLevel.TEMPLATE.name,
                "result": "模板引擎不可用，跳过"
            })
            return None
        
        # 准备数据
        paipan_data = self._extract_paipan_data(paipan_result)
        rule_data = self._extract_rule_data(paipan_result)
        
        decision_path.append({
            "level": EngineLevel.TEMPLATE.name,
            "action": f"执行模板引擎分析 (占事: {zhanshi})"
        })
        
        try:
            # 【2026-09-06 P6】模板层多次采样投票（vote_times=3）：glm-4-flash 单次
            #   判定在混杂课上有 67~79% 波动，众数投票稳定化（glm-4-flash 低成本可承受）
            result = self.template_engine.reason(zhanshi, paipan_data, rule_data, vote_times=3)
            
            # 【P9 2026-09-06】矛盾课升级机制：先验同时含"发用乘凶将"（强凶）
            #   与"子孙财源/旺相得财/气旺主事有成"（强吉信号）→ 模板层白虎凶心智
            #   不可翻转，升级 AI 层(glm-5.3-flash)兜底（golden 案例 021/002
            #   均为"白虎凶 vs 原文吉"深度反转课，模板投票一致错误不触发分歧升级，需此机制）
            prior_text = result.get('rule_prior', '') or ''
            has_xiong = ('乘凶将' in prior_text) or ('见凶将' in prior_text)
            has_qiang_ji = any(k in prior_text for k in ('子孙为财源', '旺相得财', '气旺主事有成'))
            if has_xiong and has_qiang_ji:
                decision_path.append({
                    "level": EngineLevel.TEMPLATE.name,
                    "result": f"矛盾课（凶将先验+强吉信号并存）：{prior_text[:60]}…，升级AI层"
                })
                return None
            
            if result.get('success'):
                confidence = result['result'].get('confidence_score', 50) / 100.0
                
                # 【P8 2026-09-06】投票分歧升级机制：3 次采样众数仅 1 票（吉/中平/凶 全不同）
                #   → 混杂课判定不稳定，升级 AI 层(glm-5.3-flash)兜底
                votes = result.get('votes') or []
                if len(votes) >= 3:
                    from collections import Counter
                    max_cnt = max(Counter(votes).values())
                    if max_cnt <= len(votes) // 2:
                        decision_path.append({
                            "level": EngineLevel.TEMPLATE.name,
                            "result": f"模板投票分歧过大 {votes}（众数仅{max_cnt}票），升级AI层"
                        })
                        return None
                
                decision_path.append({
                    "level": EngineLevel.TEMPLATE.name,
                    "result": f"模板引擎完成，置信度: {confidence:.0%} 投票:{votes}"
                })
                
                return {
                    **result['result'],
                    'confidence': confidence,
                    'raw_response': result.get('raw_response', '')
                }
            else:
                decision_path.append({
                    "level": EngineLevel.TEMPLATE.name,
                    "result": f"模板引擎失败: {result.get('error', '未知错误')}"
                })
                
        except Exception as e:
            decision_path.append({
                "level": EngineLevel.TEMPLATE.name,
                "error": str(e)
            })
        
        return None
    
    def _try_ai_engine(self, paipan_result: Dict, zhanshi: str, 
                       stock_code: str, decision_path: list) -> Optional[Dict]:
        """尝试AI引擎"""
        decision_path.append({
            "level": EngineLevel.AI.name,
            "action": "加载AI引擎 (glm-5.3-flash)"
        })
        
        if not self._ensure_ai_engine():
            decision_path.append({
                "level": EngineLevel.AI.name,
                "result": "AI引擎不可用"
            })
            return None
        
        decision_path.append({
            "level": EngineLevel.AI.name,
            "action": f"执行AI引擎分析 (占事: {zhanshi})"
        })
        
        try:
            result = self.ai_engine.judge(paipan_result, zhanshi, stock_code)
            
            if result:
                decision_path.append({
                    "level": EngineLevel.AI.name,
                    "result": "AI引擎完成"
                })
                
                return {
                    'analysis': result,
                    'jixiong': self._extract_jixiong(result),
                    'confidence': 0.7,  # AI引擎默认置信度
                    'is_ai_result': True
                }
                
        except Exception as e:
            decision_path.append({
                "level": EngineLevel.AI.name,
                "error": str(e)
            })
        
        return None
    
    def _extract_paipan_data(self, paipan_result: Dict) -> Dict:
        """从排盘结果中提取引擎需要的数据"""
        return {
            'keti': paipan_result.get('课体', '') or paipan_result.get('keti', ''),
            'sanchuan': paipan_result.get('三传', {}) or paipan_result.get('sanchuan', {}),
            'tianjiang': paipan_result.get('天将', '') or paipan_result.get('tianjiang', ''),
            'wuxing_analysis': paipan_result.get('五行分析', '') or 
                              paipan_result.get('wuxing_analysis', '') or '未分析',
            # 【2026-09-06 三轮】补透日柱/日干/日支/三传地支/四柱，
            #   供模板引擎自算六亲与空亡先验（golden 验证证明空亡/六亲是关键信号）
            '日柱': paipan_result.get('日柱', '') or paipan_result.get('rizhu', ''),
            '日干': paipan_result.get('日干', '') or paipan_result.get('day_gan', ''),
            '日支': paipan_result.get('日支', '') or paipan_result.get('day_zhi', ''),
            '三传地支': paipan_result.get('三传地支', []) or paipan_result.get('sanchuan_zhi', []),
            '四柱': paipan_result.get('四柱', ''),
        }
    
    def _extract_rule_data(self, paipan_result: Dict) -> Dict:
        """提取规则引擎分析结果"""
        # 尝试从排盘结果中提取规则引擎的输出
        rule_result = paipan_result.get('规则引擎结果', {})
        if rule_result:
            return rule_result
        
        # 如果没有，创建空的占位
        return {
            'bifa_rules': paipan_result.get('bifa_rules', []),
            'leishen_analysis': paipan_result.get('leishen_analysis', '未分析')
        }
    
    def _extract_jixiong(self, text: str) -> str:
        """从文本中提取吉凶判断"""
        if not text:
            return '中平'
        
        # 简单的关键词匹配
        if any(word in text for word in ['大吉', '大吉', '吉兆', '吉祥']):
            return '吉'
        if any(word in text for word in ['大凶', '凶兆', '凶险', '凶多吉少']):
            return '凶'
        if any(word in text for word in ['中平', '平平', '吉凶参半']):
            return '中平'
        
        # 默认
        return '中平'
    
    def _execute_at_level(self, level: EngineLevel, paipan_result: Dict,
                          zhanshi: str, stock_code: str, 
                          decision_path: list) -> Dict:
        """在指定层级执行"""
        decision_path.append({
            "level": level.name,
            "action": f"强制执行 {level.name} 层"
        })
        
        if level == EngineLevel.RULE:
            result = self._try_rule_engine(paipan_result, zhanshi, decision_path)
            if result:
                return self._format_response(result, level, decision_path)
                
        elif level == EngineLevel.TEMPLATE:
            if zhanshi:
                result = self._try_template_engine(paipan_result, zhanshi, decision_path)
                if result:
                    return self._format_response(result, level, decision_path)
                    
        elif level == EngineLevel.AI:
            result = self._try_ai_engine(paipan_result, zhanshi, stock_code, decision_path)
            if result:
                return self._format_response(result, level, decision_path)
        
        return self._format_response(
            {"error": f"强制层级 {level.name} 执行失败"},
            level,
            decision_path,
            success=False
        )
    
    def _format_response(self, result: Dict, engine_level: EngineLevel, 
                         decision_path: list, success: bool = True) -> Dict:
        """格式化最终响应"""
        return {
            "success": success,
            "result": result,
            "engine_used": engine_level.name if engine_level else "unknown",
            "engine_id": engine_level.value if engine_level else 0,
            "confidence": result.get('confidence', 0) if success else 0,
            "cost_estimate": self._estimate_cost(engine_level),
            "decision_path": decision_path,
            "error": result.get('error') if not success else None
        }
    
    def _estimate_cost(self, engine_level: EngineLevel) -> str:
        """估算成本"""
        cost_map = {
            EngineLevel.RULE: "0元 (规则引擎，零成本)",
            EngineLevel.TEMPLATE: "约0.01元 (glm-4-flash，低成本)",
            EngineLevel.AI: "约0.1-0.3元 (glm-5.3-flash，中成本)",
            EngineLevel.TRAINING: "约0.5-1.0元 (glm-5.3-pro，高成本)"
        }
        return cost_map.get(engine_level, "未知")
    
    def get_statistics(self) -> Dict:
        """获取引擎使用统计"""
        stats = {
            "rule_engine_available": self.rule_engine_available,
            "stock_rule_engine_available": self.stock_rule_engine_available,
            "template_engine_available": self.template_engine_available,
            "ai_engine_available": self.ai_engine_available,
            "template_suitable_types": len(self.TEMPLATE_SUITABLE_ZANSHI),
            "stock_zhanshi_types": list(self.STOCK_ZANSHI_TYPES),
            "cost_estimate": {
                "rule": "¥0",
                "stock_rule": "¥0 (股票专用规则引擎)",
                "template": "¥2-5/月",
                "ai": "¥10-20/月",
                "training": "¥5-10/月"
            }
        }
        
        # 添加股票规则引擎统计
        if self.stock_rule_engine_available:
            stats['stock_rule_engine_stats'] = self.stock_rule_engine.get_stats()
        
        # 添加蒸馏统计
        if self.distill_engine:
            distill_stats = self.distill_engine.get_knowledge_stats()
            stats['distillation'] = {
                'total_distillations': distill_stats['distill_stats']['total_distillations'],
                'successful': distill_stats['distill_stats']['successful_distillations'],
                'knowledge_rules': distill_stats['knowledge_rules_count'],
                'zanshi_templates': distill_stats['zanshi_template_count']
            }
        
        return stats
    
    # ============ 蒸馏相关方法 ============
    
    def distill_case(self, case: Dict, zhanshi: str = None) -> Dict:
        """
        蒸馏单个案例
        
        参数：
        case: 案例数据
        zhanshi: 占事类型
        
        返回：蒸馏结果
        """
        if not self.distill_engine:
            return {
                'success': False,
                'error': '蒸馏引擎未初始化'
            }
        return self.distill_engine.distill_case(case, zhanshi)
    
    def batch_distill(self, cases: List[Dict], zhanshi: str = None) -> Dict:
        """
        批量蒸馏
        
        参数：
        cases: 案例列表
        zhanshi: 统一占事类型（可选）
        
        返回：批量蒸馏结果
        """
        if not self.distill_engine:
            return {
                'success': False,
                'error': '蒸馏引擎未初始化'
            }
        return self.distill_engine.batch_distill(cases, zhanshi)
    
    def trigger_distillation(self, zhanshi: str = None, 
                             case_count: int = 10) -> Dict:
        """
        触发自动蒸馏
        
        从训练案例中选取样本进行蒸馏
        
        参数：
        zhanshi: 指定占事类型（可选）
        case_count: 蒸馏案例数量
        
        返回：蒸馏结果
        """
        print(f"\n🔬 触发自动蒸馏: 占事={zhanshi or '全部'}, 数量={case_count}")
        
        # 获取案例数据（从多个数据源）
        cases = self._get_distillation_cases(zhanshi, case_count)
        
        if not cases:
            return {
                'success': False,
                'error': '没有可用的蒸馏案例'
            }
        
        print(f"   📚 选取了 {len(cases)} 个案例")
        
        # 执行批量蒸馏
        result = self.batch_distill(cases, zhanshi)
        
        # 更新模板引擎
        if result.get('successful', 0) > 0 and self.template_updater:
            update_result = self.template_updater.update_template_engine(
                self.template_engine
            )
            result['template_update'] = update_result
        
        return result
    
    def _get_distillation_cases(self, zhanshi: str = None, 
                                 case_count: int = 10) -> list:
        """获取蒸馏案例（从多个数据源）"""
        cases = []
        
        # 数据源1: 训练知识库
        try:
            from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
            kb = LiuRenTrainingKnowledge()
            
            if zhanshi:
                cases = kb.query_by_zhanshi(zhanshi)
            else:
                cases = kb.query_similar_cases(limit=case_count * 2)
            
            if cases:
                print(f"   📖 从训练知识库获取 {len(cases)} 个案例")
                return cases[:case_count]
        except Exception as e:
            print(f"   ⚠️ 训练知识库不可用: {e}")
        
        # 数据源2: 六壬断案疏正案例
        try:
            cases_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "daliuren_shuzheng_cases.json"
            )
            if os.path.exists(cases_file):
                with open(cases_file, 'r', encoding='utf-8') as f:
                    raw_cases = json.load(f)
                
                # 转换为蒸馏引擎需要的格式
                for case in raw_cases:
                    formatted = {
                        'id': case.get('id', ''),
                        'name': case.get('name', ''),
                        '四柱': f"{case.get('year', '')}年 {case.get('month', '')}月 {case.get('day', '')}日 {case.get('hour', '')}时",
                        '课体': case.get('ke_ti', ''),
                        '三传': case.get('sanchuan', ''),
                        '占事': case.get('question', ''),
                        '实际结果': case.get('interpretation', ''),
                        '三传解释': case.get('sanchuan_interpretation', ''),
                        '应期': case.get('yingqi', '')
                    }
                    
                    # 如果指定了占事类型，进行筛选
                    if zhanshi:
                        if zhanshi in formatted['占事'] or self._match_zhanshi(zhanshi, formatted['占事']):
                            cases.append(formatted)
                    else:
                        cases.append(formatted)
                
                print(f"   📖 从断案疏正案例获取 {len(cases)} 个案例")
                return cases[:case_count]
        except Exception as e:
            print(f"   ⚠️ 断案疏正案例不可用: {e}")
        
        # 数据源3: 生成示例案例（用于演示）
        print(f"   📝 生成示例案例用于演示")
        demo_cases = self._generate_demo_cases(zhanshi, case_count)
        return demo_cases
    
    def _match_zhanshi(self, target: str, source: str) -> bool:
        """匹配占事类型"""
        # 关键词映射
        mappings = {
            '求财': ['财', '利', '经营', '买卖'],
            '婚姻': ['婚', '嫁', '娶', '姻'],
            '疾病': ['病', '疾', '医', '药'],
            '出行': ['行', '出', '路', '旅'],
            '官讼': ['官', '讼', '争', '诉'],
            '功名': ['名', '功', '考', '试'],
            '家宅': ['宅', '家', '屋', '居']
        }
        
        if target in mappings:
            keywords = mappings[target]
            return any(kw in source for kw in keywords)
        return target in source
    
    def _generate_demo_cases(self, zhanshi: str = None, 
                              case_count: int = 5) -> list:
        """生成演示案例"""
        demo_cases = []
        
        default_cases = [
            {
                '四柱': '壬寅年 甲辰月 戊午日 己未时',
                '课体': '元首课',
                '三传': '初传卯 中传辰 末传巳',
                '占事': '求财',
                '实际结果': '青龙乘初传，求财得遂，三传木生火，财源广进。'
            },
            {
                '四柱': '丙午年 丙午月 庚午日 壬午时',
                '课体': '重审课',
                '三传': '初传午 中传酉 末传亥',
                '占事': '疾病',
                '实际结果': '白虎乘中传，病在西方，末传亥水克制，可愈于亥日。'
            },
            {
                '四柱': '甲子年 丙寅月 己卯日 丁卯时',
                '课体': '涉害课',
                '三传': '初传亥 中传卯 末传未',
                '占事': '婚姻',
                '实际结果': '六合乘中传，婚姻可成，但涉害需防波折，终得美满。'
            },
            {
                '四柱': '癸巳年 庚申月 乙酉日 乙酉时',
                '课体': '遥克课',
                '三传': '初传戌 中传午 末传寅',
                '占事': '出行',
                '实际结果': '驿马临门户，出行顺利，贵人乘末传，有助力。'
            },
            {
                '四柱': '辛丑年 癸丑月 丁未日 己未时',
                '课体': '昴星课',
                '三传': '初传寅 中传戌 末传午',
                '占事': '官讼',
                '实际结果': '勾陈乘初传，官讼有阻，末传午火生官，需防官司缠身。'
            }
        ]
        
        for i, case in enumerate(default_cases[:case_count]):
            if zhanshi and case['占事'] != zhanshi:
                continue
            demo_cases.append(case)
        
        # 如果筛选后为空，返回所有案例
        if not demo_cases:
            demo_cases = default_cases[:case_count]
        
        return demo_cases
    
    def get_distillation_status(self) -> Dict:
        """获取蒸馏状态"""
        if not self.distill_engine:
            return {'available': False}
        
        stats = self.distill_engine.get_knowledge_stats()
        return {
            'available': True,
            'engine_initialized': True,
            'statistics': stats,
            'template_updated': self.template_updater is not None
        }
    
    def get_knowledge_base(self, zhanshi: str = None) -> Dict:
        """获取知识库内容"""
        if not self.distill_engine:
            return {'error': '蒸馏引擎未初始化'}
        
        if zhanshi:
            return self.distill_engine.get_zanshi_knowledge(zhanshi)
        else:
            return self.distill_engine.get_all_knowledge()


# 单例模式
_instance = None

def get_smart_judge() -> SmartJudge:
    """获取智能决策引擎单例"""
    global _instance
    if _instance is None:
        _instance = SmartJudge()
    return _instance


# 测试
if __name__ == "__main__":
    judge = get_smart_judge()
    
    print("🧠 智能分层决策引擎 (Smart Judge)")
    print("=" * 50)
    
    stats = judge.get_statistics()
    print("\n📊 引擎状态:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n📋 模板引擎适用的占事类型:")
    for zs in sorted(judge.TEMPLATE_SUITABLE_ZANSHI):
        print(f"   - {zs}")
    
    # 测试决策路径（模拟数据）
    print("\n🧪 模拟决策测试:")
    test_paipan = {
        '课体': '元首课',
        '三传': {'first': '巳', 'second': '申', 'third': '辰'},
        '天将': '青龙+巳',
        'bifa_rules': [{'name': '青龙临身主吉'}],
        'leishen_analysis': '妻财临青龙'
    }
    
    # 测试强制使用模板引擎
    result = judge.judge(test_paipan, zhanshi='求财', 
                         force_level=EngineLevel.TEMPLATE)
    
    print(f"\n   强制 TEMPLATE 层结果:")
    print(f"   - 成功: {result['success']}")
    print(f"   - 使用引擎: {result['engine_used']}")
    print(f"   - 置信度: {result['confidence']}")
    print(f"   - 成本估算: {result['cost_estimate']}")
    print(f"   - 决策路径:")
    for step in result['decision_path']:
        print(f"     [{step['level']}] {step.get('action', step.get('result', ''))}")
