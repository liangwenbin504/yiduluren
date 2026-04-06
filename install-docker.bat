@echo off
chcp 65001 >nul
echo ============================================================
echo Docker Desktop 安装指南
echo ============================================================
echo.
echo 步骤 1: 访问 Docker Desktop 下载页面
echo ----------------------------------------
echo 打开浏览器访问：
echo https://docs.docker.com/desktop/install/windows-install/
echo.
echo 按任意键继续...
pause >nul
cls

echo ============================================================
echo 步骤 2: 下载 Docker Desktop
echo ----------------------------------------
echo 1. 点击 "Download for Windows" 按钮
echo 2. 等待下载完成（约 500MB）
echo.
echo 下载完成后按任意键继续...
pause >nul
cls

echo ============================================================
echo 步骤 3: 安装 Docker Desktop
echo ----------------------------------------
echo 1. 双击运行下载的 DockerDesktopInstaller.exe
echo 2. 勾选 "Use WSL 2 instead of Hyper-V"（推荐）
echo 3. 点击 "OK" 开始安装
echo 4. 等待安装完成（约 5-10 分钟）
echo.
echo 安装完成后按任意键继续...
pause >nul
cls

echo ============================================================
echo 步骤 4: 重启电脑
echo ----------------------------------------
echo Docker 安装完成后需要重启电脑
echo.
echo 是否现在重启？(Y/N)
set /p restart=
if /i "%restart%"=="Y" (
    echo 正在重启...
    shutdown /r /t 5
) else (
    echo 请手动重启电脑，然后运行 docker-deploy.ps1
)

echo ============================================================
