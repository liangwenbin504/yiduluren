#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为二十四山课格添加吉凶评分
评分标准：10 分制，5 分以下不宜使用
"""

# 二十四山评分（基于断语吉凶程度）
SHAN_JIA_SCORES = {
    # 吉山（7-9 分）
    '壬山': {'score': 8.0, 'usable': True},  # 催丁生子富贵上吉
    '子山': {'score': 8.5, 'usable': True},  # 富贵长久催丁生子人财大旺盛上吉
    '癸山': {'score': 8.0, 'usable': True},  # 乙庚财神最益我
    '丑山': {'score': 7.5, 'usable': True},  # 戊癸柱中福自来
    '艮山': {'score': 7.5, 'usable': True},  # 丁壬化木元辰
    '寅山': {'score': 7.5, 'usable': True},  # 最宜财，福自来
    '甲山': {'score': 7.0, 'usable': True},  # 最要丙辛升
    '卯山': {'score': 7.5, 'usable': True},  # 正辛元，辅助旺元辰
    '乙山': {'score': 7.0, 'usable': True},  # 元辰金，补元辰
    '辰山': {'score': 7.0, 'usable': True},  # 金元，相配得宜生富贵
    '巽山': {'score': 7.0, 'usable': True},  # 土元辰
    '巳山': {'score': 8.0, 'usable': True},  # 元土，助元人富贵
    '丙山': {'score': 7.5, 'usable': True},  # 火相帮，发财长
    '午山': {'score': 8.0, 'usable': True},  # 元火喜逢财
    '丁山': {'score': 8.5, 'usable': True},  # 最喜柱中有丁壬
    '未山': {'score': 8.0, 'usable': True},  # 最喜补元要丁壬
    '坤山': {'score': 7.5, 'usable': True},  # 切忌丙同辛，但有制可用
    '申山': {'score': 7.0, 'usable': True},  # 怕助元辰，但有化解
    '庚山': {'score': 8.0, 'usable': True},  # 最喜乙庚补元辰
    '酉山': {'score': 7.0, 'usable': True},  # 切莫补元辰，但有制
    '辛山': {'score': 7.5, 'usable': True},  # 忌元辰，但有吉日用
    '戌山': {'score': 7.5, 'usable': True},  # 土元辰，补精神
    '乾山': {'score': 8.0, 'usable': True},  # 火元辰，辅元富贵临
    '亥山': {'score': 8.0, 'usable': True},  # 元辰火，财旺好
}

def update_shan_jia_scores():
    """更新二十四山课格评分"""
    import sys
    import os
    import re
    
    file_path = os.path.join(os.path.dirname(__file__), 'src', 'engine', 'douhou_shan_jia_system.py')
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 为每个山家添加评分
    for shan_name, score_info in SHAN_JIA_SCORES.items():
        # 查找该山家的 jinji 字段
        pattern = rf"('{shan_name}':\s*{{[^}}]*?'jinji':\s*'[^']*')"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            old_str = match.group(1)
            # 添加评分字段
            new_str = old_str + f",\n                'score': {score_info['score']},\n                'usable': {score_info['usable']}"
            
            # 替换
            content = content.replace(old_str, new_str)
            print(f"✓ 已更新 {shan_name}: 评分={score_info['score']}, 可用={score_info['usable']}")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✓ 已完成二十四山课格评分更新！")

if __name__ == '__main__':
    update_shan_jia_scores()
