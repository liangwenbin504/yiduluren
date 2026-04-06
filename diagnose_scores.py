#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本：检查三个模块评分情况
找出为什么筛选出0个吉课
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'zongmen', 'src', 'utils'))

print('=' * 70)
print('三模块评分诊断')
print('=' * 70)

# 导入模块
from douhou_analyzer import DouhouKegeAnalyzer
from yanqin_analyzer import YanQinAnalyzer
from dizhi_layout_generator import arrange_tiandi_pan
from sike_sanchuan_engine import SiKeSanChuanCalculator
from gui_ren_engine import GuiRenCalculator
from sizhu_engine import get_sizhu

# 加载64课经数据
ke_jing_path = os.path.join(os.path.dirname(__file__), 'data', '64_ke_jing_accurate.json')
ke_jing_data = {}
try:
    with open(ke_jing_path, 'r', encoding='utf-8') as f:
        ke_jing = json.load(f)
        for k, v in ke_jing.get('courses', {}).items():
            ke_jing_data[v['ke_name']] = v
    print(f'[OK] 加载64课经数据: {len(ke_jing_data)}个课体')
except Exception as e:
    print(f'[FAIL] 加载64课经数据失败: {e}')

# 初始化
doushou_analyzer = DouhouKegeAnalyzer()
yanqin_analyzer = YanQinAnalyzer()
sike_calc = SiKeSanChuanCalculator()
guiren_calc = GuiRenCalculator()

# 常量
LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'}
YIMA = {'申': '寅', '子': '寅', '辰': '寅', '亥': '巳', '卯': '巳', '未': '巳', '寅': '申', '午': '申', '戌': '申', '巳': '亥', '酉': '亥', '丑': '亥'}
SHAN_XIANG = {'壬': '丙', '子': '午', '癸': '丁', '丑': '未', '艮': '坤', '寅': '申', '甲': '庚', '卯': '酉', '乙': '辛', '辰': '戌', '巽': '乾', '巳': '亥', '丙': '壬', '午': '子', '丁': '癸', '未': '丑', '坤': '艮', '申': '寅', '庚': '甲', '酉': '卯', '辛': '乙', '戌': '辰', '乾': '巽', '亥': '巳'}

# 测试参数
mountain = '壬'
xiang = SHAN_XIANG.get(mountain, '')

print(f'\n坐山: {mountain}, 向: {xiang}')
print(f'评分要求: 斗首≥70, 六壬≥70, 演禽≥70')

# 统计
stats = {
    'total': 0,
    'doushou_pass': 0,
    'daliuren_pass': 0,
    'yanqin_pass': 0,
    'all_pass': 0,
    'doushou_scores': [],
    'daliuren_scores': [],
    'yanqin_scores': []
}

# 测试日期范围：2026年1月前10天
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 1, 10)
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

print(f'\n测试日期: {start_date.strftime("%Y-%m-%d")} 至 {end_date.strftime("%Y-%m-%d")}')
print('-' * 70)

current_date = start_date
while current_date <= end_date:
    year = current_date.year
    month = current_date.month
    day = current_date.day
    
    for shichen in DIZHI:
        stats['total'] += 1
        
        # 获取四柱
        sizhu_result = get_sizhu(year, month, day, shichen)
        if not sizhu_result:
            continue
        
        sizhu = {
            '年柱': sizhu_result.get('年柱', ''),
            '月柱': sizhu_result.get('月柱', ''),
            '日柱': sizhu_result.get('日柱', ''),
            '时柱': sizhu_result.get('时柱', '')
        }
        
        ri_gan = sizhu['日柱'][0] if sizhu['日柱'] else '甲'
        ri_zhi = sizhu['日柱'][1] if len(sizhu['日柱']) > 1 else '子'
        
        # 1. 斗首评分
        kege_result = doushou_analyzer.analyze_kege(mountain, sizhu)
        doushou_score = kege_result.get('综合评分', 0)
        stats['doushou_scores'].append(doushou_score)
        if doushou_score >= 70:
            stats['doushou_pass'] += 1
        
        # 2. 大六壬评分
        try:
            tiandi_pan = arrange_tiandi_pan('亥', shichen)
            sike = sike_calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
            sanchuan = sike_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
            keti = sanchuan.get('课体', '')
            
            ke_info = ke_jing_data.get(keti, {})
            ke_score = ke_info.get('score', 50)
            
            if ke_score >= 80:
                keti_score = 20
            elif ke_score >= 70:
                keti_score = 18
            elif ke_score >= 60:
                keti_score = 15
            elif ke_score >= 50:
                keti_score = 10
            else:
                keti_score = 5
            
            ri_lu = LU.get(ri_gan, '')
            lu_score = 15 if (ri_lu == mountain or ri_lu == xiang) else 0
            
            ri_ma = YIMA.get(ri_zhi, '')
            ma_score = 15 if (ri_ma == mountain or ri_ma == xiang) else 0
            
            guiren_info = guiren_calc.arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shichen)
            tianjiang_map = guiren_info.get('天将映射', {})
            guiren_pos = None
            for zhi, tj in tianjiang_map.items():
                if tj == '贵人':
                    guiren_pos = zhi
                    break
            guiren_score = 20 if (guiren_pos == mountain or guiren_pos == xiang) else 0
            
            chu = sanchuan.get('初传', '')
            zhong = sanchuan.get('中传', '')
            mo = sanchuan.get('末传', '')
            chu_tj = tianjiang_map.get(chu, '')
            zhong_tj = tianjiang_map.get(zhong, '')
            mo_tj = tianjiang_map.get(mo, '')
            jiagui = chu_tj == '贵人' or zhong_tj == '贵人' or mo_tj == '贵人'
            jiagui_score = 15 if jiagui else 0
            
            daliuren_total = keti_score + lu_score + ma_score + guiren_score + jiagui_score
            daliuren_score = round(daliuren_total / 85 * 100)
            
        except Exception as e:
            daliuren_score = 0
        
        stats['daliuren_scores'].append(daliuren_score)
        if daliuren_score >= 70:
            stats['daliuren_pass'] += 1
        
        # 3. 演禽评分
        try:
            day_zhi = sizhu['日柱'][1] if len(sizhu['日柱']) > 1 else '子'
            yanqin_name = yanqin_analyzer.get_ri_qin(day_zhi)
            yanqin_jixiong = yanqin_analyzer.XIU_JIXIONG.get(yanqin_name, '平')
            
            if yanqin_jixiong == '吉':
                yanqin_score = 85
            elif yanqin_jixiong == '凶':
                yanqin_score = 50
            else:
                yanqin_score = 70
        except:
            yanqin_score = 60
        
        stats['yanqin_scores'].append(yanqin_score)
        if yanqin_score >= 70:
            stats['yanqin_pass'] += 1
        
        # 全部达标
        if doushou_score >= 70 and daliuren_score >= 70 and yanqin_score >= 70:
            stats['all_pass'] += 1
            print(f'[达标] {current_date.strftime("%Y-%m-%d")} {shichen}时: 斗首{doushou_score} 六壬{daliuren_score} 演禽{yanqin_score}')
    
    current_date += timedelta(days=1)

# 输出统计
print('\n' + '=' * 70)
print('诊断结果')
print('=' * 70)
print(f'总课数: {stats["total"]}')
print(f'\n各模块达标情况 (≥70分):')
print(f'  斗首达标: {stats["doushou_pass"]} ({stats["doushou_pass"]/stats["total"]*100:.1f}%)')
print(f'  六壬达标: {stats["daliuren_pass"]} ({stats["daliuren_pass"]/stats["total"]*100:.1f}%)')
print(f'  演禽达标: {stats["yanqin_pass"]} ({stats["yanqin_pass"]/stats["total"]*100:.1f}%)')
print(f'\n全部达标: {stats["all_pass"]} ({stats["all_pass"]/stats["total"]*100:.1f}%)')

print(f'\n各模块平均分:')
print(f'  斗首平均分: {sum(stats["doushou_scores"])/len(stats["doushou_scores"]):.1f}')
print(f'  六壬平均分: {sum(stats["daliuren_scores"])/len(stats["daliuren_scores"]):.1f}')
print(f'  演禽平均分: {sum(stats["yanqin_scores"])/len(stats["yanqin_scores"]):.1f}')

print(f'\n各模块分数范围:')
print(f'  斗首: {min(stats["doushou_scores"])} - {max(stats["doushou_scores"])}')
print(f'  六壬: {min(stats["daliuren_scores"])} - {max(stats["daliuren_scores"])}')
print(f'  演禽: {min(stats["yanqin_scores"])} - {max(stats["yanqin_scores"])}')

# 问题诊断
print('\n' + '=' * 70)
print('问题诊断')
print('=' * 70)

if stats['doushou_pass'] / stats['total'] < 0.1:
    print('[问题] 斗首评分过于严格，达标率低于10%')
    print('  建议: 降低斗首评分阈值或检查斗首模块计算逻辑')

if stats['daliuren_pass'] / stats['total'] < 0.1:
    print('[问题] 六壬评分过于严格，达标率低于10%')
    print('  原因: 六壬评分需要禄马贵人到山向，条件苛刻')
    print('  建议: 降低六壬评分阈值或调整评分标准')

if stats['yanqin_pass'] / stats['total'] < 0.1:
    print('[问题] 演禽评分过于严格，达标率低于10%')
    print('  建议: 降低演禽评分阈值或检查演禽模块计算逻辑')

if stats['all_pass'] == 0:
    print('\n[结论] 三种评分同时达标的概率极低')
    print('  建议: 降低评分阈值，或改为"任意两项达标"的筛选条件')
