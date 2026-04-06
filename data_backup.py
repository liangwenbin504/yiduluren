#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据备份模块
负责定期备份数据库，确保数据的安全性
"""

import os
import shutil
import time
import threading
from datetime import datetime

class DataBackup:
    def __init__(self, db_path='date_data.db', backup_dir='backups'):
        """初始化数据备份模块"""
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.running = False
        self.thread = None
        self.backup_interval = 3600  # 备份间隔（秒）
        self.max_backups = 10  # 最大备份数量
        self._init_backup_dir()
    
    def _init_backup_dir(self):
        """初始化备份目录"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"备份目录已创建: {self.backup_dir}")
    
    def start(self):
        """启动备份服务"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("数据备份服务已启动")
    
    def stop(self):
        """停止备份服务"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("数据备份服务已停止")
    
    def _run(self):
        """备份服务主循环"""
        while self.running:
            try:
                # 执行备份
                self.backup()
                # 清理旧备份
                self._cleanup_old_backups()
                # 休眠一段时间
                time.sleep(self.backup_interval)
            except Exception as e:
                print(f"备份服务错误: {e}")
                time.sleep(self.backup_interval)
    
    def backup(self):
        """执行备份"""
        try:
            if not os.path.exists(self.db_path):
                print(f"数据库文件不存在: {self.db_path}")
                return
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'date_data_{timestamp}.db')
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_file)
            print(f"数据库已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"备份失败: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            # 获取所有备份文件
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('date_data_') and file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出最大数量的旧备份
            if len(backup_files) > self.max_backups:
                for file_path, _ in backup_files[self.max_backups:]:
                    os.remove(file_path)
                    print(f"已删除旧备份: {file_path}")
        except Exception as e:
            print(f"清理旧备份失败: {e}")
    
    def restore(self, backup_file):
        """从备份恢复数据"""
        try:
            if not os.path.exists(backup_file):
                print(f"备份文件不存在: {backup_file}")
                return False
            
            # 备份当前数据库
            current_backup = self.backup()
            if current_backup:
                print(f"已备份当前数据库到: {current_backup}")
            
            # 恢复备份
            shutil.copy2(backup_file, self.db_path)
            print(f"已从备份恢复数据: {backup_file}")
            return True
        except Exception as e:
            print(f"恢复失败: {e}")
            return False
    
    def get_backups(self):
        """获取所有备份文件"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('date_data_') and file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file, os.path.getmtime(file_path)))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            return backup_files
        except Exception as e:
            print(f"获取备份文件失败: {e}")
            return []

if __name__ == "__main__":
    # 测试数据备份模块
    backup = DataBackup()
    
    # 启动备份服务
    backup.start()
    
    # 执行手动备份
    backup_file = backup.backup()
    print(f"手动备份: {backup_file}")
    
    # 获取所有备份
    backups = backup.get_backups()
    print(f"所有备份: {backups}")
    
    # 等待一段时间
    time.sleep(10)
    
    # 停止备份服务
    backup.stop()
    
    print("测试完成")