#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期数据计算模块
负责计算每年、每月、每日、每时的择日课格数据
"""

import os
import sys
import concurrent.futures
from datetime import datetime, timedelta

# 添加核心模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'core_modules', 'engine'))

class DateCalculator:
    def __init__(self, storage):
        """初始化日期计算器"""
        self.storage = storage
        self.doushou_analyzer = None
        self.sike_calculator = None
        self.yanqin_analyzer = None
        self._init_analyzers()
    
    def _init_analyzers(self):
        """初始化分析器"""
        try:
            from douhou_analyzer import DouhouKegeAnalyzer
            from sike_sanchuan_engine import SiKeSanChuanCalculator
            from yanqin_analyzer import YanQinAnalyzer
            
            self.doushou_analyzer = DouhouKegeAnalyzer()
            self.sike_calculator = SiKeSanChuanCalculator()
            self.yanqin_analyzer = YanQinAnalyzer()
        except Exception as e:
            print(f"初始化分析器失败: {e}")
    
    def calculate_date(self, date):
        """计算单个日期的课格数据"""
        try:
            # 添加日期到数据库
            date_id = self.storage.add_date(date)
            if not date_id:
                print(f"添加日期失败: {date}")
                return False
            
            # 添加时辰
            shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            for shichen in shichen_list:
                try:
                    shichen_id = self.storage.add_shichen(date_id, shichen)
                    if not shichen_id:
                        print(f"添加时辰失败: {date} {shichen}")
                        continue
                except Exception as e:
                    print(f"添加时辰异常: {date} {shichen}, 错误: {e}")
                    continue
            
            # 计算每个时辰的课格数据
            try:
                self._calculate_shichen(date_id)
            except Exception as e:
                print(f"计算时辰课格失败: {date}, 错误: {e}")
                # 即使计算失败，也要标记日期为已处理，避免重复计算
                try:
                    self.storage.mark_date_processed(date_id)
                except Exception as mark_error:
                    print(f"标记日期为已处理失败: {date}, 错误: {mark_error}")
                return False
            
            # 标记日期为已处理
            try:
                self.storage.mark_date_processed(date_id)
            except Exception as e:
                print(f"标记日期为已处理失败: {date}, 错误: {e}")
                return False
            
            return True
        except Exception as e:
            print(f"计算日期失败: {date}, 错误: {e}")
            return False
    
    def _calculate_shichen(self, date_id):
        """计算单个日期的所有时辰的课格数据"""
        try:
            # 获取所有坐山
            mountains = self.storage.get_all_mountains()
            if not mountains:
                print(f"获取坐山列表失败: {date_id}")
                return
            
            # 获取未处理的时辰
            unprocessed_shichen = self.storage.get_unprocessed_shichen(date_id)
            if not unprocessed_shichen:
                print(f"获取未处理时辰列表失败: {date_id}")
                return
            
            # 并行计算每个时辰的课格数据
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    futures = []
                    for shichen_id, shichen in unprocessed_shichen:
                        for mountain_id, mountain in mountains:
                            futures.append(executor.submit(
                                self._calculate_keges, 
                                shichen_id, 
                                mountain_id, 
                                mountain,
                                date_id,
                                shichen
                            ))
                    
                    # 等待所有计算完成
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            print(f"计算课格失败: {e}")
            except Exception as e:
                print(f"并行计算失败: {date_id}, 错误: {e}")
                # 回退到串行计算
                try:
                    for shichen_id, shichen in unprocessed_shichen:
                        for mountain_id, mountain in mountains:
                            try:
                                self._calculate_keges(shichen_id, mountain_id, mountain, date_id, shichen)
                            except Exception as e:
                                print(f"串行计算课格失败: {date_id} {shichen} {mountain}, 错误: {e}")
                                continue
                except Exception as e:
                    print(f"串行计算失败: {date_id}, 错误: {e}")
                    return
            
            # 标记时辰为已处理
            for shichen_id, shichen in unprocessed_shichen:
                try:
                    self.storage.mark_shichen_processed(shichen_id)
                except Exception as e:
                    print(f"标记时辰为已处理失败: {date_id} {shichen}, 错误: {e}")
                    continue
        except Exception as e:
            print(f"计算时辰失败: {date_id}, 错误: {e}")
    
    def _calculate_keges(self, shichen_id, mountain_id, mountain, date_id, shichen):
        """计算单个时辰的课格数据"""
        try:
            # 获取日期信息
            from datetime import datetime
            date_str = self._get_date_str(date_id)
            if not date_str:
                print(f"获取日期字符串失败: {date_id}")
                return
            
            date = datetime.strptime(date_str, '%Y-%m-%d')
            year = date.year
            month = date.month
            day = date.day
            
            # 计算四柱
            try:
                sizhu = self._get_sizhu(year, month, day, shichen)
                if not sizhu:
                    print(f"计算四柱失败: {date_str} {shichen}")
                    return
            except Exception as e:
                print(f"计算四柱异常: {date_str} {shichen}, 错误: {e}")
                return
            
            # 计算斗首评分
            try:
                doushou_score = self._calculate_doushou_score(mountain, sizhu)
            except Exception as e:
                print(f"计算斗首评分失败: {date_str} {shichen} {mountain}, 错误: {e}")
                doushou_score = 50.0
            
            # 计算大六壬评分
            try:
                daliuren_score, daliuren_keti = self._calculate_daliuren_score(mountain, sizhu, shichen)
            except Exception as e:
                print(f"计算大六壬评分失败: {date_str} {shichen} {mountain}, 错误: {e}")
                daliuren_score = 50.0
                daliuren_keti = ""
            
            # 计算演禽评分
            try:
                yanqin_score = self._calculate_yanqin_score(sizhu)
            except Exception as e:
                print(f"计算演禽评分失败: {date_str} {shichen} {mountain}, 错误: {e}")
                yanqin_score = 50.0
            
            # 计算综合评分
            total_score = doushou_score * 0.3 + daliuren_score * 0.5 + yanqin_score * 0.2
            
            # 计算禄马贵人到山到向
            try:
                luma_to_shan, luma_to_xiang, guiren_to_shan, guiren_to_xiang = self._calculate_luma_guiren(mountain, sizhu, shichen)
            except Exception as e:
                print(f"计算禄马贵人失败: {date_str} {shichen} {mountain}, 错误: {e}")
                luma_to_shan = False
                luma_to_xiang = False
                guiren_to_shan = False
                guiren_to_xiang = False
            
            # 计算夹贵、拱贵
            try:
                jia_gui, gong_gui = self._calculate_jia_gong_gui(mountain, sizhu, shichen)
            except Exception as e:
                print(f"计算夹贵拱贵失败: {date_str} {shichen} {mountain}, 错误: {e}")
                jia_gui = False
                gong_gui = False
            
            # 分析本命与到山、到向的吉凶关系
            try:
                benming_ji_xiong = self._analyze_benming(mountain, sizhu)
            except Exception as e:
                print(f"分析本命吉凶失败: {date_str} {shichen} {mountain}, 错误: {e}")
                benming_ji_xiong = ""
            
            # 判断对应流年大运的吉凶影响
            try:
                liunian_ji_xiong = self._analyze_liunian(mountain, sizhu, year)
            except Exception as e:
                print(f"分析流年吉凶失败: {date_str} {shichen} {mountain}, 错误: {e}")
                liunian_ji_xiong = ""
            
            # 构建课格数据
            keges_data = {
                'doushou_score': doushou_score,
                'daliuren_score': daliuren_score,
                'yanqin_score': yanqin_score,
                'total_score': total_score,
                'daliuren_keti': daliuren_keti,
                'luma_to_shan': luma_to_shan,
                'luma_to_xiang': luma_to_xiang,
                'guiren_to_shan': guiren_to_shan,
                'guiren_to_xiang': guiren_to_xiang,
                'jia_gui': jia_gui,
                'gong_gui': gong_gui,
                'benming_ji_xiong': benming_ji_xiong,
                'liunian_ji_xiong': liunian_ji_xiong
            }
            
            # 存储课格数据
            try:
                self.storage.add_keges(shichen_id, mountain_id, keges_data)
            except Exception as e:
                print(f"存储课格数据失败: {date_str} {shichen} {mountain}, 错误: {e}")
        except Exception as e:
            print(f"计算课格失败: {date_id} {shichen} {mountain}, 错误: {e}")
    
    def _get_date_str(self, date_id):
        """获取日期字符串"""
        try:
            # 这里需要实现从数据库中获取日期字符串的逻辑
            # 暂时返回一个示例日期
            return '2026-04-01'
        except Exception as e:
            print(f"获取日期失败: {e}")
            return None
    
    def _get_sizhu(self, year, month, day, shichen):
        """计算四柱"""
        try:
            # 这里需要实现四柱计算逻辑
            # 暂时返回一个示例四柱
            return {
                '年柱': '丙午',
                '月柱': '壬辰',
                '日柱': '壬子',
                '时柱': '癸卯'
            }
        except Exception as e:
            print(f"计算四柱失败: {e}")
            return None
    
    def _calculate_doushou_score(self, mountain, sizhu):
        """计算斗首评分"""
        try:
            if not self.doushou_analyzer:
                return 50.0
            
            kege_result = self.doushou_analyzer.analyze_kege(mountain, sizhu)
            return kege_result.get('综合评分', 50.0)
        except Exception as e:
            print(f"计算斗首评分失败: {e}")
            return 50.0
    
    def _calculate_daliuren_score(self, mountain, sizhu, shichen):
        """计算大六壬评分"""
        try:
            if not self.sike_calculator:
                return 50.0, '未知课体'
            
            # 这里需要实现大六壬评分计算逻辑
            # 暂时返回示例数据
            return 80.0, '遥克课'
        except Exception as e:
            print(f"计算大六壬评分失败: {e}")
            return 50.0, '未知课体'
    
    def _calculate_yanqin_score(self, sizhu):
        """计算演禽评分"""
        try:
            if not self.yanqin_analyzer:
                return 70.0
            
            # 这里需要实现演禽评分计算逻辑
            # 暂时返回示例数据
            return 85.0
        except Exception as e:
            print(f"计算演禽评分失败: {e}")
            return 70.0
    
    def _calculate_luma_guiren(self, mountain, sizhu, shichen):
        """计算禄马贵人到山到向"""
        try:
            # 这里需要实现禄马贵人到山到向计算逻辑
            # 暂时返回示例数据
            return True, False, False, True
        except Exception as e:
            print(f"计算禄马贵人失败: {e}")
            return False, False, False, False
    
    def _calculate_jia_gong_gui(self, mountain, sizhu, shichen):
        """计算夹贵、拱贵"""
        try:
            # 这里需要实现夹贵、拱贵计算逻辑
            # 暂时返回示例数据
            return False, True
        except Exception as e:
            print(f"计算夹贵、拱贵失败: {e}")
            return False, False
    
    def _analyze_benming(self, mountain, sizhu):
        """分析本命与到山、到向的吉凶关系"""
        try:
            # 这里需要实现本命分析逻辑
            # 暂时返回示例数据
            return '吉'
        except Exception as e:
            print(f"分析本命失败: {e}")
            return '平'
    
    def _analyze_liunian(self, mountain, sizhu, year):
        """判断对应流年大运的吉凶影响"""
        try:
            # 这里需要实现流年分析逻辑
            # 暂时返回示例数据
            return '吉'
        except Exception as e:
            print(f"分析流年失败: {e}")
            return '平'
    
    def calculate_date_range(self, start_date, end_date):
        """计算日期范围内的所有日期的课格数据"""
        try:
            current_date = start_date
            while current_date <= end_date:
                print(f"计算日期: {current_date}")
                self.calculate_date(current_date)
                current_date += timedelta(days=1)
            return True
        except Exception as e:
            print(f"计算日期范围失败: {e}")
            return False

if __name__ == "__main__":
    # 测试日期计算模块
    from date_storage import init_storage
    storage = init_storage()
    calculator = DateCalculator(storage)
    
    # 测试计算单个日期
    test_date = datetime(2026, 4, 1)
    print(f"计算日期: {test_date}")
    calculator.calculate_date(test_date)
    
    # 测试计算日期范围
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 4, 3)
    print(f"计算日期范围: {start_date} 至 {end_date}")
    calculator.calculate_date_range(start_date, end_date)
    
    # 关闭存储
    storage.close()
    print("测试完成")