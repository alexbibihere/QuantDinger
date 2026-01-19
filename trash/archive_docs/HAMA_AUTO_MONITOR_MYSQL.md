# HAMA 自动监控 - MySQL 数据库方案

## 🎯 方案概述

使用 **MySQL 数据库**存储 HAMA 监控数据，替代 Redis 缓存方案。

---

## ✅ 为什么选择 MySQL？

### 优势

1. ✅ **已配置** - 您已经有 MySQL 配置
2. ✅ **持久化** - 数据永久保存，重启不丢失
3. ✅ **查询方便** - SQL 查询，支持复杂分析
4. ✅ **统一管理** - 与其他表在同一个数据库
5. ✅ **性能足够** - 毫秒级响应，对于 HAMA 数据完全够用
6. ✅ **扩展性好** - 轻松添加字段、索引
7. ✅ **数据分析** - 可以做历史数据分析

### 对比

| 特性 | MySQL | Redis |
|------|-------|-------|
| 持久化 | ✅ 是 | ⚠️ 需配置 |
| 已配置 | ✅ 是 | ❌ 否 |
| SQL 查询 | ✅ 是 | ❌ 否 |
| 服务数量 | ✅ 1个 | ⚠️ 2个（MySQL + Redis） |
| 速度 | ✅ ~1ms | ✅ ~0.1ms |

---

## 📋 数据库表结构

### hama_monitor_cache（当前缓存）

```sql
CREATE TABLE hama_monitor_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,           -- 币种
    hama_trend VARCHAR(10),                 -- 趋势 (up/down/neutral)
    hama_color VARCHAR(10),                 -- 颜色 (green/red/unknown)
    hama_value DECIMAL(20, 8),              -- HAMA 数值
    price DECIMAL(20, 8),                    -- 当前价格
    ocr_text TEXT,                          -- OCR 原始文本
    screenshot_path VARCHAR(255),           -- 截图路径
    monitored_at TIMESTAMP,                  -- 监控时间
    created_at TIMESTAMP,                    -- 创建时间
    updated_at TIMESTAMP,                    -- 更新时间
    UNIQUE KEY (symbol)                    -- 每个币种唯一
);
```

### hama_monitor_history（可选，历史数据）

```sql
CREATE TABLE hama_monitor_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    hama_trend VARCHAR(10),
    hama_color VARCHAR(10),
    hama_value DECIMAL(20, 8),
    price DECIMAL(20, 8),
    monitored_at TIMESTAMP,
    INDEX (symbol, monitored_at)
);
```

---

## 🚀 快速开始

### 第 1 步：初始化数据库

```bash
# 方式 1: 手动执行 SQL
mysql -u quantdinger -p quantdinger < backend_api_python/sql/hama_monitor_schema.sql

# 方式 2: 使用后端自动创建（推荐）
# 后端会在首次启动时自动创建表
```

### 第 2 步：启动自动监控

```bash
# 双击运行
start_hama_monitor.bat

# 或手动运行
cd backend_api_python
python auto_hama_monitor_mysql.py
```

### 第 3 步：查看数据

```sql
-- 查询所有缓存
SELECT * FROM hama_monitor_cache ORDER BY monitored_at DESC;

-- 查询特定币种
SELECT * FROM hama_monitor_cache WHERE symbol = 'BTCUSDT';

-- 统计绿色趋势币种
SELECT COUNT(*) FROM hama_monitor_cache WHERE hama_color = 'green';
```

---

## 📊 使用示例

### 后端 API 集成

修改 `hama_market.py` 使用 MySQL 版本监控器：

```python
from app.services.hama_brave_monitor_mysql import HamaBraveMonitor

# 获取监控器
monitor = get_brave_monitor(db_client, cache_ttl=900)

# 查询缓存
hama_data = monitor.get_cached_hama('BTCUSDT')

# 监控单个币种
result = monitor.monitor_symbol('ETHUSDT')
```

### 查询最新数据

```python
# 从数据库查询最新数据
def get_latest_hama():
    cursor = db_client.execute("""
        SELECT symbol, hama_trend, hama_color, hama_value, price, monitored_at
        FROM hama_monitor_cache
        ORDER BY monitored_at DESC
    """)

    results = cursor.fetchall()
    return results
```

---

## 🔄 工作流程

```
启动监控
    ↓
第 1 轮（7 个币种）
    ├─ BTCUSDT → 截图 → OCR → 保存到 MySQL ✅
    ├─ ETHUSDT → 截图 → OCR → 保存到 MySQL ✅
    ├─ BNBUSDT → 截图 → OCR → 保存到 MySQL ✅
    └─ ... (继续 4 个币种)
    ↓
等待 10 分钟
    ↓
第 2 轮（覆盖更新）
    └─ 使用 INSERT ... ON DUPLICATE KEY UPDATE
    ↓
前端随时从 MySQL 读取
```

---

## 🗄️ 数据管理

### 清理旧数据

```sql
-- 删除 7 天前的历史数据
DELETE FROM hama_monitor_history
WHERE monitored_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

### 导出数据

```sql
-- 导出为 CSV
SELECT * FROM hama_monitor_cache
INTO OUTFILE '/tmp/hama_cache.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

### 数据分析

```sql
-- 统计各币种的颜色分布
SELECT
    symbol,
    hama_color,
    COUNT(*) as count,
    MAX(monitored_at) as last_monitored
FROM hama_monitor_history
WHERE monitored_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY symbol, hama_color
ORDER BY symbol, count DESC;
```

---

## 🎯 API 访问

### 获取监控状态

```bash
curl http://localhost:5000/api/hama-market/brave/status
```

响应：
```json
{
  "success": true,
  "data": {
    "available": true,
    "cached_symbols": 7,
    "cache_ttl_seconds": 900,
    "is_monitoring": true,
    "storage_type": "MySQL"
  }
}
```

### 获取行情列表

```bash
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT,ETHUSDT"
```

---

## 📝 配置修改

### 修改监控间隔

编辑 `auto_hama_monitor_mysql.py`：

```python
# 改为 5 分钟
interval = 300

# 改为 15 分钟
interval = 900
```

### 修改监控币种

```python
# 只监控主要币种
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

# 添加更多币种
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
           'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT']
```

---

## 🛠️ 数据库初始化

### 自动初始化（推荐）

监控器会自动创建表，无需手动操作。

### 手动初始化

```bash
# 连接数据库
mysql -u quantdinger -p quantdinger

# 执行 SQL 脚本
source backend_api_python/sql/hama_monitor_schema.sql;
```

---

## 🎉 总结

### ✅ 优势

1. **数据持久化** - 永久保存，重启不丢失
2. **简单易用** - 不需要额外服务
3. **查询方便** - SQL 查询，支持分析
4. **性能足够** - 毫秒级响应
5. **已集成** - 与现有数据库统一

### 📋 文件清单

- `app/services/hama_brave_monitor_mysql.py` - MySQL 版监控器
- `auto_hama_monitor_mysql.py` - 自动监控脚本
- `start_hama_monitor.bat` - 启动脚本
- `sql/hama_monitor_schema.sql` - 数据库表结构

### 🚀 立即开始

```bash
# 1. 双击启动
start_hama_monitor.bat

# 2. 查看数据（另开终端）
mysql -u quantdinger -p quantdinger
mysql> USE quantdinger;
mysql> SELECT * FROM hama_monitor_cache;
```

---

**开始使用吧！** 🚀
