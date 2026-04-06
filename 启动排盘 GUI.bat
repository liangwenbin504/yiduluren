@echo off
chcp 65001 >nul
echo Starting DaLiuRen Paipan Software GUI...
echo.
python paipan_gui.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start.
    pause
)
