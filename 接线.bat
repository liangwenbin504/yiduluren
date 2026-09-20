@echo off
chcp 65001 >nul
title 接线（打补丁）
echo 正在给 stock_dashboard.py 和 api_server.py 打补丁...
python "E:\仪度六壬择日\yiduluren\_memory\_wire_now.py"
if errorlevel 1 (
  echo.
  echo [失败] 如果提示 Permission denied，说明锁又回来了：
  echo   1. 重新运行 _memory\stop_guardians.py（停守护+杀进程）
  echo   2. 立即双击本 bat（中间不要停顿）
  pause
)
