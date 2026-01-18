@echo off
echo ========================================
echo 重启前端服务以应用代理配置
echo ========================================
echo.

echo 1. 停止当前前端服务 (端口 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING" ^| findstr "LISTENING"') do (
    echo 正在停止进程 %%a...
    taskkill /f /pid %%a >nul 2>&1
    echo ✅ 已停止进程 %%a
)

echo.
echo 2. 等待 3 秒...
timeout /t 3 /nobreak >nul

echo.
echo 3. 启动前端服务...
start "Frontend Dev Server" /min cmd /c "cd quantdinger_vue && npm run serve -- --no-lint"

echo.
echo 4. 等待 10秒让服务完全启动...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo ✅ 前端服务已重启！
echo ========================================
echo.
echo 前端地址: http://localhost:8000
echo 后端地址: http://localhost:5000
echo.
echo 现在可以访问 HAMA 行情页面并查看截图！
echo.
echo ========================================
echo 按任意键关闭此窗口...
pause >nul
