@echo off
chcp 65001 > nul
REM 一键启动所有服务
REM 包括：后端 API、HAMA Brave 监控、邮件通知、前端 Vue

echo ========================================
echo   QuantDinger 一键启动所有服务
echo ========================================
echo.
echo 启动的服务包括:
echo   1. 后端 API 服务 (端口 5000)
echo   2. HAMA Brave 监控服务 (自动监控 TradingView)
echo   3. 邮件通知服务 (QQ 邮箱)
echo   4. 前端 Vue 应用 (端口 8000)
echo.
echo 按 Ctrl+C 停止所有服务
echo ========================================
echo.

cd /d "%~dp0.."

REM 启动服务
python start_all_services.py

pause
