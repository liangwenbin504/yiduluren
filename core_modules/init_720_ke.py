#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化 720 课例数据库
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

# 使用导入导入模块
import importlib.util
spec = importlib.util.spec_from_file_location("ke_database", "src/engine/720_ke_database.py")
ke_database = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ke_database)
init_720_ke_database = ke_database.init_720_ke_database

if __name__ == '__main__':
    print("开始初始化 720 课例数据库...")
    db = init_720_ke_database()
    print(f"初始化完成！共创建 {len(db.ke_li_data)} 个课例")
