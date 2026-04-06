#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合吉凶评价系统

整合斗首断语与六壬课格断语
提供 0-100 分制综合评分

基于《六壬大全》（钦定四库全书本）64 课经
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'utils'))
from ganzhi_calendar import get_sizhu_accurate

sys.path.insert(0, os.path.dirname(__file__))
from precise_auspicious import PreciseAuspicousCalculator

# 导入完整的 64 课经断语库
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
from kejing_duanyu_complete import KEJING_DUANYU_COMPLETE

# 导入详细的六壬课体课格断语库
sys.path.insert(0, os.path.dirname(__file__))
from liuren_keti_duanyu import LiuRenKetiDuanyu


class ComprehensiveEvaluation:
    """综合吉凶评价类"""
    
    def __init__(self):
        self.ausp_calc = PreciseAuspicousCalculator()
        
        # 斗首断语库
        self.doushou_duanyu = {
            '武财课': {
                'score': 95,
                'duanyu': [
                    '武财生旺，财源广进，利市三倍',
                    '年月双武生山家及元辰，大吉大利',
                    '武财得地，经商获利，投资成功',
                ],
                'summary': '武财为吉星，主财富利市，最宜求财交易'
            },
            '元辰课': {
                'score': 88,
                'duanyu': [
                    '元辰旺相得令，家业兴隆，子孙昌盛',
                    '元辰临官，日时之长生或吉地也吉',
                    '元辰旺而不受克，宜见一位廉子，必大旺人丁',
                ],
                'summary': '元辰为根本，主家业人丁，宜祭祀祈福'
            },
            '廉贞课': {
                'score': 65,
                'duanyu': [
                    '元辰生旺无伤，宜见一位廉子，则人丁大旺',
                    '多见廉子则人丁稀矣',
                    '元辰衰弱受伤，若见廉子则人丁必绝',
                ],
                'summary': '廉贞为子孙星，吉凶视元辰旺衰而定'
            },
            '贪官课': {
                'score': 35,
                'duanyu': [
                    '贪官克山头元辰，为大凶之课',
                    '年、月、时三重贪官克山头元辰，大凶',
                    '贪官遇生旺之武财通关，则化凶为吉',
                ],
                'summary': '贪官为凶宿，克元辰，需谨慎使用'
            },
            '破鬼课': {
                'score': 28,
                'duanyu': [
                    '鬼破不宜见，只有鬼破衰弱而居月柱可用',
                    '鬼破重见本已凶，鬼煞又坐于长生位，大凶',
                    '破鬼本是克山头之神，最为忌之',
                ],
                'summary': '破鬼为凶星，泄元气，多主破败'
            },
        }
        
        # 六壬课格断语库（使用完整的 64 课经断语）
        self.kejing_duanyu = KEJING_DUANYU_COMPLETE
        
        # 详细六壬课体课格断语库
        self.liuren_keti = LiuRenKetiDuanyu()
    
    def evaluate_date(self, year: int, month: int, day: int, hour: int, 
                     shan_name: str = None, kejing_name: str = None) -> dict:
        """
        综合评价指定日期的吉凶
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :param shan_name: 坐山
        :param kejing_name: 六壬课格
        :return: 综合评价结果
        """
        # 1. 计算四柱
        sizhu = get_sizhu_accurate(year, month, day, hour)
        
        # 2. 计算年月日时吉凶
        year_fortune = self.ausp_calc.calculate_year_fortune(year)
        month_fortune = self.ausp_calc.calculate_month_fortune(year, month)
        day_fortune = self.ausp_calc.calculate_day_fortune(year, month, day, shan_name)
        hour_fortune = self.ausp_calc.calculate_hour_fortune(year, month, day, hour, shan_name)
        
        # 3. 斗首课格评价
        doushou_info = self._get_doushou_evaluation(day_fortune.get('斗首课格', '平课'))
        
        # 4. 六壬课格评价
        kejing_info = self._get_kejing_evaluation(kejing_name)
        
        # 5. 综合评分（0-100 分制）
        # 权重：年 15% + 月 20% + 日 35% + 斗首 15% + 六壬 15%
        total_score = (
            year_fortune['评分'] * 1.5 +      # 10 分制 → 15 分
            month_fortune['评分'] * 2.0 +     # 10 分制 → 20 分
            day_fortune['评分'] * 3.5 +       # 10 分制 → 35 分
            doushou_info['score'] * 0.15 +    # 100 分制 → 15 分
            kejing_info['score'] * 0.15       # 100 分制 → 15 分
        )
        
        # 6. 综合评语
        zonghe_pingyu = self._generate_zonghe_pingyu(
            total_score, year_fortune, month_fortune, day_fortune,
            doushou_info, kejing_info
        )
        
        # 7. 宜忌建议
        yiji = self._generate_yiji(total_score, doushou_info, kejing_info)
        
        return {
            '日期': f"{year}-{month:02d}-{day:02d} {hour:02d}:00",
            '四柱': sizhu,
            '年运': year_fortune,
            '月运': month_fortune,
            '日运': day_fortune,
            '时运': hour_fortune,
            '斗首': doushou_info,
            '六壬': kejing_info,
            '综合评分': round(total_score, 1),
            '吉凶等级': self._get_jixiong_level(total_score),
            '综合评语': zonghe_pingyu,
            '宜忌': yiji
        }
    
    def _get_doushou_evaluation(self, kege: str) -> dict:
        """获取斗首课格评价"""
        return self.doushou_duanyu.get(kege, {
            'score': 60,
            'duanyu': ['平课，无特殊吉凶'],
            'summary': '平课，平稳无奇'
        })
    
    def _get_kejing_evaluation(self, kejing: str) -> dict:
        """获取六壬课格评价（整合两个断语库）"""
        if not kejing:
            return {
                'score': 60,
                'duanyu': ['课格未定'],
                'summary': '待排盘确定',
                '详细断语': {},
                '宜事': [],
                '忌事': []
            }
        
        # 从完整断语库获取基础信息
        base_info = self.kejing_duanyu.get(kejing, {
            'score': 60,
            'level': '吉凶参半',
            'duanyu': ['平课，无特殊吉凶'],
            'summary': '平课，平稳无奇'
        })
        
        # 从详细断语库获取补充信息
        detail_info = self.liuren_keti.keti_jixiong.get(kejing, {})
        
        # 合并信息
        result = {
            'score': base_info.get('score', 60),
            'level': base_info.get('level', '吉凶参半'),
            'duanyu': base_info.get('duanyu', []),
            'summary': base_info.get('summary', ''),
            '详细断语': detail_info.get('详细断语', {}),
            '宜事': detail_info.get('宜事', []),
            '忌事': detail_info.get('忌事', []),
            '属相吉': detail_info.get('属相吉', []),
            '属相凶': detail_info.get('属相凶', []),
            '行业': detail_info.get('行业', []),
            '发福年限': detail_info.get('发福年限', ''),
            '吉神宜趋': detail_info.get('吉神宜趋', []),
            '凶神宜忌': detail_info.get('凶神宜忌', [])
        }
        
        return result
    
    def _generate_zonghe_pingyu(self, score: float, year: dict, month: dict, 
                               day: dict, doushou: dict, kejing: dict) -> str:
        """生成综合评语"""
        pingyu = []
        
        # 年运评语
        pingyu.append(f"【年运】{year['年柱']}：{year['说明']}")
        
        # 月运评语
        pingyu.append(f"【月运】{month['月柱']}：{month['说明']}")
        
        # 日运评语
        pingyu.append(f"【日运】{day['日柱']}：{day['说明']}")
        
        # 斗首评语
        pingyu.append(f"【斗首】{doushou.get('summary', '')}")
        
        # 六壬详细评语
        pingyu.append(f"【六壬】{kejing.get('summary', '')}")
        
        # 添加六壬课格断语
        if kejing.get('duanyu'):
            pingyu.append("\n【课格断语】")
            for duan in kejing['duanyu']:
                pingyu.append(f"  • {duan}")
        
        # 添加详细断语（如果有）
        if kejing.get('详细断语'):
            detail_duanyu = kejing['详细断语']
            if detail_duanyu.get('总论'):
                pingyu.append(f"\n【总论】{detail_duanyu['总论']}")
        
        # 添加发福年限
        if kejing.get('发福年限'):
            pingyu.append(f"\n【发福年限】{kejing['发福年限']}")
        
        # 添加属相建议
        if kejing.get('属相吉'):
            pingyu.append(f"【属相吉】{', '.join(kejing['属相吉'])}")
        if kejing.get('属相凶'):
            pingyu.append(f"【属相凶】{', '.join(kejing['属相凶'])}")
        
        # 添加行业建议
        if kejing.get('行业'):
            pingyu.append(f"【适宜行业】{', '.join(kejing['行业'])}")
        
        # 添加吉神凶神
        if kejing.get('吉神宜趋'):
            pingyu.append(f"【吉神宜趋】{', '.join(kejing['吉神宜趋'])}")
        if kejing.get('凶神宜忌'):
            pingyu.append(f"【凶神宜忌】{', '.join(kejing['凶神宜忌'])}")
        
        # 总体评价
        pingyu.append("\n" + "=" * 40)
        if score >= 90:
            pingyu.append("【总评】上上大吉，百事皆宜，贵人扶持，谋事可成")
        elif score >= 80:
            pingyu.append("【总评】上吉，大利，宜积极进取")
        elif score >= 70:
            pingyu.append("【总评】中吉，平稳，可办一般事项")
        elif score >= 60:
            pingyu.append("【总评】小吉，平平，宜守不宜攻")
        elif score >= 50:
            pingyu.append("【总评】吉凶参半，需谨慎")
        elif score >= 40:
            pingyu.append("【总评】小凶，不利，建议另择吉日")
        elif score >= 30:
            pingyu.append("【总评】中凶，多凶少吉，不宜行事")
        elif score >= 20:
            pingyu.append("【总评】大凶，灾祸临门，严禁行事")
        else:
            pingyu.append("【总评】上凶，极凶，绝对不可用")
        
        return "\n".join(pingyu)
    
    def _generate_yiji(self, score: float, doushou: dict, kejing: dict) -> dict:
        """生成宜忌建议（优先使用详细断语库中的宜忌）"""
        # 优先使用详细断语库中的宜忌
        yi = kejing.get('宜事', [])
        ji = kejing.get('忌事', [])
        
        # 如果没有详细断语库的宜忌，则使用默认的
        if not yi and not ji:
            if score >= 80:
                yi = ['祭祀', '祈福', '嫁娶', '入宅', '开市', '交易', '求财', '出行']
                ji = ['动土', '破土']
            elif score >= 70:
                yi = ['祭祀', '祈福', '嫁娶', '入宅', '开市']
                ji = ['动土', '破土', '安葬', '远行']
            elif score >= 60:
                yi = ['祭祀', '祈福', '平事']
                ji = ['嫁娶', '入宅', '开市', '动土']
            else:
                yi = ['静守', '避灾']
                ji = ['百事不宜']
        
        return {'宜': yi, '忌': ji}
    
    def _get_jixiong_level(self, score: float) -> str:
        """根据评分返回吉凶等级"""
        if score >= 90:
            return "上上大吉"
        elif score >= 80:
            return "上吉"
        elif score >= 70:
            return "中吉"
        elif score >= 60:
            return "小吉"
        elif score >= 50:
            return "吉凶参半"
        elif score >= 40:
            return "小凶"
        elif score >= 30:
            return "中凶"
        elif score >= 20:
            return "大凶"
        else:
            return "上凶"


def test_evaluation():
    """测试综合评价"""
    eval_sys = ComprehensiveEvaluation()
    
    print("=" * 80)
    print("综合吉凶评价测试 - 验证断语库关联")
    print("=" * 80)
    
    # 测试几个常见课格
    test_kejings = ['元首课', '龙德课', '重审课', '知一课']
    
    for kejing in test_kejings:
        print(f"\n{'=' * 80}")
        print(f"测试课格：{kejing}")
        print('=' * 80)
        
        # 测试 2026-03-20 23:00 壬山
        result = eval_sys.evaluate_date(2026, 3, 20, 23, '壬山', kejing)
        
        print(f"\n日期：{result['日期']}")
        print(f"四柱：{result['四柱']['年柱']} {result['四柱']['月柱']} {result['四柱']['日柱']} {result['四柱']['时柱']}")
        print(f"\n综合评分：{result['综合评分']}分 - {result['吉凶等级']}")
        print(f"\n【综合评语】\n{result['综合评语']}")
        print(f"\n【宜忌】")
        print(f"宜：{', '.join(result['宜忌']['宜'])}")
        print(f"忌：{', '.join(result['宜忌']['忌'])}")
        
        # 验证六壬信息是否包含详细断语
        liuren_info = result.get('六壬', {})
        print(f"\n【验证断语库关联】")
        print(f"  • 有详细断语：{'是' if liuren_info.get('详细断语') else '否'}")
        print(f"  • 有宜事：{'是' if liuren_info.get('宜事') else '否'}")
        print(f"  • 有忌事：{'是' if liuren_info.get('忌事') else '否'}")
        print(f"  • 有属相吉：{'是' if liuren_info.get('属相吉') else '否'}")
        print(f"  • 有行业：{'是' if liuren_info.get('行业') else '否'}")


if __name__ == '__main__':
    test_evaluation()
