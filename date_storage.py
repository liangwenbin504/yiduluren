#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期数据存储模块
负责创建数据库、表结构，以及提供数据存储和查询功能
"""

import sqlite3
import os
from datetime import datetime

class DateStorage:
    def __init__(self, db_path='date_data.db'):
        """初始化数据库连接"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """初始化数据库和表结构"""
        # 确保数据库文件所在目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        # 连接数据库
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建表结构
        self._create_tables()
    
    def _create_tables(self):
        """创建表结构"""
        # 日期表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS dates (
            date_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            is_processed BOOLEAN DEFAULT 0,
            processed_at DATETIME
        )
        ''')
        
        # 时辰表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shichen (
            shichen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_id INTEGER NOT NULL,
            shichen TEXT NOT NULL,
            is_processed BOOLEAN DEFAULT 0,
            processed_at DATETIME,
            FOREIGN KEY (date_id) REFERENCES dates (date_id)
        )
        ''')
        
        # 坐山表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS mountains (
            mountain_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mountain TEXT NOT NULL UNIQUE
        )
        ''')
        
        # 课格表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS keges (
            keges_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shichen_id INTEGER NOT NULL,
            mountain_id INTEGER NOT NULL,
            doushou_score REAL,
            daliuren_score REAL,
            yanqin_score REAL,
            total_score REAL,
            daliuren_keti TEXT,
            luma_to_shan BOOLEAN,
            luma_to_xiang BOOLEAN,
            guiren_to_shan BOOLEAN,
            guiren_to_xiang BOOLEAN,
            jia_gui BOOLEAN,
            gong_gui BOOLEAN,
            benming_ji_xiong TEXT,
            liunian_ji_xiong TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shichen_id) REFERENCES shichen (shichen_id),
            FOREIGN KEY (mountain_id) REFERENCES mountains (mountain_id)
        )
        ''')
        
        # 创建索引
        self._create_indexes()
        
        # 提交事务
        self.conn.commit()
    
    def _create_indexes(self):
        """创建索引，优化查询性能"""
        # 日期表索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates_date ON dates (date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates_is_processed ON dates (is_processed)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates_year_month ON dates (year, month)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dates_year ON dates (year)')
        
        # 时辰表索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_shichen_date_id ON shichen (date_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_shichen_is_processed ON shichen (is_processed)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_shichen_date_id_shichen ON shichen (date_id, shichen)')
        
        # 课格表索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_shichen_id ON keges (shichen_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_mountain_id ON keges (mountain_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_total_score ON keges (total_score)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_shichen_mountain ON keges (shichen_id, mountain_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_luma_to_shan ON keges (luma_to_shan)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_luma_to_xiang ON keges (luma_to_xiang)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_guiren_to_shan ON keges (guiren_to_shan)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_guiren_to_xiang ON keges (guiren_to_xiang)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_jia_gui ON keges (jia_gui)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_keges_gong_gui ON keges (gong_gui)')
    
    def add_date(self, date):
        """添加日期记录"""
        try:
            year = date.year
            month = date.month
            day = date.day
            date_str = date.strftime('%Y-%m-%d')
            
            # 检查日期是否已存在
            self.cursor.execute('SELECT date_id FROM dates WHERE date = ?', (date_str,))
            existing = self.cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # 插入新日期
            self.cursor.execute('''
            INSERT INTO dates (date, year, month, day, is_processed) 
            VALUES (?, ?, ?, ?, ?)
            ''', (date_str, year, month, day, False))
            
            date_id = self.cursor.lastrowid
            self.conn.commit()
            return date_id
        except Exception as e:
            print(f"添加日期失败: {e}")
            self.conn.rollback()
            return None
    
    def add_shichen(self, date_id, shichen):
        """添加时辰记录"""
        try:
            # 检查时辰是否已存在
            self.cursor.execute('''
            SELECT shichen_id FROM shichen WHERE date_id = ? AND shichen = ?
            ''', (date_id, shichen))
            existing = self.cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # 插入新时辰
            self.cursor.execute('''
            INSERT INTO shichen (date_id, shichen, is_processed) 
            VALUES (?, ?, ?)
            ''', (date_id, shichen, False))
            
            shichen_id = self.cursor.lastrowid
            self.conn.commit()
            return shichen_id
        except Exception as e:
            print(f"添加时辰失败: {e}")
            self.conn.rollback()
            return None
    
    def add_mountain(self, mountain):
        """添加坐山记录"""
        try:
            # 检查坐山是否已存在
            self.cursor.execute('SELECT mountain_id FROM mountains WHERE mountain = ?', (mountain,))
            existing = self.cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # 插入新坐山
            self.cursor.execute('INSERT INTO mountains (mountain) VALUES (?)', (mountain,))
            
            mountain_id = self.cursor.lastrowid
            self.conn.commit()
            return mountain_id
        except Exception as e:
            print(f"添加坐山失败: {e}")
            self.conn.rollback()
            return None
    
    def add_keges(self, shichen_id, mountain_id, keges_data):
        """添加课格记录"""
        try:
            # 检查课格是否已存在
            self.cursor.execute('''
            SELECT keges_id FROM keges WHERE shichen_id = ? AND mountain_id = ?
            ''', (shichen_id, mountain_id))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新现有记录
                self.cursor.execute('''
                UPDATE keges SET 
                    doushou_score = ?, 
                    daliuren_score = ?, 
                    yanqin_score = ?, 
                    total_score = ?, 
                    daliuren_keti = ?, 
                    luma_to_shan = ?, 
                    luma_to_xiang = ?, 
                    guiren_to_shan = ?, 
                    guiren_to_xiang = ?, 
                    jia_gui = ?, 
                    gong_gui = ?, 
                    benming_ji_xiong = ?, 
                    liunian_ji_xiong = ?, 
                    created_at = CURRENT_TIMESTAMP
                WHERE keges_id = ?
                ''', (
                    keges_data.get('doushou_score'),
                    keges_data.get('daliuren_score'),
                    keges_data.get('yanqin_score'),
                    keges_data.get('total_score'),
                    keges_data.get('daliuren_keti'),
                    keges_data.get('luma_to_shan'),
                    keges_data.get('luma_to_xiang'),
                    keges_data.get('guiren_to_shan'),
                    keges_data.get('guiren_to_xiang'),
                    keges_data.get('jia_gui'),
                    keges_data.get('gong_gui'),
                    keges_data.get('benming_ji_xiong'),
                    keges_data.get('liunian_ji_xiong'),
                    existing[0]
                ))
                keges_id = existing[0]
            else:
                # 插入新记录
                self.cursor.execute('''
                INSERT INTO keges (
                    shichen_id, mountain_id, doushou_score, daliuren_score, yanqin_score, 
                    total_score, daliuren_keti, luma_to_shan, luma_to_xiang, 
                    guiren_to_shan, guiren_to_xiang, jia_gui, gong_gui, 
                    benming_ji_xiong, liunian_ji_xiong
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    shichen_id,
                    mountain_id,
                    keges_data.get('doushou_score'),
                    keges_data.get('daliuren_score'),
                    keges_data.get('yanqin_score'),
                    keges_data.get('total_score'),
                    keges_data.get('daliuren_keti'),
                    keges_data.get('luma_to_shan'),
                    keges_data.get('luma_to_xiang'),
                    keges_data.get('guiren_to_shan'),
                    keges_data.get('guiren_to_xiang'),
                    keges_data.get('jia_gui'),
                    keges_data.get('gong_gui'),
                    keges_data.get('benming_ji_xiong'),
                    keges_data.get('liunian_ji_xiong')
                ))
                keges_id = self.cursor.lastrowid
            
            self.conn.commit()
            return keges_id
        except Exception as e:
            print(f"添加课格失败: {e}")
            self.conn.rollback()
            return None
    
    def mark_date_processed(self, date_id):
        """标记日期为已处理"""
        try:
            self.cursor.execute('''
            UPDATE dates SET is_processed = 1, processed_at = ? WHERE date_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), date_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"标记日期处理失败: {e}")
            self.conn.rollback()
            return False
    
    def mark_shichen_processed(self, shichen_id):
        """标记时辰为已处理"""
        try:
            self.cursor.execute('''
            UPDATE shichen SET is_processed = 1, processed_at = ? WHERE shichen_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), shichen_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"标记时辰处理失败: {e}")
            self.conn.rollback()
            return False
    
    def get_all_dates(self):
        """获取所有日期"""
        try:
            self.cursor.execute('SELECT * FROM dates')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取所有日期失败: {e}")
            return []
    
    def get_all_shichen(self):
        """获取所有时辰"""
        try:
            self.cursor.execute('SELECT * FROM shichen')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取所有时辰失败: {e}")
            return []
    
    def get_all_keges(self, limit=None):
        """获取所有课格"""
        try:
            if limit:
                self.cursor.execute('SELECT * FROM keges LIMIT ?', (limit,))
            else:
                self.cursor.execute('SELECT * FROM keges')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取所有课格失败: {e}")
            return []
    
    def get_keges_by_shichen_id(self, shichen_id):
        """根据时辰ID获取课格"""
        try:
            self.cursor.execute('SELECT * FROM keges WHERE shichen_id = ?', (shichen_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取课格失败: {e}")
            return []
    
    def get_keges_by_date(self, date):
        """根据日期获取课格"""
        try:
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else date
            self.cursor.execute('''
            SELECT k.* FROM keges k
            JOIN shichen s ON k.shichen_id = s.shichen_id
            JOIN dates d ON s.date_id = d.date_id
            WHERE d.date = ?
            ''', (date_str,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取课格失败: {e}")
            return []
    
    def get_date_by_id(self, date_id):
        """根据ID获取日期"""
        try:
            self.cursor.execute('SELECT * FROM dates WHERE date_id = ?', (date_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"获取日期失败: {e}")
            return None
    
    def get_shichen_by_date_id(self, date_id):
        """根据日期ID获取时辰"""
        try:
            self.cursor.execute('SELECT * FROM shichen WHERE date_id = ?', (date_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取时辰失败: {e}")
            return []
    
    def get_unprocessed_shichen(self, date_id):
        """获取未处理的时辰"""
        try:
            self.cursor.execute('''
            SELECT shichen_id, shichen FROM shichen 
            WHERE date_id = ? AND is_processed = 0
            ''', (date_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取未处理的时辰失败: {e}")
            return []
    
    def get_unprocessed_dates(self, limit=None):
        """获取未处理的日期"""
        try:
            if limit:
                self.cursor.execute('SELECT date_id, date FROM dates WHERE is_processed = 0 LIMIT ?', (limit,))
            else:
                self.cursor.execute('SELECT date_id, date FROM dates WHERE is_processed = 0')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取未处理的日期失败: {e}")
            return []
    
    def get_all_mountains(self):
        """获取所有坐山"""
        try:
            self.cursor.execute('SELECT mountain_id, mountain FROM mountains')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取所有坐山失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.conn:
                self.conn.close()
                print("数据库连接已关闭")
                return True
        except Exception as e:
            print(f"关闭数据库连接失败: {e}")
        return False
    
    def get_keges_by_date(self, date, mountain):
        """根据日期和坐山获取课格信息"""
        try:
            self.cursor.execute('''
            SELECT k.* FROM keges k
            JOIN shichen s ON k.shichen_id = s.shichen_id
            JOIN dates d ON s.date_id = d.date_id
            JOIN mountains m ON k.mountain_id = m.mountain_id
            WHERE d.date = ? AND m.mountain = ?
            ORDER BY k.total_score DESC
            ''', (date, mountain))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"获取课格失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

# 初始化存储模块并添加默认坐山
def init_storage():
    """初始化存储模块"""
    storage = DateStorage()
    
    # 添加默认坐山
    mountains = ['壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳', '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥']
    for mountain in mountains:
        storage.add_mountain(mountain)
    
    return storage

if __name__ == "__main__":
    # 测试存储模块
    storage = init_storage()
    print("数据库初始化完成")
    
    # 测试添加日期
    from datetime import datetime
    test_date = datetime(2026, 4, 1)
    date_id = storage.add_date(test_date)
    print(f"添加日期: {test_date}, ID: {date_id}")
    
    # 测试添加时辰
    shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    for shichen in shichen_list:
        shichen_id = storage.add_shichen(date_id, shichen)
        print(f"添加时辰: {shichen}, ID: {shichen_id}")
    
    # 测试添加课格
    mountain_id = storage.add_mountain('壬')
    shichen_id = storage.add_shichen(date_id, '卯')
    keges_data = {
        'doushou_score': 50.0,
        'daliuren_score': 80.0,
        'yanqin_score': 85.0,
        'total_score': 72.0,
        'daliuren_keti': '遥克课',
        'luma_to_shan': True,
        'luma_to_xiang': False,
        'guiren_to_shan': False,
        'guiren_to_xiang': True,
        'jia_gui': False,
        'gong_gui': True,
        'benming_ji_xiong': '吉',
        'liunian_ji_xiong': '吉'
    }
    keges_id = storage.add_keges(shichen_id, mountain_id, keges_data)
    print(f"添加课格: ID: {keges_id}")
    
    # 测试标记处理状态
    storage.mark_date_processed(date_id)
    storage.mark_shichen_processed(shichen_id)
    print("标记处理状态完成")
    
    # 测试查询
    unprocessed_dates = storage.get_unprocessed_dates()
    print(f"未处理日期: {unprocessed_dates}")
    
    # 关闭连接
    storage.close()
    print("测试完成")