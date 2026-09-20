#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬灵感触发模块
在模糊判断时激发创造性解读，并通过反馈不断进化

核心机制：
1. 模糊度检测 - 识别课式中的矛盾、冲突、不确定性
2. 灵感生成 - 通过类比、隐喻、跨领域联想产生洞见
3. 进化学习 - 记录灵感准确性，动态调整触发阈值
"""

import json
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any


class FuzzinessDetector:
    """模糊度检测器 - 识别课式中的不确定性因素"""
    
    @staticmethod
    def calculate_fuzziness(keshi: Dict) -> float:
        """计算课式的模糊度分数 (0-1)，越高越模糊"""
        score = 0.0
        factors = []
        
        # 1. 三传矛盾检测
        sanchuan = keshi.get('sanchuan', [])
        if len(sanchuan) >= 3:
            # 初传与末传方向相反
            if '生' in str(sanchuan[0]) and '克' in str(sanchuan[-1]):
                factors.append(0.2)
            if '吉' in str(sanchuan[0]).lower() and '凶' in str(sanchuan[-1]).lower():
                factors.append(0.15)
        
        # 2. 神将冲突检测
        tianjiang = keshi.get('tianjiang', [])
        if tianjiang:
            has_jili = any(t in ['青龙', '贵人', '六合', '太常'] for t in tianjiang)
            has_xiongxiong = any(t in ['白虎', '螣蛇', '玄武', '天空'] for t in tianjiang)
            if has_jili and has_xiongxiong:
                factors.append(0.25)
        
        # 3. 空亡影响检测
        kongwang = keshi.get('kongwang', '')
        if kongwang:
            if any(k in sanchuan for k in kongwang):
                factors.append(0.2)
        
        # 4. 课体复杂性检测
        keti = keshi.get('keti', '')
        complex_keti = ['伏吟', '返吟', '八专', '别责', '昴星']
        if keti in complex_keti:
            factors.append(0.15)
        
        # 5. 半合/半冲检测（不完整的关系）
        hechong = keshi.get('hechong', '')
        if '半合' in hechong or '半冲' in hechong:
            factors.append(0.1)
        
        # 6. 生克链断裂检测
        if '生克不明' in str(keshi.get('fenxi', '')):
            factors.append(0.2)
        
        # 综合计算（考虑因素数量的衰减）
        if factors:
            base_score = sum(factors) / len(factors)
            # 因素越多，模糊度越高
            multiplier = 0.7 + len(factors) * 0.05
            score = min(base_score * multiplier, 1.0)
        
        return score


class InspirationGenerator:
    """灵感生成器 - 通过多种机制产生创造性解读"""
    
    # 跨领域类比库
    ANALOGY_LIBRARY = {
        '自然现象': ['春风解冻', '夏日炎炎', '秋高气爽', '冬雪纷飞', 
                     '山高水长', '云开雾散', '电闪雷鸣', '滴水穿石'],
        '人生阶段': ['少年壮志', '青年拼搏', '中年稳健', '老年通达',
                     '初生牛犊', '如日中天', '夕阳无限', '返璞归真'],
        '军事谋略': ['声东击西', '暗度陈仓', '欲擒故纵', '以退为进',
                     '釜底抽薪', '金蝉脱壳', '借刀杀人', '隔岸观火'],
        '植物生长': ['种子萌芽', '破土而出', '茁壮成长', '开花结果',
                     '根深叶茂', '枯木逢春', '老树新枝', '春华秋实'],
        '水流形态': ['小溪潺潺', '江河奔腾', '大海澎湃', '水滴石穿',
                     '水到渠成', '逆流而上', '随波逐流', '静水深流'],
        '天气变化': ['晴空万里', '乌云密布', '狂风暴雨', '雨后彩虹',
                     '山雨欲来', '拨云见日', '风平浪静', '雷电交加']
    }
    
    # 隐喻转换规则
    METAPHOR_RULES = {
        '青龙': {'积极': ['龙头高昂', '青云直上', '龙行虎步'], 
                 '消极': ['龙困浅滩', '龙游浅水']},
        '白虎': {'积极': ['白虎下山', '虎虎生威', '猛虎添翼'],
                 '消极': ['虎落平阳', '谈虎色变']},
        '朱雀': {'积极': ['朱雀衔书', '妙笔生花', '佳音传来'],
                 '消极': ['口舌是非', '纸上谈兵']},
        '玄武': {'积极': ['深藏不露', '暗度陈仓', '厚积薄发'],
                 '消极': ['阴谋诡计', '暗箭难防']},
        '生': ['如沐春风', '雨露滋润', '相辅相成'],
        '克': ['狭路相逢', '针锋相对', '此消彼长'],
        '合': ['珠联璧合', '同心协力', '水到渠成'],
        '冲': ['波涛汹涌', '急流勇退', '峰回路转']
    }
    
    @classmethod
    def generate_inspiration(cls, keshi: Dict, fuzziness: float) -> List[Dict]:
        """生成灵感解读"""
        inspirations = []
        
        # 根据模糊度调整灵感激进程度
        radical_level = min(fuzziness * 2, 1.0)
        
        # 1. 跨领域类比灵感
        if random.random() < 0.7 + radical_level * 0.2:
            analogy = cls._generate_analogy(keshi, radical_level)
            if analogy:
                inspirations.append(analogy)
        
        # 2. 隐喻转换灵感
        if random.random() < 0.6 + radical_level * 0.3:
            metaphor = cls._generate_metaphor(keshi)
            if metaphor:
                inspirations.append(metaphor)
        
        # 3. 反向思维灵感（高模糊度时触发）
        if fuzziness > 0.5 and random.random() < radical_level:
            reversal = cls._generate_reversal(keshi)
            if reversal:
                inspirations.append(reversal)
        
        # 4. 整体涌现灵感
        if random.random() < 0.5 + radical_level * 0.3:
            emergence = cls._generate_emergence(keshi)
            if emergence:
                inspirations.append(emergence)
        
        return inspirations
    
    @classmethod
    def _generate_analogy(cls, keshi: Dict, radical: float) -> Optional[Dict]:
        """生成跨领域类比灵感"""
        tianjiang = keshi.get('tianjiang', [])
        sanchuan = keshi.get('sanchuan', [])
        
        # 选择类比领域
        domain = random.choice(list(cls.ANALOGY_LIBRARY.keys()))
        analogy_items = cls.ANALOGY_LIBRARY[domain]
        
        # 根据课式特征选择类比
        if '青龙' in tianjiang or '吉' in str(keshi.get('jixiong', '')):
            item = random.choice([a for a in analogy_items if '春' in a or '高' in a or '成' in a or '长' in a])
        elif '白虎' in tianjiang or '凶' in str(keshi.get('jixiong', '')):
            item = random.choice([a for a in analogy_items if '冬' in a or '暴' in a or '雨' in a or '雷' in a])
        else:
            item = random.choice(analogy_items)
        
        return {
            'type': 'analogy',
            'domain': domain,
            'analogy': item,
            'interpretation': cls._interpret_analogy(item, keshi),
            'confidence': 0.6 + radical * 0.2
        }
    
    @classmethod
    def _interpret_analogy(cls, analogy: str, keshi: Dict) -> str:
        """解读类比的含义"""
        interpretations = {
            '春风解冻': '当前困境即将化解，新的机遇正在萌芽',
            '山高水长': '格局宏大，需要长期布局，不可急于求成',
            '云开雾散': '迷雾即将散去，事情将变得明朗',
            '滴水穿石': '需要坚持不懈，以柔克刚',
            '电闪雷鸣': '突发状况可能出现，需做好应对准备',
            '种子萌芽': '初始阶段，潜力巨大，耐心等待',
            '根深叶茂': '基础扎实，发展稳健，前景良好',
            '枯木逢春': '看似无望的局面可能出现转机',
            '水到渠成': '时机成熟，事情自然会成功',
            '逆流而上': '需要克服困难，逆势而为',
            '静水深流': '表面平静，实则暗流涌动，需谨慎',
            '雨后彩虹': '经历风雨后将迎来美好结果',
            '山雨欲来': '大事将至，提前做好准备',
            '金蝉脱壳': '巧妙脱身，避免陷入困境',
            '欲擒故纵': '先放后收，以退为进的策略',
            '如日中天': '处于鼎盛时期，把握良机',
            '夕阳无限': '虽近尾声，但仍有余晖可享'
        }
        return interpretations.get(analogy, f"类比 '{analogy}'，暗示事情将按此规律发展")
    
    @classmethod
    def _generate_metaphor(cls, keshi: Dict) -> Optional[Dict]:
        """生成隐喻转换灵感"""
        sanchuan = keshi.get('sanchuan', [])
        tianjiang = keshi.get('tianjiang', [])
        
        metaphor_parts = []
        
        # 为三传各传生成隐喻
        for i, zhuan in enumerate(sanchuan[:3]):
            zhuan_str = str(zhuan)
            for key, values in cls.METAPHOR_RULES.items():
                if key in zhuan_str:
                    if isinstance(values, dict):
                        # 有积极/消极之分
                        if '吉' in zhuan_str or '生' in zhuan_str:
                            metaphor_parts.append(random.choice(values.get('积极', [])))
                        else:
                            metaphor_parts.append(random.choice(values.get('消极', [])))
                    else:
                        metaphor_parts.append(random.choice(values))
                    break
        
        if metaphor_parts:
            return {
                'type': 'metaphor',
                'chain': metaphor_parts,
                'narrative': cls._build_narrative(metaphor_parts),
                'confidence': 0.7
            }
        return None
    
    @classmethod
    def _build_narrative(cls, parts: List[str]) -> str:
        """将隐喻片段组合成连贯的叙事"""
        if len(parts) == 1:
            return f"初传 {parts[0]}，开局即见端倪"
        elif len(parts) == 2:
            return f"初传 {parts[0]}，末传 {parts[1]}，前后呼应，事有因果"
        else:
            return f"初传 {parts[0]}，中传 {parts[1]}，末传 {parts[2]}，三传连珠，大势已成"
    
    @classmethod
    def _generate_reversal(cls, keshi: Dict) -> Optional[Dict]:
        """生成反向思维灵感 - 挑战传统判断"""
        original = keshi.get('jixiong', '中性')
        
        reversal_ideas = [
            {'condition': '吉', 'idea': '物极必反，盛极而衰', 'suggestion': '见好就收，不可贪多'},
            {'condition': '凶', 'idea': '否极泰来，绝处逢生', 'suggestion': '坚守信念，等待转机'},
            {'condition': '中性', 'idea': '静极生动，暗流涌动', 'suggestion': '保持警觉，准备应对变化'}
        ]
        
        for idea in reversal_ideas:
            if idea['condition'] in original or (original == '中性' and idea['condition'] == '中性'):
                return {
                    'type': 'reversal',
                    'original_judgment': original,
                    'reversal_idea': idea['idea'],
                    'suggestion': idea['suggestion'],
                    'confidence': 0.5
                }
        return None
    
    @classmethod
    def _generate_emergence(cls, keshi: Dict) -> Optional[Dict]:
        """生成整体涌现灵感 - 从系统角度看课式"""
        keti = keshi.get('keti', '')
        sike = keshi.get('sike', [])
        sanchuan = keshi.get('sanchuan', [])
        
        emergence_patterns = {
            '重审课': '反复审议，多方考量，最终定案',
            '元首课': '一锤定音，开局即定大局',
            '比用课': '多方竞争，择优选取',
            '涉害课': '利害交织，权衡利弊',
            '遥克课': '远因触发，间接影响',
            '伏吟课': '原地徘徊，等待时机',
            '返吟课': '快速反复，变动频繁'
        }
        
        pattern_desc = emergence_patterns.get(keti, '复杂多变的局势')
        
        return {
            'type': 'emergence',
            'pattern': keti,
            'system_view': pattern_desc,
            'holistic_judgment': cls._holistic_view(keshi, pattern_desc),
            'confidence': 0.65
        }
    
    @classmethod
    def _holistic_view(cls, keshi: Dict, pattern: str) -> str:
        """生成整体视角的判断"""
        views = {
            '反复审议，多方考量，最终定案': '目前处于决策阶段，需要广泛听取意见，谨慎做出选择',
            '一锤定音，开局即定大局': '开局至关重要，第一步的选择将决定最终结果',
            '多方竞争，择优选取': '面临多种选择，需要比较分析，选择最有利的方案',
            '利害交织，权衡利弊': '利弊共存，需要仔细权衡，做出最优决策',
            '远因触发，间接影响': '注意看似无关的因素，可能是问题的关键',
            '原地徘徊，等待时机': '当前不宜行动，等待合适的时机再动',
            '快速反复，变动频繁': '局势多变，保持灵活，随时调整策略',
            '复杂多变的局势': '多种因素相互作用，需要系统分析，把握主线'
        }
        return views.get(pattern, '从整体看，事情正朝着综合方向发展')


class EvolutionLearner:
    """进化学习器 - 记录灵感准确性，动态优化"""
    
    def __init__(self, memory_path: str = None):
        self.memory_path = memory_path or 'e:\\仪度六壬择日\\yiduluren\\_memory\\inspiration_history.json'
        self.history = self._load_history()
        self.threshold = self._calculate_optimal_threshold()
    
    def _load_history(self) -> List[Dict]:
        """加载灵感历史记录"""
        try:
            with open(self.memory_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_history(self):
        """保存灵感历史记录"""
        with open(self.memory_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def record_inspiration(self, inspiration: Dict, keshi_hash: str, actual_result: str = None):
        """记录灵感（可后续补充实际结果）"""
        record = {
            'id': hashlib.md5(f"{keshi_hash}{datetime.now()}".encode()).hexdigest(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'keshi_hash': keshi_hash,
            'inspiration_type': inspiration['type'],
            'content': inspiration,
            'actual_result': actual_result,
            'accuracy': None,
            'feedback': None
        }
        self.history.append(record)
        self._save_history()
    
    def update_accuracy(self, inspiration_id: str, actual_result: str, feedback: str = None):
        """更新灵感的准确性评估"""
        for record in self.history:
            if record['id'] == inspiration_id:
                record['actual_result'] = actual_result
                record['feedback'] = feedback
                
                # 简单的准确性判断
                content = str(record['content'])
                if '吉' in content.lower() and '涨' in actual_result.lower():
                    record['accuracy'] = 1.0
                elif '凶' in content.lower() and '跌' in actual_result.lower():
                    record['accuracy'] = 1.0
                elif ('吉' in content.lower() and '跌' in actual_result.lower()) or \
                     ('凶' in content.lower() and '涨' in actual_result.lower()):
                    record['accuracy'] = 0.0
                else:
                    record['accuracy'] = 0.5  # 中性或不明确
                
                self._save_history()
                self.threshold = self._calculate_optimal_threshold()
                break
    
    def _calculate_optimal_threshold(self) -> float:
        """计算最优触发阈值"""
        if len(self.history) < 10:
            return 0.4  # 默认阈值
        
        # 统计灵感类型的准确率
        accurate_count = sum(1 for r in self.history if r.get('accuracy') == 1.0)
        total_count = sum(1 for r in self.history if r.get('accuracy') is not None)
        
        if total_count == 0:
            return 0.4
        
        accuracy_rate = accurate_count / total_count
        
        # 动态调整阈值：准确率高则降低阈值（更易触发），准确率低则提高阈值
        optimal_threshold = 0.4 - (accuracy_rate - 0.5) * 0.2
        return max(0.2, min(0.7, optimal_threshold))
    
    def get_statistics(self) -> Dict:
        """获取灵感统计信息"""
        stats = {
            'total_records': len(self.history),
            'evaluated_records': sum(1 for r in self.history if r.get('accuracy') is not None),
            'overall_accuracy': 0.0,
            'type_distribution': {},
            'current_threshold': self.threshold
        }
        
        if stats['evaluated_records'] > 0:
            accurate = sum(1 for r in self.history if r.get('accuracy') == 1.0)
            stats['overall_accuracy'] = accurate / stats['evaluated_records']
        
        for record in self.history:
            insp_type = record.get('inspiration_type', 'unknown')
            stats['type_distribution'][insp_type] = stats['type_distribution'].get(insp_type, 0) + 1
        
        return stats


class InspirationTriggerModule:
    """灵感触发模块 - 整合所有功能"""
    
    def __init__(self):
        self.detector = FuzzinessDetector()
        self.generator = InspirationGenerator()
        self.learner = EvolutionLearner()
    
    def process_keshi(self, keshi: Dict) -> Dict:
        """处理课式，生成灵感（如需要）"""
        result = {
            'has_inspiration': False,
            'fuzziness': 0.0,
            'threshold': self.learner.threshold,
            'inspirations': [],
            'statistics': self.learner.get_statistics()
        }
        
        # 计算模糊度
        fuzziness = self.detector.calculate_fuzziness(keshi)
        result['fuzziness'] = fuzziness
        
        # 判断是否触发灵感
        if fuzziness >= self.learner.threshold:
            result['has_inspiration'] = True
            
            # 生成多种类型的灵感
            inspirations = self.generator.generate_inspiration(keshi, fuzziness)
            result['inspirations'] = inspirations
            
            # 记录灵感（待后续验证）
            keshi_hash = hashlib.md5(str(keshi).encode()).hexdigest()
            for insp in inspirations:
                self.learner.record_inspiration(insp, keshi_hash)
        
        return result
    
    def provide_feedback(self, inspiration_id: str, actual_result: str, feedback: str = None):
        """提供反馈，帮助系统进化"""
        self.learner.update_accuracy(inspiration_id, actual_result, feedback)
    
    def get_learner_statistics(self) -> Dict:
        """获取学习统计"""
        return self.learner.get_statistics()


# 单例模式
_inspiration_module = None

def get_inspiration_module() -> InspirationTriggerModule:
    """获取灵感触发模块实例"""
    global _inspiration_module
    if _inspiration_module is None:
        _inspiration_module = InspirationTriggerModule()
    return _inspiration_module


# 测试
if __name__ == '__main__':
    module = InspirationTriggerModule()
    
    # 测试课式1：高模糊度
    test_keshi1 = {
        'keti': '重审课',
        'sanchuan': ['巳(白虎)', '戌(螣蛇)', '卯(青龙)'],
        'tianjiang': ['白虎', '螣蛇', '青龙'],
        'sike': [['子', '丁'], ['巳', '子'], ['辰', '亥'], ['酉', '辰']],
        'jixiong': '吉',
        'kongwang': '午未',
        'hechong': '半合木局'
    }
    
    result1 = module.process_keshi(test_keshi1)
    print("=" * 60)
    print(f"测试课式1 - 模糊度: {result1['fuzziness']:.2f}, 阈值: {result1['threshold']:.2f}")
    print(f"触发灵感: {result1['has_inspiration']}")
    if result1['inspirations']:
        for i, insp in enumerate(result1['inspirations']):
            print(f"\n  灵感{i+1} ({insp['type']}):")
            print(f"    内容: {insp}")
    
    # 测试课式2：低模糊度
    test_keshi2 = {
        'keti': '元首课',
        'sanchuan': ['寅(青龙)', '午(朱雀)', '戌(天空)'],
        'tianjiang': ['青龙', '朱雀', '天空'],
        'sike': [['寅', '甲'], ['子', '寅'], ['辰', '戌'], ['申', '辰']],
        'jixiong': '吉',
        'kongwang': '',
        'hechong': '三合火局'
    }
    
    result2 = module.process_keshi(test_keshi2)
    print("\n" + "=" * 60)
    print(f"测试课式2 - 模糊度: {result2['fuzziness']:.2f}, 阈值: {result2['threshold']:.2f}")
    print(f"触发灵感: {result2['has_inspiration']}")
    
    print("\n" + "=" * 60)
    print("学习统计:")
    stats = module.get_learner_statistics()
    print(f"  总记录数: {stats['total_records']}")
    print(f"  已评估数: {stats['evaluated_records']}")
    print(f"  整体准确率: {stats['overall_accuracy']:.2%}")
    print(f"  当前阈值: {stats['current_threshold']:.2f}")
    print(f"  类型分布: {stats['type_distribution']}")
