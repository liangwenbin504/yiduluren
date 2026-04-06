#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
龙德课快速查看工具
用于浏览和筛选 990 个龙德课结果
"""

import json
import os

def load_results():
    """加载筛选结果"""
    filepath = 'data/龙德课筛选结果_2026_2036.json'
    if not os.path.exists(filepath):
        print(f"未找到文件：{filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def show_statistics(results):
    """显示统计信息"""
    print("\n" + "=" * 80)
    print("龙德课筛选统计")
    print("=" * 80)
    print(f"总数量：{len(results)}个")
    print(f"时间范围：{results[0]['date']} 至 {results[-1]['date']}")
    
    # 按年份统计
    year_count = {}
    for item in results:
        year = item['year']
        year_count[year] = year_count.get(year, 0) + 1
    
    print("\n年度分布:")
    for year in sorted(year_count.keys()):
        print(f"  {year}年：{year_count[year]}个")
    
    # 按时辰统计
    shi_count = {}
    for item in results:
        shi = item['shi']
        shi_count[shi] = shi_count.get(shi, 0) + 1
    
    print("\n时辰分布:")
    for shi in ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']:
        count = shi_count.get(shi, 0)
        if count > 0:
            print(f"  {shi}时：{count}个")

def show_details(results, start_idx=0, count=10):
    """显示详细信息"""
    end_idx = min(start_idx + count, len(results))
    
    print(f"\n{'=' * 80}")
    print(f"龙德课列表 (第{start_idx+1}-{end_idx}个，共{len(results)}个)")
    print("=" * 80)
    
    for i in range(start_idx, end_idx):
        item = results[i]
        print(f"\n{i+1}. {item['date']} ({item['weekday']}) {item['shi']}时")
        print(f"   年：{item['year_gan_zhi']}年 (太岁：{item['tai_sui']})")
        print(f"   日干支：{item['ri_gan_zhi']}")
        print(f"   月将：{item['yue_jiang']} (农历{item['lunar_month']}月)")
        print(f"   三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
        print(f"   课体：{', '.join(item['ke_ti'][:5])}{'...' if len(item['ke_ti']) > 5 else ''}")
        
        # 龙德课类型
        notes = item['notes']
        if '太岁=True' in notes:
            print(f"   类型：★ 太岁发用 (力量最强)")
        elif '月将=True' in notes:
            print(f"   类型：☆ 月将发用 (太阳之光)")

def search_by_date(results, target_date):
    """按日期搜索"""
    matches = [r for r in results if r['date'] == target_date]
    
    if matches:
        print(f"\n找到 {len(matches)} 个龙德课 ({target_date}):")
        for item in matches:
            print(f"  {item['shi']}时 - {item['ri_gan_zhi']}")
            print(f"    三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
    else:
        print(f"\n{target_date} 没有龙德课")

def search_by_year(results, year):
    """按年份搜索"""
    matches = [r for r in results if r['year'] == year]
    
    if matches:
        print(f"\n{year}年共有 {len(matches)} 个龙德课")
        print(f"前 10 个:")
        for i, item in enumerate(matches[:10], 1):
            print(f"  {i}. {item['date']} {item['shi']}时 - {item['ri_gan_zhi']}")
    else:
        print(f"\n未找到 {year}年的龙德课")

def filter_by_type(results, ke_type='taishui'):
    """按类型筛选"""
    if ke_type == 'taishui':
        # 太岁发用
        matches = [r for r in results if '太岁=True' in r['notes']]
        print(f"\n太岁发用的龙德课：{len(matches)}个")
    elif ke_type == 'yuejiang':
        # 月将发用
        matches = [r for r in results if '月将=True' in r['notes']]
        print(f"\n月将发用的龙德课：{len(matches)}个")
    
    # 显示前 10 个
    for i, item in enumerate(matches[:10], 1):
        print(f"  {i}. {item['date']} {item['shi']}时 - {item['ri_gan_zhi']}")

def show_best_choices(results, year=2026):
    """显示最佳选择"""
    print(f"\n{'=' * 80}")
    print(f"{year}年最佳龙德课推荐")
    print("=" * 80)
    
    # 筛选该年份的课
    year_results = [r for r in results if r['year'] == year]
    
    # 优先太岁发用
    taishui = [r for r in year_results if '太岁=True' in r['notes']]
    
    # 次选月将发用 + 吉课多
    yuejiang = [r for r in year_results if '月将=True' in r['notes']]
    
    print("\n【★★★★★ 太岁发用 - 力量最强】")
    for i, item in enumerate(taishui[:5], 1):
        print(f"{i}. {item['date']} {item['shi']}时")
        print(f"   日干支：{item['ri_gan_zhi']}, 三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
        print(f"   课体：{', '.join(item['ke_ti'][:3])}")
    
    print("\n【★★★★☆ 月将发用 + 吉课】")
    # 筛选有吉课的
    good_ones = [r for r in yuejiang if any(k in r['ke_ti'] for k in ['三光课', '全局课', '富贵课', '三阳课'])]
    for i, item in enumerate(good_ones[:5], 1):
        print(f"{i}. {item['date']} {item['shi']}时")
        print(f"   日干支：{item['ri_gan_zhi']}, 三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
        print(f"   课体：{', '.join(item['ke_ti'][:3])}")

def interactive_menu(results):
    """交互式菜单"""
    while True:
        print("\n" + "=" * 80)
        print("龙德课查看工具菜单")
        print("=" * 80)
        print("1. 显示统计信息")
        print("2. 浏览龙德课列表")
        print("3. 按日期搜索")
        print("4. 按年份搜索")
        print("5. 按类型筛选（太岁/月将）")
        print("6. 显示年度最佳选择")
        print("7. 导出为文本")
        print("0. 退出")
        print("=" * 80)
        
        choice = input("请选择功能 (0-7): ").strip()
        
        if choice == '1':
            show_statistics(results)
        
        elif choice == '2':
            try:
                start = int(input("起始序号 (1-" + str(len(results)) + "): ").strip()) - 1
                count = int(input("显示数量 (默认 10): ").strip() or 10)
                if start < 0 or start >= len(results):
                    print("起始序号超出范围")
                else:
                    show_details(results, start, count)
            except ValueError:
                print("输入无效")
        
        elif choice == '3':
            date = input("输入日期 (YYYY-MM-DD): ").strip()
            search_by_date(results, date)
        
        elif choice == '4':
            try:
                year = int(input("输入年份 (2026-2036): ").strip())
                search_by_year(results, year)
            except ValueError:
                print("输入无效")
        
        elif choice == '5':
            print("\n筛选类型:")
            print("1. 太岁发用")
            print("2. 月将发用")
            type_choice = input("请选择 (1-2): ").strip()
            if type_choice == '1':
                filter_by_type(results, 'taishui')
            elif type_choice == '2':
                filter_by_type(results, 'yuejiang')
        
        elif choice == '6':
            try:
                year = int(input("输入年份 (2026-2036): ").strip())
                show_best_choices(results, year)
            except ValueError:
                print("输入无效")
        
        elif choice == '7':
            filename = input("输入文件名 (默认 exported_long_de.txt): ").strip() or 'exported_long_de.txt'
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("大六壬龙德课导出列表\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"总数量：{len(results)}个\n")
                f.write(f"时间范围：{results[0]['date']} 至 {results[-1]['date']}\n\n")
                
                for i, item in enumerate(results, 1):
                    f.write(f"{i}. {item['date']} ({item['weekday']}) {item['shi']}时\n")
                    f.write(f"   年：{item['year_gan_zhi']}年\n")
                    f.write(f"   日干支：{item['ri_gan_zhi']}\n")
                    f.write(f"   三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}\n")
                    f.write(f"   课体：{', '.join(item['ke_ti'][:5])}\n")
                    f.write("\n")
            
            print(f"已导出到：{filename}")
        
        elif choice == '0':
            print("\n再见！")
            break
        
        else:
            print("无效选择，请重新输入")

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("大六壬龙德课快速查看工具")
    print("=" * 80)
    
    results = load_results()
    
    if not results:
        print("未加载到数据，请确保已运行筛选工具")
        return
    
    print(f"成功加载 {len(results)} 个龙德课")
    
    # 显示快速统计
    show_statistics(results)
    
    # 显示前 5 个示例
    print("\n" + "=" * 80)
    print("前 5 个龙德课示例:")
    show_details(results, 0, 5)
    
    # 显示 2026 年最佳选择
    show_best_choices(results, 2026)
    
    # 进入交互菜单
    print("\n")
    interactive_menu(results)

if __name__ == '__main__':
    main()
