@echo off
chcp 65001 >nul
echo Starting Comprehensive Date Selection System...
echo.
python comprehensive_date_selector_gui.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo Please check:
    echo 1. Python is installed correctly
    echo 2. tkinter library is installed
    echo.
    pause
)
