#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬AI智能推理模块
整合训练结果知识库与GLM推理能力

功能：
1. 接收占事输入，自动排盘
2. 查询类似案例
3. 结合类象知识进行GLM推理
4. 输出具体事情判断
"""

import json
import time
import requests
import sys
import os
from typing import Dict, List, Optional, Tuple

# ===== 统一密钥管理 (解决401 invalid_request_error) =====
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api_key_manager import KeyManager, Provider as _Provider
    _KM = KeyManager()
    _GLM_CFG = _KM.get_best_provider(_Provider.GLM)
    if _GLM_CFG:
        API_KEY = _GLM_CFG.api_key
        API_URL = _GLM_CFG.base_url
        DEFAULT_MODEL = "glm-5.3-flash"  # 强制使用 Ox Alpha
    else:
        # GLM不通，尝试DeepSeek/Kimi回退
        _ANY = _KM.any_available()
        if _ANY:
            API_KEY = _ANY.api_key
            API_URL = _ANY.base_url
            DEFAULT_MODEL = "glm-5.3-flash"  # 强制使用 Ox Alpha
        else:
            API_KEY = ""
            API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            DEFAULT_MODEL = "glm-4-flash"
except Exception as _e:
    # KeyManager不可用时只读取环境变量，禁止硬编码密钥（防高价模型误烧钱）
    API_KEY = os.getenv("BIGMODEL_API_KEY", "") or os.getenv("GLM_API_KEY", "")
    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    DEFAULT_MODEL = "glm-5.3-flash"  # 强制便宜模型，禁止高价模型


class LiuRenAIJudge:
    """大六壬AI智能推理类"""

    SYSTEM_PROMPT = """你是一位精通《大六壬断案疏正》的大六壬大师，擅长根据类象知识进行具体事情推断。

【核心能力】
1. 精确判断吉凶
2. 精细类象分析
3. 具体到人、事、物、时、地的推演

【类象知识库】
一、十二地支核心类象：
- 亥：天门、天雨师、鬼神、幼子、将军、夫人、上客、醉人、稻麦、盐、楼阁、厕、肝肾
- 戌：天斗魁、天罗、牢狱、印绶、奴仆、足腿、城廓、寺观、五谷
- 酉：金刀、阴私、赏赐、婢妾、首饰、碑碣、金银、皮毛、口窍
- 申：道路、疾病、信耗、僧医、刀兵、药物、大麦、骸骨
- 未：天酒星、酒食、婚姻、姑姨、井泉、风伯、坟地、丧服
- 午：文书、光怪、心目、城门、厨、蚕丝、马、血光
- 巳：口舌、忧惊、车骑、炉冶、花果、蛇、蝉
- 辰：天哭星、狱神、死丧、田宅、甲胄、网罟、米麦
- 卯：驿马、船车、门户、桥梁、竹木、大肠
- 寅：文书、婚姻、官吏、道士、栋柱、棺椁、神祠
- 丑：田宅、桥、井、长者、六畜、龟鳖、脾肺
- 子：阴私、妇女、后妃、乳媪、婢妾、肾膀胱、渔江湖

二、十二神将核心含义：
- 贵人(丑)：官禄、文章、珍宝、鳖獬牛、贵人
- 螣蛇(巳)：惊狂、火光、血光、口舌、蛇
- 朱雀(午)：文章、印信、口舌、刑戮、马
- 六合(卯)：婚姻、喜庆、交易、门户、竹木
- 勾陈(辰)：战斗、词讼、争田、尸骨、鱼龙
- 青龙(寅)：文字、财帛、舟车、婚喜、僧道
- 天空(戌)：奴婢、公吏、虚伪、狗狼
- 白虎(申)：道路、兵戈、孝服、死丧、猴
- 太常(未)：祭祀、酒食、婚姻、绢帛、羊
- 玄武(亥)：盗贼、奸邪、聪明、哭泣、猪
- 太阴(酉)：阴私、蔽匿、婢妾、鸡
- 天后(子)：阴私、庆贺、恩泽、胎产、鼠

三、三传阴神链条推理方法：
三传每个地支都有阴神，阴神再推阴神形成推理链条。
例如：巳→阴神申→申的阴神亥
- 巳的类象：螣蛇、灶、口舌、惊忧
- 申的类象：道路、小麦、药物
- 亥的类象：水、楼阁、稻麦
综合：煮面引起的事（灶=巳，申=小麦，亥=水）

四、已知训练案例参考（当提供时）

【输出格式】
请按以下格式输出：
【课体判断】
课体名称：xxx
吉凶：吉/凶/中性

【三传分析】
三传：xxx→xxx→xxx
阴神链条：xxx→xxx→xxx

【类象推理】
初传：xxx（类象含义）
中传：xxx（类象含义）
末传：xxx（类象含义）

【具体事情推断】
根据以上分析，具体推断如下：
1. ...
2. ...
3. ...

【注意事项】
- 必须输出具体的事情，不是笼统的吉凶
- 要结合类象知识进行详细推理
- 推理过程要清晰明了"""

    def __init__(self, enable_knowledge_base=True, use_smart_engine=True):
        self.enable_knowledge_base = enable_knowledge_base
        self.use_smart_engine = use_smart_engine  # 是否使用分层智能引擎
        self.knowledge_base = None
        self.smart_judge = None
        
        # 引擎使用统计
        self._engine_stats = {
            'total_calls': 0,
            'rule_engine': 0,
            'template_engine': 0,
            'ai_engine': 0,
            'original_engine': 0,
            'failed_calls': 0,
            'last_used_engine': None,
            'last_confidence': 0.0
        }
        
        if enable_knowledge_base:
            self._load_knowledge_base()
            
        if use_smart_engine:
            self._init_smart_engine()
            
    def _init_smart_engine(self):
        """初始化分层智能决策引擎"""
        try:
            from engine.smart_judge import SmartJudge
            self.smart_judge = SmartJudge()
            print("🧠 分层智能引擎已初始化")
        except Exception as e:
            print(f"⚠️ 分层智能引擎初始化失败: {e}")
            self.smart_judge = None

    def _load_knowledge_base(self):
        """加载知识库"""
        try:
            from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
            self.knowledge_base = LiuRenTrainingKnowledge()
        except ImportError:
            try:
                import sys
                sys.path.insert(0, 'engine')
                from liuren_training_knowledge import LiuRenTrainingKnowledge
                self.knowledge_base = LiuRenTrainingKnowledge()
            except:
                self.knowledge_base = None

    def _call_glm(self, prompt: str, max_retries=3) -> str:
        """调用AI API (多服务商容错降级：GLM → DeepSeek → Kimi)

        最佳实践（2026-08）：
          - GLM(glm-5.3-flash) 优先，六壬推理核心任务强制走 Ox Alpha
          - DeepSeek 作为次级降级（更便宜更快）
          - 规则类判断：显式关闭 thinking，节省思考token
          - 指数退避重试（1s→2s→4s），而非固定8s
        """
        # 1) 列出候选：GLM优先(glm-5.3-flash)，其次DeepSeek，最后Kimi
        candidates = []
        try:
            if _GLM_CFG:
                candidates.append((_GLM_CFG, DEFAULT_MODEL or "glm-5.3-flash", True))
            for cfg in getattr(_KM, 'list_candidates', lambda _p: [])(_Provider.GLM):
                if cfg.api_key and (not _GLM_CFG or cfg.name != _GLM_CFG.name):
                    candidates.append((cfg, "glm-5.3-flash", True))
            for cfg in getattr(_KM, 'list_candidates', lambda _p: [])(_Provider.DEEPSEEK):
                if cfg.api_key:
                    candidates.append((cfg, "deepseek-v4-flash", False))
            for cfg in getattr(_KM, 'list_candidates', lambda _p: [])(_Provider.KIMI):
                if cfg.api_key:
                    candidates.append((cfg, "moonshot-v1-8k", True))
        except Exception:
            pass

        # 2) Fallback兜底，至少保证有1个可用候选
        if not candidates:
            candidates.append((type('C', (), {
                'api_key': API_KEY,
                'base_url': API_URL,
                'name': 'fallback',
                'provider': _Provider.GLM,
            })(), "glm-5.3-flash", True))

        for attempt in range(max_retries):
            # 轮询每个候选【2026-09-06 快速失败】预检：无 key 或上次判定为 401/404 的候选跳过，
            #   避免复核链路被 DeepSeek(401)/Kimi(404) 空转拖垮（模板判吉→AI复核 每案例等 240s×3 不可接受）
            dead_names = set()
            for cfg, model, is_glm in candidates:
                if not cfg.api_key:
                    continue
                if getattr(cfg, 'name', None) in dead_names:
                    continue
                headers = {
                    "Authorization": f"Bearer {cfg.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                }
                # DeepSeek：显式关闭 thinking（规则类判断，省钱）+ 低温度
                if not is_glm:
                    payload["thinking"] = {"type": "disabled"}
                    payload["temperature"] = 0.2
                    payload["max_tokens"] = 3000
                else:
                    payload["temperature"] = 0.8
                    payload["top_p"] = 0.95
                    # 【2026-09-05 修复】glm-5.3-flash 大 prompt 默认思考易超时（Read timed out），
                    #   显式开启 thinking + 低 reasoning_effort 限制思考开销
                    payload["thinking"] = {"type": "enabled", "reasoning_effort": "low"}
                try:
                    # 【2026-09-05 调优】240→120s：黄金案例 prompt（~200字）实测多数 40s 内返回，
                    #   但 open.bigmodel.cn 服务端偶发慢响应（曾实测 111s 才返回）；
                    #   【2026-09-06 复核快速失败】模板判吉→AI复核为增量路径，120s 未返回即放弃，
                    #   退回模板原判，避免复核拖垮整轮（DeepSeek/Kimi 401/404 已早停）
                    resp = requests.post(cfg.base_url, headers=headers, json=payload, timeout=120)
                    if resp.status_code == 200:
                        result = resp.json()
                        try:
                            return result["choices"][0]["message"]["content"]
                        except (KeyError, IndexError):
                            continue
                    elif resp.status_code == 401:
                        print(f"  ⚠️  [{cfg.name}] 密钥无效/过期 (401 invalid_request_error)，尝试下一条...")
                        dead_names.add(getattr(cfg, 'name', ''))
                        continue
                    elif resp.status_code == 429:
                        print(f"  ⏳ [{cfg.name}] 限流(429)，指数退避重试...")
                        continue
                    else:
                        print(f"  ⚠️  [{cfg.name}] API错误 {resp.status_code}: {resp.text[:120]}")
                        if resp.status_code == 404:
                            dead_names.add(getattr(cfg, 'name', ''))
                        continue
                except Exception as e:
                    print(f"  ⚠️  [{cfg.name}] 网络异常: {e}")
                    continue
            # 本轮所有候选失败，指数退避（1s→2s→4s）
            if attempt < max_retries - 1:
                backoff = 2 ** attempt
                print(f"  ⏳ 指数退避 {backoff}s 后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(backoff)

        print("  ❌ 所有AI服务商均失败，进入离线降级模式。请通过 `python api_key_manager.py --check` 检查密钥状态")
        return ""

    def query_similar_cases(self, zhanshi: str = None, raw_text: str = None, limit: int = 5) -> List[Dict]:
        """查询类似案例"""
        if not self.knowledge_base:
            return []

        if zhanshi:
            cases = self.knowledge_base.query_by_zhanshi(zhanshi)
        elif raw_text:
            cases = self.knowledge_base.query_similar_cases(raw_text, zhanshi)
        else:
            all_cases = []
            for cat_cases in self.knowledge_base.knowledge_base.get("占事分类", {}).values():
                all_cases.extend(cat_cases)
            cases = all_cases

        return cases[:limit]

    def _normalize_stock_zhanshi(self, zhanshi):
        """统一股票占事分类标识：支持 'stock' / '股市投资' / 'gushi_touzi' 多种写法"""
        if zhanshi in ('stock', '股市投资', 'gushi_touzi'):
            return 'stock'
        return zhanshi

    def judge(self, paipan_result: Dict, zhanshi: str = None, stock_code: str = None, 
              use_smart: bool = None, force_level: str = None) -> Dict:
        """
        AI智能判断（支持分层决策）

        参数：
            paipan_result: 排盘结果，包含四课三传等信息
            zhanshi: 占事类型（可选）
            stock_code: 股票代码（股市占事时必传）
            use_smart: 是否使用分层智能引擎 (None=使用默认设置)
            force_level: 强制使用特定层级 ('rule', 'template', 'ai', 'original')

        返回：
            {
                "success": bool,
                "result": str (判断结果),
                "engine_used": str (使用的引擎层级),
                "confidence": float,
                "cost_estimate": str,
                "error": str (如有)
            }
        """
        self._engine_stats['total_calls'] += 1
        
        # 如果强制使用原始引擎
        if force_level == 'original':
            result = self._judge_with_original_engine(paipan_result, zhanshi, stock_code)
            self._record_engine_usage('original_engine', result.get('confidence', 0))
            return result
        
        # 决定是否使用智能引擎
        should_use_smart = use_smart if use_smart is not None else self.use_smart_engine
        
        if should_use_smart and self.smart_judge and zhanshi:
            # 如果强制使用特定层级
            if force_level in ('rule', 'template', 'ai'):
                from engine.smart_judge import EngineLevel
                level_map = {
                    'rule': EngineLevel.RULE,
                    'template': EngineLevel.TEMPLATE,
                    'ai': EngineLevel.AI
                }
                smart_result = self.smart_judge.judge(
                    paipan_result, zhanshi, stock_code,
                    force_level=level_map.get(force_level)
                )
            else:
                # 尝试使用分层智能引擎
                smart_result = self._judge_with_smart_engine(paipan_result, zhanshi, stock_code)
            
            if smart_result.get('success'):
                engine = smart_result.get('engine_used', 'smart')
                self._record_engine_usage(engine, smart_result.get('confidence', 0))
                return smart_result
            else:
                self._engine_stats['failed_calls'] += 1
        
        # 回退到原始 AI 引擎 (glm-5.3-flash)
        result = self._judge_with_original_engine(paipan_result, zhanshi, stock_code)
        self._record_engine_usage('original_engine', result.get('confidence', 0))
        
        return result
    
    def _record_engine_usage(self, engine: str, confidence: float):
        """记录引擎使用统计"""
        self._engine_stats['last_used_engine'] = engine
        self._engine_stats['last_confidence'] = confidence
        self._engine_stats['total_calls'] += 1
        
        engine_key = engine.lower().replace('-', '_')
        if 'rule' in engine_key:
            self._engine_stats['rule_engine'] += 1
        elif 'template' in engine_key:
            self._engine_stats['template_engine'] += 1
        elif 'ai' in engine_key and 'original' not in engine_key:
            self._engine_stats['ai_engine'] += 1
        elif 'original' in engine_key:
            self._engine_stats['original_engine'] += 1
    
    def get_engine_stats(self) -> Dict:
        """获取引擎使用统计"""
        stats = self._engine_stats.copy()
        total = max(stats['total_calls'], 1)
        
        # 计算占比
        stats['rule_ratio'] = round(stats['rule_engine'] / total * 100, 1)
        stats['template_ratio'] = round(stats['template_engine'] / total * 100, 1)
        stats['ai_ratio'] = round(stats['ai_engine'] / total * 100, 1)
        stats['original_ratio'] = round(stats['original_engine'] / total * 100, 1)
        
        # 估算成本节省
        # 规则引擎: 0元, 模板引擎: glm-4-flash约1元/百万token, AI引擎: glm-5.3-flash约10元/百万token
        estimated_cost = (
            stats['rule_engine'] * 0 +
            stats['template_engine'] * 0.01 +  # 模板引擎成本估算
            stats['ai_engine'] * 0.1 +         # AI引擎成本估算
            stats['original_engine'] * 0.15     # 原始引擎成本估算
        )
        potential_savings = (
            stats['rule_engine'] * 0.15 +  # 如果全部用AI的话
            stats['template_engine'] * 0.14
        )
        stats['estimated_cost_yuan'] = round(estimated_cost, 4)
        stats['potential_savings_yuan'] = round(potential_savings, 4)
        stats['saving_rate'] = round(potential_savings / max(estimated_cost + potential_savings, 0.001) * 100, 1)
        
        return stats

    def _judge_with_smart_engine(self, paipan_result: Dict, zhanshi: str, 
                                  stock_code: str) -> Dict:
        """使用分层智能引擎进行判断"""
        try:
            # 调用分层决策
            smart_result = self.smart_judge.judge(
                paipan_result, zhanshi, stock_code
            )
            
            if smart_result.get('success'):
                result_content = smart_result.get('result', {})
                # 确保结果包含必要的文本信息
                if isinstance(result_content, dict):
                    # 从模板引擎结果中提取分析文本
                    analysis_text = result_content.get('specific_advice', 
                                    result_content.get('trend_analysis', ''))
                    jixiong = result_content.get('overall_jixiong', '中平')
                    
                    # 构建完整结果
                    full_result = f"【判断结果】{jixiong}\n\n【分析】{analysis_text}"
                    
                    return {
                        "success": True,
                        "result": full_result,
                        "engine_used": smart_result.get('engine_used', 'smart'),
                        "confidence": smart_result.get('confidence', 0.5),
                        "cost_estimate": smart_result.get('cost_estimate', '未知'),
                        "decision_path": smart_result.get('decision_path', []),
                        "error": None
                    }
                else:
                    return {
                        "success": True,
                        "result": str(result_content),
                        "engine_used": smart_result.get('engine_used', 'smart'),
                        "confidence": smart_result.get('confidence', 0.5),
                        "cost_estimate": smart_result.get('cost_estimate', '未知'),
                        "error": None
                    }
            
            return {
                "success": False,
                "result": "",
                "engine_used": "smart_failed",
                "error": smart_result.get('error', '智能引擎返回失败')
            }
            
        except Exception as e:
            print(f"⚠️ 智能引擎调用异常: {e}")
            return {
                "success": False,
                "result": "",
                "engine_used": "smart_error",
                "error": str(e)
            }

    def _judge_with_original_engine(self, paipan_result: Dict, zhanshi: str, 
                                     stock_code: str) -> Dict:
        """使用原始 AI 引擎 (glm-5.3-flash)"""
        zhanshi = self._normalize_stock_zhanshi(zhanshi)
        sizhu = paipan_result.get('四柱', '未知')
        sike = paipan_result.get('四课', {})
        sanchuan = paipan_result.get('三传', {})
        keti = paipan_result.get('课体', '未知')

        similar_cases = []
        if zhanshi and self.knowledge_base:
            similar_cases = self.query_similar_cases(
                zhanshi='stock' if zhanshi == 'stock' else zhanshi, limit=5
            )

        user_prompt = self._build_prompt(sizhu, sike, sanchuan, keti, 
                                          zhanshi, similar_cases, stock_code)

        result = self._call_glm(user_prompt)
        
        return {
            "success": bool(result),
            "result": result,
            "engine_used": "glm-5.3-flash",
            "confidence": 0.7 if result else 0.0,
            "cost_estimate": "约0.1-0.3元",
            "error": None if result else "API调用失败"
        }

    def _build_prompt(self, sizhu: str, sike: Dict, sanchuan: Dict,
                      keti: str, zhanshi: str, similar_cases: List[Dict],
                      stock_code: str = None) -> str:
        """构建提示词"""
        zhanshi = self._normalize_stock_zhanshi(zhanshi)
        prompt_parts = []

        if zhanshi:
            display_type = "📊 股市投资" if zhanshi == "stock" else zhanshi
            prompt_parts.append(f"【占事类型】{display_type}\n")

        stock_quotes = ""
        if zhanshi == "stock":
            from engine.stock_analyzer import StockAnalyzer
            stock_knowledge = StockAnalyzer.get_stock_class_knowledge()
            if stock_knowledge:
                prompt_parts.append(stock_knowledge)

            try:
                from engine.liuren_stock_rules import StockLiuRenRules
                rules_intro = """
【大六壬股市规则引擎参考】
六亲在股市中的映射：
- 父母: 政策/消息面/大盘环境
- 妻财: 利润/资金流入/盈利
- 官鬼: 主力/庄家/风险/监管
- 兄弟: 同行/板块联动/竞争
- 子孙: 散户/跟风盘/成交量

天将股市速查：
- 青龙: 资金流入/主升浪 → 吉
- 白虎: 暴跌/恐慌/放量跌 → 凶
- 朱雀: 消息驱动/传闻 → 快变
- 玄武: 庄家出货/陷阱 → 凶
- 贵人: 国家队护盘 → 稳
- 勾陈: 横盘/阻力 → 慢
- 腾蛇: 洗盘/假突破 → 反复
- 太常: 业绩兑现/常规 → 慢稳
- 太阴: 主力吸筹 → 隐秘
- 天后: 流动性宽松 → 利好
- 天空: 利好落空 → 利空
- 六合: 并购/合作 → 利好

发用吉凶速查：
- 妻财+青龙/六合 → 大涨信号
- 官鬼+白虎 → 暴跌预警
- 妻财+玄武/腾蛇 → 涨势不稳
- 父母+朱雀 → 消息驱动
- 兄弟+白虎 → 板块利空
"""
                prompt_parts.append(rules_intro)
            except Exception as e:
                print(f"加载规则引擎失败: {e}")

            try:
                sa = StockAnalyzer()
                query_code = stock_code or "000001"
                quote = sa.get_realtime_quote(query_code)
                if quote:
                    stock_quotes = sa.format_quote_for_prompt(quote)
                    prompt_parts.append(f"【查询股票】{quote.get('name', query_code)}（代码：{query_code}）")
            except Exception as e:
                print(f"获取股票行情失败: {e}")

        prompt_parts.append("【六壬排盘信息】")
        prompt_parts.append(f"四柱：{sizhu}")
        prompt_parts.append(f"课体：{keti}")

        if sike:
            prompt_parts.append("\n【四课】")
            if isinstance(sike, dict):
                for key, value in sike.items():
                    prompt_parts.append(f"  {key}：{value}")
            else:
                prompt_parts.append(f"  {sike}")

        if sanchuan:
            prompt_parts.append("\n【三传】")
            if isinstance(sanchuan, dict):
                for key, value in sanchuan.items():
                    prompt_parts.append(f"  {key}：{value}")
            else:
                prompt_parts.append(f"  {sanchuan}")

        if similar_cases:
            prompt_parts.append("\n【类似训练案例参考】")
            for i, case in enumerate(similar_cases[:3], 1):
                prompt_parts.append(f"\n案例{i}:")
                prompt_parts.append(f"  占事：{case.get('占事', '未知')}")
                actual = case.get('实际事情', '')
                if actual:
                    prompt_parts.append(f"  实际结果：{actual[:150]}...")

        if stock_quotes:
            prompt_parts.append(f"\n{stock_quotes}")

        if zhanshi == "stock":
            prompt_parts.append("\n\n请根据以上【大六壬股市规则引擎】进行六壬股市类象推理，分析该股走势趋势，")
            prompt_parts.append("判断以下内容：")
            prompt_parts.append("1. 大盘整体气运如何（结合父母/官鬼看政策与风险）")
            prompt_parts.append("2. 该股短期走势方向（上涨/下跌/震荡，结合妻财/官鬼判断）")
            prompt_parts.append("3. 主力资金动向（结合青龙/白虎/玄武看资金流向）")
            prompt_parts.append("4. 买卖时机建议（结合三传应期判断时间窗口）")
            prompt_parts.append("5. 风险提示（结合白虎/官鬼判断风险点）")
        else:
            prompt_parts.append("\n\n请根据以上信息进行六壬类象推理，判断具体会发生什么事情。")

        return "\n".join(prompt_parts)

    def quick_judge(self, sizhu: str, sike: str, sanchuan: str,
                    keti: str = None, zhanshi: str = None,
                    stock_code: str = None, force_level: str = None) -> str:
        """
        快速判断（直接传入字符串，支持分层引擎）

        参数：
        sizhu: 四柱字符串，如"壬寅年 甲辰月 戊午日 己未时"
        sike: 四课字符串，如"干上卯 干下辰 支上巳 支下午"
        sanchuan: 三传字符串，如"初传卯 中传辰 末传巳"
        keti: 课体名称
        zhanshi: 占事类型
        stock_code: 股票代码（股市占事时必传）
        force_level: 强制使用特定层级 ('rule', 'template', 'ai', 'original', None)

        返回：
        判断结果（字符串）
        """
        result = self.quick_judge_with_meta(
            sizhu=sizhu, sike=sike, sanchuan=sanchuan,
            keti=keti, zhanshi=zhanshi, stock_code=stock_code,
            force_level=force_level
        )
        return result.get('result', '')

    def quick_judge_with_meta(self, sizhu: str, sike: str, sanchuan: str,
                              keti: str = None, zhanshi: str = None,
                              stock_code: str = None, force_level: str = None) -> Dict:
        """
        快速判断（带元数据返回）

        返回：
        {
            'success': bool,
            'result': str,
            'engine_used': str,
            'confidence': float,
            'cost_estimate': str,
            'meta': { ... }
        }
        """
        zhanshi = self._normalize_stock_zhanshi(zhanshi)

        # 构建 paipan_result 字典以支持分层引擎
        paipan_result = {
            '四柱': sizhu,
            '四课': sike,
            '三传': sanchuan,
            '课体': keti or '未知',
            '占事': zhanshi or '未知',
            'stock_code': stock_code
        }

        # 优先尝试使用分层智能引擎（成本优化）
        if zhanshi and (self.use_smart_engine or force_level) and self.smart_judge:
            try:
                judge_result = self.judge(
                    paipan_result, zhanshi, stock_code, 
                    use_smart=self.use_smart_engine,
                    force_level=force_level
                )
                if judge_result.get('success') and judge_result.get('result'):
                    engine_used = judge_result.get('engine_used', 'smart')
                    confidence = judge_result.get('confidence', 0)
                    print(f"✅ 分层引擎判定: engine={engine_used}, confidence={confidence:.2f}")
                    return judge_result
                else:
                    print(f"⚠️ 分层引擎返回失败: {judge_result.get('error', '未知原因')}")
            except Exception as e:
                print(f"⚠️ 分层引擎异常: {e}")

        # 回退到原始 AI 引擎 (glm-5.3-flash)
        print(f"🔄 回退到原始AI引擎 (glm-5.3-flash)")
        result_text = self._quick_judge_original(sizhu, sike, sanchuan, keti, zhanshi, stock_code)
        
        return {
            'success': True,
            'result': result_text,
            'engine_used': 'original_engine',
            'confidence': 0.7,
            'cost_estimate': 'glm-5.3-flash (高成本)',
            'meta': {
                'forced_level': force_level,
                'fallback_reason': 'smart_engine_failed_or_disabled',
                'is_fallback': True
            }
        }

    def _quick_judge_original(self, sizhu: str, sike: str, sanchuan: str,
                               keti: str = None, zhanshi: str = None,
                               stock_code: str = None) -> str:
        """原始 quick_judge 实现（直接调用 glm-5.3-flash）"""
        similar_cases = []
        if zhanshi and self.knowledge_base:
            similar_cases = self.query_similar_cases(zhanshi='stock' if zhanshi == 'stock' else zhanshi, limit=5)

        prompt_parts = []

        if zhanshi:
            display_type = "📊 股市投资" if zhanshi == "stock" else zhanshi
            prompt_parts.append(f"【占事类型】{display_type}\n")

        stock_quotes = ""
        if zhanshi == "stock":
            from engine.stock_analyzer import StockAnalyzer
            stock_knowledge = StockAnalyzer.get_stock_class_knowledge()
            if stock_knowledge:
                prompt_parts.append(stock_knowledge)

            try:
                from engine.liuren_stock_rules import StockLiuRenRules
                rules_intro = """
【大六壬股市规则引擎参考】
六亲在股市中的映射：
- 父母: 政策/消息面/大盘环境
- 妻财: 利润/资金流入/盈利
- 官鬼: 主力/庄家/风险/监管
- 兄弟: 同行/板块联动/竞争
- 子孙: 散户/跟风盘/成交量

天将股市速查：
- 青龙: 资金流入/主升浪 → 吉
- 白虎: 暴跌/恐慌/放量跌 → 凶
- 朱雀: 消息驱动/传闻 → 快变
- 玄武: 庄家出货/陷阱 → 凶
- 贵人: 国家队护盘 → 稳
- 勾陈: 横盘/阻力 → 慢
- 腾蛇: 洗盘/假突破 → 反复
- 太常: 业绩兑现/常规 → 慢稳
- 太阴: 主力吸筹 → 隐秘
- 天后: 流动性宽松 → 利好
- 天空: 利好落空 → 利空
- 六合: 并购/合作 → 利好

发用吉凶速查：
- 妻财+青龙/六合 → 大涨信号
- 官鬼+白虎 → 暴跌预警
- 妻财+玄武/腾蛇 → 涨势不稳
- 父母+朱雀 → 消息驱动
- 兄弟+白虎 → 板块利空
"""
                prompt_parts.append(rules_intro)
            except Exception as e:
                print(f"加载规则引擎失败: {e}")

            try:
                sa = StockAnalyzer()
                query_code = stock_code or "000001"
                quote = sa.get_realtime_quote(query_code)
                if quote:
                    stock_quotes = sa.format_quote_for_prompt(quote)
                    prompt_parts.append(f"【查询股票】{quote.get('name', query_code)}（代码：{query_code}）")
            except Exception as e:
                print(f"获取股票行情失败: {e}")

        prompt_parts.append("【六壬排盘信息】")
        prompt_parts.append(f"四柱：{sizhu}")
        if keti:
            prompt_parts.append(f"课体：{keti}")
        prompt_parts.append(f"四课：{sike}")
        prompt_parts.append(f"三传：{sanchuan}")

        if similar_cases:
            prompt_parts.append("\n【类似训练案例参考】")
            for i, case in enumerate(similar_cases[:3], 1):
                prompt_parts.append(f"\n案例{i}:")
                prompt_parts.append(f"  占事：{case.get('占事', '未知')}")
                actual = case.get('实际事情', '')
                if actual:
                    prompt_parts.append(f"  实际结果：{actual[:150]}...")

        if stock_quotes:
            prompt_parts.append(f"\n{stock_quotes}")

        if zhanshi == "stock":
            prompt_parts.append("\n\n请根据以上【大六壬股市规则引擎】进行六壬股市类象推理，分析该股走势趋势，")
            prompt_parts.append("判断以下内容：")
            prompt_parts.append("1. 大盘整体气运如何（结合父母/官鬼看政策与风险）")
            prompt_parts.append("2. 该股短期走势方向（上涨/下跌/震荡，结合妻财/官鬼判断）")
            prompt_parts.append("3. 主力资金动向（结合青龙/白虎/玄武看资金流向）")
            prompt_parts.append("4. 买卖时机建议（结合三传应期判断时间窗口）")
            prompt_parts.append("5. 风险提示（结合白虎/官鬼判断风险点）")
        else:
            prompt_parts.append("\n\n请根据以上信息进行六壬类象推理，判断具体会发生什么事情。")

        return self._call_glm("\n".join(prompt_parts))


def test_judge():
    """测试判断功能"""
    judge = LiuRenAIJudge()

    print("=== 大六壬AI智能推理测试 ===\n")

    test_cases = [
        {
            "name": "天时案例",
            "sizhu": "壬寅年 甲辰月 辛亥日 壬辰时",
            "sike": "干上子 干下亥 支上丑 支下戌",
            "sanchuan": "初传丑 中传寅 末传卯",
            "keti": "三阳课",
            "zhanshi": "天时"
        },
        {
            "name": "婚姻案例",
            "sizhu": "庚子年 辛巳月 丁丑日 壬寅时",
            "sike": "干上卯 干下辰 支上巳 支下午",
            "sanchuan": "初传巳 中传午 末传未",
            "keti": "元首课",
            "zhanshi": "婚姻"
        }
    ]

    for tc in test_cases:
        print(f"\n{'='*50}")
        print(f"测试案例：{tc['name']}")
        print(f"{'='*50}")

        result = judge.quick_judge(
            sizhu=tc['sizhu'],
            sike=tc['sike'],
            sanchuan=tc['sanchuan'],
            keti=tc['keti'],
            zhanshi=tc['zhanshi']
        )

        print(f"\n【判断结果】\n{result}\n")


if __name__ == "__main__":
    test_judge()
