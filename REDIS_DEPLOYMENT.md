# Redis Docker 部署指南

## 快速开始

### 1. 启动所有服务 (推荐)

```bash
cd d:\github\QuantDinger
docker-compose up -d
```

这将启动:
- **Redis** (缓存服务)
- **Backend** (Python API, 连接 Redis)
- **Frontend** (Vue Web UI)

### 2. 验证服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 预期输出:
# NAME                   STATUS          PORTS
# quantdinger-redis      Up (healthy)     127.0.0.1:6379->6379/tcp
# quantdinger-backend    Up (healthy)     127.0.0.1:5000->5000/tcp
# quantdinger-frontend   Up (healthy)     0.0.0.0:8888->80/tcp
```

### 3. 测试 Redis 连接

```bash
# 连接到 Redis 容器
docker exec -it quantdinger-redis redis-cli

# 测试命令
> PING
# 应该返回: PONG

# 查看 HAMA 缓存
> KEYS hama:analysis:*
# 应该显示所有已缓存的币种

# 退出
> exit
```

### 4. 测试后端连接

```bash
# 查看后端日志
docker-compose logs backend | grep -i redis

# 预期看到:
# "连接Redis: redis:6379"
# "Redis连接成功"
# "HAMA调度器初始化完成"
```

### 5. 验证定时任务

```bash
# 查看定时任务状态
curl http://localhost:5000/api/gainer-analysis/scheduler/status

# 预期返回:
# {
#   "code": 1,
#   "data": {
#     "running": true,
#     "symbols_count": 78,
#     "interval_minutes": 5,
#     "cache_stats": {
#       "available": true,
#       "cached_symbols": 78
#     }
#   }
# }
```

## 单独启动 Redis (如果需要)

### 只启动 Redis

```bash
docker-compose up -d redis
```

### 验证 Redis

```bash
# 检查容器
docker ps | grep redis

# 测试连接
docker exec -it quantdinger-redis redis-cli ping
```

## 常用命令

### 查看日志

```bash
# Redis 日志
docker-compose logs -f redis

# 后端日志 (包含 Redis 连接信息)
docker-compose logs -f backend | grep -i redis
```

### 重启服务

```bash
# 重启 Redis
docker-compose restart redis

# 重启后端 (会自动重连 Redis)
docker-compose restart backend

# 重启所有服务
docker-compose restart
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷 (⚠️ 会清空 Redis 数据)
docker-compose down -v
```

### 清理 Redis 缓存

```bash
# 方法1: 通过 Redis CLI
docker exec -it quantdinger-redis redis-cli
> FLUSHDB
> exit

# 方法2: 重启 Redis (数据会丢失但重新开始)
docker-compose restart redis
```

## 配置说明

### Docker Compose 配置

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: quantdinger-redis
    ports:
      - "127.0.0.1:6379:6379"  # 仅本地访问
    volumes:
      - redis-data:/data       # 持久化数据
    command: redis-server --appendonly yes  # AOF 持久化
```

### 后端环境变量

```bash
# .env 或 docker-compose.yml
REDIS_ENABLED=true              # 启用 Redis
REDIS_HOST=redis                # Redis 主机 (容器名)
REDIS_PORT=6379                 # Redis 端口
HAMA_SCHEDULER_ENABLED=true     # 启用定时任务
HAMA_SCHEDULER_AUTO_START=true  # 自动启动定时任务
HAMA_SCHEDULER_INTERVAL=5       # 刷新间隔(分钟)
HAMA_CACHE_TTL=300              # 缓存过期时间(秒)
```

## 故障排查

### 问题1: Redis 容器未启动

**症状**: `docker-compose ps` 看不到 quantdinger-redis

**解决方案**:
```bash
# 查看日志
docker-compose logs redis

# 重新创建容器
docker-compose up -d --force-recreate redis
```

### 问题2: 后端无法连接 Redis

**症状**: 后端日志显示 "Redis连接失败,将使用内存缓存"

**解决方案**:
```bash
# 1. 确保 Redis 运行
docker-compose ps redis

# 2. 检查网络
docker network inspect quantdinger-network

# 3. 重启后端 (会重连)
docker-compose restart backend
```

### 问题3: 数据丢失

**症状**: 重启后缓存数据为空

**原因**: 默认使用 AOF 持久化,但如果未正确关闭可能丢失数据

**解决方案**:
```bash
# 1. 检查持久化文件
docker exec quantdinger-redis ls -la /data/

# 2. 应该看到 appendonly.aof 文件

# 3. 如果没有,启用持久化
# 编辑 docker-compose.yml,确保有:
command: redis-server --appendonly yes

# 4. 重新创建容器
docker-compose up -d --force-recreate redis
```

### 问题4: 内存不足

**症状**: Redis 容器频繁重启

**解决方案**:
```bash
# 限制 Redis 内存
# 编辑 docker-compose.yml:
services:
  redis:
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

# 重启 Redis
docker-compose up -d --force-recreate redis
```

## 性能优化

### Redis 配置优化

```yaml
services:
  redis:
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
```

参数说明:
- `--maxmemory 512mb`: 最大内存 512MB
- `--maxmemory-policy allkeys-lru`: 内存满时删除最少使用的键
- `--save 900 1`: 900秒内至少1个key变化则保存
- `--save 300 10`: 300秒内至少10个key变化则保存
- `--save 60 10000`: 60秒内至少10000个key变化则保存

### 监控 Redis

```bash
# 查看 Redis 信息
docker exec quantdinger-redis redis-cli INFO

# 查看内存使用
docker exec quantdinger-redis redis-cli INFO memory

# 查看统计信息
docker exec quantdinger-redis redis-cli INFO stats

# 实时监控
docker exec quantdinger-redis redis-cli --stat
```

## 数据备份

### 备份 Redis 数据

```bash
# 创建备份目录
mkdir -p backups/redis

# 备份
docker exec quantdinger-redis redis-cli SAVE
docker cp quantdinger-redis:/data/dump.rdb backups/redis/dump_$(date +%Y%m%d).rdb
docker cp quantdinger-redis:/data/appendonly.aof backups/redis/aof_$(date +%Y%m%d).aof
```

### 恢复 Redis 数据

```bash
# 停止 Redis
docker-compose stop redis

# 恢复数据
docker cp backups/redis/dump_20260110.rdb quantdinger-redis:/data/dump.rdb

# 启动 Redis
docker-compose start redis
```

## 总结

✅ **Redis 已集成到 docker-compose**
✅ **自动持久化数据** (AOF 模式)
✅ **后端自动连接** (降级机制)
✅ **定时任务自动启动** (5分钟刷新)

### 关键点

1. **端口**: Redis 仅监听 127.0.0.1:6379 (安全)
2. **持久化**: 使用 AOF 模式,数据保存在 /data
3. **网络**: 所有服务在 quantdinger-network 网络
4. **降级**: Redis 不可用时自动使用内存缓存

### 下一步

- 访问 http://localhost:8888 查看 TradingView Scanner
- 查看 HAMA 分析结果 (从 Redis 缓存读取)
- 监控定时任务日志: `docker-compose logs backend | grep HAMA`
