# -*- coding: utf-8 -*-
import http.server
import socketserver
import webbrowser
import os
import threading
import time

def start_server(directory, port=8000):
    os.chdir(directory)
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler)
    print(f"服务器启动在 http://localhost:{port}")
    httpd.serve_forever()

def open_docx_preview(docx_path):
    # 获取文件所在目录
    directory = os.path.dirname(docx_path)
    docx_filename = os.path.basename(docx_path)
    
    # 启动服务器
    server_thread = threading.Thread(target=start_server, args=(directory, 8000))
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(1)
    
    # 打开浏览器
    preview_url = f"http://localhost:8000/{docx_filename}"
    print(f"打开预览: {preview_url}")
    webbrowser.open(preview_url)
    
    # 提示用户
    print("\n=== 预览说明 ===")
    print("1. 这将在浏览器中打开 docx 文件")
    print("2. 浏览器会尝试使用内置的 docx 查看器")
    print("3. 按 Ctrl+C 停止服务器")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    docx_path = r'd:\新建文件夹\仪度六壬择日\yiduluren\择日课单_20260330_091220.docx'
    open_docx_preview(docx_path)
