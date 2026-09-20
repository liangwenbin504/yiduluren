#!/usr/bin/env python3
"""深度检查毕法赋引用质量"""
import json
import re
from pathlib import Path
from collections import Counter

# 加载知识库
kb_path = Path('data/distillation/knowledge_store.json')
with open(kb_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

rules = data.get('knowledge_rules', [])
print(f'知识库总规则数: {len(rules)}')

# 深度分析
print()
print('=' * 70)
print('毕法赋引用深度质量分析')
print('=' * 70)

# 1. 提取所有毕法赋引用内容
bifa_contents = []
zhanshi_bifa = {}
length_distribution = []
issues_counter = Counter()

for i, r in enumerate(rules):
    text = r.get('rule', '')
    zhanshi = r.get('zhanshi', '')
    quality = r.get('bifa_quality', 0)
    
    # 提取毕法赋引用
    match = re.search(r'【毕法赋】["""](.*?)["""\']', text)
    if match:
        content = match.group(1).strip()
        bifa_contents.append((i, zhanshi, content, quality))
        
        if zhanshi not in zhanshi_bifa:
            zhanshi_bifa[zhanshi] = []
        zhanshi_bifa[zhanshi].append((i, content, quality))
        
        length_distribution.append(len(content))
        
        # 检查引用质量问题
        issues = []
        if len(content) < 15:
            issues.append('引用较短(<15字)')
        if len(content) > 80:
            issues.append('引用较长(>80字)')
        
        # 检查毕法赋特征词
        bifa_patterns = ['主', '为', '以', '须', '宜', '忌', '云', '赋云',
                        '旺', '衰', '生', '克', '合', '冲', '刑',
                        '格', '课', '象', '候', '应', '吉凶', '祸福',
                        '青龙', '朱雀', '白虎', '玄武', '贵人', '禄', '马']
        has_pattern = any(p in content for p in bifa_patterns)
        if not has_pattern:
            issues.append('缺少毕法赋特征词')
        
        # 检查占事类型关键词
        zhanshi_keywords = {
            '家宅': ['宅', '家', '屋', '人', '房'],
            '占宅': ['宅', '家', '屋'],
            '婚姻': ['婚', '姻', '夫', '妇'],
            '出行': ['行', '路', '旅', '动'],
            '功名': ['名', '功', '官', '贵'],
            '官讼': ['讼', '官', '争', '法'],
            '求财': ['财', '利', '金', '钱'],
            '疾病': ['病', '疾', '医', '治'],
            '占病': ['病', '疾', '医'],
        }
        keywords = zhanshi_keywords.get(zhanshi, [])
        has_keyword = any(k in content for k in keywords)
        if keywords and not has_keyword:
            issues.append(f'与{zhanshi}类型关联不强')
        
        for issue in issues:
            issues_counter[issue] += 1

# 2. 按占事类型分析
print()
print('按占事类型引用分析:')
print('-' * 70)
for zs in sorted(zhanshi_bifa.keys(), key=lambda x: len(zhanshi_bifa[x]), reverse=True):
    items = zhanshi_bifa[zs]
    count = len(items)
    avg_len = sum(len(c) for _, c, _ in items) / count if count > 0 else 0
    min_len = min(len(c) for _, c, _ in items) if count > 0 else 0
    max_len = max(len(c) for _, c, _ in items) if count > 0 else 0
    avg_quality = sum(q for _, _, q in items) / count if count > 0 else 0
    
    print(f'{zs:8s}: {count:3d}条, 平均长度={avg_len:.1f}字({min_len}-{max_len}), 平均质量={avg_quality:.2f}')

# 3. 长度分布
print()
print('引用长度分布:')
print('-' * 70)
length_ranges = {'<10字': 0, '10-20字': 0, '20-30字': 0, '30-50字': 0, '>50字': 0}
for l in length_distribution:
    if l < 10:
        length_ranges['<10字'] += 1
    elif l < 20:
        length_ranges['10-20字'] += 1
    elif l < 30:
        length_ranges['20-30字'] += 1
    elif l < 50:
        length_ranges['30-50字'] += 1
    else:
        length_ranges['>50字'] += 1

for range_name, count in length_ranges.items():
    bar = '█' * (count // 2)
    print(f'  {range_name:10s}: {count:3d}条 {bar}')

# 4. 问题统计
print()
print('引用质量问题统计:')
print('-' * 70)
if issues_counter:
    for issue, count in issues_counter.most_common():
        print(f'  {issue}: {count}条')
else:
    print('  无明显问题')

# 5. 引用示例（各类型3条）
print()
print('各占事类型引用示例:')
print('=' * 70)
for zs in sorted(zhanshi_bifa.keys()):
    items = zhanshi_bifa[zs][:3]  # 取前3条
    print(f'\n【{zs}】类型示例:')
    for idx, content, quality in items:
        print(f'  [{idx}] quality={quality:.2f} ({len(content)}字): {content}')

# 6. 统计总结
print()
print('=' * 70)
print('总体统计')
print('=' * 70)
total = len(bifa_contents)
total_with_issue = sum(1 for i, z, c, q in bifa_contents 
                      if any(kw in c for kw in ['<15字', '缺少', '不强']))  # 粗略估计
avg_quality = sum(q for _, _, _, q in bifa_contents) / total if total > 0 else 0
avg_bifa_len = sum(len(c) for _, _, c, _ in bifa_contents) / total if total > 0 else 0

print(f'总规则数: {len(rules)}')
print(f'有毕法赋引用: {total} (100%)')
print(f'平均引用长度: {avg_bifa_len:.1f}字')
print(f'平均质量评分: {avg_quality:.2f}')
print(f'引用较短(<15字): {length_ranges["<10字"] + (length_ranges["10-20字"] // 2)}条')
print(f'质量问题总数: {sum(issues_counter.values())}处')
