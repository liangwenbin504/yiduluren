#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成家宅类型毕法赋引用（AI高质量版）

策略：
1. 使用扩展毕法赋条文库作为参考
2. 调用AI（glm-4-flash免费模型）重新生成高质量引用
3. 统一引用格式为 【毕法赋】"条文内容"
4. 批量处理，每5条为一组
"""

import json
import os
import sys
import re
from datetime import datetime

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.distillation_engine import DistillationEngine, KnowledgeOptimizer
from engine.extended_bifa_articles import EXTENDED_BIFA_ARTICLES, get_bifa_articles_by_zhanshi
from glm_service import GLMService


def clean_bifa_quote(rule_text: str) -> str:
    """清除规则中原有的毕法赋引用"""
    # 清除各种格式的毕法赋引用
    cleaned = rule_text
    
    # 清除 【毕法赋】... 格式
    cleaned = re.sub(r'【毕法赋】[「"「].*?[」"」]?', '', cleaned, flags=re.DOTALL)
    
    # 清除 "毕法赋: " 开头的引用
    cleaned = re.sub(r'毕法赋[::][\s\u4e00-\u9fff，。；：""''「」""]*', '', cleaned)
    
    # 清除多余的换行
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def generate_bifa_quote_with_ai(rule_text: str, zhanshi: str, glm: GLMService) -> dict:
    """使用AI生成毕法赋引用"""
    
    # 获取参考条文
    reference_articles = get_bifa_articles_by_zhanshi(zhanshi)
    reference_text = '\n'.join([
        f'  {i+1}. "{article[:80]}..."'
        for i, article in enumerate(reference_articles[:8])
    ])
    
    prompt = f"""你是一位精通大六壬毕法赋的专家。请为以下规则生成一个准确的毕法赋引用。

占事类型：{zhanshi}

【参考毕法赋条文】：
{reference_text}

规则内容：
"{rule_text[:150]}..."

要求：
1. 从参考条文中选择最相关的一条毕法赋条文
2. 引用格式：【毕法赋】"条文内容"
3. 条文长度20-60字
4. 必须与【{zhanshi}】类型和规则内容相关
5. 直接输出引用，不要额外解释

输出：
【毕法赋】"选择的条文内容"
"""
    
    messages = [
        {"role": "system", "content": "你是一位精通大六壬毕法赋的专家，能够为每条规则选择最相关的毕法赋条文。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = glm.generate(messages=messages, thinking=False, max_tokens=100)
        response_text = response.get('content', '')
        
        # 提取引用
        quote_match = re.search(r'【毕法赋】[」"「"]?(.*?)[」"「"]?', response_text)
        if quote_match:
            return {
                'success': True,
                'quote': quote_match.group(1),
                'full_quote': f'【毕法赋】"{quote_match.group(1)}"',
                'raw_response': response_text
            }
        else:
            # 兜底：直接返回第一条参考条文
            if reference_articles:
                fallback = reference_articles[0]
                return {
                    'success': True,
                    'quote': fallback[:50],
                    'full_quote': f'【毕法赋】"{fallback[:50]}"',
                    'raw_response': response_text,
                    'is_fallback': True
                }
            return {'success': False, 'error': '无法生成引用'}
    except Exception as e:
        # 兜底
        if reference_articles:
            fallback = reference_articles[0]
            return {
                'success': True,
                'quote': fallback[:50],
                'full_quote': f'【毕法赋】"{fallback[:50]}"',
                'error': str(e),
                'is_fallback': True
            }
        return {'success': False, 'error': str(e)}


def run_regeneration():
    """重新生成毕法赋引用"""
    
    print("=" * 70)
    print("📚 重新生成家宅类型毕法赋引用（AI高质量版）")
    print("=" * 70)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载引擎
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    
    # 获取当前规则
    rules = engine.knowledge_store.get('knowledge_rules', [])
    jiazhai_rules = [(i, r) for i, r in enumerate(rules) if r.get('zhanshi') == '家宅']
    
    print(f"\n📊 当前状态:")
    print(f"   - 家宅规则总数: {len(jiazhai_rules)}")
    
    # 初始化GLM服务
    glm = GLMService()
    glm.set_model('glm-4-flash')  # 使用免费模型
    
    # 重新生成引用
    print("\n" + "=" * 70)
    print("🔥 开始AI重新生成毕法赋引用")
    print("=" * 70)
    
    updated_rules = rules.copy()
    success_count = 0
    fallback_count = 0
    fail_count = 0
    
    # 批量处理，每5条为一组
    for batch_start in range(0, len(jiazhai_rules), 5):
        batch_end = min(batch_start + 5, len(jiazhai_rules))
        batch = jiazhai_rules[batch_start:batch_end]
        
        print(f"\n   处理第 {batch_start+1}-{batch_end} 条...")
        
        for idx, rule in batch:
            rule_text = rule.get('rule', '')
            
            # 清除原有毕法赋引用
            cleaned_text = clean_bifa_quote(rule_text)
            
            # 使用AI生成新引用
            result = generate_bifa_quote_with_ai(cleaned_text, '家宅', glm)
            
            if result['success']:
                # 重新组合规则
                new_rule = cleaned_text + '\n\n' + result['full_quote']
                rule['rule'] = new_rule
                updated_rules[idx] = rule
                success_count += 1
                
                if result.get('is_fallback'):
                    fallback_count += 1
                    print(f'     ✅ 规则 {idx} 已更新（兜底方案）')
                else:
                    print(f'     ✅ 规则 {idx} 已更新（AI生成）')
            else:
                fail_count += 1
                print(f'     ❌ 规则 {idx} 生成失败: {result.get("error", "未知错误")}')
    
    # 更新引擎中的规则
    engine.knowledge_store['knowledge_rules'] = updated_rules
    engine._save_knowledge_store()
    
    # 输出结果
    print("\n" + "=" * 70)
    print("📈 重新生成结果汇总")
    print("=" * 70)
    
    print(f"\n   总处理数: {len(jiazhai_rules)}")
    print(f"   成功生成: {success_count}")
    print(f"   其中AI生成: {success_count - fallback_count}")
    print(f"   其中兜底方案: {fallback_count}")
    print(f"   失败数量: {fail_count}")
    if len(jiazhai_rules) > 0:
        success_rate = success_count / len(jiazhai_rules) * 100
        print(f"   成功率: {success_rate:.1f}%")
    
    # 增强后状态
    engine2 = DistillationEngine()
    updated_rules = engine2.knowledge_store.get('knowledge_rules', [])
    updated_jiazhai = [r for r in updated_rules if r.get('zhanshi') == '家宅']
    
    # 质量评估
    print(f"\n📊 增强后状态:")
    print(f"   - 家宅规则总数: {len(updated_jiazhai)}")
    
    # 统计引用质量
    has_valid_quote = 0
    for r in updated_jiazhai:
        rule_text = r.get('rule', '')
        if '【毕法赋】"' in rule_text and len(rule_text) > 30:
            has_valid_quote += 1
    
    print(f"   - 有效毕法赋引用: {has_valid_quote}")
    print(f"   - 引用覆盖率: {has_valid_quote/max(len(updated_jiazhai),1)*100:.1f}%")
    
    # 生成质量报告
    print("\n📈 生成质量报告...")
    quality_report = optimizer.generate_quality_report()
    
    # 保存报告
    report = {
        'generated_at': datetime.now().isoformat(),
        'task': '家宅类型毕法赋引用AI重新生成',
        'total_rules': len(updated_jiazhai),
        'success_count': success_count,
        'ai_generated': success_count - fallback_count,
        'fallback_count': fallback_count,
        'fail_count': fail_count,
        'valid_quotes': has_valid_quote,
        'coverage_rate': has_valid_quote / max(len(updated_jiazhai), 1),
        'quality_report': quality_report
    }
    
    report_path = os.path.join(_ROOT, 'data', 'distillation', 'bifa_regeneration_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 报告已保存: {report_path}")
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("🎉🎉🎉 毕法赋引用重新生成完成！")
    print("=" * 70)


if __name__ == '__main__':
    run_regeneration()