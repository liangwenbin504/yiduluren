@echo off
chcp 65001 >nul
echo 正在启动大六壬起课方法验证系统...
cd /d "%~dp0"
python "src\ui\qike_verification_gui.py"
pause
