@echo off
REM QuantDinger 简化部署脚本
REM 不使用 choice 命令,避免兼容性问题

echo ========================================
echo QuantDinger Docker 部署脚本
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
    echo [错误] Docker 未运行
    echo.
    echo 请先启动 Docker Desktop，然后重新运行此脚本
    pause
    exit /b 1
)

echo [1/4] 停止现有容器...
docker-compose down
echo.

echo [2/4] 构建镜像...
docker-compose build
echo.

echo [3/4] 启动容器...
docker-compose up -d
echo.

echo [4/4] 等待服务启动...
timeout /t 10 /nobreak >nul
echo.

echo ========================================
echo 检查容器状态...
echo ========================================
echo.
docker-compose ps
echo.

echo ========================================
echo 部署完成!
echo ========================================
echo.
echo 前端地址: http://localhost:8888
echo 后端地址: http://localhost:5000
echo 涨幅榜分析: http://localhost:8888/gainer-analysis
echo.
echo 提示：
echo   - 首次启动可能需要等待 30 秒让服务完全启动
echo   - 如果前端无法访问，请稍等片刻后刷新页面
echo   - 查看日志: docker-compose logs -f backend
echo.
pause
