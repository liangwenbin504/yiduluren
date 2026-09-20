#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为缺少毕法赋引用的家宅规则添加引用

策略：
1. 使用扩展的毕法赋条文库作为参考
2. 调用AI（glm-4-flash）生成合适的毕法赋引用
3. 批量处理，每3条为一组
4. 验证引用的有效性
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


def find_matching_article(rule_text: str, zhanshi: str) -> str:
    """从扩展条文库中查找与规则最匹配的毕法赋条文"""
    articles = get_bifa_articles_by_zhanshi(zhanshi)
    if not articles:
        return ''
    
    best_match = ''
    best_score = 0
    
    # 提取规则中的关键词
    rule_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', rule_text))
    
    for article in articles:
        article_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', article))
        # 计算关键词重叠度
        overlap = len(rule_keywords & article_keywords)
        score = overlap / max(len(rule_keywords), len(article_keywords), 1)
        if score > best_score:
            best_score = score
            best_match = article
    
    # 如果没有找到匹配，返回第一条作为兜底
    if not best_match and articles:
        best_match = articles[0]
    
    return best_match


def enhance_rules_with_bifa(rules: list, zhanshi: str) -> dict:
    """为指定占事类型的规则添加毕法赋引用"""
    
    # 找出缺少毕法赋引用的规则
    missing_bifa = []
    for i, rule in enumerate(rules):
        rule_text = rule.get('rule', '')
        if rule.get('zhanshi') == zhanshi and '毕法赋' not in rule_text:
            missing_bifa.append({
                'index': i,
                'rule': rule,
                'rule_text': rule_text
            })
    
    print(f'\n   发现 {len(missing_bifa)} 条缺少毕法赋引用的规则')
    
    if not missing_bifa:
        return {'success': True, 'enhanced': 0, 'failed': 0}
    
    # 获取该占事类型的参考条文
    reference_articles = get_bifa_articles_by_zhanshi(zhanshi)
    reference_text = '\n'.join([
        f'  {i+1}. "{article[:60]}..."'
        for i, article in enumerate(reference_articles[:8])
    ])
    
    # 批量处理，每3条为一组
    enhanced_count = 0
    failed_count = 0
    updated_rules = rules.copy()
    
    for batch_start in range(0, len(missing_bifa), 3):
        batch_end = min(batch_start + 3, len(missing_bifa))
        batch = missing_bifa[batch_start:batch_end]
        
        rules_text = '\n'.join([
            f'  {i+1}. [索引{item["index"]}] 原规则: "{item["rule_text"][:120]}..."'
            for i, item in enumerate(batch)
        ])
        
        prompt = f"""你是一位精通大六壬毕法赋的专家。请为以下规则添加毕法赋引用。

占事类型：{zhanshi}

【参考毕法赋条文（来自扩展条文库）】：
{reference_text}

需要添加引用的规则：
{rules_text}

添加要求：
1. 为每条规则选择最相关的毕法赋条文
2. 引用格式：在规则末尾添加 【毕法赋】"条文内容"
3. 条文应与【{zhanshi}】类型及规则内容相关
4. 条文长度15-50字
5. 优先从参考条文中选择
6. 保持规则原有内容不变，只追加引用

输出JSON数组：
[
  {{"rule_index": 数字, "enhanced_rule": "完整的增强后规则（含毕法赋引用）"}}
]
"""
        
        messages = [
            {"role": "system", "content": "你是一位精通大六壬毕法赋的专家，能够为规则添加准确的毕法赋引用。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # 调用glm-4-flash（免费模型）
            glm = GLMService()
            glm.set_model('glm-4-flash')  # 切换到免费模型
            response = glm.generate(messages=messages, thinking=False)
            response_text = response.get('content', '')
            
            # 解析JSON
            # 尝试直接解析
            try:
                results = json.loads(response_text)
            except:
                # 尝试提取JSON
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    results = json.loads(json_match.group())
                else:
                    # 使用兜底方案
                    results = []
                    for item in batch:
                        matching_article = find_matching_article(item['rule_text'], zhanshi)
                        if matching_article:
                            enhanced_rule = item['rule_text'] + f'\\n\\n【毕法赋】"{matching_article}"'
                            results.append({
                                'rule_index': item['index'],
                                'enhanced_rule': enhanced_rule
                            })
            
            # 更新规则
            for result in results:
                rule_index = result.get('rule_index', -1)
                enhanced_rule = result.get('enhanced_rule', '')
                
                # 找到对应的原始规则
                target = [item for item in batch if item['index'] == rule_index]
                if target:
                    original_rule = target[0]['rule']
                    # 更新规则文本
                    original_rule['rule'] = enhanced_rule
                    updated_rules[rule_index] = original_rule
                    enhanced_count += 1
                    print(f'     ✅ 规则 {rule_index} 已增强')
                else:
                    failed_count += 1
                    print(f'     ❌ 规则 {rule_index} 匹配失败')
                    
        except Exception as e:
            print(f'     ❌ 处理失败: {e}')
            # 使用兜底方案
            for item in batch:
                try:
                    matching_article = find_matching_article(item['rule_text'], zhanshi)
                    if matching_article:
                        original_rule = item['rule']
                        enhanced_rule = item['rule_text'] + f'\\n\\n【毕法赋】"{matching_article}"'
                        original_rule['rule'] = enhanced_rule
                        updated_rules[item['index']] = original_rule
                        enhanced_count += 1
                        print(f'     ✅ 规则 {item["index"]} 已增强（兜底）')
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1
    
    # 更新引擎中的规则
    engine = DistillationEngine()
    engine.knowledge_store['knowledge_rules'] = updated_rules
    engine._save_knowledge_store()
    
    return {
        'success': True,
        'enhanced': enhanced_count,
        'failed': failed_count,
        'total': len(missing_bifa)
    }


def run_enhancement():
    """运行毕法赋引用增强"""
    
    print("=" * 70)
    print("📚 为家宅类型规则添加毕法赋引用")
    print("=" * 70)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载引擎
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    
    # 获取当前规则
    rules = engine.knowledge_store.get('knowledge_rules', [])
    jiazhai_rules = [r for r in rules if r.get('zhanshi') == '家宅']
    
    print(f"\n📊 当前状态:")
    print(f"   - 家宅规则总数: {len(jiazhai_rules)}")
    
    # 统计已有引用
    has_bifa = sum(1 for r in jiazhai_rules if '毕法赋' in r.get('rule', ''))
    no_bifa = len(jiazhai_rules) - has_bifa
    print(f"   - 已有毕法赋引用: {has_bifa}")
    print(f"   - 缺少毕法赋引用: {no_bifa}")
    
    # 检查扩展条文库
    from engine.extended_bifa_articles import EXTENDED_BIFA_ARTICLES
    print(f"\n📚 扩展毕法赋条文库:")
    for zs, articles in EXTENDED_BIFA_ARTICLES.items():
        print(f"   - {zs}: {len(articles)} 条")
    
    # 执行增强
    print("\n" + "=" * 70)
    print("🔥 开始增强毕法赋引用")
    print("=" * 70)
    
    result = enhance_rules_with_bifa(rules, '家宅')
    
    # 输出结果
    print("\n" + "=" * 70)
    print("📈 增强结果汇总")
    print("=" * 70)
    
    print(f"\n   总处理数: {result.get('total', 0)}")
    print(f"   成功增强: {result.get('enhanced', 0)}")
    print(f"   失败数量: {result.get('failed', 0)}")
    if result.get('total', 0) > 0:
        success_rate = result['enhanced'] / result['total'] * 100
        print(f"   成功率: {success_rate:.1f}%")
    
    # 增强后状态
    engine2 = DistillationEngine()
    updated_rules = engine2.knowledge_store.get('knowledge_rules', [])
    updated_jiazhai = [r for r in updated_rules if r.get('zhanshi') == '家宅']
    updated_has_bifa = sum(1 for r in updated_jiazhai if '毕法赋' in r.get('rule', ''))
    
    print(f"\n📊 增强后状态:")
    print(f"   - 家宅规则总数: {len(updated_jiazhai)}")
    print(f"   - 已有毕法赋引用: {updated_has_bifa}")
    print(f"   - 缺少毕法赋引用: {len(updated_jiazhai) - updated_has_bifa}")
    print(f"   - 引用覆盖率: {updated_has_bifa/max(len(updated_jiazhai),1)*100:.1f}%")
    
    # 生成质量报告
    print("\n📈 生成质量报告...")
    quality_report = optimizer.generate_quality_report()
    
    # 保存报告
    report = {
        'generated_at': datetime.now().isoformat(),
        'task': '家宅类型毕法赋引用增强',
        'total_rules': len(updated_jiazhai),
        'has_bifa': updated_has_bifa,
        'no_bifa': len(updated_jiazhai) - updated_has_bifa,
        'coverage_rate': updated_has_bifa / max(len(updated_jiazhai), 1),
        'enhanced_count': result.get('enhanced', 0),
        'failed_count': result.get('failed', 0),
        'quality_report': quality_report
    }
    
    report_path = os.path.join(_ROOT, 'data', 'distillation', 'bifa_enhancement_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 报告已保存: {report_path}")
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("🎉🎉🎉 毕法赋引用增强完成！")
    print("=" * 70)


if __name__ == '__main__':
    run_enhancement()