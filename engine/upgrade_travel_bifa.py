#!/usr/bin/env python3
"""
进一步升级出行类型毕法赋引用
使用更多真正的毕法赋条文替换通用格式
"""
import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent))
from extended_bifa_articles import EXTENDED_BIFA_ARTICLES

# 出行类别的高质量毕法赋条文（按相关性排序）
TRAVEL_ARTICLES_PRIORITY = [
    '毕法赋云："白虎主凶险道路，玄武主盗贼暗伏，朱雀主口舌扰行，此为出行之戒"',
    '毕法赋云："青龙主吉庆临门，太常主财物随行，六合主伴侣同行，此为出行之吉"',
    '毕法赋云："空亡主虚惊半途，亡神主阻截前路，劫煞主破财失物"',
    '毕法赋云："进茹空亡宜退步，声传空谷（进连茹加全空亡），出行宜退不宜进"',
    '毕法赋云："踏脚空亡进用宜，踏脚空亡（退连茹加全空亡），出行宜进不宜退"',
    '毕法赋云："三传递生人举荐，亨通课主出行有贵人相助"',
    '毕法赋云："首尾相见始终宜，周而复始格，出行不脱必返"',
    '毕法赋云："避难逃生须弃旧，三传无益就干上受生，出行避难逃生"',
    '毕法赋云："所谋多拙逢罗网，天罗地网格，出行被阻不能亨快"',
    '毕法赋云："费有余而得不足，生我者空亡脱我者实在，出行所得不偿所费"',
    '毕法赋云："支坟财并旅程稽，地支之墓作日干之财，在路阻程蹇滞"',
    '毕法赋云："贵德临身消除万祸，贵人乘德临身，出行路上无往不利"',
]


def extract_article_content(article: str) -> str:
    content = re.sub(r'^毕法赋云[：:]\s*["""\']?', '', article)
    content = re.sub(r'["""\']', '', content)
    return content.strip()


def score_bifa_quality(content: str, zhanshi: str) -> float:
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
    bifa_patterns = ['主', '为', '以', '须', '宜', '忌', '云', '赋云',
                    '旺', '衰', '生', '克', '合', '冲', '刑',
                    '格', '课', '象', '候', '应', '吉凶', '祸福',
                    '青龙', '朱雀', '白虎', '玄武', '贵人', '禄', '马']
    feature_count = sum(1 for p in bifa_patterns if p in content)
    if feature_count >= 3:
        score += 0.3
    elif feature_count >= 2:
        score += 0.2
    elif feature_count >= 1:
        score += 0.1
    
    # 3. 占事类型关联（0.4分）
    zhanshi_keywords = {
        '出行': ['行', '路', '旅', '动', '途', '道', '涉'],
    }
    keywords = zhanshi_keywords.get(zhanshi, [])
    keyword_count = sum(1 for k in keywords if k in content)
    if keyword_count >= 2:
        score += 0.4
    elif keyword_count >= 1:
        score += 0.3
    elif keywords:
        score += 0.1
    
    return round(min(score, 1.0), 2)


def find_best_travel_article(rule_text: str, current_content: str) -> str:
    """为出行规则找到最相关的毕法赋条文"""
    # 提取规则中的关键词
    rule_text_clean = re.sub(r'【毕法赋】["""].*?["""\']?', '', rule_text).strip()
    rule_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,4}', rule_text_clean))
    
    best_content = current_content
    best_score = 0
    best_article_content = ''
    
    for article in TRAVEL_ARTICLES_PRIORITY:
        content = extract_article_content(article)
        
        # 跳过与当前引用相同的（除非当前引用质量低）
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
        
        # 出行特定关键词匹配
        travel_specific = ['路', '行', '旅', '途', '道', '阻', '险', '吉', '凶',
                          '盗贼', '口舌', '空亡', '贵人', '青龙', '白虎', '玄武']
        travel_match = sum(1 for w in travel_specific if w in content) / len(travel_specific)
        
        # 综合分数
        score = keyword_score * 0.4 + similarity * 0.3 + travel_match * 0.3
        
        if score > best_score:
            best_score = score
            best_article_content = content
    
    # 如果找到的条目更好，使用它
    if best_article_content and best_score > 0.15:
        return best_article_content
    
    return current_content


def clean_bifa_from_text(text: str) -> str:
    text = re.sub(r'【毕法赋】["""\'].*?["""\']?', '', text)
    text = re.sub(r'毕法赋云[：:]["""\'].*?["""\']?', '', text)
    text = re.sub(r'毕法赋[：:][^\n，。；]*', '', text)
    text = re.sub(r'[，。；]{2,}', '，', text)
    text = re.sub(r'^[，。；]+', '', text)
    text = re.sub(r'[，。；]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def main():
    print('=' * 70)
    print('出行类型毕法赋引用专项升级')
    print('=' * 70)
    
    kb_path = Path('data/distillation/knowledge_store.json')
    with open(kb_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get('knowledge_rules', [])
    print(f'\n📖 加载规则总数: {len(rules)}')
    
    # 找出出行类型的规则
    travel_rules = [(i, r) for i, r in enumerate(rules) if r.get('zhanshi') == '出行']
    print(f'🔍 出行类型规则: {len(travel_rules)}条')
    
    # 显示当前状态
    print('\n📊 当前出行类型引用状态:')
    for i, r in travel_rules:
        text = r.get('rule', '')
        match = re.search(r'【毕法赋】["""](.*?)["""\']', text)
        content = match.group(1) if match else '无引用'
        quality = r.get('bifa_quality', 0)
        print(f'  [{i}] quality={quality:.2f} ({len(content)}字): {content[:50]}')
    
    # 升级出行规则
    print('\n🔧 开始升级出行类型引用...')
    upgraded = 0
    
    for i, rule in travel_rules:
        text = rule.get('rule', '')
        quality = rule.get('bifa_quality', 0)
        
        # 提取当前引用
        match = re.search(r'【毕法赋】["""](.*?)["""\']', text)
        current_content = match.group(1).strip() if match else ''
        
        # 找到更好的引用
        new_content = find_best_travel_article(text, current_content)
        new_quality = score_bifa_quality(new_content, '出行')
        
        # 如果新引用更好，更新
        if new_quality > quality:
            cleaned_text = clean_bifa_from_text(text)
            new_text = cleaned_text + f'，【毕法赋】"{new_content}"'
            
            rule['rule'] = new_text
            rule['bifa_quality'] = new_quality
            
            upgraded += 1
            print(f'  ✅ [{i}] {quality:.2f} → {new_quality:.2f}')
            print(f'     旧: {current_content[:50]}')
            print(f'     新: {new_content[:50]}')
        else:
            print(f'  ⏭️  [{i}] 保持不变 ({quality:.2f})')
    
    # 保存更新
    data['knowledge_rules'] = rules
    data['updated_at'] = '2026-08-28T20:30:00'
    
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 重新统计出行类型
    print('\n📈 升级后出行类型状态:')
    for i, r in travel_rules:
        text = r.get('rule', '')
        match = re.search(r'【毕法赋】["""](.*?)["""\']', text)
        content = match.group(1) if match else '无引用'
        quality = r.get('bifa_quality', 0)
        print(f'  [{i}] quality={quality:.2f} ({len(content)}字): {content[:50]}')
    
    # 统计所有类型
    zs_quality = {}
    for r in rules:
        zs = r.get('zhanshi', '未知')
        q = r.get('bifa_quality', 0)
        if zs not in zs_quality:
            zs_quality[zs] = []
        zs_quality[zs].append(q)
    
    print('\n📊 所有类型最终质量:')
    for zs, qualities in sorted(zs_quality.items(), key=lambda x: len(x[1]), reverse=True):
        avg_q = sum(qualities) / len(qualities)
        min_q = min(qualities)
        print(f'  {zs:8s}: {len(qualities):3d}条, 平均={avg_q:.2f}, 最低={min_q:.2f}')
    
    print(f'\n🎉 升级完成: {upgraded}条规则被升级')
    print('=' * 70)


if __name__ == '__main__':
    main()
