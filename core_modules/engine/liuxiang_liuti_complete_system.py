#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
六相六替完整系统 - 基于《仪度六壬选日要诀》

模块架构：
1. 基础状态模块 (LiuXiangLiuTiStates) - 六相六替的 12 种状态定义
2. 查询工具模块 (SixtyDaysQueryTable) - 六十日相替定局查询表
3. 核心诀法模块 (HuaQiJueFa) - 化气六相诀、化气六替诀
4. 应用策略模块 (RemedyStrategy) - 补救之法
5. 判断分析模块 (DecisionAnalyzer) - 决断生死真假辨、与大六壬三传结合

作者：AI 助手
日期：2026-03-24
版本：v2.0
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# 1. 基础状态模块
# ============================================================================

class LiuXiangState(Enum):
    """六相状态枚举（吉）"""
    CHANG_SHENG = "长生"      # 出生、萌芽
    GUAN_DAI = "冠带"        # 成长、包装
    LIN_GUAN = "临官"        # 成熟、任职
    DI_WANG = "帝旺"         # 巅峰、旺盛
    TAI = "胎"              # 孕育、酝酿
    YANG = "养"             # 养育、培养


class LiuTiState(Enum):
    """六替状态枚举（凶）"""
    MU_YU = "沐浴"          # 洗礼、暴露
    SHUAI = "衰"            # 衰退、减弱
    BING = "病"             # 疾病、问题
    SI = "死"               # 死亡、终结
    MU = "墓"               # 埋葬、收藏
    JUE = "绝"              # 绝灭、消失


@dataclass
class StateInfo:
    """状态信息数据类"""
    name: str           # 状态名称
    type: str          # 类型（吉/凶）
    meaning: str       # 含义
    application: str   # 应用场景
    score: int         # 基础分数


class LiuXiangLiuTiStates:
    """
    基础状态模块
    
    功能：
    - 定义六相的 6 种状态（长生、冠带、临官、帝旺、胎、养）
    - 定义六替的 6 种状态（沐浴、衰、病、死、墓、绝）
    - 提供状态查询和判断方法
    """
    
    def __init__(self):
        """初始化状态信息"""
        # 六相状态详细信息（吉）
        self.liuxiang_states = {
            '长生': StateInfo(
                name='长生',
                type='吉',
                meaning='人财盛，生机勃勃',
                application='最吉，主人丁兴旺、财富增长',
                score=95
            ),
            '冠带': StateInfo(
                name='冠带',
                type='吉',
                meaning='福禄昌，包装成长',
                application='次吉，主福禄双全、名声渐起',
                score=85
            ),
            '临官': StateInfo(
                name='临官',
                type='吉',
                meaning='功名显，事业有成',
                application='大吉，主功名利禄、官运亨通',
                score=90
            ),
            '帝旺': StateInfo(
                name='帝旺',
                type='吉',
                meaning='人财盛，巅峰状态',
                application='最吉，主人财两旺、事业巅峰',
                score=95
            ),
            '胎': StateInfo(
                name='胎',
                type='吉',
                meaning='有喜孕，孕育新机',
                application='小吉，主婚姻喜庆、孕育新人',
                score=75
            ),
            '养': StateInfo(
                name='养',
                type='吉',
                meaning='有喜孕，培养成长',
                application='小吉，主养育后人、培养根基',
                score=75
            )
        }
        
        # 六替状态详细信息（凶）
        self.liuti_states = {
            '沐浴': StateInfo(
                name='沐浴',
                type='凶',
                meaning='风声露，风流暴露',
                application='凶，主风流韵事、名声不好',
                score=40
            ),
            '衰': StateInfo(
                name='衰',
                type='凶',
                meaning='祸侵，衰退无力',
                application='凶，主运势衰退、力量减弱',
                score=35
            ),
            '病': StateInfo(
                name='病',
                type='凶',
                meaning='祸侵，疾病缠身',
                application='凶，主疾病灾祸、身体不适',
                score=30
            ),
            '死': StateInfo(
                name='死',
                type='凶',
                meaning='祸侵，死亡终结',
                application='大凶，主死亡败亡、事业终结',
                score=10
            ),
            '墓': StateInfo(
                name='墓',
                type='凶',
                meaning='人才不得兴，埋葬收藏',
                application='凶，主人才埋没、财富收藏',
                score=25
            ),
            '绝': StateInfo(
                name='绝',
                type='凶',
                meaning='人才不得兴，绝灭消失',
                application='大凶，主绝后无人、事业断绝',
                score=5
            )
        }
    
    def get_state_info(self, state_name: str) -> Optional[StateInfo]:
        """
        获取状态信息
        
        Args:
            state_name: 状态名称
            
        Returns:
            StateInfo 对象，如果不存在则返回 None
        """
        if state_name in self.liuxiang_states:
            return self.liuxiang_states[state_name]
        elif state_name in self.liuti_states:
            return self.liuti_states[state_name]
        return None
    
    def is_liuxiang(self, state_name: str) -> bool:
        """判断是否为六相（吉）"""
        return state_name in self.liuxiang_states
    
    def is_liuti(self, state_name: str) -> bool:
        """判断是否为六替（凶）"""
        return state_name in self.liuti_states
    
    def get_state_score(self, state_name: str) -> int:
        """获取状态分数"""
        info = self.get_state_info(state_name)
        return info.score if info else 50
    
    def get_all_liuxiang(self) -> List[str]:
        """获取所有六相状态"""
        return list(self.liuxiang_states.keys())
    
    def get_all_liuti(self) -> List[str]:
        """获取所有六替状态"""
        return list(self.liuti_states.keys())


# ============================================================================
# 2. 查询工具模块
# ============================================================================

@dataclass
class DayStateInfo:
    """日柱状态信息"""
    ganzhi: str           # 干支
    state_sequence: List[str]  # 12 状态序列
    liuxiang_zhi: List[str]    # 六相地支
    liuti_zhi: List[str]       # 六替地支


class SixtyDaysQueryTable:
    """
    查询工具模块
    
    功能：
    - 六十日相替定局查询表
    - 按天干分组查询
    - 提供六相六替地支查询
    """
    
    def __init__(self):
        """初始化六十日相替定局"""
        # 六十日相替定局（按天干分组）
        # 格式：{天干组：(起始地支，12 状态序列)}
        self.sixty_days_table = {
            '甲己': {
                'start_zhi': '寅',
                'states': ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', 
                          '病', '死', '墓', '绝', '胎', '养'],
                'zhi_sequence': ['寅', '卯', '辰', '巳', '午', '未',
                                '申', '酉', '戌', '亥', '子', '丑']
            },
            '乙庚': {
                'start_zhi': '寅',
                'states': ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                          '病', '死', '墓', '绝', '胎', '养'],
                'zhi_sequence': ['寅', '卯', '辰', '巳', '午', '未',
                                '申', '酉', '戌', '亥', '子', '丑']
            },
            '丙辛': {
                'start_zhi': '寅',
                'states': ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                          '病', '死', '墓', '绝', '胎', '养'],
                'zhi_sequence': ['寅', '卯', '辰', '巳', '午', '未',
                                '申', '酉', '戌', '亥', '子', '丑']
            },
            '丁壬': {
                'start_zhi': '寅',
                'states': ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                          '病', '死', '墓', '绝', '胎', '养'],
                'zhi_sequence': ['寅', '卯', '辰', '巳', '午', '未',
                                '申', '酉', '戌', '亥', '子', '丑']
            },
            '戊癸': {
                'start_zhi': '寅',
                'states': ['长生', '沐浴', '冠带', '临官', '帝旺', '衰',
                          '病', '死', '墓', '绝', '胎', '养'],
                'zhi_sequence': ['寅', '卯', '辰', '巳', '午', '未',
                                '申', '酉', '戌', '亥', '子', '丑']
            }
        }
        
        # 天干分组映射
        self.tiangan_groups = {
            '甲': '甲己', '己': '甲己',
            '乙': '乙庚', '庚': '乙庚',
            '丙': '丙辛', '辛': '丙辛',
            '丁': '丁壬', '壬': '丁壬',
            '戊': '戊癸', '癸': '戊癸'
        }
    
    def get_day_state_info(self, tiangan: str) -> Optional[DayStateInfo]:
        """
        获取某日的状态信息
        
        Args:
            tiangan: 天干
            
        Returns:
            DayStateInfo 对象
        """
        group = self.tiangan_groups.get(tiangan)
        if not group:
            return None
        
        table_data = self.sixty_days_table[group]
        
        # 计算六相地支和六替地支
        liuxiang_zhi = []
        liuti_zhi = []
        
        for i, state in enumerate(table_data['states']):
            zhi = table_data['zhi_sequence'][i]
            if state in ['长生', '冠带', '临官', '帝旺', '胎', '养']:
                liuxiang_zhi.append(zhi)
            else:
                liuti_zhi.append(zhi)
        
        return DayStateInfo(
            ganzhi=f"{tiangan}X",  # X 表示地支待定
            state_sequence=table_data['states'],
            liuxiang_zhi=liuxiang_zhi,
            liuti_zhi=liuti_zhi
        )
    
    def get_liuxiang_zhi(self, tiangan: str) -> List[str]:
        """
        获取某天干的六相地支
        
        Args:
            tiangan: 天干
            
        Returns:
            六相地支列表
        """
        info = self.get_day_state_info(tiangan)
        return info.liuxiang_zhi if info else []
    
    def get_liuti_zhi(self, tiangan: str) -> List[str]:
        """
        获取某天干的六替地支
        
        Args:
            tiangan: 天干
            
        Returns:
            六替地支列表
        """
        info = self.get_day_state_info(tiangan)
        return info.liuti_zhi if info else []
    
    def get_state_by_zhi(self, tiangan: str, dizhi: str) -> Optional[str]:
        """
        根据天干地支获取状态
        
        Args:
            tiangan: 天干
            dizhi: 地支
            
        Returns:
            状态名称
        """
        info = self.get_day_state_info(tiangan)
        if not info:
            return None
        
        zhi_sequence = self.sixty_days_table[self.tiangan_groups[tiangan]]['zhi_sequence']
        states = self.sixty_days_table[self.tiangan_groups[tiangan]]['states']
        
        if dizhi in zhi_sequence:
            idx = zhi_sequence.index(dizhi)
            return states[idx]
        
        return None
    
    def is_liuxiang_zhi(self, tiangan: str, dizhi: str) -> bool:
        """判断某干支是否为六相地支"""
        state = self.get_state_by_zhi(tiangan, dizhi)
        return state in ['长生', '冠带', '临官', '帝旺', '胎', '养'] if state else False
    
    def is_liuti_zhi(self, tiangan: str, dizhi: str) -> bool:
        """判断某干支是否为六替地支"""
        state = self.get_state_by_zhi(tiangan, dizhi)
        return state in ['沐浴', '衰', '病', '死', '墓', '绝'] if state else False
    
    def print_query_table(self):
        """打印六十日相替定局查询表"""
        print("=" * 80)
        print("六十日相替定局查询表")
        print("=" * 80)
        
        for group, data in self.sixty_days_table.items():
            print(f"\n{group}日组（起{data['start_zhi']}顺数）:")
            print("-" * 80)
            
            for i, (zhi, state) in enumerate(zip(data['zhi_sequence'], data['states'])):
                state_type = "六相【吉】" if state in ['长生', '冠带', '临官', '帝旺', '胎', '养'] else "六替【凶】"
                print(f"  {i+1:2d}. {zhi:2s} - {state:4s} {state_type}")


# ============================================================================
# 3. 核心诀法模块
# ============================================================================

class HuaQiJueFa:
    """
    核心诀法模块
    
    功能：
    - 化气六相诀
    - 化气六替诀
    - 斗首五行六相六替诀
    """
    
    def __init__(self):
        """初始化诀法"""
        # 化气六相诀
        self.liuxiang_jue = """
生旺人财盛，冠带福禄昌。
临官功名显，胎养有喜孕。
六相外又取，墓库富丰盈。
廉贞年一位，生旺子孙昌。
三元三武吉，富贵永安康。
元辰和五气，三才仔细详。
        """
        
        # 化气六替诀
        self.liuti_jue = """
沐浴风声露，衰病死祸侵。
贪破年月上，灾祥各半分。
元廉居墓绝，人才不得兴。
贪官墓绝上，庶吉仕凶评。
        """
        
        # 斗首五行六相六替诀
        self.douhou_jue = """
三吉喜居六相支，二凶喜居六替支。
尤喜三吉在替支，二凶六替即三吉。
总求三元旺相主，四柱必透一元辰。
若不及透地支多，元辰六相妙谛真。
        """
        
        # 诀法解释
        self.juefa_explanation = {
            '化气六相诀': {
                '生旺人财盛': '长生、帝旺主人丁和财富旺盛',
                '冠带福禄昌': '冠带可增加福禄',
                '临官功名显': '临官有利当官和名声',
                '胎养有喜孕': '胎和养有利婚姻和怀孕',
                '六相外又取，墓库富丰盈': '六相之外还可取墓库为用，墓库主财丰盈',
                '廉贞年一位，生旺子孙昌': '破鬼之年只得一位廉贞，生旺子孙',
                '三元三武吉，富贵永安康': '三元三武的局格最吉，主富贵永安康',
                '元辰和五气，三才仔细详': '要仔细参详日课的元辰、五气和表三元'
            },
            '化气六替诀': {
                '沐浴风声露': '沐浴主风流、名声不好',
                '衰病死祸侵': '衰、病、死主有祸害',
                '贪破年月上，灾祥各半分': '贪官破鬼在年月，吉凶各半',
                '元廉居墓绝，人才不得兴': '元辰、廉子居在墓绝上，人丁和财富都不得兴旺',
                '贪官墓绝上，庶吉仕凶评': '贪官居在墓绝上，是吉无凶来评断'
            },
            '斗首五行六相六替诀': {
                '三吉喜居六相支': '元辰、武财、廉子喜居六相地支',
                '二凶喜居六替支': '贪官、破鬼喜居六替地支',
                '尤喜三吉在替支': '特别喜欢三吉在六替地支（凶在外）',
                '二凶六替即三吉': '二凶的六替地支即为三吉的六相地支',
                '总求三元旺相主': '总求三元旺相为主',
                '四柱必透一元辰': '四柱一定要透一个元辰',
                '若不及透地支多': '如果四柱不透，地支一定要多',
                '元辰六相妙谛真': '元辰六相是妙诀真谛'
            }
        }
    
    def get_liuxiang_jue(self) -> str:
        """获取化气六相诀"""
        return self.liuxiang_jue.strip()
    
    def get_liuti_jue(self) -> str:
        """获取化气六替诀"""
        return self.liuti_jue.strip()
    
    def get_douhou_jue(self) -> str:
        """获取斗首五行六相六替诀"""
        return self.douhou_jue.strip()
    
    def explain_juefa(self, juefa_name: str) -> Dict[str, str]:
        """
        解释诀法
        
        Args:
            juefa_name: 诀法名称
            
        Returns:
            解释字典
        """
        return self.juefa_explanation.get(juefa_name, {})
    
    def analyze_state_meaning(self, state: str) -> str:
        """
        分析状态含义
        
        Args:
            state: 状态名称
            
        Returns:
            含义解释
        """
        if state in ['长生', '帝旺']:
            return "主人丁和财富旺盛"
        elif state == '冠带':
            return "可增加福禄"
        elif state == '临官':
            return "有利当官和名声"
        elif state in ['胎', '养']:
            return "有利婚姻和怀孕"
        elif state == '墓':
            return "主财丰盈（墓库）"
        elif state == '沐浴':
            return "主风流、名声不好"
        elif state in ['衰', '病', '死']:
            return "主有祸害"
        elif state == '绝':
            return "主绝灭"
        
        return "未知"


# ============================================================================
# 4. 应用策略模块
# ============================================================================

@dataclass
class RemedyPlan:
    """补救方案"""
    method: str           # 方法名称
    priority: int         # 优先级（1 最高）
    description: str      # 描述
    application: str      # 应用场景
    example: str          # 示例


class RemedyStrategy:
    """
    应用策略模块
    
    功能：
    - 补救之法
    - 提供多种补救方案
    - 按优先级排序
    """
    
    def __init__(self):
        """初始化补救策略"""
        self.remedy_methods = [
            RemedyPlan(
                method='以元补元',
                priority=1,
                description='用元辰的时柱来补助，用元辰的年月柱来扶助',
                application='元辰衰弱时的首选补救方法',
                example='午山子向用癸亥日（火绝在亥），用癸丑、戊午二时补助元辰，再用戊寅、戊辰等年月扶助'
            ),
            RemedyPlan(
                method='以武补元',
                priority=2,
                description='用武财之支来补助元辰',
                application='不能以元补元时的次选方法',
                example='用庚辰、庚午等武财之支来补助元辰'
            ),
            RemedyPlan(
                method='以廉补元',
                priority=3,
                description='用廉子之支来补助元辰',
                application='不能以武补元时的再次方法',
                example='用甲辰、甲午等廉子之支来补助元辰'
            ),
            RemedyPlan(
                method='以贪破补元',
                priority=4,
                description='用贪官或破鬼的临官、帝旺支来补助',
                application='最不得已的方法，需贪官破鬼无气且到山到向发传',
                example='用丁巳、壬午等贪官病死之支（但为元辰临帝旺）补元'
            )
        ]
        
        # 补救原则
        self.remedy_principles = [
            '凶宜在外（年月），吉宜在内（日时）',
            '贪官和破鬼在外需居六替地支',
            '若居六相地支便生祸',
            '四柱必透一元辰',
            '若不及透，地支一定要多元辰六相之支'
        ]
    
    def get_remedy_methods(self) -> List[RemedyPlan]:
        """获取所有补救方法（按优先级排序）"""
        return sorted(self.remedy_methods, key=lambda x: x.priority)
    
    def get_best_remedy(self) -> RemedyPlan:
        """获取最佳补救方法"""
        return self.remedy_methods[0]
    
    def get_remedy_by_priority(self, priority: int) -> Optional[RemedyPlan]:
        """
        根据优先级获取补救方法
        
        Args:
            priority: 优先级（1-4）
            
        Returns:
            RemedyPlan 对象
        """
        for method in self.remedy_methods:
            if method.priority == priority:
                return method
        return None
    
    def analyze_remedy_case(self, shan: str, day_ganzhi: str, problem: str) -> Dict:
        """
        分析补救案例
        
        Args:
            shan: 坐山
            day_ganzhi: 日柱干支
            problem: 问题描述
            
        Returns:
            分析结果字典
        """
        return {
            '坐山': shan,
            '日柱': day_ganzhi,
            '问题': problem,
            '补救方案': [
                {
                    '优先级': method.priority,
                    '方法': method.method,
                    '描述': method.description,
                    '示例': method.example
                }
                for method in self.get_remedy_methods()
            ],
            '原则': self.remedy_principles
        }
    
    def print_remedy_guide(self):
        """打印补救指南"""
        print("=" * 80)
        print("六相六替补救之法指南")
        print("=" * 80)
        
        print("\n【补救原则】")
        for principle in self.remedy_principles:
            print(f"  • {principle}")
        
        print("\n【补救方法】（按优先级排序）")
        for method in self.get_remedy_methods():
            print(f"\n{method.priority}. {method.method}（优先级：{method.priority}）")
            print(f"   描述：{method.description}")
            print(f"   应用：{method.application}")
            print(f"   示例：{method.example}")


# ============================================================================
# 5. 判断分析模块
# ============================================================================

@dataclass
class LifeDeathJudgment:
    """生死判断数据类"""
    ganzhi: str           # 干支
    judgment: str         # 判断结果
    reason: str          # 原因
    is_special: bool     # 是否为特殊情况


class DecisionAnalyzer:
    """
    判断分析模块
    
    功能：
    - 决断生死真假辨
    - 与大六壬三传的结合判断
    - 综合分析
    """
    
    def __init__(self):
        """初始化判断分析器"""
        # 决断生死真假辨的特殊干支
        self.special_judgments = [
            LifeDeathJudgment(
                ganzhi='庚子',
                judgment='金真死',
                reason='金寒水冷水旺金泄的缘故',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='辛卯',
                judgment='水真死',
                reason='水死于卯',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='己巳',
                judgment='土不绝',
                reason='丙火得临官，己土怎会绝呢',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='辛未',
                judgment='水难养',
                reason='三伏天土干燥，水怎能养呢',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='辛酉',
                judgment='水不败',
                reason='辛金生壬水的缘故',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='癸酉',
                judgment='火真死',
                reason='火死于酉',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='壬子',
                judgment='木不败',
                reason='阴水生阳木的缘故',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='癸未',
                judgment='火不衰',
                reason='三伏天酷热秋阳暴虐的缘故',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='己酉',
                judgment='土真败',
                reason='金强土弱的缘故',
                is_special=True
            ),
            LifeDeathJudgment(
                ganzhi='庚戌',
                judgment='金不衰',
                reason='土生金的缘故',
                is_special=True
            )
        ]
        
        # 与大六壬三传结合的规则
        self.daliuren_rules = {
            '活马': '初传发出的马神，不在地盘本位而在其他位置',
            '真禄': '中传或初传发出的禄神，不在地盘本位而在其他位置',
            '天机灵动': '禄马贵在三传中发用，吉气迎入',
            '发传': '触发三吉之窍法',
            '到山到向': '用六壬盘将禄马贵吊到本山或本向'
        }
    
    def get_special_judgment(self, ganzhi: str) -> Optional[LifeDeathJudgment]:
        """
        获取特殊干支的生死判断
        
        Args:
            ganzhi: 干支
            
        Returns:
            LifeDeathJudgment 对象
        """
        for judgment in self.special_judgments:
            if judgment.ganzhi == ganzhi:
                return judgment
        return None
    
    def analyze_ganzhi_life_death(self, ganzhi: str, month: str = None) -> Dict:
        """
        分析干支的生死真假
        
        Args:
            ganzhi: 干支
            month: 月份（可选）
            
        Returns:
            分析结果字典
        """
        special = self.get_special_judgment(ganzhi)
        
        if special:
            return {
                '干支': ganzhi,
                '判断': special.judgment,
                '原因': special.reason,
                '特殊': True,
                '建议': '需结合月令、地支所藏、相生等分析'
            }
        
        return {
            '干支': ganzhi,
            '判断': '普通干支',
            '原因': '无特殊生死判断',
            '特殊': False,
            '建议': '按常规六相六替判断'
        }
    
    def analyze_daliuren_transmission(self, transmission_type: str, 
                                       shan: str, xiang: str,
                                       sanzhuang: List[str]) -> Dict:
        """
        分析大六壬三传的发用情况
        
        Args:
            transmission_type: 传课类型（如'活马'、'真禄'）
            shan: 坐山
            xiang: 向
            sanzhuang: 三传
            
        Returns:
            分析结果字典
        """
        rule = self.daliuren_rules.get(transmission_type, '未知')
        
        return {
            '类型': transmission_type,
            '规则': rule,
            '坐山': shan,
            '向': xiang,
            '三传': sanzhuang,
            '分析': f'{transmission_type}需在三传中发用，才能天机灵动',
            '吉凶': '发传为吉，不发传力小'
        }
    
    def comprehensive_analysis(self, shan: str, sizhu: Dict, 
                                sanzhuang: List[str] = None) -> Dict:
        """
        综合分析（结合六相六替和大六壬三传）
        
        Args:
            shan: 坐山
            sizhu: 四柱信息
            sanzhuang: 三传（可选）
            
        Returns:
            综合分析结果
        """
        result = {
            '坐山': shan,
            '四柱': sizhu,
            '六相六替分析': {},
            '大六壬三传分析': {},
            '综合判断': ''
        }
        
        # 分析四柱的六相六替
        for pillar_name, ganzhi in sizhu.items():
            if len(ganzhi) >= 2:
                tiangan = ganzhi[0]
                dizhi = ganzhi[1]
                
                # 获取状态
                # （这里需要查询表，简化处理）
                result['六相六替分析'][pillar_name] = {
                    '干支': ganzhi,
                    '状态': '待查询',
                    '吉凶': '待判断'
                }
        
        # 分析三传
        if sanzhuang:
            result['大六壬三传分析'] = {
                '三传': sanzhuang,
                '发用情况': '待分析',
                '是否天机灵动': len(sanzhuang) == 3
            }
        
        # 综合判断
        result['综合判断'] = '需结合六相六替和三传发用综合判断'
        
        return result
    
    def print_life_death_table(self):
        """打印生死真假辨表"""
        print("=" * 80)
        print("决断生死真假辨表")
        print("=" * 80)
        
        print(f"\n{'干支':<8} {'判断':<10} {'原因':<40}")
        print("-" * 80)
        
        for judgment in self.special_judgments:
            print(f"{judgment.ganzhi:<8} {judgment.judgment:<10} {judgment.reason:<40}")
        
        print("\n【说明】")
        print("  分析地支的六相和六替，需结合月令、地支所藏、相生等分析")
        print("  则知其生死真假。")


# ============================================================================
# 6. 系统集成类
# ============================================================================

class LiuXiangLiuTiSystem:
    """
    六相六替完整系统
    
    集成所有模块：
    1. 基础状态模块
    2. 查询工具模块
    3. 核心诀法模块
    4. 应用策略模块
    5. 判断分析模块
    """
    
    def __init__(self):
        """初始化系统"""
        self.states = LiuXiangLiuTiStates()
        self.query_table = SixtyDaysQueryTable()
        self.juefa = HuaQiJueFa()
        self.remedy = RemedyStrategy()
        self.analyzer = DecisionAnalyzer()
    
    def analyze_day(self, tiangan: str, dizhi: str) -> Dict:
        """
        分析单日的六相六替
        
        Args:
            tiangan: 天干
            dizhi: 地支
            
        Returns:
            分析结果字典
        """
        state = self.query_table.get_state_by_zhi(tiangan, dizhi)
        is_liuxiang = self.query_table.is_liuxiang_zhi(tiangan, dizhi)
        
        return {
            '干支': f"{tiangan}{dizhi}",
            '状态': state,
            '六相/六替': '六相' if is_liuxiang else '六替',
            '吉凶': '吉' if is_liuxiang else '凶',
            '分数': self.states.get_state_score(state) if state else 50,
            '含义': self.juefa.analyze_state_meaning(state) if state else '未知'
        }
    
    def analyze_sizhu(self, sizhu: Dict) -> Dict:
        """
        分析四柱的六相六替
        
        Args:
            sizhu: 四柱字典
            
        Returns:
            分析结果字典
        """
        result = {
            '四柱分析': {},
            '六相统计': 0,
            '六替统计': 0,
            '总评分': 0,
            '吉凶判断': ''
        }
        
        total_score = 0
        
        for pillar_name, ganzhi in sizhu.items():
            if len(ganzhi) >= 2:
                tiangan = ganzhi[0]
                dizhi = ganzhi[1]
                
                analysis = self.analyze_day(tiangan, dizhi)
                result['四柱分析'][pillar_name] = analysis
                
                if analysis['六相/六替'] == '六相':
                    result['六相统计'] += 1
                else:
                    result['六替统计'] += 1
                
                total_score += analysis['分数']
        
        result['总评分'] = total_score // len(sizhu) if sizhu else 0
        
        # 吉凶判断
        if result['六相统计'] >= 3:
            result['吉凶判断'] = '大吉（三吉居六相）'
        elif result['六相统计'] >= 2:
            result['吉凶判断'] = '吉（二吉居六相）'
        elif result['六替统计'] >= 3:
            result['吉凶判断'] = '凶（多凶居六替）'
        else:
            result['吉凶判断'] = '平'
        
        return result
    
    def get_complete_report(self, shan: str, sizhu: Dict, 
                           sanzhuang: List[str] = None) -> str:
        """
        获取完整报告
        
        Args:
            shan: 坐山
            sizhu: 四柱
            sanzhuang: 三传（可选）
            
        Returns:
            完整报告字符串
        """
        report = []
        report.append("=" * 80)
        report.append(f"六相六替完整分析报告 - {shan}山")
        report.append("=" * 80)
        
        # 四柱分析
        report.append("\n【四柱六相六替分析】")
        sizhu_analysis = self.analyze_sizhu(sizhu)
        for pillar, analysis in sizhu_analysis['四柱分析'].items():
            report.append(f"  {pillar}: {analysis['干支']} - {analysis['状态']} "
                         f"({analysis['六相/六替']}, {analysis['吉凶']}, "
                         f"{analysis['分数']}分)")
        
        report.append(f"\n  六相数：{sizhu_analysis['六相统计']}")
        report.append(f"  六替数：{sizhu_analysis['六替统计']}")
        report.append(f"  总评分：{sizhu_analysis['总评分']}")
        report.append(f"  吉凶判断：{sizhu_analysis['吉凶判断']}")
        
        # 核心诀法
        report.append("\n【核心诀法】")
        report.append("  化气六相诀：")
        for line in self.juefa.get_liuxiang_jue().split('\n'):
            if line.strip():
                report.append(f"    {line.strip()}")
        
        report.append("\n  化气六替诀：")
        for line in self.juefa.get_liuti_jue().split('\n'):
            if line.strip():
                report.append(f"    {line.strip()}")
        
        # 大六壬三传分析
        if sanzhuang:
            report.append("\n【大六壬三传分析】")
            report.append(f"  三传：{' '.join(sanzhuang)}")
            report.append(f"  发用情况：{'已发传' if len(sanzhuang) == 3 else '未发传'}")
            report.append(f"  天机灵动：{'是' if len(sanzhuang) == 3 else '否'}")
        
        # 补救建议
        if sizhu_analysis['六替统计'] > sizhu_analysis['六相统计']:
            report.append("\n【补救建议】")
            best_remedy = self.remedy.get_best_remedy()
            report.append(f"  推荐方法：{best_remedy.method}")
            report.append(f"  描述：{best_remedy.description}")
        
        return '\n'.join(report)


# ============================================================================
# 7. 测试函数
# ============================================================================

def test_complete_system():
    """测试完整系统"""
    print("=" * 80)
    print("六相六替完整系统测试")
    print("=" * 80)
    
    # 创建系统
    system = LiuXiangLiuTiSystem()
    
    # 测试 1：查询六十日相替定局
    print("\n【测试 1】六十日相替定局查询表")
    system.query_table.print_query_table()
    
    # 测试 2：分析单日
    print("\n\n【测试 2】分析单日（甲辰日）")
    day_analysis = system.analyze_day('甲', '辰')
    print(f"  干支：{day_analysis['干支']}")
    print(f"  状态：{day_analysis['状态']}")
    print(f"  六相/六替：{day_analysis['六相/六替']}")
    print(f"  吉凶：{day_analysis['吉凶']}")
    print(f"  分数：{day_analysis['分数']}")
    print(f"  含义：{day_analysis['含义']}")
    
    # 测试 3：分析四柱
    print("\n\n【测试 3】分析四柱（丙午 辛卯 甲辰 辛未）")
    sizhu = {
        '年柱': '丙午',
        '月柱': '辛卯',
        '日柱': '甲辰',
        '时柱': '辛未'
    }
    sizhu_analysis = system.analyze_sizhu(sizhu)
    print(f"  六相数：{sizhu_analysis['六相统计']}")
    print(f"  六替数：{sizhu_analysis['六替统计']}")
    print(f"  总评分：{sizhu_analysis['总评分']}")
    print(f"  吉凶判断：{sizhu_analysis['吉凶判断']}")
    
    # 测试 4：获取完整报告
    print("\n\n【测试 4】完整分析报告（壬山，丙午 辛卯 甲辰 辛未）")
    report = system.get_complete_report('壬', sizhu, ['申', '午', '午'])
    print(report)
    
    # 测试 5：生死真假辨
    print("\n\n【测试 5】决断生死真假辨")
    system.analyzer.print_life_death_table()
    
    # 测试 6：补救之法
    print("\n\n【测试 6】补救之法指南")
    system.remedy.print_remedy_guide()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    test_complete_system()
