#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大六壬 720 课例数据库与年月匹配系统

功能：
1. 存储 720 个基础课例
2. 根据年月日时匹配课例
3. 关联 64 课经
"""

import json
import os
from datetime import datetime
from itertools import product


class LiuShiJiaZi:
    """六十甲子工具类"""
    
    # 天干
    TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支
    DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 阴阳
    YIN_YANG = {
        '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳',
        '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴',
        '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴', '辰': '阳',
        '巳': '阴', '午': '阳', '未': '阴', '申': '阳', '酉': '阴',
        '戌': '阳', '亥': '阴'
    }
    
    @classmethod
    def get_gan_zhi(cls, year):
        """
        获取年份的干支
        
        :param year: 公元年份
        :return: (天干，地支)
        """
        # 基准：1984 年为甲子年
        base_year = 1984
        offset = year - base_year
        
        gan_index = offset % 10
        zhi_index = offset % 12
        
        return cls.TIAN_GAN[gan_index], cls.DI_ZHI[zhi_index]
    
    @classmethod
    def get_all_gan_zhi(cls):
        """获取所有六十甲子"""
        gan_zhi_list = []
        for i in range(60):
            gan = cls.TIAN_GAN[i % 10]
            zhi = cls.DI_ZHI[i % 12]
            gan_zhi_list.append(f"{gan}{zhi}")
        return gan_zhi_list


class SevenTwentyKeDatabase:
    """720 课例数据库"""
    
    def __init__(self):
        self.data_file = "data/720_ke_li.json"
        self.ke_li_data = {}
        self.load_data()
    
    def load_data(self):
        """加载课例数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.ke_li_data = json.load(f)
                print(f"已加载 {len(self.ke_li_data)} 个课例")
        else:
            print("课例数据库不存在，需要创建")
    
    def save_data(self):
        """保存课例数据"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.ke_li_data, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(self.ke_li_data)} 个课例")
    
    def generate_720_ke(self):
        """
        生成 720 个基础课例
        
        720 课 = 60 甲子 × 12 月 × 12 时
        实际应用中，根据月将和占时起课
        """
        print("正在生成 720 课例...")
        
        gan_zhi_list = LiuShiJiaZi.get_all_gan_zhi()
        months = LiuShiJiaZi.DI_ZHI  # 12 个月
        hours = LiuShiJiaZi.DI_ZHI   # 12 个时辰
        
        count = 0
        for ri_gan_zhi in gan_zhi_list:
            for yue in months:
                for shi in hours:
                    ke_key = f"{ri_gan_zhi}_{yue}_{shi}"
                    
                    self.ke_li_data[ke_key] = {
                        'ri_gan_zhi': ri_gan_zhi,
                        'yue': yue,
                        'shi': shi,
                        'yue_jiang': self._get_yue_jiang(yue),
                        'gan_zhi_info': {
                            'year_gan_zhi': '',
                            'month_gan_zhi': '',
                            'day_gan_zhi': ri_gan_zhi,
                            'hour_gan_zhi': shi
                        },
                        'matched_ke_jing': [],
                        'notes': ''
                    }
                    count += 1
        
        print(f"已生成 {count} 个课例")
        self.save_data()
        return count
    
    def _get_yue_jiang(self, month):
        """
        根据月份确定月将
        
        月将规则：
        正月亥（登明），二月戌（河魁），三月酉（从魁）
        四月申（传送），五月未（小吉），六月午（胜光）
        七月巳（太乙），八月辰（天罡），九月卯（太冲）
        十月寅（功曹），十一月丑（大吉），十二月子（神后）
        """
        yue_jiang_map = {
            '寅': '亥', '卯': '戌', '辰': '酉',
            '巳': '申', '午': '未', '未': '午',
            '申': '巳', '酉': '辰', '戌': '卯',
            '亥': '寅', '子': '丑', '丑': '子'
        }
        return yue_jiang_map.get(month, month)
    
    def match_ke_by_datetime(self, ri_gan_zhi, yue, shi):
        """
        根据年月日时匹配课例
        
        :param ri_gan_zhi: 日干支
        :param yue: 月支
        :param shi: 时支
        :return: 匹配的课例数据
        """
        ke_key = f"{ri_gan_zhi}_{yue}_{shi}"
        return self.ke_li_data.get(ke_key, None)
    
    def match_ke_by_gan_zhi(self, year, month, day, hour):
        """
        根据公历时间匹配课例
        
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :return: 匹配的课例数据
        """
        # 获取干支
        year_gan_zhi = "".join(LiuShiJiaZi.get_gan_zhi(year))
        
        # 这里需要完整的四柱计算，暂时简化
        # 实际应用中应调用专业的四柱计算库
        ri_gan_zhi = self._calculate_day_gan_zhi(year, month, day)
        shi_gan_zhi = self._calculate_hour_gan_zhi(ri_gan_zhi[0], hour)
        
        # 月支
        yue_zhi = self._get_month_zhi(month)
        
        return self.match_ke_by_datetime(ri_gan_zhi, yue_zhi, shi_gan_zhi[1])
    
    def _calculate_day_gan_zhi(self, year, month, day):
        """计算日干支（简化版）"""
        # 实际应用中应使用专业的干支计算库
        # 这里返回一个示例值
        return "甲子"
    
    def _calculate_hour_gan_zhi(self, ri_gan, hour):
        """计算时干支"""
        # 简化处理
        hour_zhi = self._get_hour_zhi(hour)
        return f"{ri_gan}{hour_zhi}"
    
    def _get_month_zhi(self, month):
        """获取月支"""
        # 简化：正月=寅，二月=卯...
        zhi_list = LiuShiJiaZi.DI_ZHI
        return zhi_list[(month - 1) % 12]
    
    def _get_hour_zhi(self, hour):
        """获取时支"""
        # 子时：23-1 点，丑时：1-3 点...
        hour_zhi_map = {
            (23, 1): '子', (1, 3): '丑', (3, 5): '寅',
            (5, 7): '卯', (7, 9): '辰', (9, 11): '巳',
            (11, 13): '午', (13, 15): '未', (15, 17): '申',
            (17, 19): '酉', (19, 21): '戌', (21, 23): '亥'
        }
        
        for (start, end), zhi in hour_zhi_map.items():
            if start <= hour < end or (start > end and (hour >= start or hour < end)):
                return zhi
        
        return '子'
    
    def associate_ke_jing(self, ke_key, ke_jing_list):
        """
        关联课经到课例
        
        :param ke_key: 课例键
        :param ke_jing_list: 课经列表
        """
        if ke_key in self.ke_li_data:
            self.ke_li_data[ke_key]['matched_ke_jing'] = ke_jing_list
            self.save_data()
            return True
        return False


class KeJingMatcher:
    """课经匹配器"""
    
    def __init__(self):
        from engine.ke_jing_engine import LiuShiSiKeEngine
        self.ke_jing_engine = LiuShiSiKeEngine()
        self.db = SevenTwentyKeDatabase()
    
    def match_and_associate(self, qi_ke_result, year, month, day, hour):
        """
        匹配课经并关联到课例
        
        :param qi_ke_result: 起课结果
        :param year: 年
        :param month: 月
        :param day: 日
        :param hour: 时
        :return: 匹配结果
        """
        # 1. 匹配课经
        matched_ke_jing = self.ke_jing_engine.match_ke_jing(qi_ke_result)
        
        # 2. 匹配课例
        ke_li = self.db.match_ke_by_gan_zhi(year, month, day, hour)
        
        if ke_li:
            # 3. 关联课经到课例
            ke_jing_names = [item['ke_name'] for item in matched_ke_jing]
            ke_key = f"{qi_ke_result.get('日干支', '')}_{ke_li['yue']}_{ke_li['shi']}"
            self.db.associate_ke_jing(ke_key, ke_jing_names)
        
        # 4. 返回完整结果
        result = {
            'qi_ke': qi_ke_result,
            'matched_ke_jing': matched_ke_jing,
            'ke_li': ke_li,
            'time_info': {
                'year': year,
                'month': month,
                'day': day,
                'hour': hour
            }
        }
        
        return result


def init_720_ke_database():
    """初始化 720 课例数据库"""
    db = SevenTwentyKeDatabase()
    count = db.generate_720_ke()
    print(f"720 课例数据库初始化完成！")
    return db


if __name__ == '__main__':
    # 初始化数据库
    db = init_720_ke_database()
    
    # 测试匹配
    matcher = KeJingMatcher()
    
    test_qi_ke = {
        '课体': '涉害课',
        '起法': '涉害法',
        '日干支': '甲子',
        '初传': '酉',
        '格局': '见机格'
    }
    
    result = matcher.match_and_associate(test_qi_ke, 2024, 3, 15, 10)
    
    print(f"\n匹配结果：")
    print(f"  课例：{result['ke_li']}")
    print(f"  匹配课经：{len(result['matched_ke_jing'])} 条")
    for item in result['matched_ke_jing'][:3]:
        print(f"    - {item['ke_name']} (分数：{item['score']})")
