#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 综合评价系统

基于本地安全模型服务，对斗首、演禽、六壬三个模块的课格课体数据进行全面分析
集成传统六壬课体课格吉凶断语，提供专业的属相、年份、行业建议
"""

import json
import requests
from typing import Dict, List, Optional
from core_modules.engine.liuren_keti_duanyu import LiuRenKetiDuanyu
from core_modules.engine.optimized_evaluation import OptimizedEvaluation


class AIEvaluation:
    """AI 综合评价类"""
    
    def __init__(self, enable_ai=False):
        """
        初始化 AI 评价器
        
        :param enable_ai: 是否启用 AI 评价（默认 False，使用传统断语）
        """
        # AI 服务配置（仅当 enable_ai=True 时使用）
        self.enable_ai = enable_ai
        self.api_url = "http://localhost:80/v1/chat/completions"
        self.api_key = "local-safe-chat-123456"
        self.model = "local-safe-model"
        
        # 初始化六壬课体断语库
        self.liuren_duanyu = LiuRenKetiDuanyu()
        
        # 初始化优化版评价器
        self.optimized_eval = OptimizedEvaluation()
        
        # 行业分类
        self.industries = [
            "金融投资", "房地产", "制造业", "科技互联网", "教育培训",
            "医疗健康", "文化娱乐", "餐饮服务", "零售商业", "农业"
        ]
        
        # 属相信息
        self.shuxiang = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
        
        # AI 服务可用性标记
        self.ai_available = False
        if self.enable_ai:
            self.ai_available = self._check_ai_service()
    
    def _check_ai_service(self) -> bool:
        """
        检查 AI 服务是否可用
        
        :return: AI 服务是否可用
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            return True
        except:
            print("⚠️  AI 服务不可用，将使用传统断语模式")
            return False
    
    def _call_ai(self, prompt: str) -> str:
        """
        调用本地安全模型服务
        
        :param prompt: 提示词
        :return: AI 回复内容
        """
        if not self.enable_ai or not self.ai_available:
            return self._get_traditional_evaluation(prompt)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的中国传统术数分析师，精通斗首择日、演禽真法和大六壬等传统术数理论。请基于提供的课格课体数据，给出全面、专业的评价分析，包括对不同属相的吉凶利弊评估、特定年份的运势走向判断，以及针对各行业的发展前景建议。分析过程需结合传统术数理论与实际应用场景，确保评价内容具有参考价值和可操作性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "AI 评价失败")
            
        except Exception as e:
            print(f"AI 调用错误：{e}")
            # AI 调用失败，降级到传统断语
            self.ai_available = False
            return self._get_traditional_evaluation(prompt)
    
    def _get_traditional_evaluation(self, prompt: str) -> str:
        """
        生成传统断语评价（不依赖 AI）
        
        :param prompt: 提示词（包含课格信息）
        :return: 传统断语评价
        """
        evaluation_parts = []
        
        evaluation_parts.append("【传统术数综合评价】\n")
        
        # 解析 prompt 中的课格信息
        if "课格类型" in prompt or "课格列表" in prompt:
            evaluation_parts.append("◆ 课体分析：")
            keti_list = []
            if "课格列表" in prompt:
                # 简单提取课格列表
                for line in prompt.split('\n'):
                    if "课格列表" in line:
                        keti_str = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                        keti_list = [k.strip() for k in keti_str.split(',') if k.strip()]
                        break
            
            if not keti_list and "课格类型" in prompt:
                for line in prompt.split('\n'):
                    if "课格类型" in line:
                        keti_str = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                        keti_list = [k.strip() for k in keti_str.split(',') if k.strip()]
                        break
            
            for keti in keti_list:
                keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
                evaluation_parts.append(f"\n  · {keti}（{keti_info['等级']}）：{keti_info['断语']}")
        
        if "斗首课格" in prompt or "斗首评分" in prompt:
            evaluation_parts.append("\n\n◆ 斗首分析：")
            for line in prompt.split('\n'):
                if "斗首课格" in line or "斗首评分" in line:
                    evaluation_parts.append(f"  {line.strip()}")
        
        if "六壬评分" in prompt or "六壬信息" in prompt:
            evaluation_parts.append("\n\n◆ 六壬分析：")
            for line in prompt.split('\n'):
                if "六壬评分" in line or "六壬信息" in line or "课格列表" in line:
                    evaluation_parts.append(f"  {line.strip()}")
        
        evaluation_parts.append("\n\n【建议】")
        evaluation_parts.append("\n· 以上分析基于传统六壬课体断语，具体应用请结合实际情况。")
        evaluation_parts.append("\n· 如需更详细的 AI 智能分析，请配置并启用 AI 服务。")
        
        return ''.join(evaluation_parts)
    
    def evaluate_comprehensive(self, data: Dict) -> Dict:
        """
        综合评价分析
        
        :param data: 包含斗首、演禽、六壬数据的字典
        :return: 综合评价结果
        """
        # 构建提示词
        prompt = self._build_prompt(data)
        
        # 调用 AI（如果不可用会返回传统断语）
        ai_response = self._call_ai(prompt)
        
        # 解析 AI 回复
        evaluation = self._parse_ai_response(ai_response)
        
        # 生成传统断语分析
        traditional_duanyu = self._generate_traditional_duanyu(data)
        
        # 如果 AI 不可用，ai_response 已经是传统断语格式
        if not self.ai_available:
            # AI 不可用时，将传统断语作为 ai_evaluation 返回
            return {
                "ai_evaluation": traditional_duanyu,
                "structured_evaluation": evaluation,
                "traditional_duanyu": traditional_duanyu
            }
        else:
            # AI 可用时，返回 AI 评价和传统断语
            return {
                "ai_evaluation": ai_response,
                "structured_evaluation": evaluation,
                "traditional_duanyu": traditional_duanyu
            }
    
    def _build_prompt(self, data: Dict) -> str:
        """
        构建 AI 提示词
        
        :param data: 包含斗首、演禽、六壬数据的字典
        :return: 提示词
        """
        prompt_parts = []
        
        # 基本信息
        prompt_parts.append(f"【基本信息】")
        if "日期" in data:
            prompt_parts.append(f"日期：{data['日期']}")
        if "四柱" in data:
            prompt_parts.append(f"四柱：{data['四柱']}")
        if "山向" in data:
            prompt_parts.append(f"山向：{data['山向']}")
        if "综合评分" in data:
            prompt_parts.append(f"综合评分：{data['综合评分']}")
        
        # 斗首信息
        prompt_parts.append(f"\n【斗首信息】")
        if "斗首课格" in data:
            prompt_parts.append(f"斗首课格：{data['斗首课格']}")
        if "斗首评分" in data:
            prompt_parts.append(f"斗首评分：{data['斗首评分']}")
        
        # 六壬信息
        prompt_parts.append(f"\n【六壬信息】")
        if "课格类型" in data:
            prompt_parts.append(f"课格类型：{data['课格类型']}")
        if "六壬评分" in data:
            prompt_parts.append(f"六壬评分：{data['六壬评分']}")
        if "课格列表" in data:
            prompt_parts.append(f"课格列表：{', '.join(data['课格列表'])}")
        
        # 演禽信息
        prompt_parts.append(f"\n【演禽信息】")
        if "演禽" in data:
            prompt_parts.append(f"演禽：{data['演禽']}")
        
        # 其他信息
        prompt_parts.append(f"\n【其他信息】")
        if "吉神" in data:
            prompt_parts.append(f"吉神：{data['吉神']}")
        if "龙德课" in data:
            prompt_parts.append(f"龙德课：{'是' if data['龙德课'] else '否'}")
        if "龙德类型" in data and data['龙德类型']:
            prompt_parts.append(f"龙德类型：{data['龙德类型']}")
        
        # 分析要求
        prompt_parts.append(f"\n【分析要求】")
        prompt_parts.append(f"1. 对不同属相的吉凶利弊进行评估，特别关注与当前课格相关的属相")
        prompt_parts.append(f"2. 对特定年份的运势走向给出判断，结合当前课格特点")
        prompt_parts.append(f"3. 针对各行业的发展前景提供专业建议，基于传统术数理论")
        prompt_parts.append(f"4. 分析过程需结合传统术数理论与实际应用场景")
        prompt_parts.append(f"5. 确保评价内容具有参考价值和可操作性")
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """
        解析 AI 回复，提取结构化信息
        
        :param response: AI 回复内容
        :return: 结构化评价结果
        """
        # 简单解析，实际应用中可以使用更复杂的解析逻辑
        evaluation = {
            "shuxiang_analysis": [],  # 属相分析
            "yearly_outlook": "",  # 年度运势
            "industry_advice": [],  # 行业建议
            "general_advice": ""  # 综合建议
        }
        
        # 提取属相分析
        if "属相" in response:
            lines = response.split('\n')
            in_shuxiang_section = False
            for line in lines:
                if "属相" in line:
                    in_shuxiang_section = True
                    continue
                if in_shuxiang_section and line.strip():
                    for sx in self.shuxiang:
                        if sx in line:
                            evaluation["shuxiang_analysis"].append(line.strip())
                            break
        
        # 提取年度运势
        if "年度" in response or "运势" in response:
            lines = response.split('\n')
            in_year_section = False
            year_lines = []
            for line in lines:
                if "年度" in line or "运势" in line:
                    in_year_section = True
                if in_year_section and line.strip():
                    year_lines.append(line.strip())
            if year_lines:
                evaluation["yearly_outlook"] = "\n".join(year_lines[:5])  # 取前5行
        
        # 提取行业建议
        if "行业" in response:
            lines = response.split('\n')
            in_industry_section = False
            for line in lines:
                if "行业" in line:
                    in_industry_section = True
                    continue
                if in_industry_section and line.strip():
                    for industry in self.industries:
                        if industry in line:
                            evaluation["industry_advice"].append(line.strip())
                            break
        
        # 提取综合建议
        if "建议" in response:
            lines = response.split('\n')
            in_advice_section = False
            advice_lines = []
            for line in lines:
                if "建议" in line:
                    in_advice_section = True
                if in_advice_section and line.strip():
                    advice_lines.append(line.strip())
            if advice_lines:
                evaluation["general_advice"] = "\n".join(advice_lines[:10])  # 取前10行
        
        return evaluation
    
    def _generate_traditional_duanyu(self, data: Dict) -> str:
        """
        生成传统断语分析（优化精简版）
        
        :param data: 包含斗首、演禽、六壬数据的字典
        :return: 传统断语内容
        """
        duanyu_parts = []
        
        keti_list = data.get('课格列表', [])
        if not keti_list and '课格类型' in data:
            keti_list = [k.strip() for k in data['课格类型'].split(',')]
        
        if not keti_list and 'patterns' in data:
            patterns = data.get('patterns', [])
            keti_list = []
            for p in patterns:
                if isinstance(p, str):
                    keti_list.append(p)
                elif isinstance(p, dict) and p.get('格局名称'):
                    keti_list.append(p['格局名称'])
        
        if keti_list:
            duanyu_parts.append("【核心判断】")
            level_map = {'上吉': 4, '中吉': 3, '平': 2, '下凶': 1}
            best_keti = None
            best_level = 0
            
            for keti in keti_list[:3]:
                keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
                level = level_map.get(keti_info['等级'], 2)
                if level > best_level:
                    best_level = level
                    best_keti = keti_info
            
            if best_keti:
                duanyu_parts.append(f"\n◆ 课体等级：{best_keti['等级']}")
                duanyu_parts.append(f"\n◆ 综合断语：{best_keti['断语'][:60]}")
            
            duanyu_parts.append("\n\n【课体断语速查】")
            for keti in keti_list[:3]:
                keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
                duanyu_parts.append(f"\n◆ {keti}（{keti_info['等级']}）：{keti_info['断语'][:40]}")
        
        luma_info = data.get('luma_guiren_info', {})
        if luma_info:
            duanyu_parts.append("\n\n【禄马贵人双重达标】")
            
            double_qualified_items = luma_info.get('double_qualified_items', [])
            dq_detail = luma_info.get('ri_double_qualified_detail', {})
            
            if double_qualified_items:
                duanyu_parts.append(f"\n◆ 双重达标：{', '.join(double_qualified_items)}")
                
                if dq_detail.get('ri_lu_double_qualified'):
                    lu_zhi = self._get_lu_zhi(data)
                    duanyu_parts.append(f"\n◆ 禄神{lu_zhi}：到山到向+发传，主财禄双全")
                
                if dq_detail.get('ri_ma_double_qualified'):
                    ma_zhi = self._get_ma_zhi(data)
                    duanyu_parts.append(f"\n◆ 驿马{ma_zhi}：到山到向+发传，主出行顺利")
                
                if dq_detail.get('ri_guiren_double_qualified'):
                    guiren_zhi = self._get_guiren_zhi(data)
                    duanyu_parts.append(f"\n◆ 贵人{guiren_zhi}：到山到向+发传，主贵人扶持")
            else:
                single_items = luma_info.get('single_qualified_items', [])
                if single_items:
                    duanyu_parts.append(f"\n◆ 单一达标：{'; '.join(single_items[:2])}")
                    duanyu_parts.append(f"\n  提示：未达双重标准，吉力减半")
                else:
                    duanyu_parts.append(f"\n◆ 无双重达标项")
                    duanyu_parts.append(f"\n  提示：此课禄马贵人未双重达标，需谨慎")
            
            duanyu_parts.append("\n\n【禄马贵人速查】")
            if double_qualified_items:
                ji_shuxiang = []
                xiong_shuxiang = []
                
                if dq_detail.get('ri_lu_double_qualified'):
                    lu_zhi = self._get_lu_zhi(data)
                    lu_sx = self._get_shuxiang_info(lu_zhi)
                    ji_shuxiang.append(f"{lu_sx['本命']}（禄神本命）")
                    ji_shuxiang.extend([f"{sx}（三合）" for sx in lu_sx['三合']])
                    if lu_sx['六冲']:
                        xiong_shuxiang.append(f"{lu_sx['六冲']}（六冲）")
                
                if dq_detail.get('ri_ma_double_qualified'):
                    ma_zhi = self._get_ma_zhi(data)
                    ma_sx = self._get_shuxiang_info(ma_zhi)
                    ji_shuxiang.append(f"{ma_sx['本命']}（驿马本命）")
                    ji_sx_set = set([s.split('（')[0] for s in ji_shuxiang])
                    for sx in ma_sx['三合']:
                        if sx not in ji_sx_set:
                            ji_shuxiang.append(f"{sx}（三合）")
                    if ma_sx['六冲'] and ma_sx['六冲'] not in set([s.split('（')[0] for s in xiong_shuxiang]):
                        xiong_shuxiang.append(f"{ma_sx['六冲']}（六冲）")
                
                if dq_detail.get('ri_guiren_double_qualified'):
                    guiren_zhi = self._get_guiren_zhi(data)
                    if guiren_zhi:
                        gr_sx = self._get_shuxiang_info(guiren_zhi)
                        ji_sx_set = set([s.split('（')[0] for s in ji_shuxiang])
                        if gr_sx['本命'] not in ji_sx_set:
                            ji_shuxiang.append(f"{gr_sx['本命']}（贵人本命）")
                
                if ji_shuxiang:
                    duanyu_parts.append(f"\n◆ 大吉属相：{', '.join(ji_shuxiang[:6])}")
                if xiong_shuxiang:
                    duanyu_parts.append(f"\n◆ 需谨慎属相：{', '.join(xiong_shuxiang)}")
            else:
                duanyu_parts.append(f"\n◆ 无双重达标，属相吉凶参考课体断语")
            
            duanyu_parts.append("\n\n【宜忌速查】")
            all_yi = set()
            all_ji = set()
            all_hangye = set()
            
            for keti in keti_list:
                keti_info = self.liuren_duanyu.get_keti_duanyu(keti)
                if keti_info.get('宜事'):
                    all_yi.update(keti_info['宜事'])
                if keti_info.get('忌事'):
                    all_ji.update(keti_info['忌事'])
                if keti_info.get('行业'):
                    all_hangye.update(keti_info['行业'])
            
            if all_yi:
                duanyu_parts.append(f"\n◆ 宜：{', '.join(sorted(list(all_yi))[:6])}")
            if all_ji:
                duanyu_parts.append(f"\n◆ 忌：{', '.join(sorted(list(all_ji))[:4])}")
            if all_hangye:
                duanyu_parts.append(f"\n◆ 适宜行业：{', '.join(sorted(list(all_hangye))[:5])}")
        
        shuxiang_param = data.get('属相', '')
        if shuxiang_param:
            duanyu_parts.append("\n\n【指定属相分析】")
            sx_info = self.liuren_duanyu.get_shuxiang_duanyu(shuxiang_param)
            duanyu_parts.append(f"\n◆ {shuxiang_param}：{sx_info['断语'][:50]}")
            if sx_info.get('吉方'):
                duanyu_parts.append(f"\n  吉方：{', '.join(sx_info['吉方'])}")
        
        return ''.join(duanyu_parts)
    
    def _get_lu_zhi(self, data: dict) -> str:
        """获取禄神地支"""
        sizhu = data.get('sizhu', {})
        ri_zhu = sizhu.get('日柱', '')
        if ri_zhu:
            ri_gan = ri_zhu[0]
            LU_MAP = {
                '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
                '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
            }
            return LU_MAP.get(ri_gan, '')
        return ''
    
    def _get_ma_zhi(self, data: dict) -> str:
        """获取驿马地支"""
        sizhu = data.get('sizhu', {})
        ri_zhu = sizhu.get('日柱', '')
        if ri_zhu and len(ri_zhu) >= 2:
            ri_zhi = ri_zhu[1]
            MA_MAP = {
                '申': '寅', '子': '寅', '辰': '寅',
                '寅': '申', '午': '申', '戌': '申',
                '亥': '巳', '卯': '巳', '未': '巳',
                '巳': '亥', '酉': '亥', '丑': '亥'
            }
            return MA_MAP.get(ri_zhi, '')
        return ''
    
    def _get_guiren_zhi(self, data: dict) -> str:
        """获取贵人地支"""
        sizhu = data.get('sizhu', {})
        ri_zhu = sizhu.get('日柱', '')
        if ri_zhu:
            ri_gan = ri_zhu[0]
            GUIREN_MAP = {
                '甲': '丑未', '乙': '申子', '丙': '亥酉', '丁': '亥酉', '戊': '丑未',
                '己': '申子', '庚': '丑未', '辛': '寅午', '壬': '卯巳', '癸': '卯巳'
            }
            guiren = GUIREN_MAP.get(ri_gan, '')
            return guiren[:1] if guiren else ''
        return ''
    
    def _get_shuxiang_info(self, zhi: str) -> dict:
        """根据地支获取属相信息（本命、三合、六冲）"""
        DIZHI_SHUXIANG = {
            '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
            '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
            '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
        }
        
        SANHE = {
            '子': ['申', '辰'], '丑': ['巳', '酉'], '寅': ['午', '戌'], '卯': ['亥', '未'],
            '辰': ['子', '申'], '巳': ['丑', '酉'], '午': ['寅', '戌'], '未': ['卯', '亥'],
            '申': ['子', '辰'], '酉': ['丑', '巳'], '戌': ['寅', '午'], '亥': ['卯', '未']
        }
        
        LIUCHONG = {
            '子': '午', '丑': '未', '寅': '申', '卯': '酉',
            '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
            '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
        }
        
        benming = DIZHI_SHUXIANG.get(zhi, '')
        sanhe_zhi = SANHE.get(zhi, [])
        sanhe_shuxiang = [DIZHI_SHUXIANG.get(z, '') for z in sanhe_zhi]
        liuchong_zhi = LIUCHONG.get(zhi, '')
        liuchong_shuxiang = DIZHI_SHUXIANG.get(liuchong_zhi, '')
        
        return {
            '本命': benming,
            '三合': sanhe_shuxiang,
            '六冲': liuchong_shuxiang
        }
    
    def get_ai_evaluation_for_result(self, result: Dict) -> str:
        """
        为择日结果获取 AI 评价
        
        :param result: 择日结果字典
        :return: AI 评价内容
        """
        evaluation = self.evaluate_comprehensive(result)
        
        # 构建完整的评价内容
        evaluation_content = []
        
        # 添加 AI 评价
        if evaluation.get("ai_evaluation"):
            evaluation_content.append("【AI 综合评价】")
            evaluation_content.append(evaluation["ai_evaluation"])
        
        # 添加传统断语
        if evaluation.get("traditional_duanyu"):
            evaluation_content.append("\n\n" + evaluation["traditional_duanyu"])
        
        return '\n'.join(evaluation_content)
    
    def get_detailed_shuxiang_analysis(self, keti_list: List[str]) -> Dict:
        """
        获取详细的属相分析
        
        :param keti_list: 课体列表
        :return: 属相分析结果
        """
        result = {
            '吉属相': set(),
            '凶属相': set(),
            '平属相': set(self.shuxiang),
            '详细分析': []
        }
        
        for keti in keti_list:
            analysis = self.liuren_duanyu.analyze_shuxiang_for_keti(keti)
            
            # 收集吉凶属相
            result['吉属相'].update(analysis['吉属相'])
            result['凶属相'].update(analysis['凶属相'])
            
            # 添加详细分析
            result['详细分析'].append(analysis)
        
        # 计算平属相
        result['平属相'] = result['平属相'] - result['吉属相'] - result['凶属相']
        
        # 转换为列表
        result['吉属相'] = list(result['吉属相'])
        result['凶属相'] = list(result['凶属相'])
        result['平属相'] = list(result['平属相'])
        
        return result
    
    def get_detailed_hangye_analysis(self, keti_list: List[str]) -> Dict:
        """
        获取详细的行业分析
        
        :param keti_list: 课体列表
        :return: 行业分析结果
        """
        result = {
            '适宜行业': {},
            '不宜行业': {},
            '详细分析': []
        }
        
        for keti in keti_list:
            analysis = self.liuren_duanyu.analyze_hangye_for_keti(keti)
            
            # 统计适宜行业
            for hangye in analysis['适宜行业']:
                if hangye not in result['适宜行业']:
                    result['适宜行业'][hangye] = []
                result['适宜行业'][hangye].append(keti)
            
            # 统计不宜行业
            for hangye in analysis['不宜行业']:
                if hangye not in result['不宜行业']:
                    result['不宜行业'][hangye] = []
                result['不宜行业'][hangye].append(keti)
            
            # 添加详细分析
            result['详细分析'].append(analysis)
        
        return result
    
    def get_fuke_nianfen_analysis(self, keti_list: List[str]) -> Dict:
        """
        获取发科甲年份分析
        
        :param keti_list: 课体列表
        :return: 发科甲年份分析结果
        """
        result = {
            '发科年份': [],
            '发福年限': [],
            '综合分析': ''
        }
        
        for keti in keti_list:
            analysis = self.liuren_duanyu.analyze_fuke_nianfen(keti)
            result['发科年份'].append({
                '课体': keti,
                '发科年': analysis['发科年'],
                '发福年限': analysis['发福年限']
            })
        
        # 生成综合分析
        if result['发科年份']:
            years = [item['发科年'] for item in result['发科年份']]
            result['综合分析'] = f"综合课体分析，{', '.join(years)}为发科甲之年。"
        
        return result


def test_ai_evaluation():
    """测试 AI 评价"""
    ai_eval = AIEvaluation()
    
    # 测试数据
    test_data = {
        "日期": "2026-03-29",
        "四柱": "丙午 辛卯 己亥 甲子",
        "山向": "壬山丙向",
        "斗首课格": "元辰课",
        "斗首评分": 8.5,
        "六壬评分": 9.2,
        "综合评分": 9.0,
        "课格类型": "龙德课, 富贵课, 荣华课",
        "课格列表": ["龙德课", "富贵课", "荣华课", "官爵课"],
        "吉神": "天德, 月德, 三合, 六合, 贵人",
        "龙德课": True,
        "龙德类型": "真龙德",
        "daliuren_detail": {
            "shan_jia": "子",
            "xiang_shou": "午",
            "ri_qualified": True,
            "ri_shan_count": 1,
            "ri_xiang_count": 1,
            "yue_qualified": True,
            "yue_shan_count": 1,
            "yue_xiang_count": 0,
            "nian_qualified": False,
            "nian_shan_count": 0,
            "nian_xiang_count": 0,
            "qualified_count": 2
        }
    }
    
    print("=" * 80)
    print("AI 综合评价测试")
    print("=" * 80)
    
    result = ai_eval.evaluate_comprehensive(test_data)
    print(f"\n【AI 评价】\n{result['ai_evaluation']}")
    print(f"\n【传统断语】\n{result['traditional_duanyu']}")
    
    # 测试属相分析
    print("\n" + "=" * 80)
    print("属相分析测试")
    print("=" * 80)
    shuxiang_result = ai_eval.get_detailed_shuxiang_analysis(test_data['课格列表'])
    print(f"吉属相：{', '.join(shuxiang_result['吉属相'])}")
    print(f"凶属相：{', '.join(shuxiang_result['凶属相'])}")
    print(f"平属相：{', '.join(shuxiang_result['平属相'])}")
    
    # 测试行业分析
    print("\n" + "=" * 80)
    print("行业分析测试")
    print("=" * 80)
    hangye_result = ai_eval.get_detailed_hangye_analysis(test_data['课格列表'])
    print(f"适宜行业：{list(hangye_result['适宜行业'].keys())}")
    print(f"不宜行业：{list(hangye_result['不宜行业'].keys())}")
    
    # 测试发科甲年份
    print("\n" + "=" * 80)
    print("发科甲年份测试")
    print("=" * 80)
    fuke_result = ai_eval.get_fuke_nianfen_analysis(test_data['课格列表'])
    print(f"发科年份：{fuke_result['发科年份']}")
    print(f"综合分析：{fuke_result['综合分析']}")


if __name__ == '__main__':
    test_ai_evaluation()
