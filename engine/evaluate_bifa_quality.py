#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查并优化毕法赋引用质量"""

import sys
import os
import re
import json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.distillation_engine import DistillationEngine
from engine.extended_bifa_articles import EXTENDED_BIFA_ARTICLES, get_bifa_articles_by_zhanshi


def evaluate_bifa_quality(rule_text: str, zhanshi: str) -> dict:
    """评估毕法赋引用的质量"""
    
    # 提取毕法赋部分
    bifa_match = re.search(r'【毕法赋】[」"「"]?(.*?)[」"「"]?', rule_text)
    if not bifa_match:
        return {'score': 0, 'issues': ['未找到毕法赋引用'], 'bifa_text': ''}
    
    bifa_text = bifa_match.group(1)
    
    # 评分
    score = 0.0
    issues = []
    
    # 1. 长度检查（0.2分）
    if len(bifa_text) >= 20:
        score += 0.2
    elif len(bifa_text) >= 10:
        score += 0.1
    else:
        issues.append('引用过短')
    
    # 2. 毕法赋特征词检查（0.3分）
    bifa_patterns = ['主', '为', '以', '须', '宜', '忌', '云', '赋云',
                     '旺', '衰', '生', '克', '合', '冲', '刑',
                     '格', '课', '象', '候', '应']
    has_pattern = any(p in bifa_text for p in bifa_patterns)
    if has_pattern:
        score += 0.3
    else:
        issues.append('缺少毕法赋特征词')
    
    # 3. 占事关联检查（0.3分）
    zhanshi_keywords_map = {
        '家宅': ['宅', '家', '屋', '人', '房'],
        '婚姻': ['婚', '姻', '夫', '妇', '嫁'],
        '出行': ['行', '路', '旅', '动', '迁'],
        '功名': ['名', '功', '官', '禄', '贵'],
        '官讼': ['讼', '官', '争', '刑', '法'],
        '求财': ['财', '利', '富', '金', '钱'],
        '疾病': ['病', '疾', '医', '治', '愈'],
    }
    keywords = zhanshi_keywords_map.get(zhanshi, [])
    has_keyword = any(k in bifa_text for k in keywords)
    if has_keyword:
        score += 0.3
    else:
        issues.append(f'与{zhanshi}类型关联不强')
    
    # 4. 与扩展条文库匹配（0.2分）
    articles = get_bifa_articles_by_zhanshi(zhanshi)
    best_match_score = 0
    for article in articles:
        # 简化匹配：检查关键词重叠
        article_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', article))
        bifa_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', bifa_text))
        if article_keywords and bifa_keywords:
            overlap = len(article_keywords & bifa_keywords)
            match_score = overlap / max(len(article_keywords), len(bifa_keywords), 1)
            best_match_score = max(best_match_score, match_score)
    
    if best_match_score >= 0.3:
        score += 0.2
    elif best_match_score >= 0.15:
        score += 0.1
    else:
        issues.append('与条文库匹配度低')
    
    return {
        'score': round(score, 2),
        'bifa_text': bifa_text,
        'issues': issues,
        'match_score': round(best_match_score, 2)
    }


def main():
    engine = DistillationEngine()
    rules = engine.knowledge_store.get('knowledge_rules', [])
    
    # 获取家宅类型规则
    jiazhai_rules = [r for r in rules if r.get('zhanshi') == '家宅']
    
    print('📖 家宅类型毕法赋引用质量评估')
    print('=' * 70)
    
    # 评估每条规则
    quality_stats = {'high': 0, 'medium': 0, 'low': 0}
    low_quality_rules = []
    medium_quality_rules = []
    
    for i, rule in enumerate(jiazhai_rules):
        rule_text = rule.get('rule', '')
        eval_result = evaluate_bifa_quality(rule_text, '家宅')
        
        score = eval_result['score']
        if score >= 0.8:
            quality_stats['high'] += 1
        elif score >= 0.6:
            quality_stats['medium'] += 1
            medium_quality_rules.append({
                'index': i,
                'score': score,
                'issues': eval_result['issues'],
                'bifa_text': eval_result['bifa_text']
            })
        else:
            quality_stats['low'] += 1
            low_quality_rules.append({
                'index': i,
                'score': score,
                'issues': eval_result['issues'],
                'bifa_text': eval_result['bifa_text']
            })
    
    # 输出统计
    print(f'\n📊 引用质量分布:')
    print(f'  高质量(≥0.8): {quality_stats["high"]} 条 ({quality_stats["high"]/max(len(jiazhai_rules),1)*100:.1f}%)')
    print(f'  中质量(0.6-0.8): {quality_stats["medium"]} 条 ({quality_stats["medium"]/max(len(jiazhai_rules),1)*100:.1f}%)')
    print(f'  低质量(<0.6): {quality_stats["low"]} 条 ({quality_stats["low"]/max(len(jiazhai_rules),1)*100:.1f}%)')
    
    # 输出低质量规则详情
    if low_quality_rules:
        print(f'\n⚠️  低质量引用详情 ({len(low_quality_rules)} 条):')
        for rule in low_quality_rules[:10]:
            bifa_text = rule.get('bifa_text', '')
            print(f'  [{rule["index"]}] 分数:{rule["score"]} | 问题:{rule["issues"]}')
            print(f'       引用: {bifa_text[:80]}...')
    
    # 输出中质量规则详情
    if medium_quality_rules:
        print(f'\n📋 中质量引用详情 ({len(medium_quality_rules)} 条):')
        for rule in medium_quality_rules[:5]:
            bifa_text = rule.get('bifa_text', '')
            print(f'  [{rule["index"]}] 分数:{rule["score"]} | 问题:{rule["issues"]}')
            print(f'       引用: {bifa_text[:80]}...')
    
    # 保存结果
    report = {
        'total': len(jiazhai_rules),
        'high_quality': quality_stats['high'],
        'medium_quality': quality_stats['medium'],
        'low_quality': quality_stats['low'],
        'low_quality_rules': low_quality_rules[:30],  # 最多保存30条
        'medium_quality_rules': medium_quality_rules[:30]
    }
    
    report_path = os.path.join(_ROOT, 'data', 'distillation', 'bifa_quality_eval.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'\n📝 质量评估报告已保存: {report_path}')
    
    # 总结
    print(f'\n📈 总结:')
    if quality_stats['low'] > 0:
        print(f'  有 {quality_stats["low"]} 条规则的毕法赋引用需要优化')
        print(f'  建议：使用AI重新生成高质量引用')
    else:
        print(f'  所有规则的毕法赋引用质量良好！')
    
    return low_quality_rules, medium_quality_rules


if __name__ == '__main__':
    main()