#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器，用于提供前端界面，同时启动API服务器
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess
import time
import threading

PORT = 8000
API_PORT = 5000

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

print("=" * 80)
print("仪度六壬择日系统 - 前端服务器")
print("=" * 80)
print(f"前端服务地址: http://localhost:{PORT}")
print(f"API服务地址: http://localhost:{API_PORT}")
print(f"主界面: http://localhost:{PORT}/主界面.html")
print("=" * 80)

# 启动API服务器
api_process = None
try:
    print("\n正在启动API服务器...")
    api_process = subprocess.Popen(
        [sys.executable, "api_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print("✓ API服务器已启动")
    
    # 等待API服务器启动
    time.sleep(2)
except Exception as e:
    print(f"✗ 启动API服务器失败: {e}")

print("\n正在启动前端服务器...")

def start_http_server():
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"✓ 前端服务器已启动！")
            print(f"\n请在浏览器中访问:")
            print(f"  http://localhost:{PORT}/主界面.html")
            print("\n按 Ctrl+C 停止服务器")
            print("=" * 80)
            
            # 自动打开浏览器
            webbrowser.open(f"http://localhost:{PORT}/主界面.html")
            
            httpd.serve_forever()
    except Exception as e:
        print(f"\n✗ 启动前端服务器失败: {e}")
        if api_process:
            api_process.terminate()
        sys.exit(1)

try:
    server_thread = threading.Thread(target=start_http_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 监控进程
    while True:
        if api_process and api_process.poll() is not None:
            print(f"\nAPI服务器已停止，退出代码: {api_process.returncode}")
            break
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n正在停止服务器...")
    if api_process:
        api_process.terminate()
    print("✓ 所有服务器已停止")
    sys.exit(0)
