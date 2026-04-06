#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课筛选工具（10 年版）
从 2026-2036 年 10 年中筛选壬山丙向的龙德课
并生成 DOC 格式文档
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


class LongDeKeScanner:
    """龙德课扫描器（10 年版）"""
    
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
        yue_jiang_index = (12 - lunar_month) % 12
        return LiuShiJiaZi.DI_ZHI[yue_jiang_index]
    
    def scan_10_years(self, start_year: int = 2026, end_year: int = 2036,
                     specific_hours: list = None) -> list:
        """
        扫描 10 年范围内的龙德课
        
        Args:
            start_year: 开始年份
            end_year: 结束年份
            specific_hours: 指定时辰列表，None 表示扫描全部 12 时辰
        
        Returns:
            龙德课列表
        """
        start_date = datetime(start_year, 3, 15)
        end_date = datetime(end_year, 3, 14)
        
        long_de_results = []
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        print("=" * 80)
        print(f"大六壬龙德课 10 年扫描 ({start_year}-{end_year}年)")
        print("=" * 80)
        print(f"扫描范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"总天数：{total_days}天")
        print(f"扫描时辰：{specific_hours if specific_hours else '全部 12 时辰'}")
        print("龙德课条件：太岁或月将发用 + 乘贵人")
        print("-" * 80)
        
        day_count = 0
        long_de_count = 0
        last_print_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日干支
            ri_gan_zhi = self.get_date_gan_zhi(current_date)
            ri_gan = ri_gan_zhi[0]
            
            # 获取年支（太岁）
            year = current_date.year
            year_gan, tai_sui = LiuShiJiaZi.get_gan_zhi(year)
            
            # 获取月将
            lunar_month = ((current_date.month - 1) % 12) + 1
            yue_jiang = self.get_yue_jiang(lunar_month)
            
            # 获取日干贵人
            gui_ren_list = self.ke_ti_judge.SHI_GAN_GUI_REN.get(ri_gan, [])
            
            # 遍历时辰
            hours_to_scan = specific_hours if specific_hours else LiuShiJiaZi.DI_ZHI
            
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
                    
                    if (is_tai_sui_yong or is_yue_jiang_yong) and is_gui_ren_yong:
                        long_de_count += 1
                        
                        ke_ti_list = result.get('课体', [])
                        
                        long_de_results.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'weekday': self._get_weekday(current_date),
                            'ri_gan_zhi': ri_gan_zhi,
                            'shi': shi,
                            'lunar_month': lunar_month,
                            'yue_jiang': yue_jiang,
                            'tai_sui': tai_sui,
                            'year_gan_zhi': f'{year_gan}{tai_sui}',
                            'year': year,
                            'sanchuan': sanchuan,
                            'ke_ti': ke_ti_list,
                            'notes': f'初传{chu_chuan}，太岁={is_tai_sui_yong}，月将={is_yue_jiang_yong}，贵人={is_gui_ren_yong}'
                        })
                
                except Exception as e:
                    pass
            
            # 进度显示（每发现 1 个或每 100 天）
            if long_de_count > last_print_count:
                last_print_count = long_de_count
                print(f"发现 #{long_de_count}: {current_date.strftime('%Y-%m-%d')} {shi}时 - {ri_gan_zhi}")
            
            if day_count % 100 == 0:
                progress = (day_count / total_days) * 100
                print(f"进度：{day_count}/{total_days}天 ({progress:.1f}%), 已发现：{long_de_count}个")
            
            current_date += timedelta(days=1)
        
        print("=" * 80)
        print(f"扫描完成！共发现 {long_de_count} 个龙德课")
        print(f"平均每年：{long_de_count / (end_year - start_year):.1f}个")
        print(f"平均每：{total_days / long_de_count:.1f}天出现一个")
        
        return long_de_results
    
    def _get_weekday(self, date: datetime) -> str:
        """获取星期"""
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        return f'星期{weekdays[date.weekday()]}'
    
    def save_json(self, results: list, filename: str):
        """保存 JSON"""
        os.makedirs('data', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"JSON 已保存：{filename}")
    
    def generate_doc_report(self, results: list, filename: str):
        """生成 DOC 格式报告（使用 python-docx）"""
        try:
            from docx import Document
            from docx.shared import Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            print("未安装 python-docx，跳过 DOC 生成")
            return
        
        doc = Document()
        
        # 标题
        title = doc.add_heading('大六壬龙德课筛选报告', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 基本信息
        doc.add_heading('基本信息', level=1)
        p = doc.add_paragraph()
        p.add_run('筛选范围：' + results[0]['date'] + ' 至 ' + results[-1]['date'] + '\n')
        p.add_run('总数量：' + str(len(results)) + '个龙德课\n')
        p.add_run('扫描年份：' + str(results[0]['year']) + '年 至 ' + str(results[-1]['year']) + '年\n')
        
        # 统计
        doc.add_heading('年度分布统计', level=1)
        year_count = {}
        for item in results:
            year = item['year']
            year_count[year] = year_count.get(year, 0) + 1
        
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = '年份'
        hdr_cells[1].text = '龙德课数量'
        
        for year in sorted(year_count.keys()):
            row_cells = table.add_row().cells
            row_cells[0].text = f'{year}年 ({LiuShiJiaZi.get_gan_zhi(year)[0]}{LiuShiJiaZi.get_gan_zhi(year)[1]}年)'
            row_cells[1].text = f'{year_count[year]}个'
        
        # 详细列表
        doc.add_heading('龙德课详细列表', level=1)
        
        for i, item in enumerate(results, 1):
            p = doc.add_paragraph()
            p.add_run(f'{i}. {item["date"]} ({item["weekday"]}) {item["shi"]}时\n').bold = True
            p.add_run(f'   年：{item["year_gan_zhi"]}年 (太岁：{item["tai_sui"]})\n')
            p.add_run(f'   日干支：{item["ri_gan_zhi"]}\n')
            p.add_run(f'   月将：{item["yue_jiang"]} (农历{item["lunar_month"]}月)\n')
            p.add_run(f'   三传：{item["sanchuan"].get("初传", "")} {item["sanchuan"].get("中传", "")} {item["sanchuan"].get("末传", "")}\n')
            p.add_run(f'   课体：{", ".join(item["ke_ti"][:5])}{"..." if len(item["ke_ti"]) > 5 else ""}\n')
            p.add_run(f'   备注：{item["notes"]}\n')
            
            if i % 10 == 0:
                doc.add_page_break()
        
        # 保存
        os.makedirs('docs', exist_ok=True)
        doc.save(filename)
        print(f"DOC 报告已生成：{filename}")
    
    def generate_txt_report(self, results: list, filename: str):
        """生成 TXT 格式报告"""
        os.makedirs('docs', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("大六壬龙德课筛选报告\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"筛选范围：{results[0]['date']} 至 {results[-1]['date']}\n")
            f.write(f"总数量：{len(results)}个龙德课\n")
            f.write(f"扫描年份：{results[0]['year']}年 至 {results[-1]['year']}年\n\n")
            
            # 年度统计
            f.write("=" * 80 + "\n")
            f.write("年度分布统计\n")
            f.write("=" * 80 + "\n")
            
            year_count = {}
            for item in results:
                year = item['year']
                year_count[year] = year_count.get(year, 0) + 1
            
            for year in sorted(year_count.keys()):
                year_gan_zhi = LiuShiJiaZi.get_gan_zhi(year)
                f.write(f"{year}年 ({year_gan_zhi[0]}{year_gan_zhi[1]}年): {year_count[year]}个\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("龙德课详细列表\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(results, 1):
                f.write(f"{i}. {item['date']} ({item['weekday']}) {item['shi']}时\n")
                f.write(f"   年：{item['year_gan_zhi']}年 (太岁：{item['tai_sui']})\n")
                f.write(f"   日干支：{item['ri_gan_zhi']}\n")
                f.write(f"   月将：{item['yue_jiang']} (农历{item['lunar_month']}月)\n")
                f.write(f"   三传：{item['sanchuan'].get('初传', '')} {item['sanchuan'].get('中传', '')} {item['sanchuan'].get('末传', '')}\n")
                f.write(f"   课体：{', '.join(item['ke_ti'][:5])}{'...' if len(item['ke_ti']) > 5 else ''}\n")
                f.write(f"   备注：{item['notes']}\n")
                f.write("\n")
        
        print(f"TXT 报告已生成：{filename}")


def main():
    """主函数"""
    scanner = LongDeKeScanner()
    
    print("\n" + "=" * 80)
    print("龙德课 10 年扫描工具 (2026-2036)")
    print("=" * 80)
    print("\n说明：")
    print("- 扫描 2026 年 3 月 15 日至 2036 年 3 月 14 日（10 年）")
    print("- 龙德课条件：太岁或月将发用 + 乘贵人")
    print("- 预计耗时：约 5-10 分钟（43800 次起课）")
    print("\n开始扫描...\n")
    
    # 扫描 10 年
    results = scanner.scan_10_years(2026, 2036)
    
    if results:
        # 保存结果
        scanner.save_json(results, 'data/龙德课筛选结果_2026_2036.json')
        scanner.generate_txt_report(results, 'docs/龙德课筛选报告_2026_2036.txt')
        scanner.generate_doc_report(results, 'docs/龙德课筛选报告_2026_2036.docx')
        
        print("\n" + "=" * 80)
        print("生成文件清单:")
        print("=" * 80)
        print("1. data/龙德课筛选结果_2026_2036.json - JSON 数据")
        print("2. docs/龙德课筛选报告_2026_2036.txt - TXT 报告")
        print("3. docs/龙德课筛选报告_2026_2036.docx - Word 文档")
        print("\n所有文件已保存到项目目录")
    else:
        print("\n未找到龙德课")


if __name__ == '__main__':
    main()
