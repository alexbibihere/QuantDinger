#!/bin/bash
# QuantDinger Docker 快速重启脚本
# 用于重新部署涨幅榜分析功能

set -e

echo "========================================"
echo "QuantDinger Docker 重启脚本"
echo "========================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "错误：请将此脚本放在 QuantDinger 根目录下运行"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "[错误] Docker 未运行，请先启动 Docker"
    exit 1
fi

echo "[1/5] 停止现有容器..."
docker-compose down

echo ""
echo "[2/5] 重新构建镜像..."
read -p "是否清理旧镜像? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

echo ""
echo "[3/5] 启动容器..."
docker-compose up -d

echo ""
echo "[4/5] 等待服务启动..."
sleep 5

echo ""
echo "[5/5] 检查服务状态..."
echo ""
docker-compose ps

echo ""
echo "========================================"
echo "测试后端健康..."
echo "========================================"
echo ""

if curl -s http://localhost:5000/api/health > /dev/null; then
    echo ""
    echo "[成功] 后端健康检查通过!"
else
    echo ""
    echo "[警告] 后端可能还在启动中，请稍等片刻"
fi

echo ""
echo "========================================"
echo "部署完成!"
echo "========================================"
echo ""
echo "前端地址: http://localhost:8888"
echo "后端地址: http://localhost:5000"
echo "涨幅榜分析: http://localhost:8888/gainer-analysis"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f backend"
echo "  停止服务: docker-compose down"
echo "  重启后端: docker-compose restart backend"
echo "  进入容器: docker exec -it quantdinger-backend bash"
echo ""
