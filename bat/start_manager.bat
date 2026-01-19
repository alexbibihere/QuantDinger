@echo off
chcp 65001 >nul
title QuantDinger 启动管理器

:MENU
cls
echo.
echo ================================================================================
echo                      QuantDinger 启动管理器
echo ================================================================================
echo.
echo  1. 启动后端服务 (Flask API)
echo  2. 启动前端服务 (Vue.js)
echo  3. 启动所有服务 (后端 + 前端)
echo  4. 启动 HAMA 监控 (Brave Browser)
echo  5. 启动邮件测试
echo  6. 查看服务状态
echo  0. 退出
echo.
echo ================================================================================
echo.

set /p choice="请选择操作 (0-6): "

if "%choice%"=="1" goto START_BACKEND
if "%choice%"=="2" goto START_FRONTEND
if "%choice%"=="3" goto START_ALL
if "%choice%"=="4" goto START_HAMA
if "%choice%"=="5" goto TEST_EMAIL
if "%choice%"=="6" goto CHECK_STATUS
if "%choice%"=="0" goto EXIT
goto MENU

:START_BACKEND
cls
echo.
echo ================================================================================
echo                         启动后端服务
echo ================================================================================
echo.
cd backend_api_python
echo [信息] 启动 Flask API 服务器...
echo.
start "QuantDinger-Backend" cmd /k "python run.py"
echo.
echo [成功] 后端服务已在新窗口启动
echo.
echo 后端地址: http://localhost:5000
echo API健康检查: http://localhost:5000/api/health
echo.
pause
goto MENU

:START_FRONTEND
cls
echo.
echo ================================================================================
echo                         启动前端服务
echo ================================================================================
echo.

if not exist "quantdinger_vue\node_modules" (
    echo [警告] 前端依赖未安装
    echo.
    set /p install_deps="是否立即安装依赖? (Y/N): "
    if /i "%install_deps%"=="Y" (
        echo.
        echo [信息] 正在安装前端依赖...
        cd quantdinger_vue
        call npm install
        cd ..
        echo.
        echo [成功] 依赖安装完成
        echo.
    ) else (
        echo [跳过] 请手动安装依赖：cd quantdinger_vue ^&^& npm install
        pause
        goto MENU
    )
)

cd quantdinger_vue
echo [信息] 启动 Vue.js 开发服务器...
echo.
start "QuantDinger-Frontend" cmd /k "npm run serve"
echo.
echo [成功] 前端服务已在新窗口启动
echo.
echo 前端地址: http://localhost:8000
echo.
pause
goto MENU

:START_ALL
cls
echo.
echo ================================================================================
echo                       启动所有服务
echo ================================================================================
echo.

REM 启动后端
echo [1/2] 启动后端服务...
cd backend_api_python
start "QuantDinger-Backend" cmd /k "python run.py"
cd ..

REM 等待后端启动
echo [等待] 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动前端服务...
if exist "quantdinger_vue" (
    cd quantdinger_vue
    start "QuantDinger-Frontend" cmd /k "npm run serve"
    cd ..
)

echo.
echo [成功] 所有服务已启动
echo.
echo 后端地址: http://localhost:5000
echo 前端地址: http://localhost:8000
echo.
pause
goto MENU

:START_HAMA
cls
echo.
echo ================================================================================
echo                     启动 HAMA 监控服务
echo ================================================================================
echo.
echo [信息] HAMA 监控会自动监控以下币种:
echo   - BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT
echo   - ADAUSDT, DOGEUSDT
echo.
echo [功能]
echo   - 每 10 分钟自动监控一次
echo   - 检测趋势变化会发送邮件通知
echo   - 收件人: 329731984@qq.com
echo.
set /p confirm="确认启动 HAMA 监控? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

cd backend_api_python
echo.
echo [信息] 启动 HAMA 监控...
echo.
start "HAMA-Monitor" cmd /k "python auto_hama_monitor_mysql.py"
echo.
echo [成功] HAMA 监控已启动
echo.
echo 提示: 监控日志会显示在窗口中
echo.
pause
goto MENU

:TEST_EMAIL
cls
echo.
echo ================================================================================
echo                     测试邮件发送功能
echo ================================================================================
echo.
echo [信息] 发送测试邮件到: 329731984@qq.com
echo.
set /p confirm="确认发送测试邮件? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

cd backend_api_python
echo.
echo [信息] 正在发送测试邮件...
echo.
python diagnose_smtp.py
echo.
pause
goto MENU

:CHECK_STATUS
cls
echo.
echo ================================================================================
echo                       服务状态检查
echo ================================================================================
echo.

echo [检查] 后端服务 (Flask API)
echo.
tasklist /FI "WINDOWTITLE eq QuantDinger-Backend*" 2>nul | find /v "INFO" >nul
if %errorlevel%==0 (
    echo [运行中] 后端服务正在运行
) else (
    echo [未运行] 后端服务未启动
)

echo.
echo [检查] 前端服务 (Vue.js)
echo.
tasklist /FI "WINDOWTITLE eq QuantDinger-Frontend*" 2>nul | find /v "INFO" >nul
if %errorlevel%==0 (
    echo [运行中] 前端服务正在运行
) else (
    echo [未运行] 前端服务未启动
)

echo.
echo [检查] HAMA 监控
echo.
tasklist /FI "WINDOWTITLE eq HAMA-Monitor*" 2>nul | find /v "INFO" >nul
if %errorlevel%==0 (
    echo [运行中] HAMA 监控正在运行
) else (
    echo [未运行] HAMA 监控未启动
)

echo.
echo ================================================================================
echo.
echo 服务地址:
echo   后端 API: http://localhost:5000
echo   前端界面: http://localhost:8000
echo   健康检查: http://localhost:5000/api/health
echo.
pause
goto MENU

:EXIT
cls
echo.
echo [退出] 感谢使用 QuantDinger！
echo.
timeout /t 2 /nobreak >nul
exit /b 0
