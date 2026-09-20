@echo off
chcp 65001 >nul
title 5555 择日服务
cd /d E:\仪度六壬择日\yiduluren
echo 正在启动 5555 择日服务（stock_dashboard.py）...
echo 启动后请勿关闭本窗口（窗口关闭服务即停）
echo 验证: 浏览器打开 http://127.0.0.1:5555/api/health
echo.
start "5555择日服务" pythonw stock_dashboard.py
timeout /t 5 /nobreak >nul
netstat -ano | findstr ":5555" && (
  echo.
  echo ✔ 服务已启动，端口 5555 已监听
  echo   验证地址: http://127.0.0.1:5555/api/health
) || (
  echo.
  echo ✖ 5 秒内未检测到 5555 端口，可能启动较慢或失败
  echo   稍等几秒再访问 http://127.0.0.1:5555/api/health 确认
)
pause
