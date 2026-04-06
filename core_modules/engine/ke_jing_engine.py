#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 64 课经提取与关联引擎

功能：
1. 从《白话大六壬全书》PDF 提取 64 课经
2. 结构化存储课经数据
3. 与起课结果自动关联匹配
4. 在 GUI 中显示匹配的课经
"""

import json
import os
import re

class LiuShiSiKeEngine:
    """64 课经引擎"""
    
    def __init__(self):
        self.ke_jing_data = {}  # 课经数据
        self.data_file = "data/64_ke_jing.json"
        self.load_data()
    
    def load_data(self):
        """加载课经数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.ke_jing_data = json.load(f)
    
    def save_data(self):
        """保存课经数据"""
        os.makedirs('data', exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.ke_jing_data, f, ensure_ascii=False, indent=2)
    
    def add_ke_jing(self, ke_name, ke_type, features, description, judgment, examples=None):
        """添加课经"""
        self.ke_jing_data[ke_name] = {
            'ke_name': ke_name,
            'ke_type': ke_type,
            'features': features,
            'description': description,
            'judgment': judgment,
            'examples': examples or []
        }
        self.save_data()
    
    def match_ke_jing(self, qi_ke_result):
        """
        匹配课经
        
        :param qi_ke_result: 起课结果
        :return: 匹配的课经列表
        """
        matched = []
        
        # 1. 根据课体匹配
        ke_ti = qi_ke_result.get('课体', '')
        qi_fa = qi_ke_result.get('起法', '')
        
        for ke_name, ke_data in self.ke_jing_data.items():
            score = 0
            reasons = []
            
            # 课体匹配
            if ke_ti == ke_name or qi_fa.replace('法', '') in ke_name:
                score += 50
                reasons.append(f"课体匹配：{ke_ti}")
            
            # 特征匹配
            features = ke_data.get('features', {})
            if features:
                # 三传特征匹配
                if 'chu_chuan' in features:
                    if qi_ke_result.get('初传') == features['chu_chuan']:
                        score += 20
                        reasons.append(f"初传匹配：{features['chu_chuan']}")
                
                # 特殊格局匹配
                if 'te_shu' in features:
                    te_shu = features['te_shu']
                    if te_shu in qi_ke_result.get('格局', ''):
                        score += 30
                        reasons.append(f"特殊格局匹配：{te_shu}")
            
            # 分数超过阈值，认为匹配
            if score >= 50:
                matched.append({
                    'ke_name': ke_name,
                    'ke_data': ke_data,
                    'score': score,
                    'reasons': reasons
                })
        
        # 按分数排序
        matched.sort(key=lambda x: x['score'], reverse=True)
        
        return matched
    
    def get_all_ke_jing_list(self):
        """获取所有课经列表"""
        return list(self.ke_jing_data.keys())
    
    def get_ke_jing_detail(self, ke_name):
        """获取课经详情"""
        return self.ke_jing_data.get(ke_name, None)


# 示例：初始化 64 课经基础数据
def init_64_ke_jing():
    """初始化 64 课经基础数据"""
    engine = LiuShiSiKeEngine()
    
    # 示例数据 - 实际应从 PDF 提取
    ke_jing_list = [
        {
            'ke_name': '涉害课',
            'ke_type': '涉害法',
            'features': {
                'te_shu': '孟仲季'
            },
            'description': '涉害课者，用神相克，涉害深浅也。',
            'judgment': '取涉害最深者为用，浅者次之。',
            'examples': []
        },
        {
            'ke_name': '见机课',
            'ke_type': '涉害法',
            'features': {
                'te_shu': '孟上神'
            },
            'description': '见机课者，涉害相等，取孟上神发用也。',
            'judgment': '事主见机而作，当机立断。',
            'examples': []
        },
        {
            'ke_name': '察微课',
            'ke_type': '涉害法',
            'features': {
                'te_shu': '仲上神'
            },
            'description': '察微课者，涉害相等，无孟取仲也。',
            'judgment': '事主察微知著，谨慎行事。',
            'examples': []
        },
        {
            'ke_name': '伏吟课',
            'ke_type': '伏吟法',
            'features': {
                'te_shu': '月将=占时'
            },
            'description': '伏吟课者，天地盘相同，神将伏而不动也。',
            'judgment': '事主伏而不动，宜静不宜动。',
            'examples': []
        },
        {
            'ke_name': '反吟课',
            'ke_type': '反吟法',
            'features': {
                'te_shu': '月将冲占时'
            },
            'description': '反吟课者，天地盘对冲，神将反复不定也。',
            'judgment': '事主反复无常，进退两难。',
            'examples': []
        },
    ]
    
    for ke_jing in ke_jing_list:
        engine.add_ke_jing(
            ke_name=ke_jing['ke_name'],
            ke_type=ke_jing['ke_type'],
            features=ke_jing['features'],
            description=ke_jing['description'],
            judgment=ke_jing['judgment'],
            examples=ke_jing['examples']
        )
    
    print(f"已初始化 {len(engine.ke_jing_data)} 条课经数据")
    return engine


if __name__ == '__main__':
    # 初始化 64 课经
    engine = init_64_ke_jing()
    
    # 测试匹配
    test_result = {
        '课体': '涉害课',
        '起法': '涉害法',
        '初传': '酉',
        '格局': '见机格'
    }
    
    matched = engine.match_ke_jing(test_result)
    print(f"\n匹配到的课经：")
    for item in matched:
        print(f"  {item['ke_name']} - 分数：{item['score']}")
        for reason in item['reasons']:
            print(f"    - {reason}")
