#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器，用于提供前端界面
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

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
print(f"主界面: http://localhost:{PORT}/主界面.html")
print("=" * 80)

try:
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✓ 前端服务器已启动！")
        print(f"\n请在浏览器中访问:")
        print(f"  http://localhost:{PORT}/主界面.html")
        
        # 自动打开浏览器
        webbrowser.open(f"http://localhost:{PORT}/主界面.html")
        
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 80)
        
        httpd.serve_forever()
except Exception as e:
    print(f"\n✗ 启动前端服务器失败: {e}")
    sys.exit(1)
