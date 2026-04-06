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
start "API服务器" /min python api_server.py

echo 正在启动API服务器...
echo 等待服务器启动中...

rem 等待3秒让服务器启动
timeout /t 3 /nobreak >nul

rem 打开主界面
echo 启动主界面...
start "仪度六壬择日" "主界面.html"

echo 启动完成！
echo 请等待API服务器完全启动后再使用系统。
pause
