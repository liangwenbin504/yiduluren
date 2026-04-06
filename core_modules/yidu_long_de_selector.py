#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪度择日法：龙德课 + 贵人禄马到山到向筛选工具
从 2026-2036 年 10 年中筛选壬山丙向的龙德课，并要求贵人禄马到山到向
"""

import json
import os
import sys
import importlib.util
from datetime import datetime, timedelta

# 添加引擎路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'engine'))

# 加载 720_ke_database 模块
spec = importlib.util.spec_from_file_location("ke_database", 
    os.path.join(os.path.dirname(__file__), 'src', 'engine', '720_ke_database.py'))
ke_database = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ke_database)
LiuShiJiaZi = ke_database.LiuShiJiaZi

from complete_qi_ke_engine import CompleteQiKeEngine
from ke_ti_judge_pro import KeTiJudgeProfessional


class YiduLongDeKeSelector:
    """仪度择日法：龙德课 + 贵人禄马到山到向筛选器"""
    
    def __init__(self, mountain='壬', direction='丙'):
        self.engine = CompleteQiKeEngine()
        self.ke_ti_judge = KeTiJudgeProfessional()
        self.mountain = mountain  # 坐山
        self.direction = direction  # 朝向
        
        # 壬山丙向的元辰和禄马贵
        self._init_shan_jia_info()
    
    def _init_shan_jia_info(self):
        """初始化山家信息（壬山丙向）"""
        # 壬山属火，元辰戊癸化火
        # 根据斗首择日秘本：
        # 壬山丙向土元辰，甲已千重化戊深
        # 禄在巳宫马在亥，天乙贵人酉亥找
        
        self.shan_jia_info = {
            '壬山': {
                '元辰': '土',
                '禄': '巳',  # 禄在巳
                '马': '亥',  # 马在亥
                '贵人': ['酉', '亥'],  # 天乙贵人酉亥找
                '五行': '火'  # 壬山属火
            },
            '丙向': {
                '禄': '巳',  # 丙禄在巳
                '马': '亥',  # 丙马在亥
                '贵人': ['亥', '酉']  # 丙丁猪鸡位
            }
        }
    
    def get_date_gan_zhi(self, date: datetime) -> str:
        """获取日干支"""
        base_date = datetime(1984, 1, 1)  # 甲子日
        days_offset = (date - base_date).days
        gan_zhi_index = days_offset % 60
        return LiuShiJiaZi.get_all_gan_zhi()[gan_zhi_index]
    
    def get_yue_jiang(self, lunar_month: int) -> str:
        """获取月将（正月亥，二月戌，...）"""
        yue_jiang_index = (12 - lunar_month) % 12
        return LiuShiJiaZi.DI_ZHI[yue_jiang_index]
    
    def get_year_lu_ma_gui(self, year_gan_zhi: tuple) -> dict:
        """获取年柱的禄马贵"""
        year_gan, year_zhi = year_gan_zhi
        
        result = {}
        
        # 年禄（按年干）
        lu_map = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
            '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
        }
        if year_gan in lu_map:
            result['年禄'] = lu_map[year_gan]
        
        # 年马（按年支三合局）
        ma_map = {
            '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥'
        }
        for san_he, ma in ma_map.items():
            if year_zhi in san_he:
                result['年马'] = ma
                break
        
        # 年贵人（按年干）
        gui_map = {
            '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
            '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
            '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
            '癸': ['巳', '卯']
        }
        if year_gan in gui_map:
            result['年贵人'] = gui_map[year_gan]
        
        return result
    
    def get_day_lu_ma_gui(self, ri_gan_zhi: str) -> dict:
        """获取日柱的禄马贵"""
        ri_gan = ri_gan_zhi[0]
        ri_zhi = ri_gan_zhi[1]
        
        result = {}
        
        # 日禄（按日干）
        lu_map = {
            '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳',
            '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
        }
        if ri_gan in lu_map:
            result['日禄'] = lu_map[ri_gan]
        
        # 日马（按日支三合局）
        ma_map = {
            '申子辰': '寅', '亥卯未': '巳', '寅午戌': '申', '巳酉丑': '亥'
        }
        for san_he, ma in ma_map.items():
            if ri_zhi in san_he:
                result['日马'] = ma
                break
        
        # 日贵人（按日干）
        gui_map = {
            '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
            '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
            '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
            '癸': ['巳', '卯']
        }
        if ri_gan in gui_map:
            result['日贵人'] = gui_map[ri_gan]
        
        return result
    
    def check_lu_ma_gui_to_shan(self, year_lu_ma_gui: dict, day_lu_ma_gui: dict, 
                                  shi_zhi: str) -> dict:
        """
        检查禄马贵是否到山到向
        
        壬山丙向：
        - 禄在巳：巳到山/向为禄到
        - 马在亥：亥到山/向为马到
        - 贵人在酉、亥：酉/亥到山/向为贵到
        """
        result = {
            '禄到山': False,
            '禄到向': False,
            '马到山': False,
            '马到向': False,
            '贵到山': False,
            '贵到向': False,
            '总结': []
        }
        
        # 山家禄马贵
        shan_lu = self.shan_jia_info['壬山']['禄']  # 巳
        shan_ma = self.shan_jia_info['壬山']['马']  # 亥
        shan_gui = self.shan_jia_info['壬山']['贵人']  # 酉、亥
        
        # 向方禄马贵（丙向）
        xiang_lu = self.shan_jia_info['丙向']['禄']  # 巳
        xiang_ma = self.shan_jia_info['丙向']['马']  # 亥
        xiang_gui = self.shan_jia_info['丙向']['贵人']  # 亥、酉
        
        # 检查年禄马贵
        if '年禄' in year_lu_ma_gui:
            if year_lu_ma_gui['年禄'] == shan_lu:
                result['禄到山'] = True
                result['总结'].append('年禄到山')
            if year_lu_ma_gui['年禄'] == xiang_lu:
                result['禄到向'] = True
                result['总结'].append('年禄到向')
        
        if '年马' in year_lu_ma_gui:
            if year_lu_ma_gui['年马'] == shan_ma:
                result['马到山'] = True
                result['总结'].append('年马到山')
            if year_lu_ma_gui['年马'] == xiang_ma:
                result['马到向'] = True
                result['总结'].append('年马到向')
        
        if '年贵人' in year_lu_ma_gui:
            for gui in year_lu_ma_gui['年贵人']:
                if gui in shan_gui:
                    result['贵到山'] = True
                    if '年贵到山' not in result['总结']:
                        result['总结'].append('年贵到山')
                if gui in xiang_gui:
                    result['贵到向'] = True
                    if '年贵到向' not in result['总结']:
                        result['总结'].append('年贵到向')
        
        # 检查日禄马贵
        if '日禄' in day_lu_ma_gui:
            if day_lu_ma_gui['日禄'] == shan_lu:
                result['禄到山'] = True
                result['总结'].append('日禄到山')
            if day_lu_ma_gui['日禄'] == xiang_lu:
                result['禄到向'] = True
                result['总结'].append('日禄到向')
        
        if '日马' in day_lu_ma_gui:
            if day_lu_ma_gui['日马'] == shan_ma:
                result['马到山'] = True
                result['总结'].append('日马到山')
            if day_lu_ma_gui['日马'] == xiang_ma:
                result['马到向'] = True
                result['总结'].append('日马到向')
        
        if '日贵人' in day_lu_ma_gui:
            for gui in day_lu_ma_gui['日贵人']:
                if gui in shan_gui:
                    result['贵到山'] = True
                    if '日贵到山' not in result['总结']:
                        result['总结'].append('日贵到山')
                if gui in xiang_gui:
                    result['贵到向'] = True
                    if '日贵到向' not in result['总结']:
                        result['总结'].append('日贵到向')
        
        # 检查时支
        if shi_zhi == shan_lu:
            result['禄到山'] = True
            result['总结'].append('时禄到山')
        if shi_zhi == xiang_lu:
            result['禄到向'] = True
            result['总结'].append('时禄到向')
        
        if shi_zhi == shan_ma:
            result['马到山'] = True
            result['总结'].append('时马到山')
        if shi_zhi == xiang_ma:
            result['马到向'] = True
            result['总结'].append('时马到向')
        
        if shi_zhi in shan_gui:
            result['贵到山'] = True
            result['总结'].append('时贵到山')
        if shi_zhi in xiang_gui:
            result['贵到向'] = True
            result['总结'].append('时贵到向')
        
        return result
    
    def is_long_de_ke(self, ri_gan_zhi: str, yue_jiang: str, tai_sui: str, 
                      sanchuan: dict) -> bool:
        """判断龙德课"""
        chu_chuan = sanchuan.get('初传', '') if isinstance(sanchuan, dict) else ''
        
        if not chu_chuan:
            return False
        
        # 条件 1：太岁或月将发用
        is_tai_sui_yong = (chu_chuan == tai_sui)
        is_yue_jiang_yong = (chu_chuan == yue_jiang)
        
        if not (is_tai_sui_yong or is_yue_jiang_yong):
            return False
        
        # 条件 2：乘贵人
        ri_gan = ri_gan_zhi[0]
        gui_ren_list = self.ke_ti_judge.SHI_GAN_GUI_REN.get(ri_gan, [])
        is_gui_ren_yong = (chu_chuan in gui_ren_list)
        
        return is_gui_ren_yong and (is_tai_sui_yong or is_yue_jiang_yong)
    
    def scan_10_years(self, start_year: int = 2026, end_year: int = 2036) -> list:
        """
        扫描 10 年范围，筛选龙德课 + 贵人禄马到山到向
        
        Returns:
            符合条件的课例列表
        """
        start_date = datetime(start_year, 3, 15)
        end_date = datetime(end_year, 3, 14)
        
        qualified_results = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        print("=" * 80)
        print(f"仪度择日法：龙德课 + 贵人禄马到山到向筛选")
        print("=" * 80)
        print(f"坐山：{self.mountain}山，朝向：{self.direction}向")
        print(f"扫描范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"总天数：{total_days}天")
        print(f"山家禄马贵：禄={self.shan_jia_info['壬山']['禄']}, 马={self.shan_jia_info['壬山']['马']}, 贵人={self.shan_jia_info['壬山']['贵人']}")
        print("-" * 80)
        
        day_count = 0
        qualified_count = 0
        long_de_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日干支
            ri_gan_zhi = self.get_date_gan_zhi(current_date)
            ri_gan = ri_gan_zhi[0]
            ri_zhi = ri_gan_zhi[1]
            
            # 获取年干支
            year = current_date.year
            year_gan_zhi = LiuShiJiaZi.get_gan_zhi(year)
            _, tai_sui = year_gan_zhi
            
            # 获取月将
            lunar_month = ((current_date.month - 1) % 12) + 1
            yue_jiang = self.get_yue_jiang(lunar_month)
            
            # 获取年日禄马贵
            year_lu_ma_gui = self.get_year_lu_ma_gui(year_gan_zhi)
            day_lu_ma_gui = self.get_day_lu_ma_gui(ri_gan_zhi)
            
            # 遍历时辰
            for shi in LiuShiJiaZi.DI_ZHI:
                try:
                    result = self.engine.qi_ke(
                        ri_gan_zhi=ri_gan_zhi,
                        yue_jiang=yue_jiang,
                        shi_chen=shi,
                        lunar_month=lunar_month,
                        nian_zhi=tai_sui
                    )
                    
                    sanchuan = result.get('三传', {})
                    
                    # 判断龙德课
                    if not self.is_long_de_ke(ri_gan_zhi, yue_jiang, tai_sui, sanchuan):
                        continue
                    
                    long_de_count += 1
                    
                    # 检查禄马贵到山到向
                    lu_ma_gui_result = self.check_lu_ma_gui_to_shan(
                        year_lu_ma_gui, day_lu_ma_gui, shi
                    )
                    
                    # 筛选：至少禄或马或贵到山/向
                    has_arrival = (
                        lu_ma_gui_result['禄到山'] or lu_ma_gui_result['禄到向'] or
                        lu_ma_gui_result['马到山'] or lu_ma_gui_result['马到向'] or
                        lu_ma_gui_result['贵到山'] or lu_ma_gui_result['贵到向']
                    )
                    
                    if has_arrival:
                        qualified_count += 1
                        
                        ke_ti_list = result.get('课体', [])
                        
                        qualified_results.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'weekday': self._get_weekday(current_date),
                            'ri_gan_zhi': ri_gan_zhi,
                            'shi': shi,
                            'lunar_month': lunar_month,
                            'yue_jiang': yue_jiang,
                            'tai_sui': tai_sui,
                            'year_gan_zhi': f'{year_gan_zhi[0]}{year_gan_zhi[1]}',
                            'year': year,
                            'sanchuan': sanchuan,
                            'ke_ti': ke_ti_list,
                            'year_lu_ma_gui': year_lu_ma_gui,
                            'day_lu_ma_gui': day_lu_ma_gui,
                            'lu_ma_gui_arrival': lu_ma_gui_result,
                            'notes': f'龙德课，{" + ".join(lu_ma_gui_result["总结"])}'
                        })
                        
                        print(f"\n[符合 #{qualified_count}]")
                        print(f"  日期：{current_date.strftime('%Y-%m-%d')} ({self._get_weekday(current_date)}) {shi}时")
                        print(f"  年：{year_gan_zhi[0]}{year_gan_zhi[1]}年 (太岁：{tai_sui})")
                        print(f"  日干支：{ri_gan_zhi}")
                        print(f"  三传：{sanchuan.get('初传', '')} {sanchuan.get('中传', '')} {sanchuan.get('末传', '')}")
                        print(f"  课体：{', '.join(ke_ti_list[:5])}{'...' if len(ke_ti_list) > 5 else ''}")
                        print(f"  禄马贵：{', '.join(lu_ma_gui_result['总结'])}")
                
                except Exception as e:
                    pass
            
            # 进度显示
            if day_count % 100 == 0:
                progress = (day_count / total_days) * 100
                print(f"\n进度：{day_count}/{total_days}天 ({progress:.1f}%), 龙德课={long_de_count}, 符合={qualified_count}")
            
            current_date += timedelta(days=1)
        
        print("\n" + "=" * 80)
        print(f"扫描完成！")
        print(f"龙德课总数：{long_de_count}个")
        print(f"符合（龙德课 + 贵人禄马到山到向）：{qualified_count}个")
        print(f"平均每年：{qualified_count / (end_year - start_year):.1f}个")
        
        return qualified_results
    
    def _get_weekday(self, date: datetime) -> str:
        """获取星期"""
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        return f'星期{weekdays[date.weekday()]}'
    
    def save_results(self, results: list, output_file: str):
        """保存结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到：{output_file}")
    
    def generate_report(self, results: list, report_file: str):
        """生成报告"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("仪度择日法：龙德课 + 贵人禄马到山到向筛选报告\n")
            f.write("=" * 80 + "\n\n")
            
            if not results:
                f.write("未找到符合条件的课例\n")
                return
            
            f.write(f"坐山：{self.mountain}山\n")
            f.write(f"朝向：{self.direction}向\n")
            f.write(f"筛选范围：{results[0]['date']} 至 {results[-1]['date']}\n")
            f.write(f"总数量：{len(results)}个\n\n")
            
            # 按年份统计
            year_count = {}
            for item in results:
                year = item['year']
                year_count[year] = year_count.get(year, 0) + 1
            
            f.write("年度分布:\n")
            for year in sorted(year_count.keys()):
                f.write(f"  {year}年：{year_count[year]}个\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("详细列表\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(results, 1):
                f.write(f"{i}. {item['date']} ({item['weekday']}) {item['shi']}时\n")
                f.write(f"   年：{item['year_gan_zhi']}年\n")
                f.write(f"   日干支：{item['ri_gan_zhi']}\n")
                f.write(f"   三传：{item['sanchuan'].get('初传', '')} {item['sanchuan'].get('中传', '')} {item['sanchuan'].get('末传', '')}\n")
                f.write(f"   课体：{', '.join(item['ke_ti'][:5])}\n")
                f.write(f"   禄马贵：{item['notes']}\n")
                f.write("\n")
        
        print(f"报告已生成：{report_file}")


def main():
    """主函数"""
    selector = YiduLongDeKeSelector(mountain='壬', direction='丙')
    
    print("\n" + "=" * 80)
    print("仪度择日法：龙德课 + 贵人禄马到山到向筛选")
    print("=" * 80)
    print("\n筛选条件：")
    print("1. 龙德课（太岁或月将发用 + 乘贵人）")
    print("2. 贵人禄马到山到向（壬山丙向）")
    print("   - 禄在巳，马在亥，贵人在酉、亥")
    print("\n扫描 10 年（2026-2036），预计耗时 5-10 分钟...")
    print("\n开始扫描...\n")
    
    results = selector.scan_10_years(2026, 2036)
    
    if results:
        # 保存结果
        selector.save_results(results, 'data/仪度龙德课_贵人禄马到山到向_2026_2036.json')
        selector.generate_report(results, 'docs/仪度龙德课_贵人禄马到山到向_报告.txt')
        
        print("\n" + "=" * 80)
        print("生成文件:")
        print("1. data/仪度龙德课_贵人禄马到山到向_2026_2036.json")
        print("2. docs/仪度龙德课_贵人禄马到山到向_报告.txt")
        print("\n任务完成！")
    else:
        print("\n未找到符合条件的课例")
        print("建议：")
        print("1. 放宽条件（只要求龙德课，或只要求禄马贵到山）")
        print("2. 扩大扫描范围")


if __name__ == '__main__':
    main()
