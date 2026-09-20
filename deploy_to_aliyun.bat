@echo off
chcp 65001 >nul
echo ============================================================
echo  仪度六壬择日 - 阿里云部署
echo ============================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查部署包
if not exist "liuren-deploy-update.zip" (
    echo ❌ 部署包不存在！
    echo 请先运行打包脚本...
    pause
    exit /b 1
)

for %%A in ("liuren-deploy-update.zip") do set /a "size=%%~zA/1048576"
echo 📦 部署包大小: %size% MB
echo.

echo 📤 步骤1：上传部署包到服务器...
echo    请在弹出的密码提示中输入服务器密码
echo.

REM 上传到服务器
scp -o StrictHostKeyChecking=no "liuren-deploy-update.zip" root@47.97.244.134:/tmp/

if errorlevel 1 (
    echo ❌ 上传失败！
    pause
    exit /b 1
)

echo ✅ 上传成功
echo.

echo 🔧 步骤2：在服务器上解压并部署...
echo.

REM SSH 执行远程命令
ssh -o StrictHostKeyChecking=no root@47.97.244.134 ^
"set -e; ^
if [ -d '/opt/liuren' ]; then cp -r '/opt/liuren' '/opt/liuren.bak_$(date +%%Y%%m%%d_%%H%%M%%S)' 2>/dev/null || true; fi; ^
mkdir -p /opt/liuren; ^
cd /tmp; ^
rm -rf liuren_deploy_temp; ^
mkdir -p liuren_deploy_temp; ^
if command -v unzip &>/dev/null; then unzip -o liuren-deploy-update.zip -d liuren_deploy_temp/; ^
elif command -v python3 &>/dev/null; then python3 -c \"import zipfile; zipfile.ZipFile('liuren-deploy-update.zip').extractall('liuren_deploy_temp')\"; ^
else echo '❌ 无法解压'; exit 1; fi; ^
cp -rf liuren_deploy_temp/* /opt/liuren/; ^
chmod +x /opt/liuren/install_on_server.sh 2>/dev/null || true; ^
cd /opt/liuren; ^
bash install_on_server.sh; ^
rm -rf /tmp/liuren_deploy_temp /tmp/liuren-deploy-update.zip; ^
echo ''; ^
echo '✅ 部署完成！'; ^
echo '   服务状态: systemctl status liuren'; ^
echo '   访问地址: https://liuren.souhuertong.net.cn'"

echo.
echo ============================================================
echo  部署流程完成
echo ============================================================
echo.
echo 🌐 访问地址: https://liuren.souhuertong.net.cn
echo.
pause
