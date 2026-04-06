#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首择日第一斗首课格断语系统

包含第一斗首课格的完整断语内容
断语依据传统斗首择日秘本整理
"""


class DiYiDouShouKeGe:
    """第一斗首课格断语类"""
    
    def __init__(self):
        self.ke_ge_data = self._init_ke_ge_data()
    
    def _init_ke_ge_data(self):
        """初始化第一斗首课格数据（依据斗首择日秘本）"""
        return {
            '元辰课': {
                'name': '元辰课',
                'description': '元辰与山家五行相同者即为元辰，元辰宜生旺，最宜临月令长生、临官、帝旺之地',
                'duanyu': [
                    '元辰旺相得令，家业兴隆，子孙昌盛',
                    '元辰休囚失令，家道中落，人丁不旺',
                    '元辰临官、日时之长生或吉地也吉',
                    '元辰为吉神，如衰弱或受贪官夹克，虽有如无',
                    '元辰旺而不受克，宜见一位廉子，如此必大旺人丁',
                    '建阳宅，元辰入墓，日久必绝嗣',
                ],
                'shiyong': '宜：祭祀、祈福、求嗣、嫁娶、入宅、建祠\n忌：动土、破土、安葬（元辰入墓时）',
                'jixiong': '吉星，宜生旺，不宜衰弱',
                'score': 8.5,  # 吉星，但需视旺衰
                'usable': True
            },
            '武财课': {
                'name': '武财课',
                'description': '武财为山家所克之五行，其番化五行生山家元辰，故武财是吉星',
                'duanyu': [
                    '武财宜生旺，不宜受克',
                    '武财生山家及元辰，为吉格',
                    '年月双武生山家及元辰，大吉',
                    '武财只宜用于阴宅行事，元辰入墓日阳宅行事则不吉',
                    '武财旺相，财源广进，利市三倍',
                    '武财得地，经商获利，投资成功',
                ],
                'shiyong': '宜：开市、交易、纳财、求财、阴宅行事\n忌：阳宅行事（元辰入墓时）',
                'jixiong': '吉星，主财运',
                'score': 9.0,  # 吉星，番化生元辰
                'usable': True
            },
            '贪官课': {
                'name': '贪官课',
                'description': '贪官之番化五行会克元辰，会克山家五行，故贪官为凶宿',
                'duanyu': [
                    '贪官遇生旺之武财通关，则化凶为吉',
                    '贪官克山头元辰，为大凶之课',
                    '年、月、时三重贪官克山头元辰，大凶',
                    '贪官为凶宿，若得制伏则不忌',
                    '贪官旺相，事业有成，名利双收',
                    '贪官遇凶，贪多嚼不烂，反遭损失',
                ],
                'shiyong': '宜：制伏后使用\n忌：三重贪官克元辰',
                'jixiong': '凶星，需制伏',
                'score': 3.0,  # 凶星，克元辰
                'usable': False
            },
            '廉贞课': {
                'name': '廉贞课',
                'description': '廉子即是子孙也，若日课得元辰生旺无伤，课中宜见一位廉子，则人丁大旺',
                'duanyu': [
                    '元辰生旺无伤，宜见一位廉子，则人丁大旺',
                    '多见廉子则人丁稀矣',
                    '元辰衰弱受伤，若见廉子则人丁必绝',
                    '廉子为山家五行所生者也，其番化五行为山家所克者',
                    '元辰旺宜见一位廉子，必大吉，此为大旺人丁之课',
                    '廉子重见则伤克子孙，不然亦会损父母',
                ],
                'shiyong': '宜：求嗣、催丁、建祠\n忌：元辰衰弱时见廉子',
                'jixiong': '吉凶视元辰旺衰而定',
                'score': 6.0,  # 吉凶参半，视情况而定
                'usable': True
            },
            '破鬼课': {
                'name': '破鬼课',
                'description': '鬼破本来为克山家之神，其番化五行又为山家所生，会泄山家之元辰精气',
                'duanyu': [
                    '鬼破不宜见，只有鬼破衰弱而居月柱，年日为武财时可用',
                    '武财关鬼格：年日为武财夹克鬼破，此课为可用之吉课',
                    '鬼破重见本已凶，鬼煞又坐于长生位，大凶',
                    '破鬼本是克山头之神，是鬼杀也，番化又为我生，最为忌之',
                    '破鬼逢制伏，不能兴风作浪，此课可用',
                    '破鬼旺相，除旧布新，改革成功',
                ],
                'shiyong': '宜：武财夹克时可用\n忌：鬼破重见、鬼破坐长生',
                'jixiong': '凶星，需制伏方可用',
                'score': 2.5,  # 凶星，泄元气
                'usable': False
            },
        }
    
    def get_ke_ge(self, ke_ge_name: str) -> dict:
        """
        获取课格信息
        :param ke_ge_name: 课格名称
        :return: 课格数据字典
        """
        return self.ke_ge_data.get(ke_ge_name, None)
    
    def get_all_ke_ge_names(self) -> list:
        """获取所有课格名称"""
        return list(self.ke_ge_data.keys())
    
    def get_ke_ge_duanyu(self, ke_ge_name: str) -> list:
        """
        获取课格断语列表
        :param ke_ge_name: 课格名称
        :return: 断语列表
        """
        ke_ge = self.get_ke_ge(ke_ge_name)
        if ke_ge:
            return ke_ge.get('duanyu', [])
        return []
    
    def get_ke_ge_shiyong(self, ke_ge_name: str) -> str:
        """
        获取课格宜忌
        :param ke_ge_name: 课格名称
        :return: 宜忌说明
        """
        ke_ge = self.get_ke_ge(ke_ge_name)
        if ke_ge:
            return ke_ge.get('shiyong', '')
        return ''
    
    def get_ke_ge_jixiong(self, ke_ge_name: str) -> str:
        """
        获取课格吉凶
        :param ke_ge_name: 课格名称
        :return: 吉凶说明
        """
        ke_ge = self.get_ke_ge(ke_ge_name)
        if ke_ge:
            return ke_ge.get('jixiong', '')
        return ''
    
    def get_ke_ge_score(self, ke_ge_name: str) -> float:
        """获取课格吉凶评分（10 分制）"""
        ke_ge = self.get_ke_ge(ke_ge_name)
        if ke_ge:
            return ke_ge.get('score', 5.0)
        return 0.0
    
    def is_ke_ge_usable(self, ke_ge_name: str) -> bool:
        """判断课格是否可用（5 分以上为可用）"""
        score = self.get_ke_ge_score(ke_ge_name)
        return score >= 5.0
    
    def get_score_description(self, score: float) -> str:
        """根据评分返回吉凶描述"""
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
    
    def analyze_ke_ge(self, ke_ge_name: str) -> str:
        """
        分析课格（完整报告）
        :param ke_ge_name: 课格名称
        :return: 完整分析报告
        """
        ke_ge = self.get_ke_ge(ke_ge_name)
        if not ke_ge:
            return f"未找到课格：{ke_ge_name}"
        
        report = []
        report.append("=" * 70)
        report.append(f"第一斗首课格：{ke_ge['name']}")
        report.append("=" * 70)
        report.append(f"\n【课格说明】{ke_ge['description']}\n")
        report.append("【断语】")
        for i, duanyu in enumerate(ke_ge['duanyu'], 1):
            report.append(f"  {i}. {duanyu}")
        report.append(f"\n【宜忌】{ke_ge['shiyong']}")
        report.append(f"\n【吉凶】{ke_ge['jixiong']}")
        report.append("=" * 70)
        
        return "\n".join(report)


def test_di_yi_dou_shou():
    """测试第一斗首课格系统"""
    analyzer = DiYiDouShouKeGe()
    
    print("\n可用的课格：")
    for name in analyzer.get_all_ke_ge_names():
        print(f"  - {name}")
    
    # 测试元辰课
    print("\n" + "=" * 70)
    print("测试：元辰课")
    print("=" * 70)
    report = analyzer.analyze_ke_ge('元辰课')
    print(report)
    
    # 测试武财课
    print("\n" + "=" * 70)
    print("测试：武财课")
    print("=" * 70)
    report = analyzer.analyze_ke_ge('武财课')
    print(report)


if __name__ == '__main__':
    test_di_yi_dou_shou()
