@echo off
chcp 65001 >nul
echo ================================================
echo 宗门九课起课法模块 - 快速启动菜单
echo ================================================
echo.
echo 请选择要启动的程序：
echo.
echo 1. 启动 HTTP API 服务器
echo 2. 打开 HTML 演示页面
echo 3. 启动起课验证 GUI
echo 4. 启动课例查看器
echo 5. 重新生成课例数据库
echo 0. 退出
echo.
set /p choice=请输入选项 (0-5): 

if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto open_html
if "%choice%"=="3" goto start_gui
if "%choice%"=="4" goto start_viewer
if "%choice%"=="5" goto regenerate
if "%choice%"=="0" goto end

echo 无效选项！
pause
goto end

:start_api
echo.
echo 正在启动 HTTP API 服务器...
python http_api_server.py
goto end

:open_html
echo.
echo 正在打开 HTML 演示页面...
start demo.html
echo 提示：请先确保 API 服务器已启动（选项 1）
goto end

:start_gui
echo.
echo 正在启动起课验证 GUI...
python src\ui\qike_verification_gui.py
goto end

:start_viewer
echo.
echo 正在启动课例查看器...
python view_jiu_zong_men_720.py
goto end

:regenerate
echo.
echo 正在重新生成课例数据库...
python src\engine\jiu_zong_men_720_matcher.py
echo.
echo 生成完成！
pause
goto end

:end
