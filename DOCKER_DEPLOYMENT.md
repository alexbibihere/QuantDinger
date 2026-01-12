# 🚀 QuantDinger Docker 部署指南 - 涨幅榜分析功能

## 📋 部署前准备

### 1. 检查环境变量配置

确保 `backend_api_python/.env` 文件配置正确:

```bash
# 必需配置
SECRET_KEY=your-secret-key-here
ADMIN_USER=quantdinger
ADMIN_PASSWORD=123456

# AI 配置 (可选,用于其他功能)
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=openai/gpt-4o

# 数据源配置
CCXT_DEFAULT_EXCHANGE=okx  # 或 binance

# 代理配置 (推荐,提高数据获取成功率)
PROXY_PORT=7890
# 或使用完整 URL
# PROXY_URL=socks5h://127.0.0.1:7890

# 数据库
SQLITE_DATABASE_FILE=/app/data/quantdinger.db
```

### 2. 检查依赖

确认 `backend_api_python/requirements.txt` 包含以下依赖:

```
Flask==2.3.3
flask-cors==4.0.0
ccxt>=4.0.0
numpy>=1.24.0
pandas>=1.5.0
requests>=2.28.0
PySocks>=1.7.1
SQLAlchemy>=2.0.0
PyJWT==2.8.0
python-dotenv>=1.0.1
```

## 🐳 Docker 部署步骤

### 方式 1: 完整重建部署 (推荐)

```bash
# 1. 停止并删除旧容器
docker-compose down

# 2. 重新构建并启动
docker-compose up -d --build

# 3. 查看日志
docker-compose logs -f backend
```

### 方式 2: 快速重启

```bash
# 1. 停止容器
docker-compose down

# 2. 启动容器 (使用缓存)
docker-compose up -d

# 3. 查看运行状态
docker-compose ps
```

### 方式 3: 仅重启后端

```bash
# 1. 停止后端容器
docker-compose stop backend

# 2. 删除后端容器
docker-compose rm -f backend

# 3. 重新构建并启动
docker-compose up -d --build backend

# 4. 查看日志
docker-compose logs -f backend
```

## 📊 验证部署

### 1. 检查容器状态

```bash
docker-compose ps
```

应该看到:
```
NAME                      STATUS
quantdinger-backend       Up (healthy)
quantdinger-frontend      Up (healthy)
```

### 2. 检查后端健康

```bash
curl http://localhost:5000/api/health
```

应该返回:
```json
{"status":"healthy","timestamp":"2025-01-09T..."}
```

### 3. 检查前端

访问: `http://localhost:8888`

应该看到 QuantDinger 登录页面

### 4. 测试涨幅榜 API

```bash
curl "http://localhost:5000/api/gainer-analysis/top-gainers?limit=3"
```

应该返回 JSON 数据

## 🔍 常见问题排查

### 问题 1: 容器启动失败

**检查步骤**:
```bash
# 查看详细日志
docker-compose logs backend

# 检查配置文件
cat backend_api_python/.env
```

**常见原因**:
- .env 文件不存在或配置错误
- 端口 5000 或 8888 被占用
- 依赖安装失败

**解决方法**:
```bash
# 重建镜像
docker-compose build --no-cache backend
docker-compose up -d
```

### 问题 2: API 返回 404

**原因**: 后端未正确加载新的 blueprint

**解决方法**:
```bash
# 完全重启
docker-compose down
docker-compose up -d --build
```

### 问题 3: TradingView 数据获取失败

**检查网络**:
```bash
# 进入容器检查
docker exec -it quantdinger-backend bash

# 测试网络连接
curl -I https://scanner.tradingview.com
```

**解决方法**:
- 配置代理 (在 .env 中设置 PROXY_PORT)
- 系统会自动降级到模拟数据

### 问题 4: 数据库文件权限错误

**解决方法**:
```bash
# 修复权限
chmod 666 backend_api_python/data/quantdinger.db
chmod 777 backend_api_python/data
chmod 777 backend_api_python/logs
```

## 📈 性能优化

### 1. 使用 Redis 缓存 (可选)

编辑 `docker-compose.yml`,添加:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: quantdinger-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - quantdinger-network

  backend:
    # ... 其他配置
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

### 2. 调整资源限制

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🔄 更新部署

### 当代码更新后

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并启动
docker-compose down
docker-compose up -d --build

# 3. 查看日志确认启动成功
docker-compose logs -f backend
```

### 仅更新依赖

```bash
# 1. 更新 requirements.txt

# 2. 重新构建镜像
docker-compose build --no-cache backend

# 3. 重启
docker-compose up -d backend
```

## 📊 监控和日志

### 查看实时日志

```bash
# 后端日志
docker-compose logs -f backend

# 前端日志
docker-compose logs -f frontend

# 所有服务
docker-compose logs -f
```

### 查看容器资源使用

```bash
docker stats quantdinger-backend quantdinger-frontend
```

### 导出日志

```bash
# 导出后端日志
docker-compose logs backend > backend_logs.txt

# 导出最近100行
docker-compose logs --tail=100 backend > recent_logs.txt
```

## 🧪 功能测试

### 1. 运行算法测试 (无需后端)

```bash
python test_hama_algorithm.py
```

### 2. 运行完整功能测试 (需要后端)

```bash
python test_hama_real_data.py
```

### 3. 手动测试 API

```bash
# 登录
curl -X POST http://localhost:5000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"quantdinger","password":"123456"}'

# 获取涨幅榜
curl "http://localhost:5000/api/gainer-analysis/top-gainers?limit=5"

# 分析单币种
curl -X POST http://localhost:5000/api/gainer-analysis/analyze-symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT"}'
```

## 🔧 维护命令

### 备份数据

```bash
# 备份数据库
cp backend_api_python/data/quantdinger.db backup/quantdinger_$(date +%Y%m%d).db

# 备份配置
cp backend_api_python/.env backup/.env_$(date +%Y%m%d)
```

### 清理系统

```bash
# 停止所有容器
docker-compose down

# 删除所有容器和卷
docker-compose down -v

# 删除未使用的镜像
docker image prune -a

# 删除未使用的卷
docker volume prune
```

## 🌐 生产环境建议

### 1. 使用反向代理

推荐使用 Nginx 或 Caddy:

```nginx
# Caddyfile example
localhost:8888 {
    reverse_proxy frontend:80
}

api.example.com {
    reverse_proxy backend:5000
}
```

### 2. 配置 HTTPS

```bash
# 使用 Let's Encrypt
caddy run --config /etc/caddy/Caddyfile
```

### 3. 安全加固

```bash
# 修改默认密码
# 在 .env 中设置强密码
ADMIN_PASSWORD=your-strong-password

# 修改 SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
```

### 4. 定期备份

```bash
# 添加到 crontab
0 2 * * * cp /path/to/data/quantdinger.db /backup/quantdinger_$(date +\%Y\%m\%d).db
```

## 📞 获取帮助

### 查看文档

- [GAINER_ANALYSIS_QUICK_START.md](GAINER_ANALYSIS_QUICK_START.md) - 快速开始
- [GAINER_ANALYSIS_COMPLETE.md](GAINER_ANALYSIS_COMPLETE.md) - 完整功能说明
- [HAMA_IMPLEMENTATION.md](HAMA_IMPLEMENTATION.md) - 技术实现

### 检查日志

```bash
# 查看应用日志
tail -f backend_api_python/logs/app.log

# 查看 Docker 日志
docker-compose logs -f backend
```

### 常用命令速查

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 进入容器
docker exec -it quantdinger-backend bash

# 重建
docker-compose up -d --build
```

## ✅ 部署检查清单

部署前检查:

- [ ] .env 文件已配置
- [ ] requirements.txt 包含 numpy
- [ ] 端口 5000 和 8888 未被占用
- [ ] Docker 和 Docker Compose 已安装
- [ ] 网络连接正常 (或已配置代理)

部署后验证:

- [ ] 容器状态为 Up (healthy)
- [ ] 后端健康检查通过
- [ ] 前端页面可访问
- [ ] 可以正常登录
- [ ] 涨幅榜页面可访问 (/gainer-analysis)
- [ ] API 测试通过

## 🎉 完成部署

一切就绪! 访问 `http://localhost:8888/gainer-analysis` 开始使用涨幅榜分析功能!

**提示**: 首次加载数据可能需要 10-30 秒,请耐心等待。
