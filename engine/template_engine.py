#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬模板推理引擎 (Template Engine) — 第2层

定位：
- 用低成本模型 (glm-4-flash) 处理 15% 的常规复杂占事
- 将规则引擎的输出转化为用户可读的断语
- 覆盖场景：常规占事的详细推理、类象联想补充、白话翻译

核心优势：
- 成本低 (约为 glm-5.3-flash 的 1/10)
- 速度快
- 可解释 (基于模板)
"""

import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

# 确保可以导入项目模块
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 免费/低成本模型
TEMPLATE_MODEL = "glm-4-flash"

# ============ 天将吉凶速查表（规则先验） ============
# 【2026-09-06 新增】模板引擎的"规则先验"核心：排盘天将直接映射吉凶倾向，
#   不依赖规则引擎是否传入 bifa_rules。黄金案例验证表明模型拿不到天将信号时
#   会把"白虎主暴跌"误判为"无明显风险"——天将必须作为强先验注入 prompt。
TIANJIANG_JIXIONG = {
    # 吉将
    "青龙": "吉", "六合": "吉", "天后": "吉", "贵人": "吉",
    # 凶将
    "白虎": "凶", "玄武": "凶", "勾陈": "凶", "螣蛇": "凶",
    # 中性/依位置
    "朱雀": "中", "太常": "中", "太阴": "中", "天空": "中",
}

# 各占事用神（领域判据先验：用神临吉凶将直接决定该占事的倾向）
ZANSHI_YONGSHEN = {
    "求财": "妻财",
    "婚姻": "天后/六合",
    "疾病": "官鬼",
    "出行": "驿马/青龙",
    "官讼": "官鬼",
    "功名": "官鬼/青龙",
    "家宅": "父母/青龙",
    "股票预测": "妻财",
    "大盘预测": "妻财",
    "个股预测": "妻财",
}

# 占事修正：同一神将在不同占事的吉凶含义（六壬类象随占事迁移，P2 2026-09-06）
# - 官讼白虎=乘官鬼得官府势，主胜诉（GOLDEN-006 原文"白虎临官主胜诉"，真实吉）
# - 求财勾陈=主横盘震荡非凶（GOLDEN-011 原文"勾陈主横盘震荡"，真实平）
# - 疾病朱雀=主发热/口舌/炎症（GOLDEN-003 原文"朱雀主口舌发热，巳火旺相需防炎症"，真实凶）
ZANSHI_TIANJIANG_FIX = {
    "官讼": {"白虎": "吉"},
    "求财": {"勾陈": "平"},
    "疾病": {"朱雀": "凶"},
}

# 占事修正的专属措辞（优先于通用凶/吉措辞）
ZANSHI_TIANJIANG_NOTE = {
    ("官讼", "白虎"): "发用（初传）乘白虎临官，主官讼见官得势/胜诉",
    ("求财", "勾陈"): "发用（初传）乘勾陈，主横盘震荡/拖延，财宜观望",
    ("疾病", "朱雀"): "发用（初传）乘朱雀，主口舌发热/炎症，病情有扰",
    ("疾病", "青龙"): "发用（初传）乘青龙，主生机活力/康复之象",
    ("疾病", "天后"): "发用（初传）乘天后，主身心恢复/滋养",
}

# 课体占事修正（P7 修复③b）：课体吉凶随占事迁移
# - 伏吟课求财=停滞不前/横盘（GOLDEN-011 原文"伏吟主停滞不前，等待突破方向"，真实平）
KETI_NOTE = {
    ("求财", "伏吟"): "伏吟课主停滞不前/横盘等待，财宜观望，待突破方向明朗",
}

# ============ 占事模板库 ============
# 每个模板包含：
# - system_prompt: 系统提示词（角色设定 + 领域判据）
# - analysis_template: 分析框架（【2026-09-06 精简】压缩冗余引导，排盘信息单行化）
# - output_format: 输出格式要求

ZANSHI_TEMPLATES = {
    "求财": {
        "system_prompt": """你是一位精通大六壬求财占断的专家。核心判据：先看课体吉凶，再看天将与妻财爻状态。青龙/六合临妻财主得财，白虎/玄武/勾陈临妻财主破财或被骗。""",
        
        "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：课体对求财吉凶？妻财状态生旺死绝？有无凶将破财？何时入市/离场？""",
        
        "output_format": """请输出JSON格式：
{
    "keti_judgment": "对课体的吉凶判断（10字以内）",
    "wealth_source": "财运来源分析（30字以内）",
    "risk_warning": "风险提示（如有则写，无则写'无明显风险'）",
    "timing_advice": "时机建议（结合应期）",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
    },
    
    "婚姻": {
        "system_prompt": """你是一位精通大六壬婚姻占断的专家。核心判据：天后/六合为婚姻用神，临用主吉；玄武/勾陈/螣蛇临用主有阻或有阴私。""",
        
        "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：天后/六合状态？三传走势合冲？有无勾陈玄武阻碍？何时能成/解？""",
        
        "output_format": """请输出JSON格式：
{
    "marriage_prospect": "婚姻前景判断（10字以内）",
    "emotion_trend": "感情走势分析",
    "obstacle_analysis": "阻碍因素分析",
    "timing_advice": "时机建议",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
    },
    
    "疾病": {
        "system_prompt": """你是一位精通大六壬疾病占断的专家。核心判据：官鬼为疾病用神；白虎主凶大病、青龙主康复；官鬼生旺则病重、受制则病退。""",
        
        "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：病位在何处？官鬼生旺状态？三传走势好转恶化？何时康复？""",
        
        "output_format": """请输出JSON格式：
{
    "disease_location": "病位判断",
    "severity_assessment": "病情轻重评估",
    "development_trend": "病情发展趋势",
    "recovery_time": "康复时间判断",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
    },
    
    "出行": {
        "system_prompt": """你是一位精通大六壬出行占断的专家。核心判据：驿马/青龙为出行用神，三传见驿马主动身顺利；白虎主意外、玄武主盗贼。""",
        
        "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：当前宜出行否？行程顺利坎坷？有无白虎玄武意外盗贼？出行注意什么？""",
        
        "output_format": """请输出JSON格式：
{
    "travel_timing": "出行时机判断",
    "journey_condition": "行程状况分析",
    "risk_factors": "风险因素",
    "preparation_advice": "准备建议",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
    },
    
    "官讼": {
        "system_prompt": """你是一位精通大六壬官讼占断的专家。核心判据：官鬼为官讼用神；白虎主刑讼不利、贵人主有助；勾陈主拖延。""",
        
        "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：官鬼状态？诉讼走势胜负？有无贵人助力？何时结案？""",
        
        "output_format": """请输出JSON格式：
{
    "litigation_prospect": "诉讼前景判断",
    "win_lose_analysis": "胜负分析",
    "noble_help": "贵人助力情况",
    "settlement_time": "结案时间判断",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
    }
}

# 默认模板（用于未在模板库中的占事类型）
DEFAULT_TEMPLATE = {
    "system_prompt": """你是一位精通大六壬占卜的专家。核心判据：课体定大局，三传看发展，天将看吉凶（青龙/六合/天后/贵人为吉，白虎/玄武/勾陈/螣蛇为凶）。""",
    
    "analysis_template": """【排盘】课体:{keti} | 三传:{sanchuan} | 天将:{tianjiang} | 五行:{wuxing_analysis}
【规则】毕法:{bifa_rules} | 类神:{leishen_analysis}
【先验】{rule_prior}
分析：课体吉凶含义？三传发展趋势？关键类象信号？具体建议？""",
    
    "output_format": """请输出JSON格式：
{
    "keti_meaning": "课体含义解读",
    "trend_analysis": "趋势分析",
    "key_signals": "关键信号",
    "specific_advice": "具体建议",
    "overall_jixiong": "吉/凶/中平",
    "confidence_score": 0-100
}"""
}


class LiuRenTemplateEngine:
    """大六壬模板推理引擎"""
    
    def __init__(self):
        self.template_model = TEMPLATE_MODEL
        self._init_llm_client()
        
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        try:
            # 尝试使用 glm_service.py
            sys.path.insert(0, _ROOT)
            from glm_service import GLMService
            self.llm_service = GLMService()
            # 【2026-09-05 修复】GLMService() 默认模型是 glm-5.3-flash（高价），
            #   模板引擎必须显式切换为免费模板模型 glm-4-flash，否则成本翻倍且行为不符
            self.llm_service.model = self.template_model
            self.use_llm_service = True
        except Exception as e:
            print(f"⚠️ 无法导入 GLMService: {e}")
            self.use_llm_service = False
            self.llm_service = None
            
    def get_template(self, zhanshi: str) -> Dict:
        """获取指定占事的模板"""
        if zhanshi in ZANSHI_TEMPLATES:
            return ZANSHI_TEMPLATES[zhanshi]
        return DEFAULT_TEMPLATE
    
    def build_prompt(self, zhanshi: str, paipan_data: Dict, 
                     rule_engine_result: Dict) -> Dict:
        """
        构建推理 Prompt
        
        参数：
            zhanshi: 占事类型 (求财/婚姻/疾病/出行/官讼/其他)
            paipan_data: 排盘数据 {keti, sanchuan, tianjiang, wuxing_analysis}
            rule_engine_result: 规则引擎结果 {bifa_rules, leishen_analysis}
            
        返回：
            {
                "system_prompt": 系统提示词,
                "user_prompt": 用户提示词,
                "output_format": 输出格式
            }
        """
        template = self.get_template(zhanshi)
        
        # 【2026-09-06 新增】天将格式化 + 规则先验（天将吉凶 + 毕法 + 类神）
        # 【2026-09-06 P7 修复③】展示层同样走占事修正：求财勾陈不再标凶（否则与
        #   先验层"横盘平"修正矛盾，模型信号打架）
        tianjiang_str = self._format_tianjiang(paipan_data.get('tianjiang', ''), zhanshi)
        rule_prior = self._build_rule_prior(
            zhanshi=zhanshi,
            tianjiang=paipan_data.get('tianjiang', ''),
            sanchuan=paipan_data.get('sanchuan', {}),
            bifa_rules=rule_engine_result.get('bifa_rules', []),
            leishen_analysis=rule_engine_result.get('leishen_analysis', ''),
            wuxing_analysis=paipan_data.get('wuxing_analysis', ''),
            paipan_data=paipan_data
        )
        
        # 填充分析模板（【2026-09-06 精简】排盘信息单行化，新增 {rule_prior} 占位）
        user_prompt = template["analysis_template"].format(
            keti=paipan_data.get('keti', '未知'),
            sanchuan=self._format_sanchuan(paipan_data.get('sanchuan', {})),
            tianjiang=tianjiang_str,
            wuxing_analysis=paipan_data.get('wuxing_analysis', '未分析'),
            bifa_rules=self._format_bifa_rules(rule_engine_result.get('bifa_rules', [])),
            leishen_analysis=self._truncate(rule_engine_result.get('leishen_analysis', '未分析'), 60),
            rule_prior=rule_prior
        )
        
        return {
            "system_prompt": template["system_prompt"],
            "user_prompt": user_prompt,
            "output_format": template["output_format"],
            # 【2026-09-06 P9】透出先验文本，供 SmartJudge 矛盾课检测（凶将+强吉信号并存→升级AI）
            "rule_prior": rule_prior
        }
    
    def _format_tianjiang(self, tianjiang, zhanshi: str = '') -> str:
        """格式化天将（兼容 list / str），并附吉凶标注（走占事修正）"""
        # 归一化为字符串
        if isinstance(tianjiang, (list, tuple)):
            parts = [str(t) for t in tianjiang if str(t).strip()]
            raw = '、'.join(parts) if parts else ''
        else:
            raw = str(tianjiang or '').strip()
        if not raw:
            return "未提供"
        # 【2026-09-06 P7 修复③】吉凶取值走占事修正（ZANSHI_TIANJIANG_FIX），
        #   与先验层保持一致，避免展示"凶"、先验"平"的自相矛盾
        fix = ZANSHI_TIANJIANG_FIX.get(zhanshi, {})
        def _jx(name):
            return fix.get(name) or TIANJIANG_JIXIONG.get(name, '')
        # 提取天将名（兼容"白虎+金"、"青龙+巳"、"['勾陈', '青龙']"等格式）
        names = re.findall(r'[\u4e00-\u9fa5]{2}', raw)
        ji = [n for n in names if _jx(n) == '吉']
        xiong = [n for n in names if _jx(n) == '凶']
        zhong = [n for n in names if _jx(n) == '中']
        if ji or xiong:
            tag = f"（{'吉:' + '/'.join(ji) if ji else ''}{'；凶:' + '/'.join(xiong) if xiong else ''}）"
        elif zhong:
            tag = "（中性将）"
        else:
            tag = ""
        return f"{raw}{tag}"
    
    def _build_rule_prior(self, zhanshi: str, tianjiang, sanchuan: Dict,
                          bifa_rules: List, leishen_analysis: str,
                          wuxing_analysis: str = '', paipan_data: Dict = None) -> str:
        """
        【2026-09-06 新增】构建规则先验段落——把确定性信息显式告诉模型，
        让模型"基于先验输出吉凶"而非凭空猜测（黄金案例验证：无先验时
        模板把白虎主暴跌误判为无明显风险）。

        2026-09-06 二轮：吉凶混杂弱化 + 五行旺衰先验——
        案例验证发现"白虎空亡诱多/子孙旺相发财"类课中凶将仅表征，
        天将吉凶混杂或六亲旺衰主导时应弱化一刀切，避免先验误导。

        2026-09-06 三轮：补六亲 + 空亡先验——
        golden 误判案例缺"空亡/六亲旺衰"输入（寅午戌白虎空亡诱多、末传巳空亡必跌），
        由 paipan_data 的日柱+三传自算，补齐后模型可获得"空亡=力弱/事虚"关键信号。
        """
        prior_parts = []
        
        # 0) 占事修正的吉凶取值（六壬类象随占事迁移）
        def _jx(name: str) -> str:
            fix = ZANSHI_TIANJIANG_FIX.get(zhanshi, {})
            return fix.get(name) or TIANJIANG_JIXIONG.get(name, '')
        
        # 0.5) 天将名列表（供发用/全盘/用神提示/空亡压制复用）
        if isinstance(tianjiang, (list, tuple)):
            _all_names = [str(t) for t in tianjiang if str(t).strip()]
        else:
            _all_names = re.findall(r'[\u4e00-\u9fa5]{2}', str(tianjiang or ''))
        names = [n for n in _all_names if n in TIANJIANG_JIXIONG or n in ZANSHI_TIANJIANG_FIX.get(zhanshi, {})]
        
        # 1) 发用天将先验（六壬断课"发用最重"；天将数组按三传顺序时首元素=初传乘将）
        # 【2026-09-06 二轮】golden 案例验证：初传乘凶将（如勾陈）→课凶，初传乘吉将（如天后）→课吉，
        #   发用信号远强于全盘吉凶统计；有发用定论时不再叠加"全盘混杂"避免自我矛盾
        is_seq_list = isinstance(tianjiang, (list, tuple)) and len(tianjiang) > 0
        if is_seq_list:
            first_tj = str(tianjiang[0]).strip()
            first_name = re.findall(r'[\u4e00-\u9fa5]{2}', first_tj)
            fn = first_name[0] if first_name else ''
            fjx = _jx(fn)
        else:
            fn, fjx = '', ''
        # 【2026-09-06 修正】求财勾陈=平 仅限"伏吟课"成立（GOLDEN-011 横盘等待）；
        #   不虞格等课体勾陈发用=凶（CASE-STOCK-002 原文"勾陈筑底=暴跌后筑底"应凶），
        #   ZANSHI_TIANJIANG_FIX 无条件平修正误伤——这里按课体复核
        if zhanshi == '求财' and fn == '勾陈':
            keti_txt = str(paipan_data.get('keti', '') or '').strip() if paipan_data else ''
            if '伏吟' in keti_txt:
                fjx = '平'
            else:
                fjx = '凶'
        if fjx == '凶':
            prior_parts.append(f"发用（初传）乘凶将{fn}，主事起即不利/凶险")
        elif fjx == '吉':
            # 【2026-09-06 P2】占事修正专属措辞优先（官讼白虎=胜诉吉，非通用吉将措辞）
            note = ZANSHI_TIANJIANG_NOTE.get((zhanshi, fn))
            prior_parts.append(note or f"发用（初传）乘吉将{fn}，主事起即得利/吉庆")
        elif fjx == '平':
            # 【2026-09-06 P2】占事修正为平（求财伏吟课+勾陈=横盘震荡）
            note = ZANSHI_TIANJIANG_NOTE.get((zhanshi, fn))
            prior_parts.append(note or f"发用（初传）乘{fn}，主事平稳/迟滞")
        # 发用中性或不可判 → 落入下方全盘吉凶逻辑
        
        # 2) 全盘天将吉凶先验（发用无定论时的辅助信号；吉凶混杂弱化一刀切）
        if not prior_parts:
            # 【2026-09-06 修正】全盘段同样按课体复核勾陈（非伏吟课=凶，与发用段一致）
            def _jx2(name):
                if zhanshi == '求财' and name == '勾陈':
                    keti_txt = str(paipan_data.get('keti', '') or '').strip() if paipan_data else ''
                    return '平' if '伏吟' in keti_txt else '凶'
                return _jx(name)
            ji = list(dict.fromkeys(n for n in names if _jx2(n) == '吉'))
            xiong = list(dict.fromkeys(n for n in names if _jx2(n) == '凶'))
            if xiong and ji:
                prior_parts.append(f"天将吉凶混杂（吉:{'/'.join(ji)}，凶:{'/'.join(xiong)}），主事多波折，须结合课体旺衰定吉凶")
            elif xiong:
                prior_parts.append(f"天将见凶将{'/'.join(xiong)}，主不利/凶险")
            elif ji:
                prior_parts.append(f"天将见吉将{'/'.join(ji)}，主有利/吉庆")
        
        # 3) 五行旺衰先验（有实际五行分析时补充气机强弱；疾病类占事旺衰方向相反）
        wuxing = str(wuxing_analysis or '').strip()
        if wuxing and wuxing not in ('未分析', '待分析'):
            is_ji_bing = (zhanshi == '疾病')
            if any(w in wuxing for w in ('旺', '生旺', '进气', '相生')):
                # 【2026-09-06 二轮】疾病占事官鬼旺=病重凶险（与求财用神旺=吉相反）
                if is_ji_bing:
                    prior_parts.append(f"五行{wuxing}，官鬼气旺主病情凶险/难愈")
                else:
                    prior_parts.append(f"五行{wuxing}，气旺主事有成")
            elif any(w in wuxing for w in ('死', '绝', '空亡', '休囚', '受制', '无力')):
                if is_ji_bing:
                    prior_parts.append(f"五行{wuxing}，官鬼受制主病势减退")
                else:
                    prior_parts.append(f"五行{wuxing}，气弱主事难成/迟滞")
        
        # 4) 用神提示（该占事最关键的类神；疾病类补充康复吉将判据）
        yongshen = ZANSHI_YONGSHEN.get(zhanshi, '')
        if yongshen:
            if zhanshi == '疾病':
                # 【2026-09-06 P7 修复④】疾病课官鬼为疾病本体，但青龙/贵人/天后临身
                #   主康复之象（GOLDEN-015 原文"青龙主生机活力，贵人主医疗资源，天后主恢复"=吉）
                heal_names = [n for n in names if n in ('青龙', '贵人', '天后')]
                if heal_names:
                    prior_parts.append(f"本占事用神为{yongshen}，但{'/'.join(heal_names)}临身主康复之象（疾病课吉将即吉）")
                else:
                    prior_parts.append(f"本占事用神为{yongshen}")
            else:
                prior_parts.append(f"本占事用神为{yongshen}")
        
        # 5) 毕法命中（规则引擎结论，若有）
        if bifa_rules:
            bifa_str = self._format_bifa_rules(bifa_rules)
            if bifa_str and bifa_str != '未命中':
                prior_parts.append(f"毕法命中：{bifa_str}")
        
        # 6) 类神分析（规则引擎结论，若有）
        if leishen_analysis:
            ls = self._truncate(str(leishen_analysis), 60)
            if ls and ls != '未分析':
                prior_parts.append(f"类神：{ls}")
        
        # 7) 六亲先验（三传六亲：按占事用神定向判定生旺死绝）
        # 【2026-09-06 三轮】"子孙旺相生财/官鬼受制病退"等断法依赖六亲，模型缺此信号易误判
        if paipan_data:
            lq_prior = self._build_liuqin_prior(zhanshi, paipan_data)
            if lq_prior:
                prior_parts.append(lq_prior)
        
        # 8) 空亡先验（三传逢旬空=力弱/事虚；末传空亡尤重"事终落空"）
        # 【2026-09-06 三轮】golden 案例"末传巳空亡必跌/白虎空亡诱多"均依赖空亡判定
        if paipan_data:
            kw_prior = self._build_kongwang_prior(zhanshi, paipan_data)
            if kw_prior:
                prior_parts.append(kw_prior)
        
        # 9) 课体占事修正（P7 修复③b）：课体吉凶随占事迁移
        # 【2026-09-06】伏吟课求财=停滞横盘（GOLDEN-011 真实平），模型默认判凶需修正
        if paipan_data:
            keti = str(paipan_data.get('keti', '') or '').strip()
            if keti:
                for (zs, kname), note in KETI_NOTE.items():
                    if zhanshi == zs and kname in keti:
                        prior_parts.append(note)
                        break
        
        if not prior_parts:
            return "无显著规则信号，请依据课体与三传自行判断"
        return '；'.join(prior_parts) + '。'
    
    # ============ 六亲/空亡先验（2026-09-06 三轮新增） ============
    
    _GAN_WUXING = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                   '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
    _ZHI_WUXING = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
                   '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
                   '戌': '土', '亥': '水'}
    _SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    _KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    def _get_ri_gan_zhi(self, paipan_data: Dict) -> Tuple[str, str]:
        """提取日干/日支（兼容 '日柱'/'日干'+'日支'/'四柱'）"""
        rg = str(paipan_data.get('日干', '') or '').strip()
        rz = str(paipan_data.get('日支', '') or '').strip()
        rizhu = str(paipan_data.get('日柱', '') or '').strip()
        if not rg and rizhu:
            rg = rizhu[0]
        if not rz and len(rizhu) > 1:
            rz = rizhu[1]
        if (not rg or not rz) and paipan_data.get('四柱'):
            parts = str(paipan_data['四柱']).split()
            if len(parts) >= 3:
                rg = parts[2][0]
                rz = parts[2][1]
        return rg, rz
    
    def _get_sanchuan_zhi(self, paipan_data: Dict) -> List[str]:
        """提取三传地支列表（兼容 '三传地支' 数组 / 'sanchuan' dict / '三传' dict）"""
        sc_zhi = paipan_data.get('三传地支', [])
        if sc_zhi:
            return [str(z).strip() for z in sc_zhi if str(z).strip()]
        sc = paipan_data.get('sanchuan', {}) or paipan_data.get('三传', {})
        if isinstance(sc, dict):
            return [str(sc.get(k, '')).strip() for k in ('first', 'second', 'third')
                    if str(sc.get(k, '')).strip()]
        return []
    
    def _calc_liuqin(self, ri_gan: str, dizhi: str) -> str:
        """计算地支对日干的六亲（父/鬼/子/兄/财）"""
        rw = self._GAN_WUXING.get(ri_gan, '')
        zw = self._ZHI_WUXING.get(dizhi, '')
        if not rw or not zw:
            return ''
        for w, s in self._SHENG.items():
            if s == rw and zw == w:
                return '父'
        for w, k in self._KE.items():
            if k == rw and zw == w:
                return '鬼'
        if self._SHENG.get(rw) == zw:
            return '子'
        if self._KE.get(rw) == zw:
            return '财'
        if rw == zw:
            return '兄'
        return ''
    
    def _extract_liuqin_from_text(self, sanchuan) -> List[str]:
        """
        【2026-09-06 P7 修复②】从三传文本提取原文六亲标注：
        '巳（子孙+白虎）' → '子'；'亥（子孙+白虎空亡）' → '子'。
        classic golden 案例的 ground_truth.sanchuan 存的是"地支（六亲+天将）"文本，
        六亲（子孙=财源）是原文判据关键，旧逻辑只提天将丢弃六亲致判凶。
        """
        if isinstance(sanchuan, dict):
            parts = [str(sanchuan.get(k, '')) for k in ('first', 'second', 'third')]
        else:
            parts = [str(sanchuan or '')]
        result = []
        for p in parts:
            m = re.search(r'[（(]([^）)]*)[）)]', p)
            lq = ''
            if m:
                inner = m.group(1)
                for x in ('父', '鬼', '子', '兄', '财'):
                    if x in inner:
                        lq = x
                        break
            result.append(lq)
        return result
    
    def _build_liuqin_prior(self, zhanshi: str, paipan_data: Dict) -> str:
        """构建三传六亲先验（按占事用神定向输出）"""
        rg, rz = self._get_ri_gan_zhi(paipan_data)
        sc_zhi = self._get_sanchuan_zhi(paipan_data)
        if len(sc_zhi) < 1:
            return ''
        # 【2026-09-06 P7 修复②】优先用原文六亲标注（如"巳（子孙+白虎）"），
        #   无标注且有日干时才自算（classic 案例无日柱时依赖原文标注）
        text_lq = self._extract_liuqin_from_text(paipan_data.get('sanchuan', {}) or paipan_data.get('三传', {}))
        if rg:
            lq_list = []
            for i, z in enumerate(sc_zhi):
                tl = text_lq[i] if i < len(text_lq) and text_lq[i] else ''
                lq_list.append(tl or (self._calc_liuqin(rg, z) or '?'))
        elif any(text_lq):
            lq_list = [text_lq[i] if i < len(text_lq) and text_lq[i] else '?' for i in range(len(sc_zhi))]
        else:
            return ''
        names = ['初传', '中传', '末传'][:len(lq_list)]
        lq_desc = '、'.join(f"{n}{lq}" for n, lq in zip(names, lq_list))
        # 按占事用神定向
        yongshen = ZANSHI_YONGSHEN.get(zhanshi, '')
        if yongshen:
            # 【2026-09-06 三轮 修复】从用神中提取六亲字（妻财→财、官鬼→鬼），
            #   旧逻辑用全部五亲列表导致任何六亲都误报"用神现于"
            ys_chars = [c for c in yongshen if c in ('财', '鬼', '父', '子', '兄')]
            if not ys_chars:
                return f"六亲：{lq_desc}"
            hit = [lq for lq in lq_list if lq in ys_chars]
            if hit:
                # 用神在传
                pos = [names[i] for i, lq in enumerate(lq_list) if lq in ys_chars]
                # 【2026-09-06 三轮】求财"子孙生财"吉象：三传见子（子孙）+ 财（妻财）→ 财源有根
                if '财' in ys_chars and '子' in lq_list and '财' in lq_list:
                    return f"六亲：{lq_desc}，子孙生财、用神{yongshen}现于{'、'.join(pos)}，财源旺相主得财"
                return f"六亲：{lq_desc}，用神{yongshen}现于{'、'.join(pos)}"
            # 【2026-09-06 P7 修复②】求财见子孙（财源）未现财爻：子孙旺相主财源有根
            if '财' in ys_chars and '子' in lq_list:
                return f"六亲：{lq_desc}，子孙为财源现于{'、'.join(names[i] for i, lq in enumerate(lq_list) if lq == '子')}，主财源有根/旺相得财"
            return f"六亲：{lq_desc}，用神{yongshen}未现于三传，用神乏力"
        # 无占事用神时，只描述事实
        if '鬼' in lq_list:
            return f"六亲：{lq_desc}，见官鬼主压力/阻碍"
        if '财' in lq_list:
            return f"六亲：{lq_desc}，见妻财主财事"
        return f"六亲：{lq_desc}"
    
    def _calc_kongwang(self, ri_gan: str, ri_zhi: str) -> List[str]:
        """计算日柱空亡地支（甲子旬→戌亥空，依此类推）"""
        try:
            stems = '甲乙丙丁戊己庚辛壬癸'
            branches = '子丑寅卯辰巳午未申酉戌亥'
            gi = stems.index(ri_gan)
            zi = branches.index(ri_zhi)
            idx = (gi * 6 - zi * 5) % 60
            xs = (idx // 10) * 10
            return [branches[(xs % 12 + 10) % 12], branches[(xs % 12 + 11) % 12]]
        except Exception:
            return []
    
    def _build_kongwang_prior(self, zhanshi: str, paipan_data: Dict) -> str:
        """构建三传空亡先验（逢空亡=力弱/事虚）"""
        rg, rz = self._get_ri_gan_zhi(paipan_data)
        sc_zhi = self._get_sanchuan_zhi(paipan_data)
        if not rg or not rz or len(sc_zhi) < 1:
            return ''
        kw = self._calc_kongwang(rg, rz)
        if not kw:
            return ''
        names = ['初传', '中传', '末传'][:len(sc_zhi)]
        hits = [names[i] for i, z in enumerate(sc_zhi) if z in kw]
        if not hits:
            return ''
        # 末传空亡尤重（事终无果）；初传空亡（事起即虚）
        severe = ''
        if '末传' in hits:
            severe = '，末传空亡主事终无果/落空'
        elif '初传' in hits:
            severe = '，初传空亡主事起即虚'
        # 【2026-09-06 三轮】空亡可压制发用吉将（六壬"踏空致命"铁律）：
        #   但仅当用神未现于三传时（如案例4"用神乏力+末传空亡必跌"）；
        #   若用神现于三传（如案例3"子孙生财"），空亡不压制财现吉象，避免误伤
        yongshen2 = ZANSHI_YONGSHEN.get(zhanshi, '')
        ys_chars2 = [c for c in yongshen2 if c in ('财', '鬼', '父', '子', '兄')]
        yongshen_hit = bool(rg and ys_chars2 and any(self._calc_liuqin(rg, z) in ys_chars2 for z in sc_zhi))
        tj = paipan_data.get('tianjiang', '')
        if not yongshen_hit and isinstance(tj, (list, tuple)) and tj:
            first_tj = str(tj[0]).strip()
            fn = re.findall(r'[\u4e00-\u9fa5]{2}', first_tj)
            if fn:
                # 【2026-09-06 P2】压制判断同样走占事修正（官讼白虎不判凶故不压制）
                fix = ZANSHI_TIANJIANG_FIX.get(zhanshi, {})
                fjx = fix.get(fn[0]) or TIANJIANG_JIXIONG.get(fn[0])
                if fjx == '吉':
                    severe += f'，发用虽乘吉将{fn[0]}但受空亡压制，吉象落空'
        return f"空亡：{'、'.join(hits)}逢旬空（{','.join(kw)}空），主力弱/事虚{severe}"
    
    def _truncate(self, text: str, max_len: int = 60) -> str:
        """截断长文本（超长加省略号）"""
        if not text:
            return ''
        text = str(text).strip()
        return text if len(text) <= max_len else text[:max_len] + '…'
    
    def _format_sanchuan(self, sanchuan: Dict) -> str:
        """格式化三传"""
        if not sanchuan:
            return "无"
        parts = []
        for key in ['first', 'second', 'third']:
            if key in sanchuan:
                val = sanchuan[key]
                if val:
                    ch_name = {'first': '初传', 'second': '中传', 'third': '末传'}.get(key, key)
                    parts.append(f"{ch_name}: {val}")
        return ', '.join(parts) if parts else "无"
    
    def _format_bifa_rules(self, bifa_rules: List) -> str:
        """格式化毕法规则"""
        if not bifa_rules:
            return "未命中"
        if isinstance(bifa_rules, list):
            return ', '.join([r.get('name', str(r)) if isinstance(r, dict) else str(r) for r in bifa_rules[:3]])
        return str(bifa_rules)
    
    def reason(self, zhanshi: str, paipan_data: Dict,
               rule_engine_result: Dict, vote_times: int = 1) -> Dict:
        """
        执行模板推理（支持多次采样投票稳定化）

        参数：
            zhanshi: 占事类型
            paipan_data: 排盘数据
            rule_engine_result: 规则引擎结果
            vote_times: 采样次数（>1 时多次调用取众数，glm-4-flash 低成本，
                        【2026-09-06 P6】golden 全量实测单次 67~79% 波动，投票后稳定化）

        返回：
            {
                "success": bool,
                "result": Dict (解析后的结果，投票模式取众数),
                "raw_response": str (原始API响应),
                "model_used": str,
                "error": str (如有),
                "votes": List (投票明细，vote_times>1 时)
            }
        """
        if vote_times <= 1:
            return self._reason_once(zhanshi, paipan_data, rule_engine_result)
        
        # 多次采样投票
        from collections import Counter
        rounds = []
        for _ in range(vote_times):
            rounds.append(self._reason_once(zhanshi, paipan_data, rule_engine_result))
        
        # 【2026-09-06 P6】仅统计有明确吉凶判定的轮次（排除模型照抄枚举/未选择）
        valid = [r for r in rounds
                 if r.get('result')
                 and str(r['result'].get('overall_jixiong', '未知')) in ('吉', '凶', '中平')]
        if not valid:
            # 全部无效：返回置信度最高的轮次（保留其原始输出供降级/升级决策）
            fallback = max(rounds, key=lambda r: (r.get('result') or {}).get('confidence_score', 0))
            fallback['votes'] = [r.get('result', {}).get('overall_jixiong', '无效') for r in rounds]
            fallback['success'] = False
            fallback['error'] = '多次采样均无有效吉凶判定'
            return fallback
        
        # 众数投票（平票取置信度最高者）
        votes = [r['result'].get('overall_jixiong', '未知') for r in valid]
        counter = Counter(votes)
        max_cnt = max(counter.values())
        top = [j for j, c in counter.items() if c == max_cnt]
        if len(top) == 1:
            mode = top[0]
        else:
            # 平票：取这些候选中 confidence_score 最高的那轮
            best = max(
                (r for r in valid if r['result'].get('overall_jixiong') in top),
                key=lambda r: r['result'].get('confidence_score', 0)
            )
            mode = best['result'].get('overall_jixiong', '未知')
        
        winner = next(r for r in valid if r['result'].get('overall_jixiong') == mode)
        winner['votes'] = votes
        return winner
    
    def _reason_once(self, zhanshi: str, paipan_data: Dict,
                     rule_engine_result: Dict) -> Dict:
        """执行单次模板推理（内部实现）"""
        prompt_data = self.build_prompt(zhanshi, paipan_data, rule_engine_result)
        
        # 组合完整 Prompt
        # 【2026-09-05 修复】加硬性输出约束：glm-4-flash 无强约束时输出自由文本/思考链（0 JSON），
        #   导致解析失败。约束"只输出 JSON、无解释、无 Markdown"。
        full_user_prompt = f"""【硬性输出约束】你只能输出一个 JSON 对象：
1. 直接以 "{{" 开头、以 "}}" 结尾输出 JSON，不要输出任何其他文字（禁止解释、思考过程、Markdown 代码块、前后缀说明）。
2. 字段严格遵循下方 schema，overall_jixiong 只能取 "吉"、"凶" 或 "中平"，confidence_score 为 0-100 整数。

{prompt_data['user_prompt']}

{prompt_data['output_format']}"""
        
        # 调用 LLM
        try:
            raw_response = self._call_llm(
                system_prompt=prompt_data['system_prompt'],
                user_prompt=full_user_prompt,
                max_tokens=2000,
                temperature=0.2  # 【2026-09-06 P4】0.3→0.2 降低 glm-4-flash 随机漂移（GOLDEN-015 青龙吉将偶判中平）
            )
            
            # 解析结果
            result = self._parse_result(raw_response)
            
            return {
                "success": result is not None,
                "result": result,
                "raw_response": raw_response,
                "model_used": self.template_model,
                "error": None if result else "JSON解析失败",
                # 【2026-09-06 P9】透出先验文本，供 SmartJudge 矛盾课检测
                "rule_prior": prompt_data.get('rule_prior', '')
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "raw_response": "",
                "model_used": self.template_model,
                "error": str(e),
                "rule_prior": prompt_data.get('rule_prior', '')
            }
    
    def _call_llm(self, system_prompt: str, user_prompt: str, 
                  max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """调用 LLM API"""
        if self.use_llm_service and self.llm_service:
            try:
                # 使用 glm_service（【2026-09-05 修复】签名不符：generate 接收 OpenAI 格式 messages，
                #   原传 prompt 关键字报 unexpected keyword argument）
                response = self.llm_service.generate(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    # 【2026-09-05 修复】强制 JSON 输出 + 关闭思考：glm-4-flash 默认思考时
                    #   content 为空、generate 退用 reasoning_content（英文思维链）导致解析失败
                    response_format={"type": "json_object"},
                    thinking=False,
                )
                if response.get('success'):
                    return response.get('content', '')
            except Exception as e:
                print(f"⚠️ LLM Service 调用失败: {e}")
        
        # Fallback: 直接使用 requests（只读环境变量，禁止硬编码密钥）
        import requests
        api_key = os.getenv("BIGMODEL_API_KEY", "") or os.getenv("GLM_API_KEY", "")
        api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.template_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"❌ API 错误: {resp.status_code} - {resp.text[:200]}")
                return ""
        except Exception as e:
            print(f"❌ API 调用异常: {e}")
            return ""
    
    def _parse_result(self, raw_response: str) -> Optional[Dict]:
        """解析 LLM 返回结果"""
        if not raw_response:
            return None
        
        # 尝试提取 JSON
        json_match = self._extract_json(raw_response)
        if json_match:
            return self._normalize_jixiong(json_match)
        
        # 如果不是纯 JSON，尝试从文本中提取关键字段
        result = {}
        jixiong_match = re.search(r'"overall_jixiong"\s*:\s*"(\w+)"', raw_response)
        if jixiong_match:
            result['overall_jixiong'] = jixiong_match.group(1)
            
        confidence_match = re.search(r'"confidence_score"\s*:\s*(\d+)', raw_response)
        if confidence_match:
            result['confidence_score'] = int(confidence_match.group(1))
            
        if result:
            return self._normalize_jixiong(result)
        
        return None
    
    def _normalize_jixiong(self, result: Dict) -> Optional[Dict]:
        """
        【2026-09-06 P6】归一化 overall_jixiong：
        模型偶发照抄 schema 枚举（'吉/凶/中平' 或 '吉、凶、中平'），
        此时视为未作选择（返回 None 使该轮记为无效，不参与投票污染众数）
        """
        if not isinstance(result, dict):
            return None
        jx = str(result.get('overall_jixiong', '') or '').strip()
        # 含枚举分隔符（/ 、 , 空格）→ 未作选择
        if any(sep in jx for sep in ('/', '、', ',', ' ')) or jx not in ('吉', '凶', '中平'):
            result.pop('overall_jixiong', None)
            # 仅剩 confidence 时返回 None（无有效判定）
            if 'confidence_score' in result and len(result) == 1:
                return None
        return result if result else None
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取 JSON 对象"""
        # 找到第一个 { 开始
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        # 找到最后一个 } 结束
        end_idx = text.rfind('}')
        if end_idx == -1:
            return None
        
        json_str = text[start_idx:end_idx + 1]
        
        # 清理可能的 markdown 标记
        if json_str.startswith('```'):
            json_str = json_str[json_str.find('\n') + 1:]
        if json_str.endswith('```'):
            json_str = json_str[:json_str.rfind('```')]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试修复常见问题
            try:
                # 移除 trailing commas
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def get_available_templates(self) -> List[str]:
        """获取所有可用模板类型"""
        return list(ZANSHI_TEMPLATES.keys()) + ["其他(默认)"]


# 单例模式
_instance = None

def get_template_engine() -> LiuRenTemplateEngine:
    """获取模板引擎单例"""
    global _instance
    if _instance is None:
        _instance = LiuRenTemplateEngine()
    return _instance


# 测试
if __name__ == "__main__":
    engine = get_template_engine()
    
    print("📋 可用模板类型:")
    for t in engine.get_available_templates():
        print(f"   - {t}")
    
    # 测试构建 prompt
    test_paipan = {
        "keti": "元首课",
        "sanchuan": {"first": "巳", "second": "申", "third": "辰"},
        "tianjiang": "青龙+巳, 贵人+申, 勾陈+辰",
        "wuxing_analysis": "三传木火旺相"
    }
    
    test_rule = {
        "bifa_rules": [{"name": "青龙临身主吉"}, {"name": "贵人拱日干"}],
        "leishen_analysis": "妻财临青龙，财运亨通"
    }
    
    prompt_data = engine.build_prompt("求财", test_paipan, test_rule)
    
    print("\n🧪 测试 Prompt 构建 (求财):")
    print(f"   System Prompt 长度: {len(prompt_data['system_prompt'])} 字符")
    print(f"   User Prompt 预览:")
    print(f"   {prompt_data['user_prompt'][:200]}...")
