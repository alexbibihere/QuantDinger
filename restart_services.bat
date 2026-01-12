@echo off
REM QuantDinger Docker 快速重启脚本
REM 用于重新部署涨幅榜分析功能

echo ========================================
echo QuantDinger Docker 重启脚本
echo ========================================
echo.

REM 检查是否在正确的目录
if not exist "docker-compose.yml" (
    echo 错误：请将此脚本放在 QuantDinger 根目录下运行
    pause
    exit /b 1
)

REM 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未运行,请先启动 Docker Desktop
    pause
    exit /b 1
)

echo [1/5] 停止现有容器...
docker-compose down

echo.
echo [2/5] 清理旧镜像 (可选)...
choice /C YN /M "是否清理旧镜像"
if %errorlevel% == 1 (
    docker-compose build --no-cache
) else (
    docker-compose build
)

echo.
echo [3/5] 启动容器...
docker-compose up -d

echo.
echo [4/5] 等待服务启动...
timeout /t 5 /nobreak >nul

echo.
echo [5/5] 检查服务状态...
echo.
docker-compose ps

echo.
echo ========================================
echo 测试后端健康...
echo ========================================
echo.

curl -s http://localhost:5000/api/health
if %errorlevel% == 0 (
    echo.
    echo [成功] 后端健康检查通过!
) else (
    echo.
    echo [警告] 后端可能还在启动中,请稍等片刻
)

echo.
echo ========================================
echo 部署完成!
echo ========================================
echo.
echo 前端地址: http://localhost:8888
echo 后端地址: http://localhost:5000
echo 涨幅榜分析: http://localhost:8888/gainer-analysis
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f backend
echo   停止服务: docker-compose down
echo   重启后端: docker-compose restart backend
echo   进入容器: docker exec -it quantdinger-backend bash
echo.
echo 按任意键关闭此窗口...
pause >nul
