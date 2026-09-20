#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识蒸馏引擎 (Knowledge Distillation) — Phase 4

定位：
- 使用教师模型 (glm-5.3-pro) 生成高质量推理链
- 从推理链中提炼可复用的规则、模板、类象关联
- 更新学生模型 (glm-4-flash) 的模板和知识
- 实现持续学习和优化闭环

核心流程：
1. 教师推理 → 2. 知识提炼 → 3. 模板更新 → 4. 效果评估

蒸馏目标：
- 提升模板引擎（glm-4-flash）的推理质量
- 降低对昂贵AI模型的依赖
- 建立可持续优化的知识体系
"""

import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 确保可以导入项目模块
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 模型配置
TEACHER_MODEL = "glm-5.3-flash"  # 教师模型（高质量推理，启用思考链）
STUDENT_MODEL = "glm-4-flash"  # 学生模型（免费，用于模板引擎）


class DistillationEngine:
    """知识蒸馏引擎"""
    
    def __init__(self):
        self.distill_dir = self._get_distill_dir()
        self.knowledge_store = self._load_knowledge_store()
        self.distill_log = []
        
    def _get_distill_dir(self) -> str:
        """获取蒸馏数据目录"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        distill_dir = os.path.join(base_dir, "data", "distillation")
        os.makedirs(distill_dir, exist_ok=True)
        return distill_dir
    
    def _load_knowledge_store(self) -> Dict:
        """加载知识库"""
        knowledge_file = os.path.join(self.distill_dir, "knowledge_store.json")
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载知识库失败: {e}")
        return self._create_default_knowledge()
    
    def _create_default_knowledge(self) -> Dict:
        """创建默认知识结构"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "distill_stats": {
                "total_distillations": 0,
                "successful_distillations": 0,
                "knowledge_rules_extracted": 0,
                "template_updates": 0
            },
            "knowledge_rules": [],      # 提炼的知识规则
            "zanshi_templates": {},     # 各占事的模板知识
            "class_image_mapping": {},  # 类象关联映射
            "reasoning_chains": [],     # 高质量推理链
            "quality_metrics": {        # 质量指标
                "teacher_quality": 0.0,
                "student_quality": 0.0,
                "improvement_rate": 0.0
            }
        }
    
    def _save_knowledge_store(self):
        """保存知识库"""
        knowledge_file = os.path.join(self.distill_dir, "knowledge_store.json")
        self.knowledge_store["updated_at"] = datetime.now().isoformat()
        try:
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_store, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存知识库失败: {e}")
            return False
    
    def distill_case(self, case: Dict, zhanshi: str = None) -> Dict:
        """
        蒸馏单个案例
        
        参数：
        case: 案例数据，包含排盘信息和实际结果
        zhanshi: 占事类型（可选）
        
        返回：
        {
            "success": bool,
            "teacher_reasoning": str,      # 教师推理链
            "extracted_rules": List[str],  # 提炼的规则
            "template_updates": Dict,      # 模板更新
            "quality_score": float         # 质量评分
        }
        """
        print(f"\n🔬 开始蒸馏案例...")
        print(f"   占事: {zhanshi or case.get('占事', '未知')}")
        
        result = {
            "success": False,
            "teacher_reasoning": "",
            "extracted_rules": [],
            "template_updates": {},
            "quality_score": 0.0,
            "error": None
        }
        
        try:
            # 步骤1: 教师模型推理
            print(f"   📝 调用教师模型 ({TEACHER_MODEL})...")
            teacher_result = self._teacher_reasoning(case, zhanshi)
            
            if not teacher_result.get('success'):
                result['error'] = teacher_result.get('error', '教师推理失败')
                return result
            
            result['teacher_reasoning'] = teacher_result.get('reasoning', '')
            print(f"   ✅ 教师推理完成 ({len(result['teacher_reasoning'])} 字符)")
            
            # 步骤2: 知识提炼（优先AI提取，正则兜底）
            print(f"   🔍 从推理链中提炼知识...")
            
            # 先尝试AI驱动的知识提取
            ai_extracted = self._extract_knowledge_ai(
                case, result['teacher_reasoning'], zhanshi
            )
            
            # 如果AI提取成功有结果，使用AI结果
            if ai_extracted.get('rules') or ai_extracted.get('class_image_mappings'):
                extracted = ai_extracted
                print(f"   🤖 使用AI提取结果 ({ai_extracted.get('method', 'ai')})")
            else:
                # 兜底：使用正则提取
                extracted = self._extract_knowledge(
                    case, result['teacher_reasoning'], zhanshi
                )
                extracted['method'] = 'regex'
                print(f"   📋 使用正则提取结果 (兜底)")
            
            result['extracted_rules'] = extracted.get('rules', [])
            result['template_updates'] = extracted.get('template_updates', {})
            result['extraction_method'] = extracted.get('method', 'unknown')
            
            print(f"   ✅ 提炼规则: {len(result['extracted_rules'])} 条")
            print(f"   ✅ 模板更新: {len(result['template_updates'])} 个")
            
            # 步骤3: 质量评估（先评估，确保评分写入知识库）
            result['quality_score'] = self._evaluate_quality(
                teacher_result, result['extracted_rules']
            )
            print(f"   📊 质量评分: {result['quality_score']:.2f}")
            
            # 步骤4: 更新知识库
            self._update_knowledge_store(result, zhanshi)
            
            # 更新统计
            self.knowledge_store['distill_stats']['total_distillations'] += 1
            self.knowledge_store['distill_stats']['successful_distillations'] += 1
            self.knowledge_store['distill_stats']['knowledge_rules_extracted'] += len(result['extracted_rules'])
            self.knowledge_store['distill_stats']['template_updates'] += len(result['template_updates'])
            
            result['success'] = True
            
            # 记录蒸馏日志
            self._log_distillation(result, zhanshi)
            
            # 保存知识库
            self._save_knowledge_store()
            
            print(f"   🎉 蒸馏完成！")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ 蒸馏失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _teacher_reasoning(self, case: Dict, zhanshi: str = None) -> Dict:
        """
        教师模型推理
        
        使用 glm-5.3-flash 生成高质量推理链（启用思考模式）
        全程使用中文，输出结构化推理过程
        """
        try:
            prompt = self._build_teacher_prompt(case, zhanshi)
            
            from glm_service import GLMService
            
            svc = GLMService.ox_alpha()
            svc.set_model(TEACHER_MODEL)
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一位精通《大六壬断案疏正》的大六壬宗师。你必须用中文思考和输出。

核心要求：
1. 全程用中文推理，禁止使用英文
2. 基于传统六壬理论进行严谨推理：课体判定、三传分析、天将吉凶、六亲关系、毕法赋规则
3. 给出详细的类象关联（地支→事物象征、天将→吉凶含义）
4. 最终给出明确的吉凶判断和具体预测

分析步骤：
1. 首先确认课体名称和吉凶属性
2. 分析三传的生克关系和方向性
3. 分析十二天将的吉凶属性
4. 结合占事类型进行类象推理
5. 引用毕法赋条文辅助判断
6. 综合给出吉凶结论

输出必须严格使用以下格式（全部中文）：

【课体分析】
课体名称：XXX
课体吉凶：吉/凶/中平
三传分析：初传XXX，中传XXX，末传XXX，三传生克关系分析

【天将推理】
初传天将：XXX，吉凶判断
中传天将：XXX，吉凶判断
末传天将：XXX，吉凶判断

【类象关联】
初传类象：地支XXX象征XXX事物
中传类象：地支XXX象征XXX事物
末传类象：地支XXX象征XXX事物

【毕法赋规则】
命中规则：XXX
规则含义解释：XXX

【具体推断】
1. XXX
2. XXX
3. XXX

【吉凶结论】
总评：吉/凶/中平
置信度：高/中/低
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = svc.generate(
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                thinking=True,
                extra={"reasoning_effort": "low"}
            )
            
            if response.get('success'):
                content = response.get('content', '')
                reasoning_content = response.get('reasoning_content', '')
                
                full_reasoning = content
                if reasoning_content:
                    full_reasoning = f"[思考过程]\n{reasoning_content}\n\n[最终回答]\n{content}"
                
                return {
                    "success": True,
                    "reasoning": full_reasoning,
                    "content": content,
                    "reasoning_content": reasoning_content,
                    "model": TEACHER_MODEL
                }
            else:
                return {
                    "success": False,
                    "error": response.get('error', '教师模型调用失败')
                }
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"教师推理异常: {e}"
            }
    
    def _build_teacher_prompt(self, case: Dict, zhanshi: str = None) -> str:
        """构建教师模型 prompt - 清晰描述排盘格式"""
        sizhu = case.get('四柱', '')
        sike = case.get('四课', '')
        sanchuan = case.get('三传', '')
        keti = case.get('课体', '未知')
        actual_result = case.get('实际结果', '')
        
        prompt_parts = [
            "【大六壬排盘信息】",
            "",
            f"四柱（年月日时）：{sizhu}",
            "",
            f"四课（天盘/地盘 上神/下神）：{sike}",
            f"  说明：四课格式为「上神/下神」，第一课是干上神加日干，第二课是第一课上神的上神，",
            f"  第三课是支上神加日支，第四课是第三课上神的上神",
            "",
            f"三传（初中末）：{sanchuan}",
            f"  说明：三传是由四课推算出的初传、中传、末传",
            "",
            f"课体：{keti}",
        ]
        
        if zhanshi:
            prompt_parts.append(f"占事类型：{zhanshi}")
        
        if actual_result:
            prompt_parts.extend([
                "",
                f"【已知实际结果】：{actual_result}",
                "请结合实际结果，详细分析推理过程，说明哪些判断是关键的，哪些是可以省略的。"
            ])
        
        prompt_parts.extend([
            "",
            "请按照系统提示的格式，用中文进行完整的类象推理分析。",
            "重点关注：课体吉凶、三传生克、天将属性、类象关联、毕法赋命中。"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_knowledge(self, case: Dict, reasoning: str, 
                          zhanshi: str = None) -> Dict:
        """
        从推理链中提炼知识
        
        提取内容：
        1. 课体-吉凶映射
        2. 三传类象关联
        3. 天将吉凶模式
        4. 毕法赋规则
        5. 推理步骤模式
        """
        extracted = {
            "rules": [],
            "template_updates": {},
            "class_image_mappings": [],
            "reasoning_patterns": []
        }
        
        try:
            # 分离思考过程和最终回答
            thinking_content = ""
            final_content = reasoning
            if "[思考过程]" in reasoning and "[最终回答]" in reasoning:
                parts = reasoning.split("[最终回答]")
                thinking_part = parts[0]
                final_content = parts[1] if len(parts) > 1 else ""
                thinking_content = thinking_part.replace("[思考过程]", "").strip()
            
            # 合并思考过程和最终回答用于提取
            full_text = thinking_content + "\n" + final_content
            
            # 1. 提取课体-吉凶规则
            keti_patterns = [
                r'课体名称[：:]\s*(.+?)(?:\n|$)',
                r'课体吉凶[：:]\s*(吉|凶|中平)',
                r'总评[：:]\s*(吉|凶|中平)',
            ]
            keti_name = ""
            jixiong = ""
            for pat in [r'课体名称[：:]\s*(.+?)(?:\n|$)']:
                m = re.search(pat, final_content)
                if m:
                    keti_name = m.group(1).strip()
                    break
            for pat in [r'课体吉凶[：:]\s*(吉|凶|中平)', r'总评[：:]\s*(吉|凶|中平)']:
                m = re.search(pat, final_content)
                if m:
                    jixiong = m.group(1).strip()
                    break
            
            if keti_name and jixiong:
                extracted['rules'].append(f"课体{keti_name} → {jixiong}")
            
            # 2. 提取三传类象关联（新格式）
            sanchuan_positions = ['初传', '中传', '末传']
            for pos in sanchuan_positions:
                # 尝试匹配多种格式
                patterns = [
                    rf'{pos}类象[：:]\s*(.+?)(?:\n|$)',
                    rf'{pos}天将[：:]\s*(.+?)[，,](.+?)(?:\n|$)',
                    rf'{pos}[：:]\s*(\S+).*?类象[：:]\s*(.+?)(?:\n|$)',
                ]
                for pat in patterns:
                    m = re.search(pat, final_content)
                    if m:
                        mapping = {'position': pos}
                        if len(m.groups()) == 2:
                            mapping['zhi'] = m.group(1).strip()
                            mapping['class_image'] = m.group(2).strip()
                        elif len(m.groups()) == 1:
                            mapping['class_image'] = m.group(1).strip()
                        extracted['class_image_mappings'].append(mapping)
                        break
            
            # 3. 提取毕法赋规则
            bifa_patterns = [
                r'命中规则[：:]\s*(.+?)(?:\n|$)',
                r'毕法赋[：:]\s*(.+?)(?:\n|$)',
                r'引用[：:]\s*(.+?)(?:\n|$)',
            ]
            for pat in bifa_patterns:
                for m in re.finditer(pat, full_text):
                    rule = m.group(1).strip()
                    if rule and len(rule) > 5:
                        extracted['rules'].append(f"毕法赋: {rule}")
            
            # 4. 提取推理步骤（思考过程中的关键步骤）
            reasoning_steps = []
            # 从思考过程中提取关键推理
            step_patterns = [
                r'(首先|其次|然后|最后|关键|重要|注意|结论)[：:，,]\s*(.+?)(?:\n|$)',
                r'(\d+)[.、)）]\s*(.+?)(?:\n|$)',
                r'因为|由于|所以|因此|故[，,]\s*(.+?)(?:\n|$)',
            ]
            for pat in step_patterns:
                for m in re.finditer(pat, thinking_content or final_content):
                    step = m.group(m.lastindex).strip() if m.lastindex else m.group(0).strip()
                    if len(step) > 15:
                        reasoning_steps.append(step)
            
            # 去重并限制数量
            seen = set()
            unique_steps = []
            for s in reasoning_steps:
                if s not in seen:
                    seen.add(s)
                    unique_steps.append(s)
            extracted['reasoning_patterns'] = unique_steps[:8]
            
            # 5. 从天将推理中提取天将吉凶模式
            tianjiang_pattern = re.compile(
                r'(初传|中传|末传)天将[：:]\s*(\S+?)[，,]\s*(.+?)(?:\n|$)',
                re.DOTALL
            )
            for m in tianjiang_pattern.finditer(final_content):
                pos = m.group(1)
                tj = m.group(2)
                judgment = m.group(3).strip()
                extracted['rules'].append(f"{pos}{tj} → {judgment[:20]}")
            
            # 6. 构建模板更新
            if zhanshi and (extracted['reasoning_patterns'] or extracted['class_image_mappings']):
                template_update = {
                    'zhanshi': zhanshi,
                    'keti': keti_name,
                    'jixiong': jixiong,
                    'reasoning_steps': extracted['reasoning_patterns'],
                    'class_images': [m.get('class_image', '') for m in extracted['class_image_mappings'] if m.get('class_image')],
                    'tianjiang_patterns': [r for r in extracted['rules'] if '天将' in r],
                    'extracted_at': datetime.now().isoformat()
                }
                extracted['template_updates'][zhanshi] = template_update
            
            print(f"   - 提炼规则: {len(extracted['rules'])} 条")
            print(f"   - 类象映射: {len(extracted['class_image_mappings'])} 个")
            print(f"   - 推理模式: {len(extracted['reasoning_patterns'])} 步")
            
        except Exception as e:
            print(f"   ⚠️ 知识提炼异常: {e}")
            import traceback
            traceback.print_exc()
        
        return extracted
    
    def _extract_with_regex_fallback(self, content: str) -> Optional[Dict]:
        """
        正则兜底提取 - 当JSON解析失败时使用
        直接从文本中提取关键字段
        """
        try:
            extracted = {
                "keti_rules": [],
                "class_image_mappings": [],
                "tianjiang_patterns": [],
                "bifa_rules": [],
                "reasoning_steps": [],
                "jixiong_conclusion": "",
                "confidence": ""
            }
            
            # 提取课体规则
            keti_pat = r'"keti_rules"\s*:\s*\[(.*?)\]'
            m = re.search(keti_pat, content, re.DOTALL)
            if m:
                rules_text = m.group(1)
                extracted['keti_rules'] = re.findall(r'"([^"]+)"', rules_text)
            
            # 提取类象映射
            img_pat = r'"class_image_mappings"\s*:\s*\[(.*?)\](?:\s*,|[\s\n])'
            m = re.search(img_pat, content, re.DOTALL)
            if m:
                img_text = m.group(1)
                # 提取每个对象
                for obj_match in re.finditer(r'\{([^}]+)\}', img_text):
                    obj_str = obj_match.group(1)
                    mapping = {}
                    for field in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', obj_str):
                        mapping[field.group(1)] = field.group(2)
                    if mapping:
                        extracted['class_image_mappings'].append(mapping)
            
            # 提取天将模式
            tj_pat = r'"tianjiang_patterns"\s*:\s*\[(.*?)\](?:\s*,|[\s\n])'
            m = re.search(tj_pat, content, re.DOTALL)
            if m:
                tj_text = m.group(1)
                for obj_match in re.finditer(r'\{([^}]+)\}', tj_text):
                    obj_str = obj_match.group(1)
                    pattern = {}
                    for field in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', obj_str):
                        pattern[field.group(1)] = field.group(2)
                    if pattern:
                        extracted['tianjiang_patterns'].append(pattern)
            
            # 提取毕法规则
            bifa_pat = r'"bifa_rules"\s*:\s*\[(.*?)\]'
            m = re.search(bifa_pat, content, re.DOTALL)
            if m:
                bifa_text = m.group(1)
                extracted['bifa_rules'] = re.findall(r'"([^"]+)"', bifa_text)
            
            # 提取推理步骤
            step_pat = r'"reasoning_steps"\s*:\s*\[(.*?)\]'
            m = re.search(step_pat, content, re.DOTALL)
            if m:
                step_text = m.group(1)
                extracted['reasoning_steps'] = re.findall(r'"([^"]+)"', step_text)
            
            # 提取吉凶结论
            jixiong_pat = r'"jixiong_conclusion"\s*:\s*"([^"]*)"'
            m = re.search(jixiong_pat, content)
            if m:
                extracted['jixiong_conclusion'] = m.group(1)
            
            # 提取置信度
            conf_pat = r'"confidence"\s*:\s*"([^"]*)"'
            m = re.search(conf_pat, content)
            if m:
                extracted['confidence'] = m.group(1)
            
            # 检查是否有有效数据
            total = sum([
                len(extracted['keti_rules']),
                len(extracted['class_image_mappings']),
                len(extracted['tianjiang_patterns']),
                len(extracted['bifa_rules']),
                len(extracted['reasoning_steps'])
            ])
            
            if total > 0:
                return extracted
            return None
            
        except Exception:
            return None
    
    def _extract_knowledge_ai(self, case: Dict, reasoning: str,
                               zhanshi: str = None) -> Dict:
        """
        AI驱动的知识提取（使用 glm-4-flash 免费模型）
        
        分析教师模型的推理链，提取结构化知识：
        1. 课体-吉凶映射规则
        2. 三传类象关联
        3. 天将吉凶模式
        4. 毕法赋/古法规则
        5. 关键推理步骤
        """
        try:
            from glm_service import GLMService
            
            reasoning_preview = reasoning[:3000] if len(reasoning) > 3000 else reasoning
            
            prompt = f"""请分析以下大六壬推理链，提取结构化知识。

案例信息：
- 占事：{zhanshi or case.get('占事', '未知')}
- 课体：{case.get('课体', '未知')}
- 三传：{case.get('三传', '未知')}
- 实际结果：{case.get('实际结果', '未知')}

教师推理链：
{reasoning_preview}

请从推理链中提取以下内容（用中文回答）：

1. 【课体吉凶规则】：该课体的吉凶属性、适用场景
2. 【三传类象关联】：初传、中传、末传分别象征什么事物
3. 【天将吉凶模式】：各传上天将的吉凶判断
4. 【引用规则】：引用了哪些毕法赋或其他六壬规则
5. 【关键推理步骤】：3-5个关键推理步骤

请用以下JSON格式输出（严格遵守）：
```json
{{
  "keti_rules": ["课体名称 → 吉凶属性"],
  "class_image_mappings": [
    {{"position": "初传/中传/末传", "zhi": "地支", "symbol": "象征事物"}}
  ],
  "tianjiang_patterns": [
    {{"position": "初传/中传/末传", "tianjiang": "天将名", "judgment": "吉凶判断"}}
  ],
  "bifa_rules": ["引用的毕法赋条文"],
  "reasoning_steps": ["关键推理步骤1", "关键推理步骤2"],
  "jixiong_conclusion": "最终吉凶结论",
  "confidence": "高/中/低"
}}
```"""
            
            svc = GLMService.ox_alpha()
            svc.set_model(STUDENT_MODEL)  # 使用免费模型
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一位精通大六壬的知识提取专家。你的任务是从六壬推理链中提取结构化的知识规则。
要求：
1. 严格按照JSON格式输出
2. 提取的规则要具体、可复用
3. 用中文回答
4. 如果某项无法提取，填空数组或空字符串"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = svc.generate(
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            
            if response.get('success'):
                content = response.get('content', '')
                # 尝试解析JSON（容错处理）
                json_str = content
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0]
                
                json_str = json_str.strip()
                
                # 尝试多种解析策略
                extracted_data = None
                parse_error = None
                
                # 策略1: 直接解析
                try:
                    extracted_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    parse_error = e
                
                # 策略2: 尝试修复截断的JSON
                if extracted_data is None and parse_error:
                    try:
                        # 找到错误位置，尝试修复
                        error_pos = parse_error.pos
                        # 截断到错误位置附近，添加闭合括号
                        truncated = json_str[:error_pos]
                        # 尝试补全未闭合的结构
                        open_braces = truncated.count('{') - truncated.count('}')
                        open_brackets = truncated.count('[') - truncated.count(']')
                        if open_braces > 0 or open_brackets > 0:
                            fixed = truncated
                            # 先闭合字符串
                            if fixed.count('"') % 2 != 0:
                                fixed += '"'
                            # 闭合数组
                            for _ in range(open_brackets):
                                fixed += ']'
                            # 闭合对象
                            for _ in range(open_braces):
                                fixed += '}'
                            extracted_data = json.loads(fixed)
                            print(f"   🔧 JSON修复成功 (截断修复)")
                    except (json.JSONDecodeError, Exception):
                        pass
                
                # 策略3: 用正则直接提取字段
                if extracted_data is None:
                    print(f"   ⚠️ JSON解析失败，尝试正则提取...")
                    extracted_data = self._extract_with_regex_fallback(content)
                    if extracted_data:
                        print(f"   🔧 正则提取成功")
                
                if extracted_data:
                    print(f"   ✅ AI知识提取完成")
                    print(f"      - 课体规则: {len(extracted_data.get('keti_rules', []))} 条")
                    print(f"      - 类象映射: {len(extracted_data.get('class_image_mappings', []))} 个")
                    print(f"      - 天将模式: {len(extracted_data.get('tianjiang_patterns', []))} 个")
                    print(f"      - 毕法规则: {len(extracted_data.get('bifa_rules', []))} 条")
                    print(f"      - 推理步骤: {len(extracted_data.get('reasoning_steps', []))} 步")
                    
                    # 转换为统一格式
                    rules = []
                    rules.extend(extracted_data.get('keti_rules', []))
                    rules.extend([f"毕法赋: {r}" for r in extracted_data.get('bifa_rules', [])])
                    rules.extend([
                        f"{m.get('position', '')}{m.get('tianjiang', '')} → {m.get('judgment', '')}"
                        for m in extracted_data.get('tianjiang_patterns', [])
                    ])
                    
                    class_image_mappings = extracted_data.get('class_image_mappings', [])
                    reasoning_patterns = extracted_data.get('reasoning_steps', [])
                    
                    template_updates = {}
                    if zhanshi:
                        template_updates[zhanshi] = {
                            'zhanshi': zhanshi,
                            'keti': case.get('课体', ''),
                            'jixiong': extracted_data.get('jixiong_conclusion', ''),
                            'reasoning_steps': reasoning_patterns,
                            'class_images': [m.get('symbol', '') for m in class_image_mappings],
                            'tianjiang_patterns': [
                                f"{m.get('position', '')}{m.get('tianjiang', '')}"
                                for m in extracted_data.get('tianjiang_patterns', [])
                            ],
                            'confidence': extracted_data.get('confidence', '中'),
                            'extracted_at': datetime.now().isoformat()
                        }
                    
                    return {
                        "rules": rules,
                        "template_updates": template_updates,
                        "class_image_mappings": class_image_mappings,
                        "reasoning_patterns": reasoning_patterns,
                        "raw_extraction": extracted_data,
                        "method": "ai"
                    }
                    
                else:
                    print(f"   ⚠️ 未能提取有效数据")
                    return {"rules": [], "template_updates": {}, "class_image_mappings": [],
                            "reasoning_patterns": [], "method": "regex_fallback"}
            else:
                print(f"   ⚠️ AI提取调用失败: {response.get('error', 'unknown')}")
                return {"rules": [], "template_updates": {}, "class_image_mappings": [],
                        "reasoning_patterns": [], "method": "regex_fallback"}
                        
        except Exception as e:
            print(f"   ⚠️ AI知识提取异常: {e}")
            return {"rules": [], "template_updates": {}, "class_image_mappings": [],
                    "reasoning_patterns": [], "method": "regex_fallback"}
    
    def distill_case_batch(self, cases: List[Dict], zhanshi: str = None,
                             max_cases: int = 5) -> Dict:
        """
        批量蒸馏多个案例
        
        参数：
        cases: 案例列表
        zhanshi: 占事类型
        max_cases: 最大蒸馏数量
        
        返回：
        {
            "total": int,
            "successful": int,
            "failed": int,
            "results": List[Dict]
        }
        """
        results = []
        successful = 0
        failed = 0
        cases_to_process = cases[:max_cases]
        
        print(f"\n📦 开始批量蒸馏 ({len(cases_to_process)} 个案例)...")
        print(f"   占事: {zhanshi or '多类型'}")
        print(f"   最大数量: {max_cases}")
        
        for i, case in enumerate(cases_to_process):
            case_zhanshi = zhanshi or case.get('占事', '')
            print(f"\n--- 案例 {i+1}/{len(cases_to_process)} ---")
            
            try:
                result = self.distill_case(case, case_zhanshi)
                results.append({
                    'case_id': case.get('id', f'case_{i}'),
                    'success': result.get('success'),
                    'rules_count': len(result.get('extracted_rules', [])),
                    'quality_score': result.get('quality_score'),
                    'error': result.get('error')
                })
                if result.get('success'):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                results.append({
                    'case_id': case.get('id', f'case_{i}'),
                    'success': False,
                    'error': str(e)
                })
        
        summary = {
            'total': len(cases_to_process),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
        print(f"\n📊 批量蒸馏完成:")
        print(f"   总计: {summary['total']}")
        print(f"   成功: {successful}")
        print(f"   失败: {failed}")
        
        return summary
    
    def _update_knowledge_store(self, distill_result: Dict, 
                                zhanshi: str = None):
        """更新知识库"""
        # 1. 添加提炼的规则
        for rule in distill_result.get('extracted_rules', []):
            if rule not in self.knowledge_store['knowledge_rules']:
                self.knowledge_store['knowledge_rules'].append({
                    'rule': rule,
                    'source': 'distillation',
                    'zhanshi': zhanshi,
                    'created_at': datetime.now().isoformat()
                })
        
        # 2. 更新占事模板
        if zhanshi and zhanshi in distill_result.get('template_updates', {}):
            template_data = distill_result['template_updates'][zhanshi]
            
            if zhanshi not in self.knowledge_store['zanshi_templates']:
                self.knowledge_store['zanshi_templates'][zhanshi] = {
                    'reasoning_steps': [],
                    'class_images': [],
                    'update_count': 0,
                    'last_updated': None
                }
            
            zt = self.knowledge_store['zanshi_templates'][zhanshi]
            
            # 合并推理步骤（去重）
            existing_steps = set(zt.get('reasoning_steps', []))
            new_steps = [s for s in template_data.get('reasoning_steps', []) 
                        if s not in existing_steps]
            zt['reasoning_steps'].extend(new_steps)
            
            # 合并类象
            existing_images = set(zt.get('class_images', []))
            new_images = [img for img in template_data.get('class_images', []) 
                         if img not in existing_images]
            zt['class_images'].extend(new_images)
            
            zt['update_count'] += 1
            zt['last_updated'] = datetime.now().isoformat()
        
        # 3. 添加推理链
        if distill_result.get('teacher_reasoning'):
            reasoning_chain = {
                'zhanshi': zhanshi,
                'reasoning': distill_result['teacher_reasoning'],  # 保存完整推理链
                'reasoning_summary': distill_result['teacher_reasoning'][:300],  # 摘要
                'quality_score': distill_result.get('quality_score', 0),
                'extracted_by': distill_result.get('extraction_method', 'regex'),
                'created_at': datetime.now().isoformat()
            }
            self.knowledge_store['reasoning_chains'].append(reasoning_chain)
            
            # 只保留最近100条
            if len(self.knowledge_store['reasoning_chains']) > 100:
                self.knowledge_store['reasoning_chains'] = \
                    self.knowledge_store['reasoning_chains'][-100:]
    
    def _evaluate_quality(self, teacher_result: Dict, 
                          extracted_rules: List[str]) -> float:
        """
        评估蒸馏质量
        
        评分维度：
        1. 教师推理完整性 (0.3)
        2. 知识提炼数量 (0.4)
        3. 规则可复用性 (0.3)
        """
        score = 0.0
        
        # 1. 教师推理长度评分
        reasoning_len = len(teacher_result.get('reasoning', ''))
        if reasoning_len > 500:
            score += 0.3
        elif reasoning_len > 200:
            score += 0.2
        else:
            score += 0.1
        
        # 2. 提炼规则数量评分
        rules_count = len(extracted_rules)
        if rules_count >= 5:
            score += 0.4
        elif rules_count >= 3:
            score += 0.3
        elif rules_count >= 1:
            score += 0.2
        else:
            score += 0.1
        
        # 3. 规则类型多样性
        rule_types = set()
        for rule in extracted_rules:
            if '课体' in rule:
                rule_types.add('keti')
            elif '毕法赋' in rule:
                rule_types.add('bifa')
            elif '类象' in rule or '类神' in rule:
                rule_types.add('class_image')
        
        if len(rule_types) >= 2:
            score += 0.3
        elif len(rule_types) >= 1:
            score += 0.2
        else:
            score += 0.1
        
        return round(score, 2)
    
    def _log_distillation(self, result: Dict, zhanshi: str = None):
        """记录蒸馏日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'zhanshi': zhanshi,
            'success': result.get('success', False),
            'rules_extracted': len(result.get('extracted_rules', [])),
            'quality_score': result.get('quality_score', 0),
            'error': result.get('error')
        }
        self.distill_log.append(log_entry)
    
    def batch_distill(self, cases: List[Dict], 
                      zhanshi: str = None) -> Dict:
        """
        批量蒸馏
        
        参数：
        cases: 案例列表
        zhanshi: 统一占事类型（可选）
        
        返回：
        {
            "total": int,
            "successful": int,
            "failed": int,
            "results": List[Dict],
            "summary": Dict
        }
        """
        print(f"\n📦 开始批量蒸馏 ({len(cases)} 个案例)")
        print("=" * 60)
        
        results = []
        successful = 0
        failed = 0
        
        for i, case in enumerate(cases, 1):
            case_zhanshi = zhanshi or case.get('占事', None)
            print(f"\n📋 [{i}/{len(cases)}] {case_zhanshi or '未知'}")
            
            result = self.distill_case(case, case_zhanshi)
            results.append(result)
            
            if result.get('success'):
                successful += 1
            else:
                failed += 1
        
        # 汇总
        summary = {
            'total': len(cases),
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful / max(len(cases), 1) * 100, 1),
            'avg_quality_score': 0.0,
            'total_rules_extracted': 0
        }
        
        if successful > 0:
            quality_scores = [r.get('quality_score', 0) for r in results if r.get('success')]
            summary['avg_quality_score'] = round(sum(quality_scores) / len(quality_scores), 2)
            summary['total_rules_extracted'] = sum(
                len(r.get('extracted_rules', [])) for r in results if r.get('success')
            )
        
        print(f"\n{'=' * 60}")
        print(f"📊 批量蒸馏完成")
        print(f"   总数: {summary['total']}")
        print(f"   成功: {summary['successful']}")
        print(f"   失败: {summary['failed']}")
        print(f"   成功率: {summary['success_rate']}%")
        print(f"   平均质量: {summary['avg_quality_score']}")
        print(f"   提炼规则: {summary['total_rules_extracted']} 条")
        
        return {
            **summary,
            'results': results,
            'summary': summary
        }
    
    def get_knowledge_stats(self) -> Dict:
        """获取知识库统计"""
        stats = self.knowledge_store.get('distill_stats', {})
        
        # 计算各占事模板数量
        template_count = len(self.knowledge_store.get('zanshi_templates', {}))
        
        return {
            'version': self.knowledge_store.get('version', '1.0'),
            'created_at': self.knowledge_store.get('created_at'),
            'updated_at': self.knowledge_store.get('updated_at'),
            'distill_stats': stats,
            'knowledge_rules_count': len(self.knowledge_store.get('knowledge_rules', [])),
            'zanshi_template_count': template_count,
            'reasoning_chains_count': len(self.knowledge_store.get('reasoning_chains', [])),
            'quality_metrics': self.knowledge_store.get('quality_metrics', {})
        }
    
    def get_zanshi_knowledge(self, zhanshi: str) -> Dict:
        """获取指定占事的知识"""
        return self.knowledge_store.get('zanshi_templates', {}).get(zhanshi, {})
    
    def get_all_knowledge(self) -> Dict:
        """获取全部知识"""
        return self.knowledge_store.copy()


class TemplateUpdater:
    """模板更新器 - 将蒸馏知识应用到模板引擎"""
    
    def __init__(self, distill_engine: DistillationEngine):
        self.distill_engine = distill_engine
    
    def update_template_engine(self, template_engine) -> Dict:
        """
        用蒸馏知识更新模板引擎
        
        参数：
        template_engine: 模板引擎实例
        
        返回：
        更新结果
        """
        print(f"\n🔄 更新模板引擎知识...")
        
        update_result = {
            'templates_updated': 0,
            'rules_added': 0,
            'errors': []
        }
        
        try:
            knowledge = self.distill_engine.get_all_knowledge()
            
            # 1. 更新占事模板
            # 获取模板表：优先实例属性，回退到模块级 ZANSHI_TEMPLATES 变量
            try:
                zt_table = template_engine.ZANSHI_TEMPLATES
            except AttributeError:
                from engine.template_engine import ZANSHI_TEMPLATES as zt_table

            zanshi_templates = knowledge.get('zanshi_templates', {})
            for zhanshi, template_data in zanshi_templates.items():
                if zhanshi in zt_table:
                    existing = zt_table[zhanshi]
                    
                    # 合并推理步骤到 analysis_template
                    existing_steps = existing.get('analysis_template', '')
                    new_steps = template_data.get('reasoning_steps', [])
                    
                    if new_steps:
                        # 在模板中添加知识参考
                        knowledge_ref = f"\n\n【蒸馏知识补充】\n"
                        for i, step in enumerate(new_steps[:3], 1):
                            knowledge_ref += f"{i}. {step}\n"
                        
                        # 检查是否已添加
                        if '【蒸馏知识补充】' not in existing_steps:
                            existing['analysis_template'] += knowledge_ref
                            update_result['templates_updated'] += 1
                            print(f"   ✅ 更新模板: {zhanshi}")
            
            # 2. 添加知识规则到模板引擎
            knowledge_rules = knowledge.get('knowledge_rules', [])
            for rule_data in knowledge_rules[-10:]:  # 最近10条规则
                rule = rule_data.get('rule', '')
                if rule and hasattr(template_engine, 'additional_rules'):
                    template_engine.additional_rules.append(rule)
                    update_result['rules_added'] += 1
            
            print(f"   📊 更新模板: {update_result['templates_updated']} 个")
            print(f"   📊 添加规则: {update_result['rules_added']} 条")
            
        except Exception as e:
            update_result['errors'].append(str(e))
            print(f"   ❌ 更新失败: {e}")
        
        return update_result
    
    def validate_distillation_effect(self, test_cases: List[Dict],
                                      template_engine) -> Dict:
        """
        验证蒸馏效果
        
        对比蒸馏前后模板引擎的推理质量
        """
        print(f"\n🔬 验证蒸馏效果...")
        
        validation = {
            'test_cases': len(test_cases),
            'before_quality': 0.0,
            'after_quality': 0.0,
            'improvement': 0.0,
            'details': []
        }
        
        # 这里应该实现前后对比逻辑
        # 简化版本：直接测试当前模板引擎的表现
        
        for case in test_cases[:5]:  # 最多测试5个案例
            zhanshi = case.get('占事', '未知')
            paipan_data = {
                '四柱': case.get('四柱', ''),
                '四课': case.get('四课', ''),
                '三传': case.get('三传', ''),
                '课体': case.get('课体', '')
            }
            
            try:
                # 使用模板引擎推理
                result = template_engine.reason(zhanshi, paipan_data, {})
                validation['details'].append({
                    'zhanshi': zhanshi,
                    'success': result.get('success', False),
                    'confidence': result.get('confidence', 0)
                })
            except Exception as e:
                validation['details'].append({
                    'zhanshi': zhanshi,
                    'error': str(e)[:100]
                })
        
        # 计算平均质量
        confidences = [d['confidence'] for d in validation['details'] 
                      if 'confidence' in d]
        if confidences:
            validation['after_quality'] = round(sum(confidences) / len(confidences), 2)
        
        print(f"   📊 测试案例: {validation['test_cases']}")
        print(f"   📊 当前质量: {validation['after_quality']}")
        
        return validation


def create_distillation_engine() -> DistillationEngine:
    """创建蒸馏引擎实例"""
    return DistillationEngine()


if __name__ == '__main__':
    # 测试蒸馏引擎
    print("=" * 60)
    print("🧪 知识蒸馏引擎测试")
    print("=" * 60)
    
    engine = create_distillation_engine()
    
    # 打印初始状态
    stats = engine.get_knowledge_stats()
    print(f"\n📊 初始状态:")
    print(f"   知识库版本: {stats['version']}")
    print(f"   蒸馏总数: {stats['distill_stats']['total_distillations']}")
    print(f"   知识规则: {stats['knowledge_rules_count']} 条")
    print(f"   占事模板: {stats['zanshi_template_count']} 个")
    
    print("\n✅ 蒸馏引擎初始化成功！")


class KnowledgeOptimizer:
    """
    知识优化器 — 增强蒸馏引擎的规则管理和质量评估
    
    功能：
    1. 规则去重和合并
    2. 规则质量评分
    3. 生成质量改进报告
    4. 成本控制和预算管理
    """
    
    def __init__(self, distill_engine: DistillationEngine):
        self.engine = distill_engine
        self.optimization_log = []
    
    def deduplicate_rules(self) -> Dict:
        """
        规则去重和合并
        
        返回：
        {
            'duplicates_found': int,
            'rules_before': int,
            'rules_after': int,
            'merged_rules': List[Dict]
        }
        """
        print("\n🔍 开始规则去重...")
        
        rules = self.engine.knowledge_store.get('knowledge_rules', [])
        rules_before = len(rules)
        
        # 按占事分组
        zhanshi_groups = {}
        for rule in rules:
            zs = rule.get('zhanshi', '未知')
            rule_text = rule.get('rule', '')
            
            if zs not in zhanshi_groups:
                zhanshi_groups[zs] = []
            
            # 检查是否有重复规则
            is_duplicate = False
            for existing in zhanshi_groups[zs]:
                if rule_text == existing.get('rule', ''):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                zhanshi_groups[zs].append(rule)
        
        # 重新构建规则列表
        merged_rules = []
        duplicates_found = rules_before
        
        for zs, group in zhanshi_groups.items():
            merged_rules.extend(group)
        
        # 更新知识库
        self.engine.knowledge_store['knowledge_rules'] = merged_rules
        self.engine._save_knowledge_store()
        
        result = {
            'duplicates_found': rules_before - len(merged_rules),
            'rules_before': rules_before,
            'rules_after': len(merged_rules),
            'merged_rules': merged_rules
        }
        
        print(f"   📊 去重前: {rules_before} 条")
        print(f"   📊 去重后: {len(merged_rules)} 条")
        print(f"   📊 删除重复: {result['duplicates_found']} 条")
        
        self.optimization_log.append({
            'action': 'deduplicate',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def score_rule_quality(self, rule: str) -> float:
        """
        评估单条规则的质量
        
        评分维度：
        1. 具体性（是否可复用）
        2. 准确性（是否有明确判断）
        3. 完整性（是否包含充分信息）
        """
        score = 0.0
        
        # 具体性检查
        if len(rule) > 10:
            score += 0.2
        if len(rule) > 20:
            score += 0.1
        
        # 准确性检查（包含判断词）
        judgment_words = ['吉', '凶', '平', '利于', '不利', '主', '应', '宜', '忌']
        has_judgment = any(word in rule for word in judgment_words)
        if has_judgment:
            score += 0.3
        
        # 完整性检查（包含课体或规则引用）
        completeness_indicators = ['课', '格', '毕法', '赋', '规则', '法']
        has_structure = any(word in rule for word in completeness_indicators)
        if has_structure:
            score += 0.3
        
        # 可复用性（不是特定案例）
        if '案例' not in rule and '具体' not in rule:
            score += 0.2
        
        return min(score, 1.0)
    
    def generate_quality_report(self) -> Dict:
        """
        生成知识质量改进报告
        
        包含：
        1. 当前知识库状态
        2. 规则质量分布
        3. 模板覆盖度
        4. 改进建议
        """
        print("\n📊 生成质量改进报告...")
        
        rules = self.engine.knowledge_store.get('knowledge_rules', [])
        templates = self.engine.knowledge_store.get('zanshi_templates', {})
        chains = self.engine.knowledge_store.get('reasoning_chains', [])
        stats = self.engine.knowledge_store.get('distill_stats', {})
        
        # 计算规则质量分布
        # 评分标准：
        #   高质量: > 0.7 (包含0.7以上)
        #   中质量: 0.4 - 0.7 (包含0.4和0.7)
        #   低质量: < 0.4 (严格小于0.4)
        quality_distribution = {
            'high': 0,      # > 0.7
            'medium': 0,    # 0.4-0.7 (包含两端)
            'low': 0        # < 0.4
        }
        
        rule_details = []
        for rule in rules:
            quality_score = self.score_rule_quality(rule.get('rule', ''))
            
            if quality_score > 0.7:
                quality_distribution['high'] += 1
            elif quality_score >= 0.4:
                quality_distribution['medium'] += 1
            else:
                quality_distribution['low'] += 1
            
            rule_details.append({
                'rule': rule.get('rule', ''),
                'zhanshi': rule.get('zhanshi', ''),
                'quality_score': round(quality_score, 2)
            })
        
        # 计算模板覆盖度
        # 标准占事类型映射（模板名 → 标准名）
        zhanshi_mapping = {
            '求财': '求财', '婚姻': '婚姻', '出行': '出行', 
            '官讼': '官讼', '功名': '功名', '疾病': '疾病', 
            '家宅': '家宅', '流年': '流年', '终身': '终身',
            '占宅': '家宅', '占病': '疾病', '占财': '求财',
            '占婚': '婚姻', '占出行': '出行', '占官讼': '官讼'
        }
        known_zhanshi = ['求财', '婚姻', '出行', '官讼', '功名', '疾病', '家宅', '流年', '终身']
        covered_zhanshi = set()
        for template_key in templates.keys():
            # 映射到标准类型
            standard_name = zhanshi_mapping.get(template_key, template_key)
            covered_zhanshi.add(standard_name)
        coverage_rate = len(covered_zhanshi.intersection(known_zhanshi)) / len(known_zhanshi) * 100
        
        # 生成改进建议
        suggestions = []
        
        if quality_distribution['low'] > 0:
            suggestions.append(f"建议优化 {quality_distribution['low']} 条低质量规则")
        
        if coverage_rate < 50:
            suggestions.append(f"模板覆盖率较低({coverage_rate:.1f}%)，建议扩展到更多占事类型")
        
        if stats.get('total_distillations', 0) < 10:
            suggestions.append("蒸馏案例数量不足，建议继续积累更多案例")
        
        if len(chains) < 5:
            suggestions.append("推理链存储较少，建议保存更多高质量推理链")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'current_state': {
                'total_rules': len(rules),
                'total_templates': len(templates),
                'total_chains': len(chains),
                'total_distillations': stats.get('total_distillations', 0)
            },
            'quality_distribution': quality_distribution,
            'template_coverage': {
                'known_types': len(known_zhanshi),
                'covered_types': len(covered_zhanshi),
                'coverage_rate': round(coverage_rate, 1)
            },
            'low_quality_rules': [
                r for r in rule_details 
                if r['quality_score'] < 0.4
            ][:10],  # 最多显示10条
            'suggestions': suggestions,
            'score_details': rule_details
        }
        
        print(f"   📊 规则总数: {len(rules)}")
        print(f"   📊 高质量: {quality_distribution['high']} 条")
        print(f"   📊 中质量: {quality_distribution['medium']} 条")
        print(f"   📊 低质量: {quality_distribution['low']} 条")
        print(f"   📊 模板覆盖率: {coverage_rate:.1f}%")
        
        if suggestions:
            print(f"   💡 改进建议:")
            for suggestion in suggestions:
                print(f"      - {suggestion}")
        
        # 保存报告
        report_file = os.path.join(self.engine.distill_dir, 'quality_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   📝 报告已保存: {report_file}")
        
        self.optimization_log.append({
            'action': 'generate_report',
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        
        return report
    
    def estimate_distillation_cost(self, case_count: int, 
                                    teacher_tokens_per_case: int = 2000,
                                    student_tokens_per_case: int = 1000) -> Dict:
        """
        估算蒸馏成本
        
        参数：
        case_count: 案例数量
        teacher_tokens_per_case: 教师模型每个案例消耗的token数
        student_tokens_per_case: 学生模型每个案例消耗的token数
        
        返回：
        {
            'teacher_tokens': int,
            'student_tokens': int,
            'estimated_cost_cny': float,
            'cost_breakdown': Dict
        }
        """
        # glm-5.3-flash 价格（假设）: 0.002元/1000tokens
        # glm-4-flash 价格（假设）: 免费或极低成本
        
        teacher_cost_per_1k = 0.002  # 元
        student_cost_per_1k = 0.0  # 免费模型
        
        teacher_tokens = case_count * teacher_tokens_per_case
        student_tokens = case_count * student_tokens_per_case
        
        teacher_cost = (teacher_tokens / 1000) * teacher_cost_per_1k
        student_cost = (student_tokens / 1000) * student_cost_per_1k
        
        total_cost = teacher_cost + student_cost
        
        result = {
            'case_count': case_count,
            'teacher_tokens': teacher_tokens,
            'student_tokens': student_tokens,
            'teacher_cost_cny': round(teacher_cost, 4),
            'student_cost_cny': round(student_cost, 4),
            'estimated_cost_cny': round(total_cost, 4),
            'cost_breakdown': {
                'teacher_model': {
                    'model': TEACHER_MODEL,
                    'tokens': teacher_tokens,
                    'cost_per_1k': teacher_cost_per_1k,
                    'total_cost': round(teacher_cost, 4)
                },
                'student_model': {
                    'model': STUDENT_MODEL,
                    'tokens': student_tokens,
                    'cost_per_1k': student_cost_per_1k,
                    'total_cost': round(student_cost, 4)
                }
            }
        }
        
        print(f"\n💰 蒸馏成本估算 ({case_count} 个案例):")
        print(f"   教师模型 ({TEACHER_MODEL}):")
        print(f"     - Token数: {teacher_tokens:,}")
        print(f"     - 预估成本: ¥{teacher_cost:.4f}")
        print(f"   学生模型 ({STUDENT_MODEL}):")
        print(f"     - Token数: {student_tokens:,}")
        print(f"     - 预估成本: ¥{student_cost:.4f}")
        print(f"   总计预估成本: ¥{total_cost:.4f}")
        
        return result
    
    def get_optimization_summary(self) -> Dict:
        """获取优化历史摘要"""
        return {
            'total_optimizations': len(self.optimization_log),
            'actions': [log['action'] for log in self.optimization_log],
            'last_optimization': self.optimization_log[-1] if self.optimization_log else None
        }


if __name__ == '__main__':
    # 测试知识优化器
    print("=" * 60)
    print("🧹 知识优化器测试")
    print("=" * 60)
    
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    
    # 1. 规则去重
    dedup_result = optimizer.deduplicate_rules()
    print(f"\n去重结果: {dedup_result['duplicates_found']} 条重复已删除")
    
    # 2. 生成质量报告
    report = optimizer.generate_quality_report()
    print(f"\n质量报告已生成")
    
    # 3. 成本估算
    cost = optimizer.estimate_distillation_cost(5)
    print(f"\n5个案例预估成本: ¥{cost['estimated_cost_cny']:.4f}")
    
    print("\n✅ 知识优化器测试完成！")
