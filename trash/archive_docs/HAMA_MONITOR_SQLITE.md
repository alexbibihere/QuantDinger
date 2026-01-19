# HAMA 自动监控 - SQLite 版本

## ✅ 已完成的修改

### 1. 修改 `hama_brave_monitor.py`
- 添加 SQLite 数据库支持
- 优先使用 SQLite,Redis 作为备用
- 数据持久化到本地数据库

### 2. 创建 `auto_hama_monitor_sqlite.py`
- 独立的 SQLite 监控脚本
- 不依赖 MySQL 或 Redis
- 完全本地化运行

## 📋 使用方法

### 方法 1: 使用修改后的监控器 (推荐)

```bash
cd backend_api_python
python auto_hama_monitor_sqlite.py
```

### 方法 2: 使用原有的监控器 (已支持 SQLite)

```bash
cd backend_api_python
python auto_hama_monitor.py
```

## 🗄️ 数据库位置

- **SQLite 数据库**: `backend_api_python/data/quantdinger.db`
- **表名**: `hama_monitor_cache`
- **数据持久化**: 是 (重启不丢失)

## 📊 数据库表结构

```sql
CREATE TABLE hama_monitor_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    hama_trend VARCHAR(10),
    hama_color VARCHAR(10),
    hama_value DECIMAL(20, 8),
    price DECIMAL(20, 8),
    ocr_text TEXT,
    screenshot_path VARCHAR(255),
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 启动步骤

### 1. 重启后端服务

```bash
cd backend_api_python
python run.py
```

### 2. 启动监控脚本

**新开一个终端窗口**:

```bash
cd backend_api_python
python auto_hama_monitor_sqlite.py
```

### 3. 查看前端

访问: http://localhost:8000/#/hama-market

## 📝 监控脚本输出

```
================================================================================
🤖 HAMA 自动监控服务（SQLite 存储）
================================================================================
启动时间: 2026-01-18 15:00:00

📋 配置:
  监控币种: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT
  监控间隔: 600秒 (10分钟)
  浏览器类型: chromium
  存储方式: SQLite 数据库

正在连接 SQLite...
✅ SQLite 连接成功: backend_api_python\data\quantdinger.db
✅ 数据库表初始化成功

正在初始化 Brave 监控器...
✅ OCR 提取器初始化成功
✅ 监控器初始化成功
  当前缓存: 0 个币种

================================================================================
🔄 开始监控循环（按 Ctrl+C 停止）
================================================================================

================================================================================
第 1 轮监控 - 2026-01-18 15:00:05
================================================================================

处理 1/7: BTCUSDT
🔄 正在监控 BTCUSDT...
   正在截图...
   正在 OCR 识别...
✅ BTCUSDT HAMA 数据已保存到 SQLite
   ✅ BTCUSDT HAMA 状态: green (up)

处理 2/7: ETHUSDT
...
```

## 🛠️ 手动测试

### 测试单个币种

```bash
cd backend_api_python

# 运行测试脚本
python test_brave_monitor_simple.py
```

### 查看 SQLite 数据

```bash
sqlite3 backend_api_python/data/quantdinger.db

# 查看所有缓存
SELECT * FROM hama_monitor_cache ORDER BY monitored_at DESC;

# 查看特定币种
SELECT * FROM hama_monitor_cache WHERE symbol='BTCUSDT';

# 查看缓存数量
SELECT COUNT(*) FROM hama_monitor_cache;

# 退出
.quit
```

## 🎯 API 调用

### 获取监控列表

```bash
curl "http://localhost:5000/api/hama-market/watchlist" | python -m json.tool
```

### 预期响应

```json
{
    "success": true,
    "data": {
        "watchlist": [
            {
                "symbol": "BTCUSDT",
                "price": 95159.0,
                "hama_brave": {
                    "hama_trend": "up",
                    "hama_color": "green",
                    "hama_value": 95117.59,
                    "cached_at": "2026-01-18 15:00:10",
                    "cache_source": "sqlite_brave_monitor"
                }
            }
        ]
    }
}
```

## 📌 注意事项

1. **首次监控较慢**: 每个币种需要 20-30 秒 (截图 + OCR)
2. **数据库位置**: `backend_api_python/data/quantdinger.db`
3. **监控间隔**: 默认 10 分钟 (可修改脚本中的 `interval` 变量)
4. **停止监控**: 按 Ctrl+C

## 🔧 故障排查

### 问题1: 监控失败

**检查项**:
- Playwright 是否已安装: `pip install playwright`
- 浏览器是否已安装: `playwright install chromium`
- 网络连接是否正常
- TradingView 是否可访问

### 问题2: 数据库错误

**解决方法**:
```bash
# 删除旧数据库重新初始化
rm backend_api_python/data/quantdinger.db
python init_all_tables.py
```

### 问题3: OCR 识别失败

**检查项**:
- RapidOCR 是否已安装: `pip install rapidocr-onnxruntime`
- 截图是否正常: 检查 screenshot 目录

## 🎉 完成

监控脚本将:
- ✅ 自动监控指定币种
- ✅ 保存数据到 SQLite 数据库
- ✅ 定期刷新 (默认 10 分钟)
- ✅ 数据持久化,重启不丢失

---

**最后更新**: 2026-01-18
**版本**: SQLite 版本
**状态**: ✅ 完成
