#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对剩余2条中质量规则进行二次增强
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


def main():
    """主函数"""
    print("=" * 70)
    print("🎯 大六壬知识蒸馏引擎 — 剩余2条规则二次增强")
    print("=" * 70)
    
    # 初始化
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    glm_service = GLMService()
    
    rules = engine.knowledge_store.get('knowledge_rules', [])
    
    # 识别剩余2条中质量规则
    print("\n📊 第1步：识别剩余2条中质量规则")
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
    
    print(f"   需要二次增强的规则数: {len(rules_to_enhance)} 条")
    
    for r in rules_to_enhance:
        print(f"   [{r['quality_score']}] 【{r['zhanshi']}】{r['rule']}")
        print(f"   长度: {len(r['rule'])} 字符\n")
    
    if len(rules_to_enhance) == 0:
        print("   ✅ 已经没有中质量规则了！")
        return
    
    # 第2步：调用AI进行更彻底的增强
    print("\n🤖 第2步：AI深度增强（更严格的要求）")
    print("-" * 50)
    
    # 更丰富的毕法赋条文
    bifa_articles = [
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
        '毕法赋云："中传为事情，主事情发展过程；末传为结果，主最终吉凶"',
        '毕法赋云："六合主和合，主婚姻，主合作；青龙主吉庆，主财喜"',
        '毕法赋云："贵人人宅，主贵人扶持；禄神入宅，主财禄丰盈"',
    ]
    
    bifa_text = '\n'.join([f'  {i+1}. {a}' for i, a in enumerate(bifa_articles)])
    
    rules_text = '\n'.join([
        f'  {i+1}. 【{r["zhanshi"]}】{r["rule"]}' 
        for i, r in enumerate(rules_to_enhance)
    ])
    
    prompt = f"""你是一位大六壬专家，请将以下家宅类型规则增强为高质量规则。

可用的毕法赋条文：
{bifa_text}

需要增强的规则：
{rules_text}

严格增强要求：
1. 每条规则必须引用【至少2条】具体的毕法赋条文
2. 添加条文引用格式：【毕法赋】"条文内容"
3. 补充具体的判断条件（如课体、天将、三传等）
4. 明确吉凶判断标准
5. 增强规则长度至80-150字
6. 保持原规则的核心含义
7. 添加"适用于"、"判断标准"、"吉凶"等关键词

输出格式（JSON数组）：
[
  {{"index": 1, "enhanced_rule": "增强后的规则文本，包含至少2条毕法赋引用"}},
  {{"index": 2, "enhanced_rule": "增强后的规则文本，包含至少2条毕法赋引用"}}
]

示例输出：
[
  {{"index": 1, "enhanced_rule": "家宅占断（适用于六合课、元首课），【毕法赋】「宅旺人衰，人宅两宜」「青龙主喜庆」，判断标准：宅神旺相且见青龙、六合则吉，主家宅安宁、六亲和睦；若宅神休囚则凶，主破财。三传吉凶：初传吉则开端好，中传吉则过程顺，末传吉则结果佳。"}}
]
"""
    
    messages = [
        {"role": "system", "content": "你是一位精通大六壬的专家，擅长撰写高质量、可操作的判断规则，能够准确引用毕法赋条文并结合具体课体进行说明。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        original_model = glm_service.model
        glm_service.set_model('glm-4-flash')
        
        response = glm_service.generate(
            messages=messages,
            temperature=0.1,  # 极低温度，保证输出确定性
            max_tokens=2000
        )
        
        glm_service.set_model(original_model)
        
        if isinstance(response, dict) and 'error' in response:
            print(f"❌ API错误: {response['error']}")
            return
        
        if isinstance(response, dict) and 'choices' in response:
            response_text = response['choices'][0]['message']['content'].strip()
        elif isinstance(response, dict) and 'content' in response:
            response_text = response['content'].strip()
        else:
            response_text = str(response).strip()
        
        # 解析JSON
        try:
            enhanced_results = json.loads(response_text)
        except json.JSONDecodeError:
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                enhanced_results = json.loads(response_text[start_idx:end_idx])
            else:
                print("❌ JSON解析失败")
                return
        
        print(f"   AI返回: {len(enhanced_results)} 条增强规则")
        
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
                    new_quality = optimizer.score_rule_quality(enhanced_rule)
                    
                    updated_rules[original_index]['rule'] = enhanced_rule
                    updated_rules[original_index]['original_rule'] = rules_to_enhance[idx - 1]['rule']
                    updated_rules[original_index]['enhanced_at'] = datetime.now().isoformat()
                    updated_count += 1
                    print(f"   ✅ 规则 {original_index}: 质量 {new_quality:.2f}, 长度 {len(enhanced_rule)} 字符")
        
        # 保存
        engine.knowledge_store['knowledge_rules'] = updated_rules
        engine._save_knowledge_store()
        
        # 第4步：验证
        print("\n📈 第4步：最终验证")
        print("-" * 50)
        
        quality_report = optimizer.generate_quality_report()
        
        print("\n   最终质量分布:")
        print(f"   - 高质量（≥0.8）: {quality_report['quality_distribution']['high']} 条")
        print(f"   - 中质量（0.4-0.7）: {quality_report['quality_distribution']['medium']} 条")
        print(f"   - 低质量（<0.4）: {quality_report['quality_distribution']['low']} 条")
        
        total_rules = sum(quality_report['quality_distribution'].values())
        high_ratio = quality_report['quality_distribution']['high'] / max(total_rules, 1) * 100
        
        bifa_keywords = ['毕法', '赋', '云', '曰']
        bifa_count = sum(1 for r in updated_rules if any(kw in r.get('rule', '') for kw in bifa_keywords))
        
        print(f"\n   高质量占比: {high_ratio:.1f}%")
        print(f"   毕法赋引用: {bifa_count} 条 ({bifa_count/total_rules*100:.1f}%)")
        print(f"   规则总数: {total_rules} 条")
        
        # 保存报告
        report = {
            'enhancement_time': datetime.now().isoformat(),
            'updated_count': updated_count,
            'post_quality': quality_report['quality_distribution'],
            'high_quality_ratio': round(high_ratio, 1),
            'bifa_reference_count': bifa_count,
            'total_rules': total_rules
        }
        
        report_path = os.path.join(_ROOT, 'data', 'distillation', 'final_enhancement_report.json')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 报告已保存: {report_path}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("🎉🎉🎉 二次增强完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
