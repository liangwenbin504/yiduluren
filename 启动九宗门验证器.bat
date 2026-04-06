@echo off
cd /d "%~dp0"
echo ================================
echo 启动大六壬起课方法验证系统
echo ================================
echo.
echo 正在启动 GUI...
start "QikeVerificationGUI" /B python "src\ui\qike_verification_gui.py"
echo.
echo 启动命令已发送！
echo 如果 GUI 没有启动，请检查：
echo 1. Python 是否正确安装
echo 2. 是否安装了 tkinter 模块
echo 3. 查看是否有错误提示
echo.
pause
