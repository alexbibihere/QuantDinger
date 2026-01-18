@echo off

REM 一键重启QuantDinger前后端服务脚本
cls
echo ========================================
echo QuantDinger 服务重启脚本
echo ========================================
echo.

REM 1. 终止现有进程
echo 1. 终止现有服务进程...

REM 终止后端服务进程 (端口5000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000.*LISTENING"') do (
    echo 终止后端服务进程 %%a...
    taskkill /f /pid %%a >nul 2>&1
    echo ✅ 后端服务进程 %%a 已终止
)

REM 终止前端服务进程 (端口8000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do (
    echo 终止前端服务进程 %%a...
    taskkill /f /pid %%a >nul 2>&1
    echo ✅ 前端服务进程 %%a 已终止
)

echo.

REM 2. 启动后端服务
echo 2. 启动后端服务...
start "Backend Service" /min cmd /c "cd backend_api_python && python run.py"
echo ✅ 后端服务已启动

REM 等待后端启动 (3秒)
timeout /t 3 /nobreak >nul

REM 3. 启动前端服务
echo 3. 启动前端服务...
start "Frontend Service" /min cmd /c "cd quantdinger_vue && npm run serve -- --no-lint"
echo ✅ 前端服务已启动

REM 等待前端启动 (3秒)
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 服务重启完成！
echo ========================================
echo 后端服务地址: http://localhost:5000
echo 前端服务地址: http://localhost:8000
echo 默认登录凭证: quantdinger / 123456
echo.
echo ========================================
echo 按任意键退出...
pause >nul