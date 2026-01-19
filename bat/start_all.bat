@echo off
chcp 65001 >nul
title QuantDinger - 一键启动前后端

echo.
echo ================================================================================
echo                         QuantDinger 一键启动
echo ================================================================================
echo.

REM 检查当前目录
if not exist "backend_api_python" (
    echo [错误] 请在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [信息] 正在启动后端服务...
echo.

REM 启动后端（在新窗口中）
start "QuantDinger-Backend" cmd /k "cd backend_api_python && python run.py"

REM 等待后端启动
echo [等待] 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo [信息] 正在启动前端服务...
echo.

REM 检查前端目录
if not exist "quantdinger_vue" (
    echo [警告] 前端目录不存在，跳过前端启动
    echo [提示] 请先安装前端依赖：cd quantdinger_vue && npm install
) else (
    REM 启动前端（在新窗口中）
    start "QuantDinger-Frontend" cmd /k "cd quantdinger_vue && npm run serve"
)

echo.
echo ================================================================================
echo                            启动完成！
echo ================================================================================
echo.
echo 后端地址: http://localhost:5000
echo 前端地址: http://localhost:8000
echo.
echo API文档: http://localhost:5000/api/health
echo.
echo 按任意键关闭此窗口...
pause >nul
