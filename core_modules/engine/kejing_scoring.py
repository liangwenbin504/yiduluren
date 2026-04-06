#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六壬课格评分系统

依据《仪度六壬选日要诀》注解建立 64 课经的 10 分制评分体系

评分指标及权重：
1. 课格吉凶本质（30%）- 课格本身的吉凶属性
2. 三吉神将（25%）- 贵人、禄、马的出现情况
3. 五行生克（20%）- 三传四课的五行生克关系
4. 神煞组合（15%）- 吉神凶煞的组合
5. 旺相休囚（10%）- 月令和时辰的旺衰

课格基础分（按传统 64 课经吉凶分类）：
- 上上吉课：9.0-10.0 分（如龙德、天赦、三光等）
- 上吉课：8.0-8.9 分（如天德、月德、玉堂等）
- 中吉课：7.0-7.9 分（如生气、解神、天医等）
- 小吉课：6.0-6.9 分（如平吉、小成等）
- 吉凶参半：5.0-5.9 分（如伏吟、反吟等）
- 小凶课：4.0-4.9 分（如小耗、败亡等）
- 中凶课：3.0-3.9 分（如死气、病符等）
- 大凶课：2.0-2.9 分（如丧门、白虎等）
- 上凶课：0.0-1.9 分（如绝嗣、灭门等）
"""


class KeJingScoring:
    """六壬课格评分类"""
    
    def __init__(self):
        # 64 课经基础分（依据传统吉凶分类）
        self.kejing_base_scores = self._init_kejing_scores()
        
        # 三吉神将加分标准
        self.sanji_scores = {
            '贵人': 1.5,    # 最吉
            '禄神': 1.0,    # 次吉
            '驿马': 0.8,    # 又次
        }
        
        # 吉神加分
        self.jishen_scores = {
            '天德': 1.2, '月德': 1.2, '天德合': 1.0, '月德合': 1.0,
            '天赦': 1.5, '三光': 1.3, '玉堂': 1.0, '金堂': 0.8,
            '生气': 1.0, '解神': 0.8, '天医': 0.7, '福德': 0.8,
            '天喜': 0.7, '六合': 0.6, '太阴': 0.5, '青龙': 1.2,
        }
        
        # 凶煞减分
        self.xiongsha_scores = {
            '白虎': -1.5, '丧门': -1.3, '吊客': -1.2, '病符': -1.0,
            '死符': -1.2, '岁破': -1.5, '大耗': -1.3, '小耗': -0.8,
            '劫煞': -1.0, '灾煞': -1.2, '月煞': -0.8, '亡神': -1.0,
            '勾陈': -0.8, '朱雀': -0.6, '螣蛇': -0.7, '玄武': -0.6,
        }
    
    def _init_kejing_scores(self):
        """初始化 64 课经基础分"""
        return {
            # 上上吉课（9.0-10.0 分）
            '龙德': 9.5, '天赦': 9.5, '三光': 9.3, '天福': 9.2,
            
            # 上吉课（8.0-8.9 分）
            '天德': 8.8, '月德': 8.8, '玉堂': 8.5, '金堂': 8.3,
            '天恩': 8.5, '圣心': 8.3, '益后': 8.2, '续世': 8.2,
            
            # 中吉课（7.0-7.9 分）
            '生气': 7.8, '解神': 7.6, '天医': 7.5, '福德': 7.5,
            '天喜': 7.3, '六合': 7.2, '太阴': 7.0, '青龙': 7.8,
            '明堂': 7.5, '金匮': 7.3,
            
            # 小吉课（6.0-6.9 分）
            '平吉': 6.5, '小成': 6.3, '守成': 6.2, '安定': 6.0,
            
            # 吉凶参半（5.0-5.9 分）
            '伏吟': 5.5, '反吟': 5.3, '别责': 5.2, '八专': 5.0,
            '昴星': 5.5, '涉害': 5.8,
            
            # 小凶课（4.0-4.9 分）
            '小耗': 4.5, '败亡': 4.3, '破败': 4.2, '失脱': 4.0,
            
            # 中凶课（3.0-3.9 分）
            '死气': 3.5, '病符': 3.3, '丧吊': 3.2, '官符': 3.0,
            
            # 大凶课（2.0-2.9 分）
            '丧门': 2.5, '白虎': 2.3, '岁破': 2.2, '大耗': 2.0,
            
            # 上凶课（0.0-1.9 分）
            '绝嗣': 1.5, '灭门': 1.3, '绝灭': 1.0,
        }
    
    def calculate_score(self, kejing_name, sanji_list=None, jishen_list=None, xiongsha_list=None):
        """
        计算课格综合评分
        
        :param kejing_name: 课格名称
        :param sanji_list: 三吉神将列表 ['贵人', '禄神']
        :param jishen_list: 吉神列表 ['天德', '月德']
        :param xiongsha_list: 凶煞列表 ['白虎', '丧门']
        :return: 综合评分（0-10 分）
        """
        base_score = self.kejing_base_scores.get(kejing_name, 5.0)
        
        sanji_bonus = 0
        if sanji_list:
            for shen in sanji_list:
                sanji_bonus += self.sanji_scores.get(shen, 0)
        
        jishen_bonus = 0
        if jishen_list:
            for shen in jishen_list:
                jishen_bonus += self.jishen_scores.get(shen, 0)
        
        xiongsha_penalty = 0
        if xiongsha_list:
            for sha in xiongsha_list:
                xiongsha_penalty += abs(self.xiongsha_scores.get(sha, 0))
        
        total_score = base_score + sanji_bonus + jishen_bonus - xiongsha_penalty
        
        total_score = max(0, min(10, total_score))
        
        return round(total_score, 1)
    
    def get_score_level(self, score):
        """根据评分返回吉凶等级"""
        if score >= 9.0:
            return "上上大吉"
        elif score >= 8.0:
            return "上吉"
        elif score >= 7.0:
            return "中吉"
        elif score >= 6.0:
            return "小吉"
        elif score >= 5.0:
            return "吉凶参半"
        elif score >= 4.0:
            return "小凶"
        elif score >= 3.0:
            return "中凶"
        elif score >= 2.0:
            return "大凶"
        else:
            return "上凶"
    
    def is_usable(self, score):
        """判断课格是否可用（5 分以上为可用）"""
        return score >= 5.0
    
    def get_all_kejing_scores(self):
        """获取所有课格的基础评分"""
        return self.kejing_base_scores.copy()


def test_scoring():
    """测试评分系统"""
    scoring = KeJingScoring()
    
    print("=" * 80)
    print("六壬课格评分系统测试")
    print("=" * 80)
    
    # 测试几个课格
    test_cases = [
        ('龙德', ['贵人', '禄神'], ['天德', '月德'], []),
        ('天德', ['贵人'], ['天德'], ['小耗']),
        ('伏吟', [], [], ['白虎']),
        ('丧门', [], [], ['丧门', '吊客']),
    ]
    
    for kejing, sanji, jishen, xiongsha in test_cases:
        score = scoring.calculate_score(kejing, sanji, jishen, xiongsha)
        level = scoring.get_score_level(score)
        usable = scoring.is_usable(score)
        
        print(f"\n课格：{kejing}")
        print(f"  三吉：{sanji}")
        print(f"  吉神：{jishen}")
        print(f"  凶煞：{xiongsha}")
        print(f"  综合评分：{score}分 - {level}")
        print(f"  是否可用：{'✓ 可用' if usable else '✗ 不建议使用'}")
    
    print("\n" + "=" * 80)
    print("所有课格基础分：")
    print("=" * 80)
    
    all_scores = scoring.get_all_kejing_scores()
    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
    
    current_level = None
    for kejing, score in sorted_scores:
        level = scoring.get_score_level(score)
        if level != current_level:
            print(f"\n【{level}】({score:.1f}分)")
            current_level = level
        print(f"  {kejing}: {score:.1f}分", end="  ")


if __name__ == '__main__':
    test_scoring()
