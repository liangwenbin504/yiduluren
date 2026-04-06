# -*- coding: utf-8 -*-
"""
兼容性文件 - 将斗首择日规则导出为 constants 格式
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 从斗首择日规则导入所有常量
from data.斗首择日规则 import *

# 为了向后兼容，保留原有导出格式
__all__ = [
    'TIANGAN',
    'DIZHI', 
    'TWENTY_FOUR_MOUNTAINS',
    'SHANJIA_WUXING',
    'TIANGAN_HUAQI',
    'DOUSHOU_FIVE_STARS',
    'WUXING_SHENG',
    'WUXING_KE',
    'JIGONG',
    'YUEJIANG',
    'JIEQI_YUEJIANG',
    'DIZHI_CHONG',
    'DIZHI_HE',
    'DIZHI_SANHE',
    'LU',
    'YIMA',
    'GUIREN',
    'TIANJIANG',
    'WUXING_CHANGSHENG',
    'CHANGSHENG_NAMES'
]
