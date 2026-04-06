#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终分析：综合六相六替与生死辩
重新分析 5 个吉日
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from liuxiang_liuti_correct import LiuXiangLiuTiCorrect


def analyze_with_shengsi(sizhu: dict, shan_wuxing: str = '土'):
    """
    综合分析四柱，包含生死辩（季节旺衰）
    注意：只有月柱才论季节旺衰！年柱、日柱、时柱不论！
    """
    system = LiuXiangLiuTiCorrect()
    
    result = {
        '四柱分析': {},
        '六相统计': 0,
        '六替统计': 0,
        '吉课数': 0,
        '凶课数': 0,
        '总分': 0,
        '综合评价': ''
    }
    
    # 获取月份地支用于季节旺衰判断（仅用于月柱）
    month_dizhi = sizhu['月柱'][1]
    
    for pillar_name, ganzhi in sizhu.items():
        analysis = system.analyze_pillar(ganzhi, shan_wuxing)
        
        # 只有月柱才论季节旺衰（生死辩）
        if pillar_name == '月柱':
            huaqi_wuxing = analysis['化气']
            wangshuai = system.get_wangshuai(huaqi_wuxing, month_dizhi)
            analysis['季节旺衰'] = wangshuai
            
            # 生死辩特别规则：水在夏季为囚，不可用
            if huaqi_wuxing == '水' and wangshuai == '囚':
                # 夏季水囚，即使是六相也要降级
                if analysis['六亲'] in ['元辰', '武财']:
                    analysis['生死辩判定'] = '夏季水囚，减分'
                    analysis['吉凶'] = '平'  # 降级为平
                else:
                    analysis['生死辩判定'] = '夏季水囚'
                    analysis['吉凶'] = analysis['吉凶']
            else:
                analysis['生死辩判定'] = '可用'
        else:
            # 年柱、日柱、时柱不论季节旺衰
            analysis['季节旺衰'] = '不论'
            analysis['生死辩判定'] = '不论'
        
        # 评分
        score = 0
        if analysis['吉凶'] == '吉':
            if analysis['生死辩判定'] == '可用':
                score = 95 if analysis['六相/六替'] == '六相' else 90
            elif analysis['生死辩判定'] == '夏季水囚，减分':
                score = 60  # 夏季水囚，减分
            else:
                score = 95 if analysis['六相/六替'] == '六相' else 90  # 年月日时不论
        elif analysis['吉凶'] == '平':
            score = 70
        else:  # 凶
            score = 30
        
        # 特别加分：帝旺、临官
        if analysis['长生状态'] == '帝旺':
            score += 5
        elif analysis['长生状态'] == '临官':
            score += 3
        
        analysis['分数'] = min(score, 100)  # 上限 100 分
        
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
    
    # 平均分数
    result['平均分'] = result['总分'] / 4
    
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
    print('最终分析：综合六相六替与生死辩')
    print('重新分析 5 个吉日（壬山，2026.3.24-2029.3.24）')
    print('='*100)
    
    # 原来的 5 个日课
    original_5_days = [
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
        },
        {
            '排名': 3,
            '公历': '2026 年 5 月 24 日 午时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '癸巳',
                '日柱': '庚子',
                '时柱': '壬午'
            }
        },
        {
            '排名': 4,
            '公历': '2026 年 7 月 8 日 巳时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '甲午',
                '日柱': '壬申',
                '时柱': '乙巳'
            }
        },
        {
            '排名': 5,
            '公历': '2026 年 9 月 16 日 辰时',
            'sizhu': {
                '年柱': '丙午',
                '月柱': '丙申',
                '日柱': '戊戌',
                '时柱': '丙辰'
            }
        }
    ]
    
    results = []
    
    for day in original_5_days:
        print(f'\n{"="*100}')
        print(f'第{day["排名"]}名：{day["公历"]}')
        print(f'四柱：{day["sizhu"]["年柱"]} {day["sizhu"]["月柱"]} {day["sizhu"]["日柱"]} {day["sizhu"]["时柱"]}')
        print('='*100)
        
        result = analyze_with_shengsi(day['sizhu'], '土')
        results.append({
            '排名': day['排名'],
            '公历': day['公历'],
            '四柱': f'{day["sizhu"]["年柱"]} {day["sizhu"]["月柱"]} {day["sizhu"]["日柱"]} {day["sizhu"]["时柱"]}',
            '分析结果': result
        })
        
        print(f'\n【逐柱详细分析】')
        for pillar_name, analysis in result['四柱分析'].items():
            print(f'\n{pillar_name}: {analysis["干支"]}')
            print(f'  天干化气：{analysis["天干"]} → {analysis["化气"]} ({analysis["六亲"]})')
            print(f'  地支长生：{analysis["地支"]} 为 {analysis["化气"]} 的{analysis["长生状态"]} ({analysis["六相/六替"]})')
            print(f'  季节旺衰：{analysis["季节旺衰"]} ({analysis["生死辩判定"]})')
            print(f'  吉凶判定：{analysis["吉凶"]} - {analysis["分数"]}分')
        
        print(f'\n【综合评分】')
        print(f'  六相数：{result["六相统计"]}个')
        print(f'  六替数：{result["六替统计"]}个')
        print(f'  吉课数：{result["吉课数"]}个')
        print(f'  凶课数：{result["凶课数"]}个')
        print(f'  总分：{result["总分"]}分')
        print(f'  平均分：{result["平均分"]:.1f}分')
        print(f'  综合评价：{result["综合评价"]}')
    
    # 重新排序
    print('\n' + '='*100)
    print('重新排序（按综合评分）')
    print('='*100)
    
    results_sorted = sorted(results, key=lambda x: x['分析结果']['平均分'], reverse=True)
    
    for i, result in enumerate(results_sorted, 1):
        r = result['分析结果']
        print(f'\n第{i}名：{result["公历"]}')
        print(f'  四柱：{result["四柱"]}')
        print(f'  平均分：{r["平均分"]:.1f}分 ({r["综合评价"]})')
        print(f'  吉课数：{r["吉课数"]}个，凶课数：{r["凶课数"]}个')
    
    # 月份选择对比
    compare_month_options('丙', '丙')
    
    print('\n' + '='*100)
    print('分析完成')
    print('='*100)


if __name__ == '__main__':
    main()
