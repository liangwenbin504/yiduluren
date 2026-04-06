
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
