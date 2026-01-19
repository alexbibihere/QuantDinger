@echo off
REM Redis Docker 部署脚本
echo ======================================
echo QuantDinger Redis 部署脚本
echo ======================================
echo.

cd /d %~dp0

echo [1/4] 检查 Docker 状态...
docker --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker 未运行或未安装
    pause
    exit /b 1
)
echo Docker 已就绪
echo.

echo [2/4] 拉取 Redis 镜像...
docker pull redis:7-alpine
echo.

echo [3/4] 启动 Redis 服务...
docker-compose up -d redis
timeout /t 5 >nul
echo.

echo [4/4] 验证 Redis 服务...
docker ps | findstr quantdinger-redis
if errorlevel 1 (
    echo 错误: Redis 容器未启动
    echo 请查看日志: docker-compose logs redis
    pause
    exit /b 1
)
echo.

echo ======================================
echo Redis 部署成功!
echo ======================================
echo.
echo 服务信息:
echo   - 容器名: quantdinger-redis
echo   - 端口: 127.0.0.1:6379
echo   - 数据卷: redis-data
echo.
echo 测试命令:
echo   docker exec -it quantdinger-redis redis-cli ping
echo.
echo 查看日志:
echo   docker-compose logs -f redis
echo.
echo 下一步:
echo   1. 启动后端: docker-compose up -d backend
echo   2. 查看状态: docker-compose ps
echo   3. 访问前端: http://localhost:8888
echo.

pause
