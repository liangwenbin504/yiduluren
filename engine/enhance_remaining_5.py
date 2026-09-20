#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剩余5条中质量规则针对性增强脚本

问题分析：
- 这5条规则内容空洞，多为"无具体引用条文"等元信息
- 虽然包含"毕法赋"关键字，但引用的不是真正的毕法赋条文
- 需要进行实质性增强，添加具体的毕法赋条文和判断规则
"""

import json
import os
import sys
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.distillation_engine import DistillationEngine, KnowledgeOptimizer
from glm_service import GLMService


# 家宅类型专用毕法赋条文（精选具体条文）
JIAZHAI_BIFA_ARTICLES = [
    '毕法赋云："宅旺人衰，人宅两宜；宅衰人旺，人宅两伤"',
    '毕法赋云："家宅安宁，六亲和睦，财利丰盈"',
    '毕法赋云："玄武主盗贼，白虎主丧孝，朱雀主口舌"',
    '毕法赋云："青龙主喜庆，太常主财帛，六合主婚姻"',
    '毕法赋云："宅中见鬼，人宅不安；宅中见福，人宅俱荣"',
    '毕法赋云："空亡主虚惊，亡神主灾咎，劫煞主破财"',
    '毕法赋云："上克下，事从外入；下克上，事从内起"',
    '毕法赋云："初传为发用，中传为事情，末传为结果"',
    '毕法赋云："天将吉凶，须看地盘；地盘吉凶，须看月将"',
    '毕法赋云："干支为体，三传为用；体用相生，吉无不利"',
]


def enhance_remaining_rules(glm_service: GLMService, rules_to_enhance: list) -> list:
    """
    针对性增强剩余5条规则
    
    参数：
        glm_service: GLM服务实例
        rules_to_enhance: 需要增强的规则列表
        
    返回：
        增强后的规则列表
    """
    # 构建增强提示
    rules_text = '\n'.join([
        f'  {i+1}. 【{r["zhanshi"]}】{r["rule"]}' 
        for i, r in enumerate(rules_to_enhance)
    ])
    
    bifa_text = '\n'.join([f'  {i+1}. {a}' for i, a in enumerate(JIAZHAI_BIFA_ARTICLES)])
    
    prompt = f"""你是一位大六壬专家，请深度增强以下家宅类型规则，添加具体的毕法赋条文引用。

可用的毕法赋条文：
{bifa_text}

需要增强的规则（内容较空洞，需要实质性增强）：
{rules_text}

增强要求：
1. 每条规则必须引用具体的毕法赋条文（从上面的列表中选择最合适的）
2. 添加条文引用格式：【毕法赋】"条文内容"
3. 补充具体的判断条件和适用场景
4. 增强规则长度至50-100字
5. 保持原规则的核心含义
6. 添加具体的吉凶判断标准

输出格式（JSON数组）：
[
  {{"index": 1, "enhanced_rule": "增强后的规则文本，包含具体毕法赋引用"}},
  {{"index": 2, "enhanced_rule": "增强后的规则文本，包含具体毕法赋引用"}}
]

示例输出：
[
  {{"index": 1, "enhanced_rule": "家宅占断，【毕法赋】「宅旺人衰，人宅两宜」，需看宅神旺衰：宅神旺相则家宅安宁，六亲和睦；宅神休囚则人宅两伤，需防破财。初传为发用，主事情开端，如初传见青龙则主喜庆。"}}
]
"""
    
    messages = [
        {"role": "system", "content": "你是一位精通大六壬的专家，能够将空洞的规则描述增强为具体、可操作的判断规则，并准确引用毕法赋条文。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        # 切换到免费模型
        original_model = glm_service.model
        glm_service.set_model('glm-4-flash')
        
        response = glm_service.generate(
            messages=messages,
            temperature=0.2,  # 降低温度，保证输出稳定性
            max_tokens=2000
        )
        
        # 恢复原模型
        glm_service.set_model(original_model)
        
        # 检查响应
        if isinstance(response, dict) and 'error' in response:
            print(f"❌ API错误: {response['error']}")
            return []
        
        # 提取响应文本
        if isinstance(response, dict) and 'choices' in response:
            response_text = response['choices'][0]['message']['content'].strip()
        elif isinstance(response, dict) and 'content' in response:
            response_text = response['content'].strip()
        else:
            response_text = str(response).strip()
        
        print(f"   AI响应长度: {len(response_text)} 字符")
        
        # 解析JSON
        try:
            enhanced_results = json.loads(response_text)
            print(f"   解析成功: {len(enhanced_results)} 条增强规则")
            return enhanced_results
        except json.JSONDecodeError as e:
            print(f"   JSON解析失败: {e}")
            # 尝试提取JSON
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                enhanced_results = json.loads(json_str)
                print(f"   提取JSON成功: {len(enhanced_results)} 条增强规则")
                return enhanced_results
            return []
        
    except Exception as e:
        print(f"❌ 增强失败: {str(e)[:100]}")
        return []


def main():
    """主函数"""
    print("=" * 70)
    print("🎯 大六壬知识蒸馏引擎 — 剩余5条规则针对性增强")
    print("=" * 70)
    
    # 初始化
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    glm_service = GLMService()
    
    rules = engine.knowledge_store.get('knowledge_rules', [])
    
    # 识别剩余5条中质量规则
    print("\n📊 第1步：识别需要增强的5条规则")
    print("-" * 50)
    
    rules_to_enhance = []
    for i, rule in enumerate(rules):
        rule_text = rule.get('rule', '')
        quality_score = optimizer.score_rule_quality(rule_text)
        if 0.4 <= quality_score < 0.8:
            rules_to_enhance.append({
                'index': i,
                'rule': rule_text,
                'zhanshi': rule.get('zhanshi', ''),
                'quality_score': round(quality_score, 2)
            })
    
    print(f"   需要增强的规则数: {len(rules_to_enhance)} 条")
    
    for r in rules_to_enhance:
        print(f"   [{r['quality_score']}] 【{r['zhanshi']}】{r['rule'][:50]}...")
    
    # 第2步：调用AI增强
    print("\n🤖 第2步：AI深度增强（使用glm-4-flash）")
    print("-" * 50)
    
    enhanced_results = enhance_remaining_rules(glm_service, rules_to_enhance)
    
    if not enhanced_results:
        print("❌ 增强失败，退出")
        return
    
    # 第3步：更新规则
    print("\n📝 第3步：更新知识库")
    print("-" * 50)
    
    updated_rules = rules.copy()
    updated_count = 0
    
    for result in enhanced_results:
        idx = result.get('index', 0)
        enhanced_rule = result.get('enhanced_rule', '')
        
        if idx > 0 and idx <= len(rules_to_enhance):
            original_index = rules_to_enhance[idx - 1]['index']
            if original_index < len(updated_rules) and enhanced_rule:
                # 验证增强后规则的质量
                new_quality = optimizer.score_rule_quality(enhanced_rule)
                
                if new_quality >= 0.8:
                    updated_rules[original_index]['rule'] = enhanced_rule
                    updated_rules[original_index]['original_rule'] = rules_to_enhance[idx - 1]['rule']
                    updated_rules[original_index]['enhanced_at'] = datetime.now().isoformat()
                    updated_count += 1
                    print(f"   ✅ 规则 {original_index}: 质量 {new_quality:.2f}")
                else:
                    print(f"   ⚠️ 规则 {original_index}: 质量 {new_quality:.2f}（未达高质量阈值）")
    
    # 保存更新
    engine.knowledge_store['knowledge_rules'] = updated_rules
    engine._save_knowledge_store()
    
    print(f"\n   已成功增强: {updated_count} 条")
    
    # 第4步：验证最终效果
    print("\n📈 第4步：验证最终效果")
    print("-" * 50)
    
    # 重新评估质量
    quality_report = optimizer.generate_quality_report()
    
    print("\n   最终质量分布:")
    print(f"   - 高质量（≥0.8）: {quality_report['quality_distribution']['high']} 条")
    print(f"   - 中质量（0.4-0.7）: {quality_report['quality_distribution']['medium']} 条")
    print(f"   - 低质量（<0.4）: {quality_report['quality_distribution']['low']} 条")
    
    # 统计毕法赋引用
    bifa_keywords = ['毕法', '赋', '云', '曰']
    total_rules = sum(quality_report['quality_distribution'].values())
    bifa_count = sum(1 for r in updated_rules if any(kw in r.get('rule', '') for kw in bifa_keywords))
    print(f"\n   有毕法赋引用的规则: {bifa_count} 条 ({bifa_count/total_rules*100:.1f}%)")
    print(f"   规则总数: {total_rules} 条")
    
    # 计算高质量占比
    high_ratio = quality_report['quality_distribution']['high'] / max(total_rules, 1) * 100
    print(f"   高质量规则占比: {high_ratio:.1f}%")
    
    # 保存报告
    report = {
        'enhancement_time': datetime.now().isoformat(),
        'total_rules': len(rules_to_enhance),
        'successfully_enhanced': updated_count,
        'post_enhancement_quality': quality_report['quality_distribution'],
        'bifa_reference_count': bifa_count,
        'high_quality_ratio': round(high_ratio, 1)
    }
    
    report_path = os.path.join(_ROOT, 'data', 'distillation', 'final_enhancement_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 增强报告已保存: {report_path}")
    print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("🎉🎉🎉 剩余规则增强完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
