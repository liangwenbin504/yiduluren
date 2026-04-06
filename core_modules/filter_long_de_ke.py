#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
筛选龙德课工具
从 720 课例（8640 个实例）中筛选出符合龙德课的课例

龙德课定义：太岁月将乘贵人发用
- 太岁：年支
- 月将：月将
- 贵人：日干贵人
- 发用：初传

条件：初传 = 太岁 OR 初传 = 月将，并且初传乘贵人
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


class LongDeKeFilter:
    """龙德课筛选器"""
    
    # 十干贵人
    SHI_GAN_GUI_REN = {
        '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'],
        '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'],
        '庚': ['丑', '未'], '辛': ['午', '寅'], '壬': ['巳', '卯'],
        '癸': ['巳', '卯']
    }
    
    # 地支五行
    DIZHI_WU_XING = {
        '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
        '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
    }
    
    # 五行相克
    WU_XING_KE = {
        '金': '木', '木': '土', '土': '水', '水': '火', '火': '金'
    }
    
    def __init__(self):
        self.engine = CompleteQiKeEngine()
        self.ke_ti_judge = KeTiJudgeProfessional()
    
    def get_year_zhi(self, year: int) -> str:
        """获取年支（太岁）"""
        dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        return dizhi[(year - 4) % 12]
    
    def get_gui_ren(self, ri_gan: str) -> list:
        """获取日干贵人"""
        return self.SHI_GAN_GUI_REN.get(ri_gan, [])
    
    def is_long_de_ke(self, ri_gan_zhi: str, yue_jiang: str, shi: str, 
                      tai_sui: str, sanchuan: dict, tian_jiang: dict = None) -> bool:
        """
        判断是否为龙德课
        
        龙德课条件：
        1. 太岁发用：初传 = 太岁
        2. 月将发用：初传 = 月将
        3. 乘贵人：初传是日干贵人
        
        简化判断：初传是太岁或月将，并且初传是日干贵人
        """
        # 三传格式：{'初传': '丑', '中传': '亥', '末传': '酉', ...}
        chu_chuan = sanchuan.get('初传', '') if isinstance(sanchuan, dict) else ''
        
        if not chu_chuan:
            return False
        
        # 条件 1：初传是太岁或月将
        is_tai_sui_yong = (chu_chuan == tai_sui)
        is_yue_jiang_yong = (chu_chuan == yue_jiang)
        
        if not (is_tai_sui_yong or is_yue_jiang_yong):
            return False
        
        # 条件 2：乘贵人（初传是日干贵人）
        ri_gan = ri_gan_zhi[0]
        gui_ren_list = self.get_gui_ren(ri_gan)
        
        is_cheng_gui_ren = (chu_chuan in gui_ren_list)
        
        # 如果有天将信息，检查天将是否为贵人
        if tian_jiang and isinstance(tian_jiang, dict):
            chu_chuan_tian_jiang = tian_jiang.get('初传', '')
            is_tian_jiang_gui_ren = (chu_chuan_tian_jiang == '贵人')
            is_cheng_gui_ren = is_cheng_gui_ren or is_tian_jiang_gui_ren
        
        return is_cheng_gui_ren and (is_tai_sui_yong or is_yue_jiang_yong)
    
    def filter_from_existing(self, ke_li_data: dict) -> list:
        """从现有课例数据中筛选龙德课"""
        long_de_ke_list = []
        
        for ke_key, ke_data in ke_li_data.items():
            # 检查是否已经匹配到龙德课
            if '龙德课' in ke_data.get('matched_ke_jing', []):
                long_de_ke_list.append({
                    'ke_key': ke_key,
                    'ke_data': ke_data
                })
        
        return long_de_ke_list
    
    def scan_date_range(self, start_date: datetime, end_date: datetime, 
                       mountain: str = '壬', direction: str = '丙') -> list:
        """
        扫描指定日期范围内的龙德课
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            mountain: 山（坐山），默认壬山
            direction: 向（朝向），默认丙向
        
        Returns:
            龙德课列表
        """
        long_de_results = []
        
        # 壬山丙向的干支组合
        # 壬山：坐山为壬，对应地支子
        # 丙向：朝向为丙，对应地支午
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        print(f"开始扫描：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"总天数：{total_days}天")
        print(f"坐向：{mountain}山{direction}向")
        print("-" * 80)
        
        day_count = 0
        long_de_count = 0
        
        while current_date <= end_date:
            day_count += 1
            
            # 获取日干支（使用六十甲子循环）
            # 简化：使用基准日期计算
            base_date = datetime(1984, 1, 1)  # 甲子日
            days_offset = (current_date - base_date).days
            gan_zhi_index = days_offset % 60
            ri_gan_zhi = LiuShiJiaZi.get_all_gan_zhi()[gan_zhi_index]
            ri_gan = ri_gan_zhi[0]
            ri_zhi = ri_gan_zhi[1]
            
            # 获取年支（太岁）
            year = current_date.year
            _, tai_sui = LiuShiJiaZi.get_gan_zhi(year)
            
            # 获取月将（简化：按农历月）
            lunar_month = ((current_date.month - 1) % 12) + 1
            yue_jiang = self.engine.get_yue_jiang(lunar_month) if hasattr(self.engine, 'get_yue_jiang') else LiuShiJiaZi.DI_ZHI[(lunar_month + 1) % 12]
            
            # 遍历 12 个时辰
            for shi_idx, shi in enumerate(LiuShiJiaZi.DI_ZHI):
                # 起课
                try:
                    result = self.engine.qi_ke(
                        ri_gan_zhi=ri_gan_zhi,
                        yue_jiang=yue_jiang,
                        shi_chen=shi,
                        lunar_month=lunar_month,
                        nian_zhi=tai_sui
                    )
                    
                    sanchuan = result.get('sanchuan', {})
                    sike = result.get('sike', [])
                    tiandi_pan = result.get('tiandi_pan', {})
                    
                    # 判断是否为龙德课
                    if self.is_long_de_ke(
                        ri_gan_zhi=ri_gan_zhi,
                        yue_jiang=yue_jiang,
                        shi=shi,
                        tai_sui=tai_sui,
                        sanchuan=sanchuan
                    ):
                        long_de_count += 1
                        long_de_results.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'ri_gan_zhi': ri_gan_zhi,
                            'shi': shi,
                            'yue_jiang': yue_jiang,
                            'tai_sui': tai_sui,
                            'sanchuan': sanchuan,
                            'sike': sike,
                            'matched_ke_jing': [],  # 后续可填充
                            'notes': f'太岁{tai_sui}发用，月将{yue_jiang}'
                        })
                        
                        print(f"[龙德课] {current_date.strftime('%Y-%m-%d')} {shi}时")
                        print(f"  日干支：{ri_gan_zhi}, 太岁：{tai_sui}, 月将：{yue_jiang}")
                        print(f"  三传：{sanchuan.get('初传', '')} {sanchuan.get('中传', '')} {sanchuan.get('末传', '')}")
                        print()
                
                except Exception as e:
                    # 忽略起课失败的课例
                    pass
            
            # 每 100 天显示进度
            if day_count % 100 == 0:
                progress = (day_count / total_days) * 100
                print(f"进度：{day_count}/{total_days}天 ({progress:.1f}%), 已发现龙德课：{long_de_count}个")
            
            current_date += timedelta(days=1)
        
        print("-" * 80)
        print(f"扫描完成！共发现 {long_de_count} 个龙德课")
        
        return long_de_results
    
    def save_results(self, results: list, output_file: str):
        """保存筛选结果到 JSON 文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到：{output_file}")


def main():
    """主函数"""
    filter_tool = LongDeKeFilter()
    
    # 方案 1：从现有 720 课例中筛选
    print("=" * 80)
    print("方案 1：从现有 720 课例（8640 个实例）中筛选龙德课")
    print("=" * 80)
    
    ke_li_file = 'data/720_ke_li_matched_pro.json'
    if os.path.exists(ke_li_file):
        with open(ke_li_file, 'r', encoding='utf-8') as f:
            ke_li_data = json.load(f)
        
        long_de_list = filter_tool.filter_from_existing(ke_li_data)
        
        if long_de_list:
            print(f"发现 {len(long_de_list)} 个龙德课：")
            for item in long_de_list[:10]:  # 显示前 10 个
                ke_key = item['ke_key']
                ke_data = item['ke_data']
                print(f"  {ke_key}:")
                print(f"    日干支：{ke_data['ri_gan_zhi']}, 月将：{ke_data['yue']}, 时辰：{ke_data['shi']}")
                print(f"    匹配课体：{', '.join(ke_data.get('matched_ke_jing', [])[:5])}...")
                print()
            
            # 保存结果
            output_file = 'data/龙德课筛选结果_现有课例.json'
            filter_tool.save_results(long_de_list, output_file)
        else:
            print("现有课例中未发现龙德课（因为龙德课判断尚未完全实现）")
    else:
        print(f"未找到课例文件：{ke_li_file}")
    
    print()
    
    # 方案 2：扫描 2026-2036 年的日期范围
    print("=" * 80)
    print("方案 2：扫描 2026-2036 年（10 年）的龙德课")
    print("=" * 80)
    
    start_date = datetime(2026, 3, 15)
    end_date = datetime(2026, 3, 25)  # 先测试 10 天
    
    print("\n测试模式：扫描 10 天样本")
    print("如需扫描完整 10 年，请修改 end_date 参数")
    
    response = 'y'
    
    if response.lower() == 'y':
        results = filter_tool.scan_date_range(start_date, end_date)
        
        if results:
            # 保存结果
            output_file = 'data/龙德课筛选结果_2026_2036.json'
            filter_tool.save_results(results, output_file)
            
            # 显示摘要
            print("\n" + "=" * 80)
            print("龙德课筛选摘要")
            print("=" * 80)
            print(f"总数量：{len(results)}个")
            
            # 按年份统计
            year_count = {}
            for item in results:
                year = item['date'][:4]
                year_count[year] = year_count.get(year, 0) + 1
            
            print("\n按年份分布:")
            for year in sorted(year_count.keys()):
                print(f"  {year}年：{year_count[year]}个")
            
            # 显示前 5 个示例
            print("\n前 5 个龙德课示例:")
            for i, item in enumerate(results[:5], 1):
                print(f"\n{i}. {item['date']} {item['shi']}时")
                print(f"   日干支：{item['ri_gan_zhi']}")
                print(f"   太岁：{item['tai_sui']}, 月将：{item['yue_jiang']}")
                print(f"   三传：{item['sanchuan']['初传']} {item['sanchuan']['中传']} {item['sanchuan']['末传']}")
                print(f"   备注：{item['notes']}")
        else:
            print("未发现龙德课")
    else:
        print("已取消扫描")


if __name__ == '__main__':
    main()
