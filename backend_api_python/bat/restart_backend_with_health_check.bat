@echo off
REM ========================================
REM QuantDinger 后端重启脚本
REM 功能：当 HAMA 数据检测失败时自动重载 longLogic.txt
REM ========================================

echo.
echo ========================================
echo QuantDinger 后端重启脚本
echo ========================================
echo.

REM 设置项目根目录
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo [1/3] 停止现有后端服务...
echo.

REM 查找并停止现有的 Python 进程
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do (
    echo 停止 Python 进程: PID %%i
    taskkill /PID %%i /F >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo [2/3] 清理临时文件...
echo.

REM 清理 Python 缓存
if exist "__pycache__" rmdir /s /q __pycache__
if exist "app\__pycache__" rmdir /s /q app\__pycache__

echo.
echo [3/3] 启动后端服务...
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 虚拟环境未找到，使用全局 Python
)

REM 设置环境变量
set PYTHONIOENCODING=utf-8
set HAMA_HEALTH_CHECK_ENABLED=true
set HAMA_HEALTH_CHECK_INTERVAL=60
set HAMA_HEALTH_CHECK_THRESHOLD=3

echo.
echo 配置:
echo   - 健康检查: 已启用
echo   - 检查间隔: 60 秒
echo   - 失败阈值: 3 次
echo   - 失败后操作: 自动重载 longLogic.txt
echo.

REM 启动后端服务
echo 启动 Flask 后端 (端口 5000)...
python run.py

pause
