#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终分析：综合六相六替与真假生死辨
重新分析 5 个吉日
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from liuxiang_liuti_correct import LiuXiangLiuTiCorrect


def analyze_with_shengsi(sizhu: dict, shan_wuxing: str = '土'):
    """
    综合分析四柱，包含真假生死辨（季节旺衰）
    注意：只有月柱才论真假生死辨！年柱、日柱、时柱不论！
    """
    system = LiuXiangLiuTiCorrect()

    result = {
        '四柱分析': {},
        '六相统计': 0,
        '六替统计': 0,
        '吉课数': 0,
        '凶课数': 0,
        '平课数': 0,
        '总分': 0,
        '平均分': 0,
        '综合评价': '',
        '真假辨说明': ''
    }

    # 获取月柱地支用于真假辨
    month_zhi = sizhu.get('月柱', '')[1] if len(sizhu.get('月柱', '')) > 1 else None

    # 评分标准
    score_map = {
        '吉': 90,
        '平': 70,
        '凶': 30
    }

    # 特别加分：帝旺、临官
    bonus_map = {
        '帝旺': 10,
        '临官': 5,
        '长生': 5,
        '冠带': 3,
        '胎': 2,
        '养': 1
    }

    # 特别减分：死、墓、绝
    penalty_map = {
        '死': -10,
        '墓': -5,
        '绝': -5,
        '病': -3,
        '衰': -2,
        '沐浴': -2
    }

    for pillar_name, ganzhi in sizhu.items():
        is_month = (pillar_name == '月柱')
        analysis = system.analyze_pillar(ganzhi, shan_wuxing, is_month, month_zhi)

        # 评分
        pillar_score = score_map.get(analysis['吉凶'], 50)

        # 附加分（基于长生状态）
        changsheng = analysis['长生状态']
        if changsheng in bonus_map:
            pillar_score += bonus_map[changsheng]
        elif changsheng in penalty_map:
            pillar_score += penalty_map[changsheng]

        analysis['分数'] = max(0, min(100, pillar_score))

        result['四柱分析'][pillar_name] = analysis
        result['总分'] += analysis['分数']

        if analysis['六相/六替'] == '六相':
            result['六相统计'] += 1
        else:
            result['六替统计'] += 1

        if analysis['吉凶'] == '吉':
            result['吉课数'] += 1
        elif analysis['吉凶'] == '凶':
            result['凶课数'] += 1
        else:
            result['平课数'] += 1

    # 平均分数
    result['平均分'] = result['总分'] / 4

    # 真假辨说明
    month_analysis = result['四柱分析'].get('月柱', {})
    if '真假生死辨' in month_analysis:
        zj = month_analysis['真假生死辨']
        result['真假辨说明'] = f"月柱{zj['真假']}，{zj['原因']}"

    # 综合评价
    if result['吉课数'] >= 3 and result['凶课数'] == 0:
        result['综合评价'] = '上上大吉'
    elif result['吉课数'] >= 2:
        result['综合评价'] = '吉'
    elif result['吉课数'] >= 1:
        result['综合评价'] = '平'
    else:
        result['综合评价'] = '凶'

    return result


def compare_month_options(year_tiangan: str, day_tiangan: str):
    """
    比较不同月份的选择
    例如：丙午年，丙日，可选壬辰月或丙申月
    """
    print('\n' + '='*100)
    print('月份选择对比分析')
    print('='*100)

    system = LiuXiangLiuTiCorrect()

    # 丙申月分析
    print('\n【丙申月】')
    print('丙申月干支分析：')
    analysis_bingshen = system.analyze_pillar('丙申', '土')
    print(f'  丙化{analysis_bingshen["化气"]} → {analysis_bingshen["六亲"]}')
    print(f'  申为{analysis_bingshen["化气"]}的{analysis_bingshen["长生状态"]} ({analysis_bingshen["六相/六替"]})')
    print(f'  吉凶：{analysis_bingshen["吉凶"]}')

    # 壬辰月分析
    print('\n【壬辰月】')
    print('壬辰月干支分析：')
    analysis_renchen = system.analyze_pillar('壬辰', '土')
    print(f'  壬化{analysis_renchen["化气"]} → {analysis_renchen["六亲"]}')
    print(f'  辰为{analysis_renchen["化气"]}的{analysis_renchen["长生状态"]} ({analysis_renchen["六相/六替"]})')
    print(f'  吉凶：{analysis_renchen["吉凶"]}')

    print('\n【对比结论】')
    print('丙申月：丙化水为武财（吉星），申为水的长生（六相）')
    print('        → 吉星坐六相，符合"吉星要坐六相"原则，为吉！')
    print('壬辰月：壬化木为贪官（凶星），辰为木的衰（六替）')
    print('        → 凶星坐六替，符合"凶星要坐六替"原则，为吉！')
    print('\n两者都符合六相六替原则，但丙申月更优（武财吉星坐长生旺地）！')


def main():
    print('='*100)
    print('最终分析：综合六相六替与真假生死辨')
    print('重新分析 5 个吉日（壬山，2026.3.24-2029.3.24）')
    print('='*100)

    # 测试案例
    test_cases = [
        {
            '排名': 1,
            '公历': '2026 年 4 月 22 日 申时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '壬辰',
                '日柱': '丙寅',
                '时柱': '丙申'
            }
        },
        {
            '排名': 2,
            '公历': '2026 年 3 月 31 日 未时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '辛卯',
                '日柱': '甲辰',
                '时柱': '辛未'
            }
        }
    ]

    for case in test_cases:
        print(f'\n{"="*100}')
        print(f'第{case["排名"]}名：{case["公历"]}')
        print(f'四柱：{case["sizhu"]["年柱"]} {case["sizhu"]["月柱"]} {case["sizhu"]["日柱"]} {case["sizhu"]["时柱"]}')
        print('='*100)

        result = analyze_with_shengsi(case['sizhu'], '土')

        print(f'\n【逐柱分析】（包含真假生死辨）')
        for pillar_name, analysis in result['四柱分析'].items():
            print(f'\n  {pillar_name}: {analysis["干支"]}')
            print(f'    天干化气：{analysis["天干"]} → {analysis["化气"]}')
            print(f'    六亲：{analysis["六亲"]}')
            print(f'    长生状态：{analysis["长生状态"]} ({analysis["六相/六替"]})')
            if '真假生死辨' in analysis:
                zj = analysis['真假生死辨']
                print(f'    真假生死辨：{zj["真假"]} - {zj["原因"]}')
                print(f'    可用性：{zj["可用性"]}')
            print(f'    吉凶：{analysis["吉凶"]} ({analysis["吉凶原因"]})')
            print(f'    评分：{analysis["分数"]}分')

        print(f'\n【统计】')
        print(f'  六相数：{result["六相统计"]}')
        print(f'  六替数：{result["六替统计"]}')
        print(f'  吉课数：{result["吉课数"]}')
        print(f'  平课数：{result["平课数"]}')
        print(f'  凶课数：{result["凶课数"]}')
        print(f'  总分：{result["总分"]}')
        print(f'  平均分：{result["平均分"]:.1f}')
        print(f'  综合评价：{result["综合评价"]}')
        if result['真假辨说明']:
            print(f'  真假辨：{result["真假辨说明"]}')


if __name__ == '__main__':
    main()
