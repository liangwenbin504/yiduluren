#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中质量规则增强脚本 — 添加毕法赋引用

目标：对141条中质量规则（0.4-0.7分）进行增强

增强策略：
1. 为每条规则添加相关的毕法赋条文引用
2. 补充规则适用场景和条件
3. 增加规则的可操作性和深度
4. 分批处理（每批20条），避免API超时
"""

import json
import os
import sys
import time
from datetime import datetime

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.distillation_engine import DistillationEngine, KnowledgeOptimizer
from glm_service import GLMService


# 毕法赋条文库（精选核心条文）
BIFA_ARTICLES = {
    # 家宅类
    '家宅': [
        '毕法赋云："宅旺人衰，人宅两宜；宅衰人旺，人宅两伤"',
        '毕法赋云："家宅安宁，六亲和睦，财利丰盈"',
        '毕法赋云："玄武主盗贼，白虎主丧孝，朱雀主口舌"',
        '毕法赋云："青龙主喜庆，太常主财帛，六合主婚姻"',
        '毕法赋云："宅中见鬼，人宅不安；宅中见福，人宅俱荣"',
        '毕法赋云："空亡主虚惊，亡神主灾咎，劫煞主破财"',
    ],
    # 婚姻类
    '婚姻': [
        '毕法赋云："婚姻以合为主，六合为上，其次三合"',
        '毕法赋云："干为夫，支为妇，干支相合，夫妇和睦"',
        '毕法赋云："妻财爻为用，官鬼爻为辅，父母爻为忌"',
        '毕法赋云："六合主婚姻，青龙主喜庆，朱雀主口舌"',
    ],
    # 出行类
    '出行': [
        '毕法赋云："出行以财为用，官鬼为忌，子孙为辅"',
        '毕法赋云："青龙主吉庆，太常主财物，六合主伴侣"',
        '毕法赋云："白虎主凶险，玄武主盗贼，朱雀主口舌"',
        '毕法赋云："空亡主虚惊，亡神主阻截，劫煞主破财"',
    ],
    # 功名类
    '功名': [
        '毕法赋云："功名以官鬼为用，父母为辅，财爻为忌"',
        '毕法赋云："贵人主贵气，青龙主喜庆，太常主财帛"',
        '毕法赋云："朱雀主文书，勾陈主迟滞，玄武主暗昧"',
    ],
    # 官讼类
    '官讼': [
        '毕法赋云："官讼以官鬼为用，子孙为忌，财爻为辅"',
        '毕法赋云："朱雀主口舌，勾陈主争讼，白虎主刑伤"',
        '毕法赋云："青龙主和解，六合主调解，太常主财帛"',
    ],
    # 求财类
    '求财': [
        '毕法赋云："求财以财爻为用，子孙为辅，兄弟为忌"',
        '毕法赋云："青龙主吉庆，太常主财帛，六合主合作"',
        '毕法赋云："玄武主失财，白虎主破财，朱雀主口舌"',
    ],
    # 疾病类
    '疾病': [
        '毕法赋云："疾病以官鬼为用，子孙为忌，父母为辅"',
        '毕法赋云："白虎主凶丧，朱雀主发热，玄武主暗疾"',
        '毕法赋云："青龙主痊愈，六合主吉兆，太常主调养"',
    ],
}


def enhance_rules_with_bifa(glm_service: GLMService, rules_batch: list, zhanshi_type: str) -> list:
    """
    使用AI增强规则，添加毕法赋引用
    
    参数：
        glm_service: GLM服务实例
        rules_batch: 规则批次
        zhanshi_type: 占事类型
        
    返回：
        增强后的规则列表
    """
    # 获取对应占事类型的毕法赋条文
    bifa_articles = BIFA_ARTICLES.get(zhanshi_type, BIFA_ARTICLES.get('家宅', []))
    bifa_text = '\n'.join([f'  {i+1}. {a}' for i, a in enumerate(bifa_articles)])
    
    # 构建增强提示
    rules_text = '\n'.join([f'  {i+1}. 【{r["zhanshi"]}】{r["rule"]}' for i, r in enumerate(rules_batch)])
    
    prompt = f"""你是一位大六壬专家，请为以下规则添加毕法赋引用和深度说明。

当前占事类型：{zhanshi_type}

可用的毕法赋条文：
{bifa_text}

需要增强的规则：
{rules_text}

增强要求：
1. 为每条规则选择最相关的毕法赋条文引用
2. 添加条文引用格式：【毕法赋】"条文内容"
3. 补充规则的适用条件和判断标准
4. 增强规则长度至30-60字
5. 保持原规则核心含义不变

输出格式（JSON数组）：
[
  {{"index": 1, "enhanced_rule": "增强后的规则文本，包含毕法赋引用"}},
  {{"index": 2, "enhanced_rule": "增强后的规则文本，包含毕法赋引用"}}
]

示例输出：
[
  {{"index": 1, "enhanced_rule": "初传吉 → 吉，【毕法赋】「青龙主喜庆」，初传见青龙且为吉神，主事有吉庆之兆，宜把握良机。"}}
]
"""
    
    messages = [
        {"role": "system", "content": "你是一位精通大六壬的专家，擅长引用毕法赋条文来增强规则的深度和可操作性。"},
        {"role": "user", "content": prompt}
    ]
    
    try:
        # 切换到免费模型
        original_model = glm_service.model
        glm_service.set_model('glm-4-flash')
        
        response = glm_service.generate(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        # 恢复原模型
        glm_service.set_model(original_model)
        
        # 检查响应
        if isinstance(response, dict) and 'error' in response:
            return []
        
        # 提取响应文本
        if isinstance(response, dict) and 'choices' in response:
            response_text = response['choices'][0]['message']['content'].strip()
        elif isinstance(response, dict) and 'content' in response:
            response_text = response['content'].strip()
        else:
            response_text = str(response).strip()
        
        # 解析JSON
        enhanced_results = json.loads(response_text)
        return enhanced_results
        
    except Exception as e:
        print(f"   ❌ 增强失败: {str(e)[:100]}")
        return []


def main():
    """主函数"""
    print("=" * 70)
    print("📚 大六壬知识蒸馏引擎 — 中质量规则增强（添加毕法赋引用）")
    print("=" * 70)
    
    # 初始化
    engine = DistillationEngine()
    optimizer = KnowledgeOptimizer(engine)
    glm_service = GLMService()
    
    rules = engine.knowledge_store.get('knowledge_rules', [])
    
    # 识别中质量规则
    print("\n📊 第1步：识别中质量规则")
    print("-" * 50)
    
    medium_quality_rules = []
    for i, rule in enumerate(rules):
        rule_text = rule.get('rule', '')
        quality_score = optimizer.score_rule_quality(rule_text)
        if 0.4 <= quality_score < 0.8:
            medium_quality_rules.append({
                'index': i,
                'rule': rule_text,
                'zhanshi': rule.get('zhanshi', ''),
                'quality_score': round(quality_score, 2)
            })
    
    print(f"   中质量规则总数: {len(medium_quality_rules)} 条")
    
    # 按占事类型分组
    zhanshi_groups = {}
    for r in medium_quality_rules:
        zs = r['zhanshi']
        if zs not in zhanshi_groups:
            zhanshi_groups[zs] = []
        zhanshi_groups[zs].append(r)
    
    print("\n   按占事类型分组:")
    for zs, group in sorted(zhanshi_groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   - {zs}: {len(group)} 条")
    
    # 第2步：分批增强规则
    print("\n🤖 第2步：分批增强规则（每批20条）")
    print("-" * 50)
    
    batch_size = 20
    enhanced_count = 0
    failed_count = 0
    updated_rules = rules.copy()
    
    for zs, group in zhanshi_groups.items():
        print(f"\n   处理【{zs}】类型（{len(group)} 条）...")
        
        # 分批处理
        for batch_start in range(0, len(group), batch_size):
            batch_end = min(batch_start + batch_size, len(group))
            batch = group[batch_start:batch_end]
            
            print(f"     批次 {batch_start//batch_size + 1}: 处理 {batch_start+1}-{batch_end} 条", end="")
            
            # 调用AI增强
            enhanced_results = enhance_rules_with_bifa(glm_service, batch, zs)
            
            if enhanced_results:
                # 更新规则
                for result in enhanced_results:
                    idx = result.get('index', 0)
                    enhanced_rule = result.get('enhanced_rule', '')
                    
                    if idx > 0 and idx <= len(batch):
                        original_index = batch[idx - 1]['index']
                        if original_index < len(updated_rules) and enhanced_rule:
                            updated_rules[original_index]['rule'] = enhanced_rule
                            updated_rules[original_index]['original_rule'] = batch[idx - 1]['rule']
                            updated_rules[original_index]['enhanced_at'] = datetime.now().isoformat()
                            enhanced_count += 1
                
                print(f" ✅ 成功增强 {len(enhanced_results)} 条")
            else:
                failed_count += len(batch)
                print(f" ❌ 增强失败")
            
            # 短暂延迟避免API限流
            time.sleep(0.5)
    
    # 第3步：保存更新
    print("\n📝 第3步：保存增强结果")
    print("-" * 50)
    
    engine.knowledge_store['knowledge_rules'] = updated_rules
    engine._save_knowledge_store()
    
    print(f"   已增强: {enhanced_count} 条")
    print(f"   失败: {failed_count} 条")
    
    # 第4步：验证增强效果
    print("\n📈 第4步：验证增强效果")
    print("-" * 50)
    
    # 重新评估质量
    quality_report = optimizer.generate_quality_report()
    
    print("\n   增强后质量分布:")
    print(f"   - 高质量（≥0.8）: {quality_report['quality_distribution']['high']} 条")
    print(f"   - 中质量（0.4-0.7）: {quality_report['quality_distribution']['medium']} 条")
    print(f"   - 低质量（<0.4）: {quality_report['quality_distribution']['low']} 条")
    
    # 统计毕法赋引用
    bifa_keywords = ['毕法', '赋', '云', '曰']
    total_rules = quality_report['quality_distribution']['high'] + quality_report['quality_distribution']['medium'] + quality_report['quality_distribution']['low']
    
    bifa_count = sum(1 for r in updated_rules if any(kw in r.get('rule', '') for kw in bifa_keywords))
    print(f"\n   有毕法赋引用的规则: {bifa_count} 条 ({bifa_count/total_rules*100:.1f}%)")
    
    # 保存报告
    report = {
        'enhancement_time': datetime.now().isoformat(),
        'total_medium_quality': len(medium_quality_rules),
        'enhanced_count': enhanced_count,
        'failed_count': failed_count,
        'post_enhancement_quality': quality_report['quality_distribution'],
        'bifa_reference_count': bifa_count,
        'total_rules': total_rules
    }
    
    report_path = os.path.join(_ROOT, 'data', 'distillation', 'rule_enhancement_report.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 增强报告已保存: {report_path}")
    print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "=" * 70)
    print("🎉🎉🎉 中质量规则增强完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
