@echo off
REM 启动 HAMA 自动监控服务（MySQL 版本）
REM 以管理员身份运行

echo ==========================================
echo   HAMA 自动监控服务启动 (MySQL)
echo ==========================================
echo.

cd /d "%~dp0backend_api_python"

echo 正在启动自动监控...
echo.
echo 配置:
echo   监控币种: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT
echo   监控间隔: 10分钟
echo   浏览器: Chromium (无头模式)
echo   存储: MySQL 数据库
echo.
echo 按 Ctrl+C 停止监控
echo.
echo ==========================================
echo.

python auto_hama_monitor_mysql.py

pause
