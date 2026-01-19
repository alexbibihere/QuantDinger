# ✅ HAMA 监控器集成到后端服务

## 集成方案

### 1. 后端启动时自动启动监控 ✅

**修改文件**: [`app/__init__.py`](backend_api_python/app/__init__.py)

```python
# 在后端启动时自动启动 HAMA 监控 Worker
enable_hama_worker = os.getenv('ENABLE_HAMA_WORKER', 'true').lower() == 'true'
if enable_hama_worker and _hama_brave_monitor:
    from app.services.hama_monitor_worker import get_hama_monitor_worker
    worker = get_hama_monitor_worker()
    worker.start()  # 启动后台监控线程
```

### 2. 监控 Worker 功能

**文件**: [`app/services/hama_monitor_worker.py`](backend_api_python/app/services/hama_monitor_worker.py)

**功能**:
- ✅ 后端启动时自动运行
- ✅ 每隔 10 分钟自动监控
- ✅ 数据保存到 SQLite 数据库
- ✅ API 可以查看状态和手动触发

### 3. API 端点

**新增端点**:

1. **查看 Worker 状态**
```bash
curl "http://localhost:5000/api/hama-market/worker/status"
```

2. **手动触发监控** (立即监控)
```bash
curl -X POST "http://localhost:5000/api/hama-market/worker/monitor" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT"]}'
```

3. **停止/启动 Worker**
```bash
# 停止
curl -X POST "http://localhost:5000/api/hama-market/worker/stop"

# 启动
curl -X POST "http://localhost:5000/api/hama-market/worker/start"
```

## 🚀 使用方式

### 方式 1: 自动监控 (推荐)

**后端启动时自动运行**,无需任何操作:

1. 启动后端
```bash
cd backend_api_python
python run.py
```

2. Worker 自动启动
   - 等待 30 秒让后端完全启动
   - 开始第一轮监控 (约 2-3 分钟)
   - 之后每 10 分钟自动刷新

### 方式 2: 手动触发监控

**通过 API 立即监控**:

```bash
# 前端调用
curl -X POST "http://localhost:5000/api/hama-market/worker/monitor" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]}'
```

或在前端点击"刷新 Brave 监控"按钮

## 📊 数据流程

```
后端启动
    ↓
Worker 自动启动 (后台线程)
    ↓
等待 30 秒 (后端完全启动)
    ↓
第 1 轮监控 (2-3 分钟)
    ├─ BTCUSDT (20-30秒)
    ├─ ETHUSDT (20-30秒)
    ├─ ...
    └─ 保存到 SQLite
    ↓
等待 10 分钟
    ↓
第 2 轮监控 (自动循环)
    ↓
...每 10 分钟重复...
```

## 🎯 数据获取时机

### 自动监控
- **时机**: 每 10 分钟自动
- **触发**: 后台 Worker 自动执行
- **币种**: 7 个默认币种

### 手动触发
- **时机**: 用户主动点击
- **触发**: API 调用或前端按钮
- **币种**: 可指定任意币种

### 前端刷新
- **时机**: 用户访问 HAMA 行情页面
- **触发**: API 调用 `/api/hama-market/watchlist`
- **数据源**: 从 SQLite 数据库读取

## 📋 配置

### 环境变量

在 `backend_api_python/.env` 中配置:

```bash
# 启用 HAMA 监控 Worker
ENABLE_HAMA_WORKER=true

# 监控间隔 (秒)
BRAVE_MONITOR_INTERVAL=600

# 监控币种列表
BRAVE_MONITOR_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT

# 浏览器类型
BRAVE_MONITOR_BROWSER_TYPE=chromium
```

## 🔄 使修改生效

**请重启后端服务**:

```bash
cd backend_api_python
python run.py
```

启动后你会看到:

```
✅ HAMA 监控 Worker 已启动 (后台自动监控)
```

30 秒后会看到:

```
🚀 HAMA 监控 Worker 开始运行
============================================================
第 1 轮监控 - 2026-01-18 15:00:00
============================================================
处理 1/7: BTCUSDT
  ✅ BTCUSDT: red (down)
...
```

## 💡 优势

1. **完全自动化**: 后端启动即运行,无需手动干预
2. **数据持久化**: 保存到 SQLite,重启不丢失
3. **灵活可控**: 可通过 API 随时查看状态或手动触发
4. **资源高效**: 后台线程运行,不阻塞主服务
5. **定时刷新**: 每 10 分钟自动更新数据

## 📝 验证步骤

1. **重启后端**
   ```bash
   python run.py
   ```

2. **查看日志**
   ```bash
   tail -f logs/app.log | grep -i "hama\|worker"
   ```

3. **测试 API**
   ```bash
   # 查看 Worker 状态
   curl "http://localhost:5000/api/hama-market/worker/status"

   # 查看行情数据
   curl "http://localhost:5000/api/hama-market/watchlist"
   ```

4. **访问前端**
   http://localhost:8000/#/hama-market

---

**集成状态**: ✅ 完成
**等待**: 重启后端服务
**最后更新**: 2026-01-18
