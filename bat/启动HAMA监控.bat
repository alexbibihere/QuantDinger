@echo off
chcp 65001 > nul
REM 启动 HAMA 监控服务（简化版）
REM 按照 tradingview.txt 配置流程启动

echo ========================================
echo   HAMA 指标监控服务
echo ========================================
echo.
echo 配置信息:
echo   账号: alexbibiherr
echo   浏览器: Chromium (无头模式)
echo   OCR引擎: RapidOCR
echo   监控币种: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT
echo   监控间隔: 10分钟
echo.
echo 工作流程:
echo   1. 启动无头浏览器
echo   2. 使用 Cookie 访问 TradingView
echo   3. 截图 HAMA 指标区域
echo   4. OCR 识别指标数据
echo   5. 保存到数据库
echo   6. 前端查询展示
echo.
echo 按 Ctrl+C 停止监控
echo ========================================
echo.

cd /d "%~dp0.."
python start_hama_monitor_simple.py

pause
