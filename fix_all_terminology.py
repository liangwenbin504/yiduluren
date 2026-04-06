#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修正斗首术语脚本
将所有旧术语统一修正为标准术语
"""

import os
import glob

# 定义术语映射
TERMINOLOGY_MAP = {
    '武曲': '武财',
    '贪狼': '贪官',
    '破军': '破鬼'
}

def fix_file(filepath):
    """修正单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 批量替换
        for old_term, new_term in TERMINOLOGY_MAP.items():
            content = content.replace(old_term, new_term)
        
        # 只有修改了才写入
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修正: {os.path.basename(filepath)}")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ 修正失败 {os.path.basename(filepath)}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("批量修正斗首术语")
    print("=" * 80)
    
    # 定义要修正的目录
    directories = [
        'core_modules',
        'core_modules/engine',
        'core_modules/data'
    ]
    
    total_fixed = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
        
        # 查找所有 Python 文件
        py_files = glob.glob(os.path.join(directory, '*.py'))
        
        for filepath in py_files:
            if fix_file(filepath):
                total_fixed += 1
    
    print("\n" + "=" * 80)
    print(f"✅ 共修正了 {total_fixed} 个文件")
    print("=" * 80)

if __name__ == '__main__':
    main()
