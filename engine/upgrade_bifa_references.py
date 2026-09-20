#!/usr/bin/env python3
"""
升级毕法赋引用质量脚本
为低质量引用(0.75)的规则添加真正的毕法赋条文
"""
import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

# 添加engine路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载扩展条文库
from extended_bifa_articles import EXTENDED_BIFA_ARTICLES

# 占事类型映射（知识库中的名称 -> 扩展条文库的名称）
ZHANSHI_MAPPING = {
    '占宅': '家宅',
    '家宅': '家宅',
    '婚姻': '婚姻',
    '出行': '出行',
    '功名': '功名',
    '官讼': '官讼',
    '求财': '求财',
    '占病': '疾病',
    '疾病': '疾病',
}

# 毕法赋特征词（用于质量评分）
BIFA_PATTERNS = ['主', '为', '以', '须', '宜', '忌', '云', '赋云',
                '旺', '衰', '生', '克', '合', '冲', '刑',
                '格', '课', '象', '候', '应', '吉凶', '祸福',
                '青龙', '朱雀', '白虎', '玄武', '贵人', '禄', '马',
                '干支', '三传', '四课']


def extract_article_content(article: str) -> str:
    """从扩展条文库条目中提取条文内容"""
    # 移除"毕法赋云："前缀
    content = re.sub(r'^毕法赋云[：:]\s*["""\']?', '', article)
    # 移除引号
    content = re.sub(r'["""\']', '', content)
    return content.strip()


def score_bifa_quality(content: str, zhanshi: str) -> float:
    """评分毕法赋引用质量"""
    score = 0.0
    
    # 1. 长度评分（0.3分）
    length = len(content)
    if length >= 30:
        score += 0.3
    elif length >= 20:
        score += 0.2
    elif length >= 15:
        score += 0.1
    else:
        score += 0.05
    
    # 2. 毕法赋特征词（0.3分）
    feature_count = sum(1 for p in BIFA_PATTERNS if p in content)
    if feature_count >= 3:
        score += 0.3
    elif feature_count >= 2:
        score += 0.2
    elif feature_count >= 1:
        score += 0.1
    
    # 3. 占事类型关联（0.4分）
    zhanshi_keywords = {
        '家宅': ['宅', '家', '屋', '人', '房', '居'],
        '婚姻': ['婚', '姻', '夫', '妇', '配', '合'],
        '出行': ['行', '路', '旅', '动', '途'],
        '功名': ['名', '功', '官', '贵', '考', '试'],
        '官讼': ['讼', '官', '争', '法', '刑'],
        '求财': ['财', '利', '金', '钱', '富'],
        '疾病': ['病', '疾', '医', '治', '愈'],
    }
    mapped_zs = ZHANSHI_MAPPING.get(zhanshi, zhanshi)
    keywords = zhanshi_keywords.get(mapped_zs, [])
    keyword_count = sum(1 for k in keywords if k in content)
    if keyword_count >= 2:
        score += 0.4
    elif keyword_count >= 1:
        score += 0.3
    elif keywords:  # 有关键词列表但未匹配
        score += 0.1
    
    return round(min(score, 1.0), 2)


def find_best_article(rule_text: str, zhanshi: str, current_content: str) -> tuple:
    """为规则找到最相关的毕法赋条文"""
    mapped_zs = ZHANSHI_MAPPING.get(zhanshi, zhanshi)
    articles = EXTENDED_BIFA_ARTICLES.get(mapped_zs, [])
    
    if not articles:
        # 尝试使用谋事类型的条目作为兜底
        articles = EXTENDED_BIFA_ARTICLES.get('谋事', [])
    
    if not articles:
        return current_content, 0.3  # 无可用条目
    
    rule_text_clean = re.sub(r'【毕法赋】["""].*?["""\']?', '', rule_text).strip()
    
    # 提取规则中的关键词
    rule_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', rule_text_clean))
    
    best_article = current_content
    best_score = 0
    best_similarity = 0
    
    for article in articles:
        content = extract_article_content(article)
        
        # 跳过与当前引用相同的
        if content == current_content:
            continue
        
        # 计算关键词重叠
        article_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', content))
        if article_keywords and rule_keywords:
            overlap = len(rule_keywords & article_keywords)
            keyword_score = overlap / min(len(rule_keywords), len(article_keywords)) if min(len(rule_keywords), len(article_keywords)) > 0 else 0
        else:
            keyword_score = 0
        
        # 计算文本相似度
        similarity = SequenceMatcher(None, rule_text_clean, content).ratio()
        
        # 计算特征词匹配
        feature_match = sum(1 for w in BIFA_PATTERNS if w in content) / len(BIFA_PATTERNS)
        
        # 综合分数
        score = keyword_score * 0.5 + similarity * 0.3 + feature_match * 0.2
        
        if score > best_score:
            best_score = score
            best_article = content
            best_similarity = similarity
    
    # 如果找到的条目相似度太低，保持原样
    if best_score < 0.1 and current_content:
        return current_content, 0.3
    
    return best_article, best_score


def clean_bifa_from_text(text: str) -> str:
    """清除文本中现有的毕法赋引用"""
    # 清除【毕法赋】"..."格式
    text = re.sub(r'【毕法赋】["""\'].*?["""\']?', '', text)
    # 清除毕法赋云："..."格式
    text = re.sub(r'毕法赋云[：:]["""\'].*?["""\']?', '', text)
    # 清除毕法赋: ... 格式
    text = re.sub(r'毕法赋[：:][^\n，。；]*', '', text)
    # 清理多余标点
    text = re.sub(r'[，。；]{2,}', '，', text)
    text = re.sub(r'^[，。；]+', '', text)
    text = re.sub(r'[，。；]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def main():
    """主函数：升级毕法赋引用"""
    print('=' * 70)
    print('升级毕法赋引用质量脚本')
    print('=' * 70)
    
    # 加载知识库
    kb_path = Path('data/distillation/knowledge_store.json')
    with open(kb_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get('knowledge_rules', [])
    print(f'\n📖 加载规则总数: {len(rules)}')
    
    # 统计需要升级的规则
    need_upgrade = []
    for i, r in enumerate(rules):
        quality = r.get('bifa_quality', 0)
        if quality < 0.85:
            need_upgrade.append((i, r))
    
    print(f'🔍 需要升级的规则: {len(need_upgrade)}条 (quality < 0.85)')
    
    if not need_upgrade:
        print('\n✅ 所有规则引用质量已达标！')
        return
    
    # 显示需要升级的规则分布
    zs_dist = {}
    for _, r in need_upgrade:
        zs = r.get('zhanshi', '未知')
        if zs not in zs_dist:
            zs_dist[zs] = 0
        zs_dist[zs] += 1
    
    print('\n📊 需要升级的规则按占事类型分布:')
    for zs, count in sorted(zs_dist.items(), key=lambda x: x[1], reverse=True):
        print(f'  {zs}: {count}条')
    
    # 升级规则
    print('\n🔧 开始升级毕法赋引用...')
    upgraded_count = 0
    upgraded_rules = []
    
    for i, rule in need_upgrade:
        text = rule.get('rule', '')
        zhanshi = rule.get('zhanshi', '')
        old_quality = rule.get('bifa_quality', 0)
        
        # 提取当前毕法赋引用
        match = re.search(r'【毕法赋】["""](.*?)["""\']', text)
        current_content = match.group(1).strip() if match else ''
        
        # 找到更好的毕法赋条文
        new_content, match_score = find_best_article(text, zhanshi, current_content)
        
        # 计算新质量
        new_quality = score_bifa_quality(new_content, zhanshi)
        
        # 如果新引用更好，更新
        if new_quality > old_quality:
            # 清除旧引用，添加新引用
            cleaned_text = clean_bifa_from_text(text)
            new_text = cleaned_text + f'，【毕法赋】"{new_content}"'
            
            rule['rule'] = new_text
            rule['bifa_quality'] = new_quality
            rule['bifa_upgraded_at'] = '2026-08-28T20:00:00'
            
            upgraded_count += 1
            upgraded_rules.append((i, zhanshi, old_quality, new_quality, current_content[:30], new_content[:30]))
            
            if upgraded_count <= 20:  # 只显示前20条
                print(f'  ✅ [{i}] {zhanshi}: {old_quality:.2f} → {new_quality:.2f}')
                print(f'     旧: {current_content[:40]}...')
                print(f'     新: {new_content[:40]}...')
    
    # 更新知识库
    data['knowledge_rules'] = rules
    data['updated_at'] = '2026-08-28T20:00:00'
    
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'\n📊 升级完成:')
    print(f'  升级规则数: {upgraded_count}')
    print(f'  跳过规则数: {len(need_upgrade) - upgraded_count}')
    
    # 重新统计质量分布
    quality_dist = {'high(≥0.8)': 0, 'medium(0.5-0.8)': 0, 'low(<0.5)': 0}
    for r in rules:
        q = r.get('bifa_quality', 0)
        if q >= 0.8:
            quality_dist['high(≥0.8)'] += 1
        elif q >= 0.5:
            quality_dist['medium(0.5-0.8)'] += 1
        else:
            quality_dist['low(<0.5)'] += 1
    
    print(f'\n📈 更新后质量分布:')
    for level, count in quality_dist.items():
        print(f'  {level}: {count}条')
    
    # 按占事类型统计
    zs_quality = {}
    for r in rules:
        zs = r.get('zhanshi', '未知')
        q = r.get('bifa_quality', 0)
        if zs not in zs_quality:
            zs_quality[zs] = []
        zs_quality[zs].append(q)
    
    print(f'\n📈 更新后各类型质量:')
    for zs, qualities in sorted(zs_quality.items(), key=lambda x: len(x[1]), reverse=True):
        avg_q = sum(qualities) / len(qualities)
        print(f'  {zs:8s}: {len(qualities):3d}条, 平均质量={avg_q:.2f}')
    
    # 生成报告
    report = {
        'generated_at': '2026-08-28T20:00:00',
        'total_rules': len(rules),
        'upgraded_count': upgraded_count,
        'skipped_count': len(need_upgrade) - upgraded_count,
        'upgraded_rules': [
            {
                'index': idx,
                'zhanshi': zs,
                'old_quality': old_q,
                'new_quality': new_q,
                'old_bifa': old_content,
                'new_bifa': new_content
            }
            for idx, zs, old_q, new_q, old_content, new_content in upgraded_rules
        ],
        'quality_distribution': quality_dist,
        'zhanshi_quality': {
            zs: {
                'count': len(qs),
                'avg_quality': round(sum(qs) / len(qs), 2),
                'min_quality': min(qs),
                'max_quality': max(qs)
            }
            for zs, qs in zs_quality.items()
        }
    }
    
    report_path = Path('data/distillation/bifa_upgrade_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'\n📄 报告已保存: {report_path}')
    print('\n' + '=' * 70)
    print('✅ 毕法赋引用升级完成')
    print('=' * 70)


if __name__ == '__main__':
    main()
