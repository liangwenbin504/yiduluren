# -*- coding: utf-8 -*-
"""
择事类型断法学习模块
用于存储和管理各种择事类型的判断知识
"""

class ShishiDuanfaLearner:
    """择事类型断法学习器"""

    def __init__(self):
        self.shishi_types = [
            '天时', '宅墓', '前程', '终身', '流年',
            '婚姻', '胎产', '财产', '交易', '出行',
            '行人音信', '疾病', '六畜', '亡盗', '官讼', '杂占'
        ]

        self.duanfa_knowledge = {
            '天时': {
                'description': '占卜天气气候变化',
                'key_factors': ['月将', '占时', '天地盘'],
                'focus_aspects': ['晴雨', '雷电', '风雪', '寒暑'],
                'learning_points': [
                    '子为阴雨，午为晴朗',
                    '卯辰覆日，酉戌雷雨',
                    '亥子雨雪，巳午晴天',
                    '贵人顺行主晴，逆行主雨'
                ]
            },
            '宅墓': {
                'description': '阳宅阴墓风水择日',
                'key_factors': ['山家', '向首', '来龙', '福主年命'],
                'focus_aspects': ['入宅', '安葬', '修造', '动土'],
                'learning_points': [
                    '禄马贵人到山到向为吉',
                    '龙德课主富贵发达',
                    '斗首课格需配合山家五行',
                    '冲山之日忌用'
                ]
            },
            '前程': {
                'description': '仕途功名官运预测',
                'key_factors': ['年命', '占时', '贵人', '官鬼'],
                'focus_aspects': ['求官', '考试', '升迁', '科举'],
                'learning_points': [
                    '天乙贵人立卯酉为励德课，主君子升迁',
                    '官鬼发用利求官',
                    '德举课利考试',
                    '铸印课主功名'
                ]
            },
            '终身': {
                'description': '一生命运综合分析',
                'key_factors': ['年命', '本命', '行年', '四课三传'],
                'focus_aspects': ['事业', '财运', '婚姻', '健康'],
                'learning_points': [
                    '先看命限，次看行年',
                    '三传吉者一生顺利',
                    '天官发用定终身祸福',
                    '贵人力大者得贵人助'
                ]
            },
            '流年': {
                'description': '一年运势吉凶预测',
                'key_factors': ['年命', '流年', '太岁', '月将'],
                'focus_aspects': ['吉凶', '财运', '事业', '健康'],
                'learning_points': [
                    '太岁当年为君',
                    '生克往来定一年休咎',
                    '吉神到位则吉，凶神冲破则凶',
                    '三传有情者一年顺利'
                ]
            },
            '婚姻': {
                'description': '婚姻嫁娶吉日选择',
                'key_factors': ['男女年命', '嫁娶日期', '贵人', '吉神'],
                'focus_aspects': ['订婚', '结婚', '嫁娶', '纳采'],
                'learning_points': [
                    '天喜红鸾到日吉',
                    '贵人吉神同到为美',
                    '冲破男女命者忌用',
                    '阴将阳将俱空不吉'
                ]
            },
            '胎产': {
                'description': '怀孕生产相关预测',
                'key_factors': ['胎神', '产神', '占时', '贵人'],
                'focus_aspects': ['有孕', '生产', '保胎', '难产'],
                'learning_points': [
                    '胎神临日辰吉',
                    '产神空亡者难产',
                    '阳气足者易产',
                    '天医吉星到命者平安'
                ]
            },
            '财产': {
                'description': '财产投资理财预测',
                'key_factors': ['财星', '占时', '四课三传'],
                'focus_aspects': ['求财', '投资', '置产', '理财'],
                'learning_points': [
                    '财星发用利求财',
                    '禄马到山到向者得财',
                    '三传有财者财务顺利',
                    '空亡财星难实现'
                ]
            },
            '交易': {
                'description': '买卖交易商业贸易',
                'key_factors': ['财星', '官鬼', '占时', '吉凶'],
                'focus_aspects': ['买卖', '签约', '合作', '贸易'],
                'learning_points': [
                    '财官俱到者交易成',
                    '德合相生者利合作',
                    '空亡绝地者交易败',
                    '贵人来助者得利'
                ]
            },
            '出行': {
                'description': '出行旅游迁移预测',
                'key_factors': ['行人', '占时', '马星', '吉凶'],
                'focus_aspects': ['远行', '旅游', '迁移', '出国'],
                'learning_points': [
                    '马星发用利出行',
                    '贵人到命者得助',
                    '返吟课主往返不定',
                    '空亡日辰者行难成'
                ]
            },
            '行人音信': {
                'description': '行人远近音信消息',
                'key_factors': ['行人', '占时', '马星', '三传'],
                'focus_aspects': ['来人', '来信', '来电', '音信'],
                'learning_points': [
                    '马星临日辰者即至',
                    '用神生合者有音信',
                    '空亡绝地者信阻',
                    '三传有情者归期近'
                ]
            },
            '疾病': {
                'description': '疾病健康医药预测',
                'key_factors': ['病症', '占时', '医药', '天医'],
                'focus_aspects': ['病情', '医药', '手术', '健康'],
                'learning_points': [
                    '天医吉星到命者医药有效',
                    '鬼贼发用者病重',
                    '用神空亡者病轻',
                    '贵人到山到向者得贵人救'
                ]
            },
            '六畜': {
                'description': '六畜养殖农牧预测',
                'key_factors': ['六畜', '占时', '神煞'],
                'focus_aspects': ['养殖', '畜牧', '疫病', '繁殖'],
                'learning_points': [
                    '天喜吉星利六畜',
                    '血忌血支凶',
                    '生气足者繁殖旺',
                    '空亡者畜养不成'
                ]
            },
            '亡盗': {
                'description': '逃亡盗贼官非预测',
                'key_factors': ['逃者', '占时', '玄武', '天将'],
                'focus_aspects': ['逃亡', '盗贼', '官非', '刑狱'],
                'learning_points': [
                    '玄武临日辰者必盗',
                    '天空发用者有贼',
                    '勾陈相生者有助',
                    '贵人到向者得官府助'
                ]
            },
            '官讼': {
                'description': '诉讼是非官非预测',
                'key_factors': ['官鬼', '占时', '贵人', '勾陈'],
                'focus_aspects': ['诉讼', '是非', '官非', '刑狱'],
                'learning_points': [
                    '官鬼发用者必有官非',
                    '勾陈克日者讼不利',
                    '贵人来助者得胜',
                    '德合相生者和解'
                ]
            },
            '杂占': {
                'description': '其他杂事预测',
                'key_factors': ['用神', '占时', '三传', '吉凶'],
                'focus_aspects': ['失物', '寻找', '咨询', '杂事'],
                'learning_points': [
                    '用神临日辰者物在',
                    '玄武空亡者物难寻',
                    '三传有情者事成',
                    '吉凶相参定休咎'
                ]
            }
        }

    def get_shishi_info(self, shishi_type):
        """获取择事类型信息"""
        return self.duanfa_knowledge.get(shishi_type, {})

    def get_learning_points(self, shishi_type):
        """获取学习要点"""
        info = self.get_shishi_info(shishi_type)
        return info.get('learning_points', [])

    def get_key_factors(self, shishi_type):
        """获取关键因素"""
        info = self.get_shishi_info(shishi_type)
        return info.get('key_factors', [])

    def get_focus_aspects(self, shishi_type):
        """获取重点方面"""
        info = self.get_shishi_info(shishi_type)
        return info.get('focus_aspects', [])

    def add_learning_point(self, shishi_type, point):
        """添加学习要点"""
        if shishi_type in self.duanfa_knowledge:
            if 'learning_points' not in self.duanfa_knowledge[shishi_type]:
                self.duanfa_knowledge[shishi_type]['learning_points'] = []
            self.duanfa_knowledge[shishi_type]['learning_points'].append(point)
            return True
        return False

    def learn_from_example(self, shishi_type, example_data):
        """
        从案例学习

        example_data 格式:
        {
            'date': '年月日时',
            'sike': '四课',
            'sanchuan': '三传',
            'keti': '课体',
            'result': '判断结果',
            'analysis': '分析过程'
        }
        """
        if shishi_type in self.duanfa_knowledge:
            if 'examples' not in self.duanfa_knowledge[shishi_type]:
                self.duanfa_knowledge[shishi_type]['examples'] = []
            self.duanfa_knowledge[shishi_type]['examples'].append(example_data)
            return True
        return False

    def get_examples(self, shishi_type, limit=10):
        """获取案例"""
        info = self.get_shishi_info(shishi_type)
        examples = info.get('examples', [])
        return examples[:limit]

    def generate_analysis_prompt(self, shishi_type, fuzhu_info):
        """
        生成分析提示

        fuzhu_info 格式:
        {
            'gender': '男/女',
            'profession': '职业',
            'birth_year': 年,
            'birth_month': 月,
            'birth_day': 日,
            'birth_hour': '时',
            'residence': '现居地',
            'birth_place': '出生地'
        }
        """
        info = self.get_shishi_info(shishi_type)
        prompt_parts = [
            f'择事类型：{shishi_type}',
            f'说明：{info.get("description", "")}',
            f'关键因素：{", ".join(info.get("key_factors", []))}',
            f'重点方面：{", ".join(info.get("focus_aspects", []))}',
            '学习要点：'
        ]

        for i, point in enumerate(info.get('learning_points', []), 1):
            prompt_parts.append(f'{i}. {point}')

        if fuzhu_info:
            prompt_parts.append('')
            prompt_parts.append('福主信息：')
            if fuzhu_info.get('gender'):
                prompt_parts.append(f'- 性别：{fuzhu_info["gender"]}')
            if fuzhu_info.get('profession'):
                prompt_parts.append(f'- 职业：{fuzhu_info["profession"]}')
            if fuzhu_info.get('birth_year'):
                prompt_parts.append(f'- 出生：{fuzhu_info["birth_year"]}年{fuzhu_info.get("birth_month", "")}月{fuzhu_info.get("birth_day", "")}日{fuzhu_info.get("birth_hour", "")}时')

        return '\n'.join(prompt_parts)


_singleton_instance = None

def get_duanfa_learner():
    """获取断法学习器单例"""
    global _singleton_instance
    if _singleton_instance is None:
        _singleton_instance = ShishiDuanfaLearner()
    return _singleton_instance