#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复 - 直接修复指定文档
"""

import os
import sys

# 尝试导入win32com
try:
    import win32com.client as win32
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False
    print("⚠️  win32com不可用")
    sys.exit(1)


def quick_fix(doc_path):
    """快速修复单个文档"""
    print("=" * 80)
    print("快速修复工具")
    print("=" * 80)
    print(f"修复文档: {doc_path}")
    
    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        
        try:
            doc = word.Documents.Open(os.path.abspath(doc_path))
            
            print(f"\n找到 {doc.InlineShapes.Count} 个嵌入型图片")
            print(f"找到 {doc.Shapes.Count} 个浮动图片")
            
            # 转换所有嵌入型图片
            for i in range(doc.InlineShapes.Count, 0, -1):
                try:
                    inline_shape = doc.InlineShapes(i)
                    if inline_shape.Type == 3:
                        print(f"\n转换嵌入型图片 {i} ...")
                        shape = inline_shape.ConvertToShape()
                        shape.WrapFormat.Type = 3  # wdWrapFront
                        shape.ZOrder(0)
                        print(f"  ✅ 已设置为浮于文字上方")
                except Exception as e:
                    print(f"  ⚠️  出错: {e}")
            
            # 确保所有浮动图片都是浮于文字上方
            for i in range(1, doc.Shapes.Count + 1):
                try:
                    shape = doc.Shapes(i)
                    shape.WrapFormat.Type = 3
                    shape.ZOrder(0)
                    print(f"\n浮动图片 {i} 已确认为 Type=3, ZOrder=0")
                except Exception as e:
                    print(f"  ⚠️  出错: {e}")
            
            # 保存
            doc.Save()
            doc.Close()
            print("\n" + "=" * 80)
            print("✅ 修复完成！")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            word.Quit()
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 直接修复你说的那个文档
    target_file = r"择日课单_20260403_072337.docx"
    
    if os.path.exists(target_file):
        quick_fix(target_file)
    else:
        print(f"❌ 文件不存在: {target_file}")
        print("\n当前目录下的择日课单文档:")
        for f in os.listdir("."):
            if f.startswith("择日课单_") and f.endswith(".docx"):
                print(f"  - {f}")
