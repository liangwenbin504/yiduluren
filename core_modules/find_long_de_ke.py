#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课筛选工具（实用版）
从 2026-2036 年 10 年中筛选壬山丙向的龙德课
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


class LongDeKeFinder:
    """龙德课查找器"""
    
    def __init__(self):
        self.engine = CompleteQiKeEngine()
        self.ke_ti_judge = KeTiJudgeProfessional()
    
    def get_date_gan_zhi(self, date: datetime) -> str:
        """获取日干支"""
        base_date = datetime(1984, 1, 1)  # 甲子日
        days_offset = (date - base_date).days
        gan_zhi_index = days_offset % 60
        return LiuShiJiaZi.get_all_gan_zhi()[gan_zhi_index]
    
    def get_yue_jiang(self, lunar_month: int) -> str:
        """获取月将（正月亥，二月戌，...）"""
        # 月将：正月亥，二月戌，三月酉，...
        # 对应地支索引：11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0
        yue_jiang_index = (12 - lunar_month) % 12
        return LiuShiJiaZi.DI_ZHI[yue_jiang_index]
    
    def find_long_de_ke(self, start_date: datetime, end_date: datetime, 
                       scan_hours: list = None) -> list:
        """
        查找指定日期范围内的龙德课
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            scan_hours: 要扫描的时辰列表，默认扫描全部 12 时辰
        
        Returns:
            龙德课列表
        """
        long_de_results = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        print(f"扫描范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"总天数：{total_days}天")
        print(f"扫描时辰：{scan_hours if scan_hours else '全部 12 时辰'}")
        print("-" * 80)
        
        day_count = 0
        long_de_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日干支
            ri_gan_zhi = self.get_date_gan_zhi(current_date)
            ri_gan = ri_gan_zhi[0]
            ri_zhi = ri_gan_zhi[1]
            
            # 获取年支（太岁）
            year = current_date.year
            _, tai_sui = LiuShiJiaZi.get_gan_zhi(year)
            
            # 获取月将（简化：按公历月近似农历月）
            lunar_month = ((current_date.month - 1) % 12) + 1
            yue_jiang = self.get_yue_jiang(lunar_month)
            
            # 获取日干贵人
            gui_ren_list = self.ke_ti_judge.SHI_GAN_GUI_REN.get(ri_gan, [])
            
            # 遍历时辰
            hours_to_scan = scan_hours if scan_hours else LiuShiJiaZi.DI_ZHI
            
            for shi in hours_to_scan:
                try:
                    result = self.engine.qi_ke(
                        ri_gan_zhi=ri_gan_zhi,
                        yue_jiang=yue_jiang,
                        shi_chen=shi,
                        lunar_month=lunar_month,
                        nian_zhi=tai_sui
                    )
                    
                    sanchuan = result.get('三传', {})
                    chu_chuan = sanchuan.get('初传', '')
                    
                    if not chu_chuan:
                        continue
                    
                    # 判断龙德课条件
                    is_tai_sui_yong = (chu_chuan == tai_sui)
                    is_yue_jiang_yong = (chu_chuan == yue_jiang)
                    is_gui_ren_yong = (chu_chuan in gui_ren_list)
                    
                    # 龙德课：太岁或月将发用 + 乘贵人
                    if (is_tai_sui_yong or is_yue_jiang_yong) and is_gui_ren_yong:
                        long_de_count += 1
                        
                        # 提取课体
                        ke_ti_list = result.get('课体', [])
                        
                        long_de_results.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'weekday': self._get_weekday(current_date),
                            'ri_gan_zhi': ri_gan_zhi,
                            'shi': shi,
                            'lunar_month': lunar_month,
                            'yue_jiang': yue_jiang,
                            'tai_sui': tai_sui,
                            'year_gan_zhi': f'{year}年 ({LiuShiJiaZi.get_gan_zhi(year)[0]}{tai_sui}年)',
                            'sanchuan': sanchuan,
                            'ke_ti': ke_ti_list,
                            'notes': f'初传{chu_chuan}，太岁发用={is_tai_sui_yong}，月将发用={is_yue_jiang_yong}，贵人={is_gui_ren_yong}'
                        })
                        
                        print(f"\n[龙德课 #{long_de_count}]")
                        print(f"  日期：{current_date.strftime('%Y-%m-%d')} ({self._get_weekday(current_date)}) {shi}时")
                        print(f"  年：{LiuShiJiaZi.get_gan_zhi(year)[0]}{tai_sui}年 (太岁：{tai_sui})")
                        print(f"  日干支：{ri_gan_zhi} (日干贵人：{gui_ren_list})")
                        print(f"  月将：{yue_jiang} (农历{lunar_month}月)")
                        print(f"  三传：{chu_chuan} {sanchuan.get('中传', '')} {sanchuan.get('末传', '')}")
                        print(f"  课体：{', '.join(ke_ti_list[:5])}{'...' if len(ke_ti_list) > 5 else ''}")
                        print(f"  备注：{result.get('三传', {}).get('课体', '')} - {result.get('三传', {}).get('起法', '')}")
                
                except Exception as e:
                    # 忽略起课失败
                    pass
            
            # 进度显示
            if day_count % 100 == 0:
                progress = (day_count / total_days) * 100
                print(f"\n进度：{day_count}/{total_days}天 ({progress:.1f}%), 已发现：{long_de_count}个")
            
            current_date += timedelta(days=1)
        
        print("\n" + "=" * 80)
        print(f"扫描完成！共发现 {long_de_count} 个龙德课")
        
        return long_de_results
    
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
        """生成文本报告"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("大六壬龙德课筛选报告\n")
            f.write("=" * 80 + "\n\n")
            
            if not results:
                f.write("未找到龙德课\n")
                return
            
            f.write(f"筛选范围：{results[0]['date']} 至 {results[-1]['date']}\n")
            f.write(f"总数量：{len(results)}个\n\n")
            
            # 按年份统计
            year_count = {}
            for item in results:
                year = item['date'][:4]
                year_count[year] = year_count.get(year, 0) + 1
            
            f.write("按年份分布:\n")
            for year in sorted(year_count.keys()):
                f.write(f"  {year}年：{year_count[year]}个\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("龙德课详细列表\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(results, 1):
                f.write(f"{i}. {item['date']} ({item['weekday']}) {item['shi']}时\n")
                f.write(f"   年：{item['year_gan_zhi']}\n")
                f.write(f"   日干支：{item['ri_gan_zhi']}\n")
                f.write(f"   月将：{item['yue_jiang']} (农历{item['lunar_month']}月)\n")
                f.write(f"   三传：{item['sanchuan'].get('初传', '')} {item['sanchuan'].get('中传', '')} {item['sanchuan'].get('末传', '')}\n")
                f.write(f"   课体：{', '.join(item['ke_ti'][:5])}{'...' if len(item['ke_ti']) > 5 else ''}\n")
                f.write(f"   备注：{item['notes']}\n")
                f.write("\n")
        
        print(f"报告已生成：{report_file}")


def main():
    """主函数"""
    finder = LongDeKeFinder()
    
    print("=" * 80)
    print("大六壬龙德课筛选工具")
    print("=" * 80)
    print()
    
    # 测试模式：扫描 2026 年 3 月 15 日开始的 30 天
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2026, 4, 14)
    
    print("【测试模式】扫描 30 天样本")
    print()
    
    results = finder.find_long_de_ke(start_date, end_date)
    
    if results:
        # 保存结果
        output_file = 'data/龙德课筛选结果_测试.json'
        finder.save_results(results, output_file)
        
        # 生成报告
        report_file = 'docs/龙德课筛选报告_测试.txt'
        finder.generate_report(results, report_file)
        
        print("\n" + "=" * 80)
        print("筛选结果摘要")
        print("=" * 80)
        print(f"总数量：{len(results)}个")
        print(f"平均：每{30/len(results):.1f}天出现一个龙德课")
        
        # 显示前 3 个示例
        print("\n前 3 个龙德课示例:")
        for i, item in enumerate(results[:3], 1):
            print(f"\n{i}. {item['date']} {item['shi']}时")
            print(f"   日干支：{item['ri_gan_zhi']}, 太岁：{item['tai_sui']}, 月将：{item['yue_jiang']}")
            print(f"   三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
    else:
        print("\n未找到龙德课")
        print("\n提示：龙德课条件非常严格，建议：")
        print("1. 扩大扫描范围（如 10 年）")
        print("2. 放宽判断条件（如只要求太岁或月将发用，不要求乘贵人）")


if __name__ == '__main__':
    main()
