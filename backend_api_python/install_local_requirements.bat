@echo off
REM 本地开发环境安装脚本 - Windows 版本
REM 以管理员身份运行 PowerShell 或 CMD

echo ==========================================
echo   本地开发环境安装 - Playwright + OCR
echo ==========================================
echo.

REM 检查 Python
echo 1. 检查 Python 版本...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.10+
    pause
    exit /b 1
)
echo ✅ Python 已安装
echo.

REM 安装依赖
echo 2. 安装 Python 依赖包...
pip install playwright playwright-stealth rapidocr-onnxruntime
if errorlevel 1 (
    echo ❌ Python 依赖安装失败
    pause
    exit /b 1
)
echo ✅ Python 依赖安装成功
echo.

REM 安装 Chromium 浏览器
echo 3. 安装 Playwright Chromium 浏览器...
echo 这需要下载约 300MB 文件，请耐心等待...
playwright install chromium
if errorlevel 1 (
    echo ❌ Chromium 安装失败
    pause
    exit /b 1
)
echo ✅ Chromium 安装成功
echo.

REM 验证安装
echo 4. 验证安装...
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright 导入成功')"
python -c "from rapidocr_onnxruntime import RapidOCR; print('✅ RapidOCR 导入成功')"
echo.

echo ==========================================
echo   ✅ 安装完成！
echo ==========================================
echo.
echo 下一步：
echo 1. 运行测试脚本: python test_brave_local.py
echo 2. 或手动测试
echo.
pause
