#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键修复工具 - 强制把所有文档中的印章图片设置为浮于文字上方！
"""

import os
import sys
import datetime
import traceback

# 尝试导入win32com
try:
    import win32com.client as win32
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False
    print("⚠️  win32com不可用，无法修复文档")


def fix_document_seal(doc_path):
    """修复单个文档的印章图片，强制设置为浮于文字上方"""
    if not WIN32COM_AVAILABLE:
        print("❌ win32com不可用")
        return False
    
    try:
        print(f"📝 正在修复文档: {os.path.basename(doc_path)}")
        
        # 启动Word
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        
        try:
            # 打开文档
            doc = word.Documents.Open(os.path.abspath(doc_path))
            
            print(f"  - 找到 {doc.InlineShapes.Count} 个嵌入型图片")
            print(f"  - 找到 {doc.Shapes.Count} 个浮动图片")
            
            # 1. 转换所有嵌入型图片为浮动
            for i in range(doc.InlineShapes.Count, 0, -1):
                try:
                    inline_shape = doc.InlineShapes(i)
                    if inline_shape.Type == 3:  # wdInlineShapePicture
                        print(f"    - 转换嵌入型图片 {i} 为浮动型")
                        shape = inline_shape.ConvertToShape()
                        shape.WrapFormat.Type = 3  # wdWrapFront
                        shape.ZOrder(0)
                        print(f"    - 图片 {i} 已设置为浮于文字上方")
                except Exception as e:
                    print(f"    ⚠️  转换图片 {i} 时出错: {e}")
            
            # 2. 确保所有浮动图片都是浮于文字上方
            for i in range(1, doc.Shapes.Count + 1):
                try:
                    shape = doc.Shapes(i)
                    shape.WrapFormat.Type = 3  # wdWrapFront
                    shape.ZOrder(0)
                    print(f"    - 浮动图片 {i} 已确认为浮于文字上方 (Type=3, ZOrder=0)")
                except Exception as e:
                    print(f"    ⚠️  设置图片 {i} 时出错: {e}")
            
            # 保存文档
            doc.Save()
            doc.Close()
            print(f"✅ 文档已修复: {os.path.basename(doc_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            traceback.print_exc()
            return False
        finally:
            try:
                word.Quit()
            except:
                pass
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        traceback.print_exc()
        return False


def fix_all_documents_in_directory(directory=None):
    """修复目录中所有择日课单文档"""
    if directory is None:
        directory = os.path.dirname(__file__)
    
    print("=" * 80)
    print("一键修复工具 - 强制把所有文档中的印章图片设置为浮于文字上方")
    print("=" * 80)
    print(f"📂 扫描目录: {directory}")
    
    # 查找所有择日课单文档
    doc_files = []
    for filename in os.listdir(directory):
        if filename.startswith("择日课单_") and filename.endswith(".docx"):
            doc_files.append(os.path.join(directory, filename))
    
    if not doc_files:
        print("❌ 未找到任何择日课单文档")
        return
    
    print(f"✅ 找到 {len(doc_files)} 个文档")
    
    # 修复每个文档
    success_count = 0
    for doc_path in doc_files:
        if fix_document_seal(doc_path):
            success_count += 1
    
    print("=" * 80)
    print(f"✅ 修复完成！成功: {success_count}/{len(doc_files)}")
    print("=" * 80)


if __name__ == '__main__':
    print("\n请选择:")
    print("1. 修复所有择日课单文档")
    print("2. 修复单个文档")
    
    choice = input("\n请输入选项 (1 或 2): ").strip()
    
    if choice == "1":
        fix_all_documents_in_directory()
    elif choice == "2":
        doc_path = input("请输入文档路径: ").strip()
        if os.path.exists(doc_path):
            fix_document_seal(doc_path)
        else:
            print("❌ 文件不存在")
    else:
        print("❌ 无效选项")
    
    input("\n按任意键退出...")
