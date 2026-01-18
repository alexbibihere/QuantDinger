# Redis 和 Brave 监控配置说明

## 更新时间
2026-01-18 03:58

## ✅ 已完成的配置

### 1. Redis 配置

**文件**: `backend_api_python/.env`

```bash
# Redis连接配置
REDIS_HOST=host.docker.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

**说明**: 使用 `host.docker.internal` 让 Docker 容器可以访问宿主机上的 Redis

### 2. 创建了 `hama_brave_monitor.py`

**文件**: `backend_api_python/app/services/hama_brave_monitor.py`

**功能**:
- 包装 `hama_ocr_extractor.py` 提供统一接口
- 支持 Redis 缓存
- 支持批量监控
- 支持后台持续监控

**主要方法**:
```python
get_brave_monitor(redis_client, cache_ttl)  # 获取单例
monitor_symbol(symbol, browser_type)        # 监控单个币种
monitor_batch(symbols, browser_type)        # 批量监控
start_monitoring(symbols, interval, browser_type)  # 启动持续监控
stop_monitoring()                           # 停止监控
get_stats()                                 # 获取统计信息
get_cached_symbols()                        # 获取已缓存币种列表
```

### 3. 更新了 `hama_market.py`

**变更**:
- 添加了 try-except 处理 `hama_brave_monitor` 导入失败
- `/api/hama-market/watchlist` 改为仅返回 Brave 监控数据
- 移除了所有本地计算的 HAMA 数据

## 🔧 待完成的步骤

### 步骤 1: 启动本地 Redis

在 Windows 上启动 Redis 服务：

**方案 A: 使用 Docker（推荐）**
```powershell
# 启动 Redis 容器
docker run -d --name quantdinger-redis -p 127.0.0.1:6379:6379 redis:7-alpine redis-server --appendonly yes

# 验证 Redis 运行
docker ps | findstr redis
```

**方案 B: 使用 Windows 安装版**
```powershell
# 如果已安装 Redis for Windows
redis-server.exe

# 或注册为 Windows 服务
redis-server.exe --service-start
```

### 步骤 2: 安装 Playwright 浏览器（Docker 容器中）

在 Docker 容器中安装 Playwright 浏览器：

```bash
# 进入后端容器
docker exec -it quantdinger-backend bash

# 安装 Playwright 浏览器
playwright install chromium

# 或安装所有浏览器
playwright install

# 安装系统依赖
playwright install-deps chromium
```

**或者修改 Dockerfile 自动安装**:
```dockerfile
# backend_api_python/Dockerfile

# 安装 Playwright 浏览器
RUN playwright install chromium
RUN playwright install-deps chromium
```

然后重新构建：
```bash
docker-compose build backend
docker-compose up -d backend
```

### 步骤 3: 验证配置

```bash
# 1. 检查后端健康状态
curl http://localhost:5000/api/health

# 2. 检查 Brave 监控状态
curl http://localhost:5000/api/hama-market/brave/status

# 3. 查询 HAMA 行情列表
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT,ETHUSDT"
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "available": true,
    "cached_symbols": 0,
    "cache_ttl_seconds": 900,
    "is_monitoring": true
  }
}
```

## 📊 数据流程

```
用户访问前端
    ↓
前端调用 /api/hama-market/watchlist
    ↓
后端从 Redis 读取缓存数据
    ↓
    ├─ 有缓存 → 直接返回
    └─ 无缓存 → 返回 hama_brave: null
    ↓
Brave 监控线程（后台运行）
    ↓
每隔 600 秒（10分钟）自动监控：
    ├─→ 使用 Playwright 访问 TradingView
    ├─→ 截图 HAMA 面板
    ├─→ 使用 RapidOCR 识别
    ├─→ 保存到 Redis（TTL=900秒）
    └─→ 继续下一个币种
```

## 🎯 简化方案（推荐用于测试）

如果 Playwright + OCR 配置太复杂，可以使用简化的本地计算方案：

### 选项 1: 使用本地 HAMA 计算

修改 `hama_market.py` 中的 `watchlist` 接口，添加本地计算作为后备：

```python
# 如果没有 Brave 监控数据，使用本地计算
if not brave_hama:
    # 本地计算 HAMA
    kline_data = kline_service.get_kline(...)
    hama_result = calculate_hama_from_ohlcv(ohlcv_data)
    # 添加到 watchlist
```

### 选项 2: 使用演示模式

```bash
# 编辑 backend_api_python/.env
HAMA_DEMO_MODE=true

# 重启后端
docker-compose restart backend
```

## 🔍 故障排查

### 问题 1: "Brave 监控器未初始化"

**原因**: `hama_brave_monitor` 导入失败

**检查**:
```bash
# 检查文件是否存在
ls backend_api_python/app/services/hama_brave_monitor.py

# 检查导入是否成功
docker exec quantdinger-backend python -c "from app.services.hama_brave_monitor import get_brave_monitor; print('OK')"
```

### 问题 2: Redis 连接失败

**原因**: Redis 未启动或配置错误

**检查**:
```bash
# 测试 Redis 连接
docker exec quantdinger-redis redis-cli ping

# 检查端口
netstat -ano | findstr :6379
```

### 问题 3: Playwright 浏览器未安装

**原因**: Docker 容器中缺少浏览器

**解决**:
```bash
# 进入容器
docker exec -it quantdinger-backend bash

# 安装浏览器
playwright install chromium
```

## 📝 下一步建议

### 立即可做：

1. **启动 Redis** - 最简单的步骤
```powershell
docker run -d --name quantdinger-redis -p 127.0.0.1:6379:6379 redis:7-alpine redis-server --appendonly yes
```

2. **重启后端**
```bash
docker-compose restart backend
```

3. **测试 API**
```bash
curl http://localhost:5000/api/hama-market/brave/status
```

### 后续优化：

1. 在 Dockerfile 中添加 Playwright 浏览器安装
2. 添加错误处理，当 Brave 监控失败时降级到本地计算
3. 添加更多的监控指标和日志

---

**当前状态**: 代码已更新，等待 Redis 和 Playwright 环境配置完成
