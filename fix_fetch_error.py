#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复"日期分析失败: Failed to fetch"错误的解决方案

功能：
1. 检查并启动API服务器
2. 测试API连接
3. 提供完整的错误处理
4. 自动修复常见问题
"""

import os
import sys
import subprocess
import time
import requests
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

def test_api_endpoints():
    """测试API端点是否正常工作"""
    endpoints = [
        'http://localhost:5000/api/sizhu?year=2026&month=3&day=29&hour=12',
        'http://localhost:5000/api/doushou/shanjia_wuxing?mountain=壬',
        'http://localhost:5000/api/doushou/full_range_analyze'
    ]
    
    print("🧪 测试API端点...")
    
    for endpoint in endpoints:
        try:
            if endpoint.endswith('full_range_analyze'):
                # POST请求
                response = requests.post(endpoint, json={
                    'mountain': '壬',
                    'start_date': '2026-03-29',
                    'end_date': '2026-03-30',
                    'min_daliuren_score': 70,
                    'max_results': 5
                }, timeout=10)
            else:
                # GET请求
                response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint.split('/')[-1]} - 正常")
            else:
                print(f"❌ {endpoint.split('/')[-1]} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint.split('/')[-1]} - 错误: {str(e)}")

def fix_cors_issue():
    """修复CORS问题"""
    print("🔧 检查CORS配置...")
    api_server_path = os.path.join(os.path.dirname(__file__), 'api_server.py')
    
    with open(api_server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查CORS配置
    if 'CORS(app)' in content:
        print("✅ CORS配置已存在")
    else:
        print("🔧 添加CORS配置...")
        # 在app创建后添加CORS配置
        modified_content = content.replace(
            'app = Flask(__name__)',
            'app = Flask(__name__)\nCORS(app)'
        )
        with open(api_server_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print("✅ CORS配置已添加")

def create_fix_script():
    """创建修复脚本"""
    fix_script_content = '''
@echo off

rem 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.11或更高版本
    pause
    exit /b 1
)

rem 启动API服务器
echo 正在启动API服务器...
python api_server.py
'''
    
    script_path = os.path.join(os.path.dirname(__file__), 'start_api_server.bat')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(fix_script_content)
    
    print(f"✅ 已创建启动脚本: {script_path}")

def create_html_fix():
    """修复HTML文件中的错误处理"""
    html_path = os.path.join(os.path.dirname(__file__), '主界面.html')
    
    if not os.path.exists(html_path):
        print("❌ 主界面.html 文件不存在")
        return
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加错误处理函数
    error_handler = '''
        // API错误处理函数
        function handleApiError(error, endpoint) {
            console.error(`API请求失败 (${endpoint}):`, error);
            
            // 检查是否是网络错误
            if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('fetch failed'))) {
                // 显示友好的错误提示
                alert('日期分析失败: API服务器未运行\n\n请先运行 start_api_server.bat 启动API服务器，然后重新尝试。');
                
                // 尝试自动启动API服务器（如果在本地环境）
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    console.log('尝试启动API服务器...');
                    // 这里可以添加启动服务器的逻辑
                }
            } else {
                // 其他错误
                alert('日期分析失败: ' + error.message);
            }
        }
        
        // API请求包装函数
        async function fetchApi(url, options = {}) {
            try {
                const response = await fetch(url, options);
                
                if (!response.ok) {
                    throw new Error(`API错误: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                handleApiError(error, url);
                throw error;
            }
        }'''
    
    # 在API配置后添加错误处理函数
    if 'API_BASE_URL' in content and 'handleApiError' not in content:
        modified_content = content.replace(
            'const API_BASE_URL = \'http://localhost:5000/api\';',
            'const API_BASE_URL = \'http://localhost:5000/api\';' + error_handler
        )
        
        # 替换所有的fetch调用为fetchApi
        modified_content = modified_content.replace(
            'const response = await fetch(',
            'const response = await fetchApi('
        )
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("✅ 已修复HTML文件中的错误处理")
    else:
        print("✅ HTML文件已经包含错误处理")

def main():
    """主函数"""
    print("🚀 开始修复 '日期分析失败: Failed to fetch' 错误")
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
            return
    
    # 3. 测试API端点
    print("\n2. 测试API端点...")
    test_api_endpoints()
    
    # 4. 修复CORS问题
    print("\n3. 修复CORS配置...")
    fix_cors_issue()
    
    # 5. 创建启动脚本
    print("\n4. 创建启动脚本...")
    create_fix_script()
    
    # 6. 修复HTML文件
    print("\n5. 修复HTML错误处理...")
    create_html_fix()
    
    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("\n📋 操作步骤：")
    print("1. 运行 start_api_server.bat 启动API服务器")
    print("2. 重新打开 主界面.html")
    print("3. 点击'开始择日'按钮")
    print("\n🎉 现在应该能够正常进行日期分析了！")

if __name__ == '__main__':
    main()
