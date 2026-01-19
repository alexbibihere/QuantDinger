@echo off
REM QuantDinger 快速启动 - 双击运行

REM 设置控制台编码
chcp 65001 >nul

REM 设置标题
title QuantDinger

echo.
echo ================================================================================
echo                      QuantDinger 启动中...
echo ================================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 未安装或未添加到PATH
    pause
    exit /b 1
)

REM 启动后端（隐藏窗口）
start /MIN cmd /c "cd backend_api_python && python run.py"

REM 等待后端启动
echo [等待] 后端服务启动中...
timeout /t 5 /nobreak >nul

REM 启动前端
if exist "quantdinger_vue" (
    echo [启动] 前端服务...
    start cmd /c "cd quantdinger_vue && npm run serve"
)

echo.
echo ================================================================================
echo                        启动完成！
echo ================================================================================
echo.
echo 后端: http://localhost:5000
echo 前端: http://localhost:8000
echo.
echo 此窗口将在3秒后自动关闭...
timeout /t 3 /nobreak >nul
