@echo off
chcp 65001 >nul
echo ================================================================
echo 扫描版 PDF 内容提取工具 - 快速启动
echo ================================================================
echo.
echo PDF 文件：[图解六壬大全。第 2 部。吉凶占断].许颐平。扫描版 [minxue.net].pdf
echo 目标页码：第 290 页（三光课）
echo.
echo ================================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python 已安装
echo.

REM 检查依赖包
echo 正在检查依赖包...
python -c "import pdf2image" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 缺少 pdf2image，正在安装...
    pip install pdf2image -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [✓] pdf2image 已安装
)

python -c "import pytesseract" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 缺少 pytesseract，正在安装...
    pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [✓] pytesseract 已安装
)

python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 缺少 Pillow，正在安装...
    pip install pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [✓] Pillow 已安装
)

python -c "import pdfplumber" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 缺少 pdfplumber，正在安装...
    pip install pdfplumber -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [✓] pdfplumber 已安装
)

echo.
echo ================================================================
echo 依赖包检查完成！
echo ================================================================
echo.

REM 检查 Tesseract-OCR
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 Tesseract-OCR
    echo.
    echo Tesseract-OCR 是 OCR 识别的必需组件
    echo 请下载并安装：https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 是否继续？（选择"否"将退出并先安装 Tesseract）
    echo.
    choice /C YN /M "是否继续运行"
    if errorlevel 2 (
        echo.
        echo 已退出，请先安装 Tesseract-OCR
        pause
        exit /b 1
    )
) else (
    echo [✓] Tesseract-OCR 已安装
)

echo.
echo ================================================================
echo 开始提取 PDF 内容...
echo ================================================================
echo.

REM 运行提取脚本
python extract_pdf_page.py

echo.
echo ================================================================
echo 提取完成！
echo ================================================================
echo.
echo 输出文件位置：zongmen\pdf_extract\
echo.
echo 请查看以下文件：
echo   - page_290.png          (页面图片)
echo   - page_290_ocr.txt      (OCR 识别文本)
echo   - page_290_direct.txt   (直接提取文本，如果有)
echo.
echo 提示：OCR 识别可能存在错误，建议人工校对
echo.
pause
