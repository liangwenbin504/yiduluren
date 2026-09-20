# -*- coding: utf-8 -*-
"""
壬占汇选真实案例批量蒸馏脚本
==================================
利用壬占汇选529个真实古籍案例进行批量蒸馏训练

核心流程：
1. 从 features 提取结构化规则（课体→吉凶、毕法赋→判断、特殊格局→信号）
2. 用原著断语生成推理链（AI增强，但已有 features 做锚点）
3. 验证规则在案例上的命中率
4. 生成高质量蒸馏规则入库

对比之前的人工构造案例蒸馏：
- 壬占汇选有完整的大师断语（监督信号）
- 已有结构化 features（课体/毕法赋/特殊格局预提取）
- 可直接验证准确率
"""
import json, os, sys, re
from datetime import datetime
from collections import Counter, defaultdict

# 配置
RZHY_PATH = 'data/rzhy_feature_vectors.json'
KS_PATH = 'data/distillation/knowledge_store.json'
OUTPUT_DIR = 'data/distillation'

# 占事类型映射（壬占汇选分类 → 统一占事）
ZHANLEI_MAPPING = {
    '功名': '功名',
    '家宅': '家宅',
    '疾病': '占病',
    '官讼': '官讼',
    '出行': '出行',
    '胎产': '胎产',
    '求财': '求财',
    '婚姻': '婚姻',
    '走失': '失物',
    '学业': '功名',
    '征战': '官讼',
    '其他': None,  # 跳过
    'unknown': None,
}

# 课体吉凶映射（从64课经知识库）
KETI_JIXIONG = {
    # 吉课
    '元首': 5, '重审': 3, '比用': 3, '涉害': 2,
    '遥克': 2, '昴星': 1, '返吟': 0, '伏吟': -1,
    '别责': 2, '八专': -1,
    # 吉格
    '铸印': 5, '斫轮': 4, '金车': 4, '覆盂': 3,
    '连珠': 3, '间传': 2, '六纯': 3, '三奇': 5,
    '时泰': 2, '德庆': 4, '盘珠': 2, '玄胎': 2,
    '合欢': 2, '励德': 2, '闭口': 0,
    # 凶格
    '六仪': -2, '死奇': -3, '斩关': -1, '全局': -2,
}

# 特殊格局吉凶
SPECIAL_JIXIONG = {
    '贵登天门': 3, '罡塞鬼户': 3, '贵塞鬼户': 3,
    '白虎临干': -2, '虎临干鬼': -2, '贵临鬼户': -2,
    '将逢内战': -1, '初遭夹克': -2, '干支皆败': -2,
    '干支乘墓': -2, '人宅坐墓': -1,
    '三传递生': 3, '三传递克': -2, '三传互克': -1,
    '末助初生': 2, '末助初克': 1,
}


def load_rzhy_cases():
    """加载壬占汇选案例"""
    print("📂 加载壬占汇选案例...")
    with open(RZHY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cases = data.get('cases', [])
    print(f"  总案例数: {len(cases)}")
    
    # 筛选有明确占事类型的
    filtered = []
    for c in cases:
        zhanlei = c.get('zhanlei', c.get('category', ''))
        mapped = ZHANLEI_MAPPING.get(zhanlei)
        if mapped and c.get('features'):
            c['_mapped_zhanshi'] = mapped
            filtered.append(c)
    
    print(f"  有效案例(有类型+有features): {len(filtered)}")
    
    # 按类型分组
    by_type = defaultdict(list)
    for c in filtered:
        by_type[c['_mapped_zhanshi']].append(c)
    
    print(f"\n  占事类型分布:")
    for t, cs in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"    {t}: {len(cs)}条")
    
    return filtered, by_type


def extract_rules_from_features(case):
    """
    从 features 提取结构化规则（零成本，无需AI）
    返回: list of rule dicts
    """
    rules = []
    feat = case.get('features', {})
    zhanshi = case.get('_mapped_zhanshi', 'unknown')
    ketis = feat.get('keti', [])
    bifas = feat.get('bifa', [])
    specials = feat.get('special', [])
    day_ganzhi = case.get('day_ganzhi', '')
    sanchuan = case.get('sanchuan', [])
    
    # 1. 课体规则
    for kt in ketis:
        jx = KETI_JIXIONG.get(kt, 0)
        if jx != 0:
            rules.append({
                'rule': f"课体{kt} → {'吉' if jx > 0 else '凶'}（评分{jx}）",
                'zhanshi': zhanshi,
                'source': 'rzhy_features',
                'keti': kt,
                'jixiong_signal': jx,
                'confidence': 0.85,
                'extracted_from': 'keti_list',
            })
    
    # 2. 毕法赋规则
    for bifa_item in bifas:
        if isinstance(bifa_item, (list, tuple)) and len(bifa_item) >= 1:
            bifa_text = bifa_item[0] if isinstance(bifa_item, (list, tuple)) else str(bifa_item)
            # 从毕法赋条文推断吉凶
            jixiong = 0
            if any(w in bifa_text for w in ['吉', '喜', '庆', '禄', '贵', '亨', '顺']):
                jixiong = 2
            elif any(w in bifa_text for w in ['凶', '祸', '灾', '忌', '防', '不利']):
                jixiong = -2
            
            rules.append({
                'rule': f"【毕法赋】{bifa_text}",
                'zhanshi': zhanshi,
                'source': 'rzhy_features',
                'keti': '',
                'jixiong_signal': jixiong,
                'confidence': 0.80,
                'extracted_from': 'bifa_list',
                'bifa_reference': bifa_text,
            })
    
    # 3. 特殊格局规则
    for sp in specials:
        jx = SPECIAL_JIXIONG.get(sp, 0)
        if jx != 0:
            rules.append({
                'rule': f"特殊格局{sp} → {'吉' if jx > 0 else '凶'}（评分{jx}）",
                'zhanshi': zhanshi,
                'source': 'rzhy_features',
                'keti': '',
                'jixiong_signal': jx,
                'confidence': 0.90,
                'extracted_from': 'special_list',
            })
    
    return rules


def generate_composite_rule(case, extracted_rules):
    """
    组合规则：综合课体 + 毕法赋 + 特殊格局
    生成一条综合判断规则
    """
    feat = case.get('features', {})
    zhanshi = case.get('_mapped_zhanshi', 'unknown')
    ketis = feat.get('keti', [])
    specials = feat.get('special', [])
    day_ganzhi = case.get('day_ganzhi', '')
    sanchuan = case.get('sanchuan', [])
    duanyu = case.get('duanyu', '')
    label = case.get('label', '未知')
    
    # 计算综合吉凶分
    total_score = 0
    for kt in ketis:
        total_score += KETI_JIXIONG.get(kt, 0)
    for sp in specials:
        total_score += SPECIAL_JIXIONG.get(sp, 0)
    
    # 判断吉凶
    if total_score >= 3:
        jixiong = '吉'
        jx_score = total_score
    elif total_score <= -2:
        jixiong = '凶'
        jx_score = total_score
    else:
        jixiong = '中平'
        jx_score = total_score
    
    # 从断语提取关键判断
    duanyu_key = ''
    if duanyu:
        # 简化提取：取断语中的吉凶判断词
        if any(w in duanyu for w in ['果', '占验', '果然', '应于', '应验']):
            duanyu_key = '（有验案）'
        if label and label != '未知':
            duanyu_key += f' 原著断: {label}'
    
    # 生成综合规则
    keti_str = '、'.join(ketis[:3])
    special_str = '、'.join(specials[:3]) if specials else '无'
    sanchuan_str = '→'.join(sanchuan) if sanchuan else ''
    
    composite_rule = {
        'rule': f"日干{day_ganzhi}，三传{sanchuan_str}，课体{keti_str}，特殊格局{special_str} → {jixiong}（综合分{jx_score}）{duanyu_key}",
        'zhanshi': zhanshi,
        'source': 'rzhy_composite',
        'keti': ketis[0] if ketis else '',
        'all_ketis': ketis,
        'specials': specials,
        'jixiong_signal': jx_score,
        'predicted_jixiong': jixiong,
        'original_label': label,
        'day_ganzhi': day_ganzhi,
        'sanchuan': sanchuan,
        'confidence': 0.75,
        'extracted_from': 'composite',
        'case_id': case.get('case_id', ''),
    }
    
    return composite_rule


def validate_rule_against_case(rule, case):
    """
    验证规则是否与案例的原著断语一致
    简单方法：对比规则预测的吉凶与 features 中的线索
    """
    predicted = rule.get('predicted_jixiong', '')
    label = case.get('label', '')
    
    # 简单验证：如果有明确label，对比吉凶
    if label == '未知' or not label:
        return None  # 无法验证
    
    # 归一化label
    label_jixiong = None
    if any(w in label for w in ['吉', '成', '得', '应', '好']):
        label_jixiong = '吉'
    elif any(w in label for w in ['凶', '败', '失', '不', '危']):
        label_jixiong = '凶'
    elif any(w in label for w in ['平', '中']):
        label_jixiong = '中平'
    
    if label_jixiong and predicted:
        return predicted == label_jixiong
    
    return None


def batch_distill_rzhy():
    """壬占汇选批量蒸馏主流程"""
    print("\n" + "=" * 60)
    print("🚀 壬占汇选批量蒸馏开始")
    print("=" * 60)
    
    # 1. 加载案例
    cases, by_type = load_rzhy_cases()
    
    # 2. 蒸馏
    print("\n" + "-" * 40)
    print("📝 开始批量提取规则...")
    print("-" * 40)
    
    all_rules = []
    composite_rules = []
    validation_results = []
    
    case_count = 0
    for case in cases:
        case_count += 1
        
        # 提取单条规则
        rules = extract_rules_from_features(case)
        all_rules.extend(rules)
        
        # 生成组合规则
        composite = generate_composite_rule(case, rules)
        composite_rules.append(composite)
        
        # 验证
        is_correct = validate_rule_against_case(composite, case)
        validation_results.append({
            'case_id': case.get('case_id', ''),
            'predicted': composite.get('predicted_jixiong'),
            'original': case.get('label'),
            'correct': is_correct,
        })
        
        if case_count % 50 == 0:
            print(f"  进度: {case_count}/{len(cases)} 案例, 已提取 {len(all_rules)} 条规则")
    
    print(f"\n  ✅ 完成! 处理 {case_count} 案例")
    print(f"     - 单条规则: {len(all_rules)} 条")
    print(f"     - 组合规则: {len(composite_rules)} 条")
    
    # 3. 统计各占事类型的规则
    print("\n" + "-" * 40)
    print("📊 规则分布统计")
    print("-" * 40)
    
    zhanlei_counter = Counter()
    for r in all_rules:
        zhanlei_counter[r.get('zhanshi', 'unknown')] += 1
    for r in composite_rules:
        zhanlei_counter[r.get('zhanshi', 'unknown')] += 1
    
    for zl, cnt in zhanlei_counter.most_common():
        print(f"  {zl}: {cnt}条")
    
    # 4. 验证准确率
    print("\n" + "-" * 40)
    print("🎯 验证准确率")
    print("-" * 40)
    
    valid_results = [r for r in validation_results if r['correct'] is not None]
    if valid_results:
        correct = sum(1 for r in valid_results if r['correct'])
        acc = correct / len(valid_results) * 100
        print(f"  有label的案例: {len(valid_results)}")
        print(f"  预测正确: {correct}")
        print(f"  准确率: {acc:.1f}%")
        
        # 显示几个验证案例
        print(f"\n  验证示例:")
        for vr in valid_results[:5]:
            status = "✅" if vr['correct'] else "❌"
            print(f"    {status} {vr['case_id']}: 预测={vr['predicted']}, 原著={vr['original']}")
    else:
        print("  无label可验证")
    
    # 5. 保存结果
    print("\n" + "-" * 40)
    print("💾 保存蒸馏结果")
    print("-" * 40)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUTPUT_DIR, f'rzhy_distillation_{timestamp}.json')
    
    result = {
        'generated_at': datetime.now().isoformat(),
        'source': '壬占汇选(真古籍案例)',
        'total_cases': len(cases),
        'zhanshi_distribution': dict(zhanlei_counter),
        'individual_rules_count': len(all_rules),
        'composite_rules_count': len(composite_rules),
        'validation': {
            'total_with_label': len(valid_results),
            'correct': correct if valid_results else 0,
            'accuracy': acc if valid_results else 0,
        },
        'individual_rules': all_rules[:500],  # 最多保存500条单条规则
        'composite_rules': composite_rules,
        'validation_details': validation_results[:200],
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"  已保存: {output_path}")
    
    # 6. 合并到知识库
    print("\n" + "-" * 40)
    print("🔗 合并到蒸馏知识库")
    print("-" * 40)
    
    merge_into_knowledge_store(all_rules, composite_rules)
    
    print("\n" + "=" * 60)
    print("✅ 壬占汇选批量蒸馏完成!")
    print("=" * 60)
    
    return result


def merge_into_knowledge_store(new_individual_rules, new_composite_rules):
    """将新规则合并到知识库"""
    if not os.path.exists(KS_PATH):
        print("  ⚠️ 知识库不存在，跳过合并")
        return
    
    with open(KS_PATH, 'r', encoding='utf-8') as f:
        ks = json.load(f)
    
    existing_rules = ks.get('knowledge_rules', [])
    print(f"  现有规则数: {len(existing_rules)}")
    
    # 检查重复（基于 rule 文本）
    existing_texts = {r.get('rule', '') for r in existing_rules}
    
    added_individual = 0
    added_composite = 0
    skipped = 0
    
    for r in new_individual_rules:
        r_text = r.get('rule', '')
        if r_text and r_text not in existing_texts:
            # 转换格式为知识库兼容格式
            ks_rule = {
                'rule': r_text,
                'source': r.get('source', 'rzhy'),
                'zhanshi': r.get('zhanshi', ''),
                'created_at': datetime.now().isoformat(),
                'confidence': r.get('confidence', 0.7),
                'extracted_from': r.get('extracted_from', ''),
                'jixiong_signal': r.get('jixiong_signal', 0),
            }
            if r.get('bifa_reference'):
                ks_rule['bifa_reference'] = r['bifa_reference']
            if r.get('keti'):
                ks_rule['keti'] = r['keti']
            
            existing_rules.append(ks_rule)
            existing_texts.add(r_text)
            added_individual += 1
        else:
            skipped += 1
    
    # 组合规则作为"推理链"存储
    existing_chains = ks.get('reasoning_chains', [])
    for r in new_composite_rules:
        chain = {
            'zhanshi': r.get('zhanshi', ''),
            'case_id': r.get('case_id', ''),
            'day_ganzhi': r.get('day_ganzhi', ''),
            'sanchuan': r.get('sanchuan', []),
            'ketis': r.get('all_ketis', []),
            'specials': r.get('specials', []),
            'predicted_jixiong': r.get('predicted_jixiong', ''),
            'original_label': r.get('original_label', ''),
            'composite_score': r.get('jixiong_signal', 0),
            'created_at': datetime.now().isoformat(),
        }
        existing_chains.append(chain)
        added_composite += 1
    
    # 更新知识库
    ks['knowledge_rules'] = existing_rules
    ks['reasoning_chains'] = existing_chains
    ks['updated_at'] = datetime.now().isoformat()
    
    # 更新统计
    stats = ks.get('distill_stats', {})
    stats['total_rules'] = len(existing_rules)
    stats['rzhy_sourced'] = stats.get('rzhy_sourced', 0) + added_individual
    stats['reasoning_chains'] = len(existing_chains)
    ks['distill_stats'] = stats
    
    with open(KS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ks, f, ensure_ascii=False, indent=2)
    
    print(f"  新增单条规则: {added_individual}")
    print(f"  新增推理链: {added_composite}")
    print(f"  跳过重复: {skipped}")
    print(f"  合并后总规则数: {len(existing_rules)}")


if __name__ == '__main__':
    result = batch_distill_rzhy()
    
    # 简单汇总
    print("\n" + "=" * 60)
    print("📋 蒸馏汇总")
    print("=" * 60)
    print(f"  处理案例: {result['total_cases']}")
    print(f"  提取规则: {result['individual_rules_count']}")
    print(f"  推理链: {result['composite_rules_count']}")
    if result['validation']['total_with_label'] > 0:
        print(f"  验证准确率: {result['validation']['accuracy']:.1f}%")
