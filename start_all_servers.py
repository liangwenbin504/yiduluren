#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同时启动前端和后端服务器
"""

import subprocess
import sys
import os
import time
import webbrowser

# 切换到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("仪度六壬择日系统 - 启动所有服务器")
print("=" * 80)

# 启动后端API服务器（端口5000）
print("\n[1/2] 正在启动后端API服务器 (端口 5000)...")
try:
    backend_process = subprocess.Popen(
        [sys.executable, "api_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print("✓ 后端API服务器已启动")
except Exception as e:
    print(f"✗ 启动后端服务器失败: {e}")
    sys.exit(1)

# 等待后端服务器启动
time.sleep(2)

# 启动前端服务器（端口8000）
print("\n[2/2] 正在启动前端服务器 (端口 8000)...")
try:
    frontend_process = subprocess.Popen(
        [sys.executable, "start_frontend_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print("✓ 前端服务器已启动")
except Exception as e:
    print(f"✗ 启动前端服务器失败: {e}")
    backend_process.terminate()
    sys.exit(1)

print("\n" + "=" * 80)
print("✓ 所有服务器启动成功！")
print("=" * 80)
print(f"\n后端API: http://localhost:5000")
print(f"前端界面: http://localhost:8000/主界面.html")
print("\n正在打开浏览器...")
print("\n按 Ctrl+C 停止所有服务器")
print("=" * 80)

# 自动打开浏览器
time.sleep(1)
webbrowser.open("http://localhost:8000/主界面.html")

try:
    # 监控两个进程
    while True:
        if backend_process.poll() is not None:
            print(f"\n后端服务器已停止，退出代码: {backend_process.returncode}")
            frontend_process.terminate()
            break
        if frontend_process.poll() is not None:
            print(f"\n前端服务器已停止，退出代码: {frontend_process.returncode}")
            backend_process.terminate()
            break
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n正在停止所有服务器...")
    backend_process.terminate()
    frontend_process.terminate()
    print("✓ 所有服务器已停止")
