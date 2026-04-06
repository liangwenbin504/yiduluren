#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器模块
负责管理计算任务的调度与优先级，检测系统空闲状态，触发增量计算
"""

import threading
import time
import os
from datetime import datetime, timedelta

# 尝试导入 psutil 模块
try:
    import psutil
except ImportError:
    psutil = None
    print("psutil 模块未安装，系统空闲检测将使用默认值")

class TaskScheduler:
    def __init__(self, storage, calculator):
        """初始化任务调度器"""
        self.storage = storage
        self.calculator = calculator
        self.running = False
        self.thread = None
        self.priority_queue = []
        self.lock = threading.Lock()
    
    def start(self):
        """启动任务调度器"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("任务调度器已启动")
    
    def stop(self):
        """停止任务调度器"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("任务调度器已停止")
    
    def _run(self):
        """任务调度器主循环"""
        while self.running:
            try:
                # 检测系统空闲状态
                if self._is_system_idle():
                    # 处理优先级队列中的任务
                    self._process_priority_queue()
                    
                    # 处理未处理的日期
                    self._process_unprocessed_dates()
                
                # 休眠一段时间
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"任务调度器错误: {e}")
                time.sleep(60)
    
    def _is_system_idle(self):
        """检测系统是否空闲"""
        try:
            # 检查 psutil 模块是否可用
            if psutil:
                # 检查CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 50:
                    return False
                
                # 检查内存使用率
                memory = psutil.virtual_memory()
                if memory.percent > 80:
                    return False
                
                # 检查磁盘I/O
                disk_io = psutil.disk_io_counters()
                # 简单判断：如果磁盘读写速度都很低，则认为系统空闲
                if disk_io.read_bytes > 1024 * 1024 * 10 or disk_io.write_bytes > 1024 * 1024 * 10:
                    return False
            
            # 如果 psutil 模块不可用，默认认为系统空闲
            return True
        except Exception as e:
            print(f"检测系统空闲状态失败: {e}")
            # 如果检测失败，默认认为系统空闲
            return True
    
    def _process_priority_queue(self):
        """处理优先级队列中的任务"""
        with self.lock:
            while self.priority_queue:
                task = self.priority_queue.pop(0)
                self._execute_task(task)
    
    def _process_unprocessed_dates(self):
        """处理未处理的日期"""
        try:
            # 获取未处理的日期
            unprocessed_dates = self.storage.get_unprocessed_dates(limit=10)
            if not unprocessed_dates:
                # 如果没有未处理的日期，添加未来日期
                self._add_future_dates()
                return
            
            # 处理每个未处理的日期
            for date_id, date_str, year, month, day in unprocessed_dates:
                print(f"处理日期: {date_str}")
                date = datetime.strptime(date_str, '%Y-%m-%d')
                self.calculator.calculate_date(date)
        except Exception as e:
            print(f"处理未处理日期失败: {e}")
    
    def _add_future_dates(self):
        """添加未来日期到数据库"""
        try:
            # 添加未来30天的日期
            today = datetime.now()
            for i in range(30):
                future_date = today + timedelta(days=i)
                self.storage.add_date(future_date)
            print("已添加未来30天的日期")
        except Exception as e:
            print(f"添加未来日期失败: {e}")
    
    def _execute_task(self, task):
        """执行任务"""
        try:
            task_type = task.get('type')
            if task_type == 'calculate_date':
                date = task.get('date')
                if date:
                    self.calculator.calculate_date(date)
            elif task_type == 'calculate_date_range':
                start_date = task.get('start_date')
                end_date = task.get('end_date')
                if start_date and end_date:
                    self.calculator.calculate_date_range(start_date, end_date)
        except Exception as e:
            print(f"执行任务失败: {e}")
    
    def get_priority_queue(self):
        """获取优先级队列"""
        with self.lock:
            return self.priority_queue.copy()
    
    def add_task(self, task, priority=0):
        """添加任务到优先级队列"""
        with self.lock:
            # 按优先级排序，优先级越高，插入位置越靠前
            task['priority'] = priority
            inserted = False
            for i, existing_task in enumerate(self.priority_queue):
                if priority > existing_task.get('priority', 0):
                    self.priority_queue.insert(i, task)
                    inserted = True
                    break
            if not inserted:
                self.priority_queue.append(task)
            print(f"已添加任务: {task.get('type')}")
    
    def get_queue_size(self):
        """获取队列大小"""
        with self.lock:
            return len(self.priority_queue)
    
    def clear_queue(self):
        """清空队列"""
        with self.lock:
            self.priority_queue.clear()
            print("已清空任务队列")

if __name__ == "__main__":
    # 测试任务调度器
    from date_storage import init_storage
    from date_calculator import DateCalculator
    
    storage = init_storage()
    calculator = DateCalculator(storage)
    scheduler = TaskScheduler(storage, calculator)
    
    # 启动任务调度器
    scheduler.start()
    
    # 添加测试任务
    test_date = datetime(2026, 4, 1)
    scheduler.add_task({
        'type': 'calculate_date',
        'date': test_date
    }, priority=10)
    
    # 测试添加日期范围任务
    start_date = datetime(2026, 4, 1)
    end_date = datetime(2026, 4, 3)
    scheduler.add_task({
        'type': 'calculate_date_range',
        'start_date': start_date,
        'end_date': end_date
    }, priority=5)
    
    print(f"队列大小: {scheduler.get_queue_size()}")
    
    # 等待一段时间
    time.sleep(300)  # 等待5分钟
    
    # 停止任务调度器
    scheduler.stop()
    
    # 关闭存储
    storage.close()
    print("测试完成")