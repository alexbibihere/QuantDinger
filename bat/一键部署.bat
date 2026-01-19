@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    QuantDinger 一键部署
echo ========================================
echo.
echo 正在部署,请稍候...
echo.
cd /d "%~dp0"
docker compose down 2>nul
docker compose build
docker compose up -d
echo.
echo ========================================
echo 部署完成!
echo ========================================
echo.
echo 前端地址: http://localhost:8888
echo 后端地址: http://localhost:5000
echo 涨幅榜分析: http://localhost:8888/gainer-analysis
echo.
pause
