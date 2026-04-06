@echo off
chcp 65001 >nul
title 大六壬 8640 课例精准匹配系统

echo ================================================================
echo   大六壬 8640 课例精准匹配系统
echo   使用 Qwen Max API 进行智能匹配
echo ================================================================
echo.

cd /d "%~dp0"

echo 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python 环境，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [✓] Python 环境正常
echo.

echo 检查依赖包...
python -c "import dashscope" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 dashscope 包...
    pip install dashscope -q
    if errorlevel 1 (
        echo [错误] 安装 dashscope 失败，请手动运行：pip install dashscope
        pause
        exit /b 1
    )
    echo [✓] dashscope 安装完成
) else (
    echo [✓] dashscope 已安装
)
echo.

echo ================================================================
echo  选择操作模式
echo ================================================================
echo.
echo 1. 开始批量匹配（8640 个课例）
echo 2. 验证匹配结果
echo 3. 查看当前进度
echo 4. 查看匹配报告
echo 5. 查看验证报告
echo 6. 退出
echo.
set /p choice="请输入选项 (1-6): "

if "%choice%"=="1" goto MATCH
if "%choice%"=="2" goto VALIDATE
if "%choice%"=="3" goto PROGRESS
if "%choice%"=="4" goto MATCH_REPORT
if "%choice%"=="5" goto VALIDATION_REPORT
if "%choice%"=="6" goto END

echo [错误] 无效的选项
pause
exit /b 1

:MATCH
echo.
echo ================================================================
echo  开始批量匹配
echo ================================================================
echo.
echo 提示：
echo - 匹配过程会自动保存进度，可随时中断
echo - 每 100 个课例保存一次进度
echo - 预计处理时间：约 30-60 分钟（取决于 API 响应速度）
echo.
set /p confirm="确认开始匹配？(Y/N): "
if /i not "%confirm%"=="Y" goto MENU

python qwen_max_batch_match.py
if errorlevel 1 (
    echo.
    echo [错误] 匹配过程出现错误
    pause
    goto MENU
)

echo.
echo [✓] 批量匹配完成！
pause
goto MENU

:VALIDATE
echo.
echo ================================================================
echo  验证匹配结果
echo ================================================================
echo.
python validate_match_results.py
if errorlevel 1 (
    echo.
    echo [错误] 验证过程出现错误
    pause
    goto MENU
)

echo.
echo [✓] 验证完成！
pause
goto MENU

:PROGRESS
echo.
echo ================================================================
echo  当前进度
echo ================================================================
echo.
if exist match_progress.json (
    python -c "import json; data=json.load(open('match_progress.json', 'r', encoding='utf-8')); print(f'已匹配：{data.get(\"completed\", 0)}/{data.get(\"total\", 0)} ({data.get(\"completed\", 0)/data.get(\"total\", 1)*100:.1f}%)'); print(f'错误数：{len(data.get(\"error_log\", []))}'); print(f'最后更新：{data.get(\"timestamp\", \"未知\")}')"
) else (
    echo [提示] 未找到进度文件，可能还未开始匹配
)
echo.
pause
goto MENU

:MATCH_REPORT
echo.
echo ================================================================
echo  匹配报告
echo ================================================================
echo.
if exist qwen_max_match_report.md (
    type qwen_max_match_report.md
) else (
    echo [提示] 未找到匹配报告，请先运行批量匹配
)
echo.
pause
goto MENU

:VALIDATION_REPORT
echo.
echo ================================================================
echo  验证报告
echo ================================================================
echo.
if exist validation_report.md (
    type validation_report.md
) else (
    echo [提示] 未找到验证报告，请先运行验证程序
)
echo.
pause
goto MENU

:MENU
cls
goto MENU_START

:END
echo.
echo 感谢使用，再见！
exit /b 0
