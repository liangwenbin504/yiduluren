#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动主界面时自动启动Flask API服务器

功能：
1. 检查API服务器是否正在运行
2. 如果未运行，启动API服务器
3. 打开主界面HTML文件
4. 提供完整的错误处理
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from datetime import datetime

# 添加核心模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_api_server():
    """检查API服务器是否正在运行"""
    try:
        response = requests.get('http://localhost:5000/api/sizhu?year=2026&month=3&day=29&hour=12', timeout=5)
        return response.status_code == 200
    except:
        return False

def start_api_server():
    """启动API服务器"""
    print("🔧 正在启动API服务器...")
    
    # 启动API服务器作为后台进程
    python_exe = sys.executable
    api_server_path = os.path.join(os.path.dirname(__file__), 'api_server.py')
    
    # 使用Popen启动服务器
    process = subprocess.Popen(
        [python_exe, api_server_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # 等待服务器启动
    print("⏳ 等待API服务器启动...")
    time.sleep(3)
    
    # 检查服务器是否成功启动
    for i in range(10):
        if check_api_server():
            print("✅ API服务器启动成功！")
            return True
        time.sleep(2)
    
    print("❌ API服务器启动失败，请检查错误信息")
    # 读取错误输出
    stdout, stderr = process.communicate()
    if stderr:
        print(f"错误信息: {stderr.decode('utf-8')}")
    return False

def open_main_interface():
    """打开主界面"""
    html_path = os.path.join(os.path.dirname(__file__), '主界面.html')
    if os.path.exists(html_path):
        print("🌐 正在打开主界面...")
        webbrowser.open(f'file:///{html_path.replace(os.sep, "/")}')
        print("✅ 主界面已打开")
        return True
    else:
        print("❌ 主界面.html 文件不存在")
        return False

def main():
    """主函数"""
    print("🚀 仪度六壬择日系统启动器")
    print("=" * 60)
    
    # 1. 检查API服务器状态
    print("1. 检查API服务器状态...")
    if check_api_server():
        print("✅ API服务器已经在运行")
    else:
        print("❌ API服务器未运行")
        # 2. 启动API服务器
        if not start_api_server():
            print("❌ 无法启动API服务器，请手动运行 api_server.py")
            input("按回车键退出...")
            return
    
    # 3. 打开主界面
    print("\n2. 打开主界面...")
    if not open_main_interface():
        print("❌ 无法打开主界面，请检查文件是否存在")
        input("按回车键退出...")
        return
    
    print("\n" + "=" * 60)
    print("✅ 系统启动完成！")
    print("\n📋 使用说明：")
    print("1. 等待API服务器完全启动（约5秒钟）")
    print("2. 在主界面中选择择日类型、坐山等参数")
    print("3. 点击'开始择日'按钮开始分析")
    print("\n🎉 祝您使用愉快！")
    
    # 等待用户确认
    input("\n按回车键退出启动器...")

if __name__ == '__main__':
    main()
