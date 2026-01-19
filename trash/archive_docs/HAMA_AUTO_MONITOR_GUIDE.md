# HAMA 自动监控服务 - 使用指南

## 🎯 概述

HAMA 自动监控服务可以：
- ✅ 每 10 分钟自动监控 7 个币种
- ✅ 从 TradingView 获取真实的 HAMA 指标数据
- ✅ 自动保存到 Redis 缓存
- ✅ 前端随时从 Redis 读取最新数据

---

## 🚀 快速启动

### 方法 1: 使用启动脚本（推荐）

双击运行：
```
start_hama_monitor.bat
```

### 方法 2: 手动启动

```bash
cd backend_api_python
python auto_hama_monitor.py
```

---

## 📋 配置说明

### 监控配置

```python
# auto_hama_monitor.py 中的配置

symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT']
interval = 600  # 10分钟（秒）
browser_type = 'chromium'
```

### 修改监控币种

编辑 `auto_hama_monitor.py`：

```python
# 添加或删除币种
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']  # 只监控 4 个

# 修改监控间隔（5分钟）
interval = 300
```

### 修改浏览器类型

```python
# 可选: 'chromium', 'firefox', 'webkit'
browser_type = 'chromium'  # 默认
```

---

## 🔄 工作流程

```
启动监控
    ↓
第 1 轮监控开始
    ├─→ BTCUSDT: 访问 → 截图 → OCR → 缓存到 Redis ✅
    ├─→ ETHUSDT: 访问 → 截图 → OCR → 缓存到 Redis ✅
    ├─→ BNBUSDT: 访问 → 截图 → OCR → 缓存到 Redis ✅
    └─→ ... (继续其他币种)
    ↓
等待 600 秒（10分钟）
    ↓
第 2 轮监控开始
    └─→ 重复上述流程
```

---

## 📊 输出示例

```
================================================================================
第 1 轮监控 - 2026-01-18 07:00:00
================================================================================

📊 本轮结果:
  总数: 7
  成功: 6
  失败: 1

✅ 成功的币种:
  - BTCUSDT: up / green
  - ETHUSDT: down / red
  - BNBUSDT: up / green
  - SOLUSDT: neutral / unknown
  - XRPUSDT: up / green
  - ADAUSDT: down / red

💾 Redis 缓存: 6 个币种

⏰ 等待 600 秒后进行下一轮...
   (当前时间: 07:02:00)
   (下一轮: 07:12:00)
```

---

## 🔧 Redis 配置

### 启动 Redis（可选但推荐）

```bash
docker run -d --name quantdinger-redis -p 127.0.0.1:6379:6379 redis:7-alpine redis-server --appendonly yes
```

### 验证 Redis

```bash
# 检查 Redis 运行
docker ps | findstr redis

# 测试连接
docker exec quantdinger-redis redis-cli ping
# 应返回: PONG

# 查看缓存数据
docker exec quantdinger-redis redis-cli KEYS "hama:brave:*"
```

### 查看 Redis 缓存

```bash
# 查看 BTCUSDT 的缓存
docker exec quantdinger-redis redis-cli GET "hama:brave:BTCUSDT"

# 查看所有缓存币种
docker exec quantdinger-redis redis-cli KEYS "hama:brave:*"
```

---

## 🌐 前端访问

### 访问 HAMA 行情页面

打开浏览器访问：
```
http://localhost:8000/#/hama-market
```

### API 访问

```bash
# 查看监控状态
curl http://localhost:5000/api/hama-market/brave/status

# 获取行情列表（从 Redis 读取）
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT,ETHUSDT"

# 手动触发一次监控
curl -X POST http://localhost:5000/api/hama-market/brave/monitor \
  -H "Content-Type: application/json" \
  -d '{"symbols":["BTCUSDT"],"browser_type":"chromium"}'
```

---

## 🛑 停止监控

在监控窗口中按 `Ctrl + C`

```
⏸️  监控已停止
================================================================================
停止时间: 2026-01-18 08:00:00
总轮数: 6

缓存币种: 6
  BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT
```

---

## 🔍 故障排查

### 问题 1: "Redis 连接失败"

**解决方案**:
```bash
# 启动 Redis
docker run -d --name quantdinger-redis -p 127.0.0.1:6379:6379 redis:7-alpine redis-server --appendonly yes

# 重启监控
```

### 问题 2: "OCR 识别失败"

**可能原因**:
- TradingView 页面加载慢
- 网络连接问题
- Cookie 过期

**解决方案**:
1. 检查网络连接
2. 更新 `tradingview_cookies.json`
3. 增加超时时间

### 问题 3: "浏览器无法启动"

**解决方案**:
```bash
# 重新安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium
```

### 问题 4: "识别结果不准确"

**解决方案**:
1. 查看保存的截图文件
2. 确认 HAMA 指标是否在图表上
3. 调整截图位置
4. 使用本地计算作为主要数据源

---

## 📈 性能优化

### 调整监控间隔

```python
# 快速模式（5分钟）
interval = 300

# 标准模式（10分钟）- 推荐
interval = 600

# 节能模式（15分钟）
interval = 900
```

### 减少监控币种

```python
# 只监控主要币种
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
```

---

## 🎯 最佳实践

### 推荐配置

**本地开发**:
```python
symbols = ['BTCUSDT', 'ETHUSDT']  # 只测试 2 个
interval = 300  # 5分钟，快速测试
```

**生产环境**:
```python
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT']
interval = 600  # 10分钟
```

### 混合方案

```
主要数据源: 本地计算（2-5秒，快速准确）
  ↓
定期验证: Brave 监控（每10分钟，确保准确性）
  ↓
数据缓存: Redis（900秒，减少重复计算）
```

---

## 📝 相关文件

- `auto_hama_monitor.py` - 自动监控脚本
- `start_hama_monitor.bat` - 启动脚本
- `test_tv_with_cookie.py` - 测试脚本
- `tradingview_cookies.json` - TradingView Cookie
- `hama_brave_monitor.py` - 监控器核心代码
- `hama_ocr_extractor.py` - OCR 提取器

---

## 🎉 总结

### ✅ 优势

1. **自动化** - 无需手动操作，自动定期监控
2. **真实数据** - 直接从 TradingView 获取
3. **Redis 缓存** - 前端随时获取最新数据
4. **灵活配置** - 可调整币种、间隔等

### ⚠️ 注意事项

1. **网络依赖** - 需要稳定的网络连接
2. **资源占用** - 运行浏览器需要一定资源
3. **Cookie 有效期** - 需要定期更新 Cookie

### 🚀 立即开始

```bash
# 1. 双击启动
start_hama_monitor.bat

# 2. 访问前端
http://localhost:8000/#/hama-market

# 3. 查看数据
# 数据会每 10 分钟自动更新
```

---

**开始使用吧！** 🚀
