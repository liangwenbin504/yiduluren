#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算进度监控模块
负责监控计算进度，可随时查看当前计算状态
"""

import threading
import time
from datetime import datetime

class ProgressMonitor:
    def __init__(self, storage):
        """初始化进度监控器"""
        self.storage = storage
        self.start_time = datetime.now()
        self.processed_dates = 0
        self.processed_shichen = 0
        self.processed_keges = 0
        self.errors = 0
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
    
    def start(self):
        """启动进度监控器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("进度监控器已启动")
    
    def stop(self):
        """停止进度监控器"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("进度监控器已停止")
    
    def _run(self):
        """进度监控器主循环"""
        while self.running:
            try:
                # 打印进度信息
                self.print_progress()
                # 休眠一段时间
                time.sleep(300)  # 每5分钟打印一次进度
            except Exception as e:
                print(f"进度监控器错误: {e}")
                time.sleep(300)
    
    def update_progress(self, processed_dates=0, processed_shichen=0, processed_keges=0, errors=0):
        """更新进度信息"""
        with self.lock:
            self.processed_dates += processed_dates
            self.processed_shichen += processed_shichen
            self.processed_keges += processed_keges
            self.errors += errors
    
    def get_progress(self):
        """获取进度信息"""
        with self.lock:
            # 计算总日期数和未处理日期数
            total_dates = self._get_total_dates()
            unprocessed_dates = self._get_unprocessed_dates()
            processed_dates = total_dates - unprocessed_dates
            
            # 计算总时辰数和未处理时辰数
            total_shichen = self._get_total_shichen()
            unprocessed_shichen = self._get_unprocessed_shichen()
            processed_shichen = total_shichen - unprocessed_shichen
            
            # 计算总课格数
            total_keges = self._get_total_keges()
            
            # 计算计算速度
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            if elapsed_time > 0:
                dates_per_hour = (processed_dates / elapsed_time) * 3600
                shichen_per_hour = (processed_shichen / elapsed_time) * 3600
                keges_per_hour = (total_keges / elapsed_time) * 3600
            else:
                dates_per_hour = 0
                shichen_per_hour = 0
                keges_per_hour = 0
            
            return {
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'elapsed_time': elapsed_time,
                'total_dates': total_dates,
                'processed_dates': processed_dates,
                'unprocessed_dates': unprocessed_dates,
                'total_shichen': total_shichen,
                'processed_shichen': processed_shichen,
                'unprocessed_shichen': unprocessed_shichen,
                'total_keges': total_keges,
                'errors': self.errors,
                'dates_per_hour': dates_per_hour,
                'shichen_per_hour': shichen_per_hour,
                'keges_per_hour': keges_per_hour
            }
    
    def print_progress(self):
        """打印进度信息"""
        progress = self.get_progress()
        print("=" * 80)
        print("计算进度监控")
        print("=" * 80)
        print(f"开始时间: {progress['start_time']}")
        print(f"当前时间: {progress['current_time']}")
        print(f"已运行时间: {progress['elapsed_time']:.2f}秒")
        print()
        print(f"日期处理: {progress['processed_dates']}/{progress['total_dates']} ({progress['processed_dates']/progress['total_dates']*100:.2f}%)")
        print(f"时辰处理: {progress['processed_shichen']}/{progress['total_shichen']} ({progress['processed_shichen']/progress['total_shichen']*100:.2f}%)")
        print(f"课格处理: {progress['total_keges']}个")
        print(f"错误数量: {progress['errors']}")
        print()
        print(f"处理速度: {progress['dates_per_hour']:.2f}日期/小时")
        print(f"处理速度: {progress['shichen_per_hour']:.2f}时辰/小时")
        print(f"处理速度: {progress['keges_per_hour']:.2f}课格/小时")
        print("=" * 80)
    
    def _get_total_dates(self):
        """获取总日期数"""
        try:
            # 这里需要实现从数据库中获取总日期数的逻辑
            # 暂时返回一个示例值
            return 30
        except Exception as e:
            print(f"获取总日期数失败: {e}")
            return 0
    
    def _get_unprocessed_dates(self):
        """获取未处理的日期数"""
        try:
            unprocessed_dates = self.storage.get_unprocessed_dates(limit=1000)
            return len(unprocessed_dates)
        except Exception as e:
            print(f"获取未处理日期数失败: {e}")
            return 0
    
    def _get_total_shichen(self):
        """获取总时辰数"""
        try:
            # 这里需要实现从数据库中获取总时辰数的逻辑
            # 暂时返回一个示例值
            return 30 * 12
        except Exception as e:
            print(f"获取总时辰数失败: {e}")
            return 0
    
    def _get_unprocessed_shichen(self):
        """获取未处理的时辰数"""
        try:
            # 这里需要实现从数据库中获取未处理时辰数的逻辑
            # 暂时返回一个示例值
            return 0
        except Exception as e:
            print(f"获取未处理时辰数失败: {e}")
            return 0
    
    def _get_total_keges(self):
        """获取总课格数"""
        try:
            # 这里需要实现从数据库中获取总课格数的逻辑
            # 暂时返回一个示例值
            return 30 * 12 * 24
        except Exception as e:
            print(f"获取总课格数失败: {e}")
            return 0

if __name__ == "__main__":
    # 测试进度监控器
    from date_storage import init_storage
    
    storage = init_storage()
    monitor = ProgressMonitor(storage)
    
    # 启动进度监控器
    monitor.start()
    
    # 模拟更新进度
    for i in range(5):
        monitor.update_progress(processed_dates=1, processed_shichen=12, processed_keges=12*24)
        time.sleep(1)
    
    # 打印进度
    monitor.print_progress()
    
    # 停止进度监控器
    monitor.stop()
    
    # 关闭存储
    storage.close()
    print("测试完成")