#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识融合引擎 (DistillFusion) — Phase 5

核心功能：
1. 将知识蒸馏引擎提取的规则和模板融合到现有模板引擎中
2. 增强模板推理能力，利用蒸馏知识提升glm-4-flash的推理质量
3. 支持增量融合和全量融合
4. 融合后验证模板引擎的推理效果

融合策略：
- 规则注入：将蒸馏规则添加到模板的system_prompt中作为参考知识
- 推理步骤增强：将蒸馏的reasoning_steps整合到analysis_template中
- 类象关联：将蒸馏的class_images作为额外参考注入
- 动态更新：支持运行时融合，不需要修改源码
"""

import json
import os
import sys
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from copy import deepcopy

# 确保可以导入项目模块
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 知识库路径
KNOWLEDGE_STORE_PATH = os.path.join(_ROOT, "data", "distillation", "knowledge_store.json")

# 占事类型映射（知识库名称 → 模板引擎名称）
ZHANSHI_MAPPING = {
    "占宅": "求财",      # 占宅映射到求财模板
    "占病": "疾病",      # 占病映射到疾病模板
    "婚姻": "婚姻",      # 直接映射
    "出行": "出行",      # 直接映射
    "官讼": "官讼",      # 直接映射
    "功名": "功名",      # 直接映射
    "求财": "求财",      # 直接映射
    "疾病": "疾病",      # 直接映射
}


class DistillFusion:
    """知识融合引擎"""
    
    def __init__(self):
        self.knowledge_store = self._load_knowledge_store()
        self.fusion_log = []
        self.fused_templates = {}  # 融合后的模板缓存
        self._init_stats()
    
    def _init_stats(self):
        """初始化统计信息"""
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "total_rules": 0,
            "total_templates": 0,
            "rules_injected": 0,
            "templates_updated": 0,
            "zhanshi_coverage": {},
            "fusion_duration_ms": 0,
        }
    
    def _load_knowledge_store(self) -> Dict:
        """加载知识库"""
        if not os.path.exists(KNOWLEDGE_STORE_PATH):
            print(f"⚠️ 知识库文件不存在: {KNOWLEDGE_STORE_PATH}")
            return {
                "knowledge_rules": [],
                "zanshi_templates": {},
                "reasoning_chains": [],
            }
        
        try:
            with open(KNOWLEDGE_STORE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 已加载知识库: {len(data.get('knowledge_rules', []))} 条规则, "
                  f"{len(data.get('zanshi_templates', {}))} 个模板")
            return data
        except Exception as e:
            print(f"❌ 加载知识库失败: {e}")
            return {
                "knowledge_rules": [],
                "zanshi_templates": {},
                "reasoning_chains": [],
            }
    
    def get_rules_by_zhanshi(self, zhanshi: str) -> List[Dict]:
        """按占事类型获取规则"""
        rules = self.knowledge_store.get("knowledge_rules", [])
        zhanshi_rules = [r for r in rules if r.get("zhanshi") == zhanshi]
        return zhanshi_rules
    
    def get_template_by_zhanshi(self, zhanshi: str) -> Optional[Dict]:
        """按占事类型获取模板"""
        templates = self.knowledge_store.get("zanshi_templates", {})
        return templates.get(zhanshi)
    
    def get_mapped_zhanshi(self, knowledge_zhanshi: str) -> str:
        """获取映射后的占事类型"""
        return ZHANSHI_MAPPING.get(knowledge_zhanshi, knowledge_zhanshi)
    
    def analyze_fusion_opportunities(self) -> Dict:
        """分析融合机会"""
        print("\n" + "=" * 60)
        print("📊 融合机会分析")
        print("=" * 60)
        
        # 获取现有模板引擎的占事类型
        try:
            from engine.template_engine import ZANSHI_TEMPLATES
            template_zhanshi = set(ZANSHI_TEMPLATES.keys())
        except Exception:
            template_zhanshi = {"求财", "婚姻", "疾病", "出行", "官讼", "功名"}
        
        # 分析知识库覆盖的占事类型
        knowledge_zhanshi = set()
        for rule in self.knowledge_store.get("knowledge_rules", []):
            knowledge_zhanshi.add(rule.get("zhanshi", ""))
        
        # 映射分析
        mapped_zhanshi = set()
        unmapped_zhanshi = set()
        for kz in knowledge_zhanshi:
            mapped = self.get_mapped_zhanshi(kz)
            if mapped in template_zhanshi:
                mapped_zhanshi.add(mapped)
            else:
                unmapped_zhanshi.add(kz)
        
        # 统计
        result = {
            "template_zhanshi": list(template_zhanshi),
            "knowledge_zhanshi": list(knowledge_zhanshi),
            "mapped_zhanshi": list(mapped_zhanshi),
            "unmapped_zhanshi": list(unmapped_zhanshi),
            "coverage_rate": len(mapped_zhanshi) / max(len(template_zhanshi), 1),
            "details": {},
        }
        
        # 详细分析每个占事类型
        for zs in template_zhanshi:
            # 查找对应的知识库占事
            knowledge_zs = None
            for k, v in ZHANSHI_MAPPING.items():
                if v == zs:
                    knowledge_zs = k
                    break
            
            rules = self.get_rules_by_zhanshi(knowledge_zs) if knowledge_zs else []
            tmpl = self.get_template_by_zhanshi(knowledge_zs) if knowledge_zs else None
            
            result["details"][zs] = {
                "knowledge_mapped": knowledge_zs is not None,
                "rule_count": len(rules),
                "has_template": tmpl is not None,
                "has_reasoning_steps": tmpl is not None and len(tmpl.get("reasoning_steps", [])) > 0,
                "has_class_images": tmpl is not None and len(tmpl.get("class_images", [])) > 0,
            }
        
        # 打印结果
        print(f"\n📋 模板引擎支持的占事类型 ({len(template_zhanshi)} 种):")
        for zs in sorted(template_zhanshi):
            detail = result["details"].get(zs, {})
            flag = "✅" if detail.get("knowledge_mapped") else "❌"
            print(f"   {flag} {zs}: {detail.get('rule_count', 0)} 条规则, "
                  f"{'有' if detail.get('has_template') else '无'}模板")
        
        print(f"\n📈 知识库覆盖率: {result['coverage_rate']*100:.1f}%")
        print(f"📝 已映射: {len(mapped_zhanshi)} 种, 未映射: {len(unmapped_zhanshi)} 种")
        
        return result
    
    def fuse_knowledge_to_template(self, zhanshi: str, 
                                    template_data: Dict) -> Dict:
        """将知识库融合到单个模板"""
        mapped_zhanshi = None
        for k, v in ZHANSHI_MAPPING.items():
            if v == zhanshi:
                mapped_zhanshi = k
                break
        
        if not mapped_zhanshi:
            return template_data
        
        # 获取相关知识
        rules = self.get_rules_by_zhanshi(mapped_zhanshi)
        distill_template = self.get_template_by_zhanshi(mapped_zhanshi)
        
        if not rules and not distill_template:
            return template_data
        
        # 创建副本以避免修改原始数据
        fused = deepcopy(template_data)
        
        # 1. 融合规则到system_prompt
        if rules:
            rule_text = self._format_rules_for_prompt(rules)
            if rule_text:
                # 在核心原则后添加蒸馏知识
                original_prompt = fused.get("system_prompt", "")
                if "【蒸馏知识】" not in original_prompt:
                    # 找到核心原则的结束位置
                    insertion_point = self._find_insertion_point(original_prompt)
                    if insertion_point > 0:
                        fused["system_prompt"] = (
                            original_prompt[:insertion_point] + "\n\n" +
                            rule_text + "\n\n" +
                            original_prompt[insertion_point:]
                        )
        
        # 2. 融合推理步骤到analysis_template
        if distill_template and distill_template.get("reasoning_steps"):
            steps_text = self._format_reasoning_steps(distill_template["reasoning_steps"])
            if steps_text:
                original_analysis = fused.get("analysis_template", "")
                # 在推理步骤前添加蒸馏推理参考
                if "【蒸馏推理参考】" not in original_analysis:
                    fused["analysis_template"] = steps_text + "\n\n" + original_analysis
        
        # 3. 融合类象到system_prompt（如果有）
        if distill_template and distill_template.get("class_images"):
            class_text = self._format_class_images(distill_template["class_images"])
            if class_text:
                fused["system_prompt"] += "\n\n" + class_text
        
        return fused
    
    def _format_rules_for_prompt(self, rules: List[Dict]) -> str:
        """格式化规则用于prompt"""
        rule_lines = []
        for rule in rules[:10]:  # 最多取10条规则
            rule_text = rule.get("rule", "")
            if rule_text:
                rule_lines.append(f"- {rule_text}")
        
        if not rule_lines:
            return ""
        
        return f"【蒸馏知识】\n以下是从历史案例蒸馏提取的经验规则，请在推理时参考：\n" + "\n".join(rule_lines)
    
    def _format_reasoning_steps(self, steps: List[str]) -> str:
        """格式化推理步骤"""
        if not steps:
            return ""
        
        unique_steps = list(dict.fromkeys(steps))[:8]  # 去重，最多8步
        step_lines = [f"{i+1}. {step}" for i, step in enumerate(unique_steps)]
        
        return "【蒸馏推理参考】\n以下是历史案例验证的推理步骤，请作为分析参考：\n" + "\n".join(step_lines)
    
    def _format_class_images(self, class_images: List[str]) -> str:
        """格式化类象关联"""
        if not class_images:
            return ""
        
        unique_images = list(dict.fromkeys(class_images))[:6]  # 去重，最多6个
        image_lines = [f"- {img}" for img in unique_images]
        
        return "【关键类象】\n以下是本占事类型的关键类象关联：\n" + "\n".join(image_lines)
    
    def _find_insertion_point(self, text: str) -> int:
        """找到插入点（核心原则之后）"""
        # 查找核心原则的结束
        patterns = [
            r'4\. ',  # 第4条原则
            r'【核心原则】\n',
            r'规则',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # 找到该段的结束
                pos = match.end()
                # 找到下一个换行或空行
                next_newline = text.find('\n\n', pos)
                if next_newline > 0:
                    return next_newline
        
        # 默认在第一段落之后
        first_newline = text.find('\n\n')
        return first_newline if first_newline > 0 else len(text)
    
    def perform_full_fusion(self) -> Dict:
        """执行全量融合"""
        print("\n" + "=" * 60)
        print("🔄 开始全量知识融合")
        print("=" * 60)
        
        start_time = time.time()
        
        # 分析融合机会
        analysis = self.analyze_fusion_opportunities()
        
        # 加载模板引擎
        try:
            from engine.template_engine import ZANSHI_TEMPLATES
            templates_to_fuse = deepcopy(ZANSHI_TEMPLATES)
        except Exception as e:
            print(f"⚠️ 无法加载模板引擎: {e}")
            return self._build_fusion_result(success=False, error=str(e))
        
        # 融合每个占事类型
        fused_count = 0
        for zhanshi, template_data in templates_to_fuse.items():
            fused_template = self.fuse_knowledge_to_template(zhanshi, template_data)
            
            # 检查是否实际发生了融合
            if self._has_fusion_effect(template_data, fused_template):
                self.fused_templates[zhanshi] = fused_template
                fused_count += 1
                print(f"   ✅ 已融合: {zhanshi}")
            else:
                self.fused_templates[zhanshi] = template_data
                print(f"   ⚪ 无变化: {zhanshi}")
        
        # 应用融合后的模板到模板引擎
        fusion_applied = self._apply_fused_templates()
        
        # 计算耗时
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 构建结果
        result = {
            "success": fusion_applied > 0,
            "analysis": analysis,
            "fused_count": fused_count,
            "total_templates": len(templates_to_fuse),
            "fusion_applied": fusion_applied,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.fusion_log.append(result)
        
        # 打印总结
        print("\n" + "-" * 60)
        print(f"📊 融合完成: {fused_count}/{len(templates_to_fuse)} 个模板已融合")
        print(f"⏱️  耗时: {duration_ms}ms")
        print("-" * 60)
        
        return result
    
    def _has_fusion_effect(self, original: Dict, fused: Dict) -> bool:
        """检查融合是否产生了效果"""
        # 比较system_prompt
        if original.get("system_prompt", "") != fused.get("system_prompt", ""):
            return True
        
        # 比较analysis_template
        if original.get("analysis_template", "") != fused.get("analysis_template", ""):
            return True
        
        return False
    
    def _apply_fused_templates(self) -> int:
        """应用融合后的模板"""
        if not self.fused_templates:
            return 0
        
        try:
            from engine.template_engine import ZANSHI_TEMPLATES
            
            applied_count = 0
            for zhanshi, fused_data in self.fused_templates.items():
                if zhanshi in ZANSHI_TEMPLATES:
                    # 更新模板
                    ZANSHI_TEMPLATES[zhanshi] = fused_data
                    applied_count += 1
            
            print(f"✅ 已应用 {applied_count} 个融合模板到模板引擎")
            return applied_count
            
        except Exception as e:
            print(f"❌ 应用融合模板失败: {e}")
            return 0
    
    def perform_incremental_fusion(self, zhanshi_list: List[str]) -> Dict:
        """执行增量融合（仅融合指定占事类型）"""
        print(f"\n🔄 开始增量融合: {zhanshi_list}")
        
        try:
            from engine.template_engine import ZANSHI_TEMPLATES
            
            fused_count = 0
            for zhanshi in zhanshi_list:
                if zhanshi in ZANSHI_TEMPLATES:
                    original = ZANSHI_TEMPLATES[zhanshi]
                    fused = self.fuse_knowledge_to_template(zhanshi, original)
                    
                    if self._has_fusion_effect(original, fused):
                        ZANSHI_TEMPLATES[zhanshi] = fused
                        self.fused_templates[zhanshi] = fused
                        fused_count += 1
                        print(f"   ✅ 已融合: {zhanshi}")
                    else:
                        print(f"   ⚪ 无新变化: {zhanshi}")
                else:
                    print(f"   ❓ 未知占事类型: {zhanshi}")
            
            return {
                "success": True,
                "fused_count": fused_count,
                "requested": len(zhanshi_list),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_fusion_status(self) -> Dict:
        """获取融合状态"""
        return {
            "has_knowledge_store": len(self.knowledge_store.get("knowledge_rules", [])) > 0,
            "knowledge_rules_count": len(self.knowledge_store.get("knowledge_rules", [])),
            "knowledge_templates_count": len(self.knowledge_store.get("zanshi_templates", {})),
            "fused_templates_count": len(self.fused_templates),
            "fusion_history": len(self.fusion_log),
            "last_fusion": self.fusion_log[-1] if self.fusion_log else None,
        }
    
    def generate_fusion_report(self) -> Dict:
        """生成融合报告"""
        report = {
            "report_time": datetime.now().isoformat(),
            "knowledge_summary": {
                "total_rules": len(self.knowledge_store.get("knowledge_rules", [])),
                "total_templates": len(self.knowledge_store.get("zanshi_templates", {})),
                "reasoning_chains": len(self.knowledge_store.get("reasoning_chains", [])),
            },
            "fusion_summary": self.get_fusion_status(),
            "details": [],
        }
        
        # 详细的融合信息
        for zhanshi in ["求财", "婚姻", "疾病", "出行", "官讼", "功名"]:
            mapped = self.get_mapped_zhanshi(zhanshi)
            rules = self.get_rules_by_zhanshi(mapped) if mapped != zhanshi else self.get_rules_by_zhanshi(zhanshi)
            tmpl = self.get_template_by_zhanshi(mapped) if mapped != zhanshi else self.get_template_by_zhanshi(zhanshi)
            
            report["details"].append({
                "zhanshi": zhanshi,
                "knowledge_mapped": mapped != zhanshi,
                "knowledge_zhanshi": mapped,
                "rule_count": len(rules),
                "has_template": tmpl is not None,
                "reasoning_steps_count": len(tmpl.get("reasoning_steps", [])) if tmpl else 0,
                "class_images_count": len(tmpl.get("class_images", [])) if tmpl else 0,
                "fused": zhanshi in self.fused_templates,
            })
        
        return report


# 便捷函数
def create_fusion_engine() -> DistillFusion:
    """创建融合引擎实例"""
    return DistillFusion()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 知识融合引擎测试")
    print("=" * 60)
    
    engine = create_fusion_engine()
    
    # 分析融合机会
    analysis = engine.analyze_fusion_opportunities()
    
    # 执行全量融合
    result = engine.perform_full_fusion()
    
    # 生成报告
    report = engine.generate_fusion_report()
    
    print("\n" + "=" * 60)
    print("📋 融合报告摘要")
    print("=" * 60)
    print(f"   知识库规则: {report['knowledge_summary']['total_rules']} 条")
    print(f"   知识库模板: {report['knowledge_summary']['total_templates']} 个")
    print(f"   成功融合: {result.get('fused_count', 0)} 个模板")
    print(f"   融合耗时: {result.get('duration_ms', 0)} ms")
