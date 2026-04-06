#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据校验模块
负责验证计算结果的准确性与一致性
"""

import threading
from datetime import datetime

class DataValidator:
    def __init__(self, storage):
        """初始化数据校验器"""
        self.storage = storage
        self.running = False
        self.thread = None
        self.validation_interval = 3600  # 校验间隔（秒）
        self.lock = threading.Lock()
    
    def start(self):
        """启动数据校验服务"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("数据校验服务已启动")
    
    def stop(self):
        """停止数据校验服务"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("数据校验服务已停止")
    
    def _run(self):
        """数据校验服务主循环"""
        while self.running:
            try:
                # 执行数据校验
                self.validate_data()
                # 休眠一段时间
                import time
                time.sleep(self.validation_interval)
            except Exception as e:
                print(f"数据校验服务错误: {e}")
                import time
                time.sleep(self.validation_interval)
    
    def validate_data(self):
        """执行数据校验"""
        print("开始执行数据校验...")
        
        # 校验日期数据
        self._validate_dates()
        
        # 校验时辰数据
        self._validate_shichen()
        
        # 校验课格数据
        self._validate_keges()
        
        # 校验数据一致性
        self._validate_consistency()
        
        print("数据校验完成")
    
    def _validate_dates(self):
        """校验日期数据"""
        try:
            # 获取所有日期
            dates = self.storage.get_all_dates()
            if not dates:
                print("没有日期数据需要校验")
                return
            
            # 校验日期格式
            for date_info in dates:
                date_id, date_str, year, month, day, is_processed, processed_at = date_info
                
                # 校验日期格式
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    if date.year != year or date.month != month or date.day != day:
                        print(f"日期数据不一致: {date_str}, 存储的年月日: {year}-{month}-{day}")
                except Exception as e:
                    print(f"日期格式错误: {date_str}, 错误: {e}")
            
            print(f"日期数据校验完成，共校验 {len(dates)} 条日期数据")
        except Exception as e:
            print(f"校验日期数据失败: {e}")
    
    def _validate_shichen(self):
        """校验时辰数据"""
        try:
            # 获取所有时辰
            shichen_list = self.storage.get_all_shichen()
            if not shichen_list:
                print("没有时辰数据需要校验")
                return
            
            # 校验时辰格式
            valid_shichen = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            for shichen_info in shichen_list:
                shichen_id, date_id, shichen_name, is_processed, processed_at = shichen_info
                
                # 校验时辰格式
                if shichen_name not in valid_shichen:
                    print(f"时辰格式错误: {shichen_name}")
            
            print(f"时辰数据校验完成，共校验 {len(shichen_list)} 条时辰数据")
        except Exception as e:
            print(f"校验时辰数据失败: {e}")
    
    def _validate_keges(self):
        """校验课格数据"""
        try:
            # 获取所有课格
            keges_list = self.storage.get_all_keges(limit=1000)
            if not keges_list:
                print("没有课格数据需要校验")
                return
            
            # 校验课格数据
            for keges_info in keges_list:
                keges_id, shichen_id, mountain_id, doushou_score, daliuren_score, yanqin_score, total_score, \
                daliuren_keti, luma_to_shan, luma_to_xiang, guiren_to_shan, guiren_to_xiang, jia_gui, gong_gui, \
                benming_ji_xiong, liunian_ji_xiong, created_at = keges_info
                
                # 校验分数范围
                if not (0 <= doushou_score <= 100):
                    print(f"斗首分数范围错误: {doushou_score}")
                if not (0 <= daliuren_score <= 100):
                    print(f"大六壬分数范围错误: {daliuren_score}")
                if not (0 <= yanqin_score <= 100):
                    print(f"演禽分数范围错误: {yanqin_score}")
                if not (0 <= total_score <= 100):
                    print(f"总分范围错误: {total_score}")
                
                # 校验布尔值
                if not isinstance(luma_to_shan, bool):
                    print(f"禄马到山值类型错误: {luma_to_shan}")
                if not isinstance(luma_to_xiang, bool):
                    print(f"禄马到向值类型错误: {luma_to_xiang}")
                if not isinstance(guiren_to_shan, bool):
                    print(f"贵人到山值类型错误: {guiren_to_shan}")
                if not isinstance(guiren_to_xiang, bool):
                    print(f"贵人到向值类型错误: {guiren_to_xiang}")
                if not isinstance(jia_gui, bool):
                    print(f"夹贵值类型错误: {jia_gui}")
                if not isinstance(gong_gui, bool):
                    print(f"拱贵值类型错误: {gong_gui}")
            
            print(f"课格数据校验完成，共校验 {len(keges_list)} 条课格数据")
        except Exception as e:
            print(f"校验课格数据失败: {e}")
    
    def _validate_consistency(self):
        """校验数据一致性"""
        try:
            # 校验日期与时辰的一致性
            dates = self.storage.get_all_dates()
            for date_info in dates:
                date_id, date_str, year, month, day, is_processed, processed_at = date_info
                
                # 获取该日期的时辰
                shichen_list = self.storage.get_shichen_by_date_id(date_id)
                if len(shichen_list) != 12:
                    print(f"日期 {date_str} 的时辰数量错误: {len(shichen_list)}，应该是 12")
            
            # 校验时辰与课格的一致性
            shichen_list = self.storage.get_all_shichen()
            for shichen_info in shichen_list:
                shichen_id, date_id, shichen_name, is_processed, processed_at = shichen_info
                
                # 获取该时辰的课格
                keges_list = self.storage.get_keges_by_shichen_id(shichen_id)
                mountains = self.storage.get_all_mountains()
                if len(keges_list) != len(mountains):
                    print(f"时辰 {shichen_name} 的课格数量错误: {len(keges_list)}，应该是 {len(mountains)}")
            
            print("数据一致性校验完成")
        except Exception as e:
            print(f"校验数据一致性失败: {e}")
    
    def validate_single_date(self, date):
        """校验单个日期的数据"""
        try:
            # 获取日期信息
            date_info = self.storage.get_date_by_date(date)
            if not date_info:
                print(f"日期 {date} 不存在")
                return False
            
            date_id = date_info[0]
            
            # 校验时辰数据
            shichen_list = self.storage.get_shichen_by_date_id(date_id)
            if len(shichen_list) != 12:
                print(f"日期 {date} 的时辰数量错误: {len(shichen_list)}，应该是 12")
                return False
            
            # 校验课格数据
            for shichen_info in shichen_list:
                shichen_id, _, shichen_name, _, _ = shichen_info
                keges_list = self.storage.get_keges_by_shichen_id(shichen_id)
                mountains = self.storage.get_all_mountains()
                if len(keges_list) != len(mountains):
                    print(f"日期 {date} 时辰 {shichen_name} 的课格数量错误: {len(keges_list)}，应该是 {len(mountains)}")
                    return False
            
            print(f"日期 {date} 数据校验通过")
            return True
        except Exception as e:
            print(f"校验单个日期数据失败: {e}")
            return False

if __name__ == "__main__":
    # 测试数据校验模块
    from date_storage import init_storage
    
    storage = init_storage()
    validator = DataValidator(storage)
    
    # 启动数据校验服务
    validator.start()
    
    # 执行手动校验
    validator.validate_data()
    
    # 校验单个日期
    validator.validate_single_date('2026-04-01')
    
    # 等待一段时间
    import time
    time.sleep(10)
    
    # 停止数据校验服务
    validator.stop()
    
    # 关闭存储
    storage.close()
    print("测试完成")