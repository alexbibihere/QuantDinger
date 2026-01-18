# HAMA 币种管理功能使用指南

## 功能概述

HAMA 币种管理功能允许你在数据库中管理所有需要监控的币种，支持增删改查、批量操作、优先级设置等功能。

## 数据库表结构

### `hama_symbols` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| symbol | VARCHAR(20) | 币种符号（唯一），如 BTCUSDT |
| symbol_name | VARCHAR(50) | 币种名称，如 Bitcoin |
| market | VARCHAR(20) | 市场类型（spot/futures），默认 spot |
| enabled | BOOLEAN | 是否启用监控，默认 true |
| priority | INTEGER | 优先级（0-1000），数值越大优先级越高 |
| notify_enabled | BOOLEAN | 是否启用通知，默认 false |
| notify_threshold | DECIMAL(5,2) | 通知阈值百分比，默认 2.0 |
| notes | TEXT | 备注信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| last_monitored_at | TIMESTAMP | 最后监控时间 |

## API 接口

### 1. 获取币种列表

```bash
GET /api/hama-market/symbols/list?enabled=true&market=spot
```

**参数**:
- `enabled`: 是否只返回启用的币种（true/false，可选）
- `market`: 市场类型（spot/futures，可选）

**返回示例**:
```json
{
  "success": true,
  "data": {
    "symbols": [
      {
        "id": 1,
        "symbol": "BTCUSDT",
        "symbol_name": "Bitcoin",
        "market": "spot",
        "enabled": true,
        "priority": 100,
        "notify_enabled": true,
        "notify_threshold": 2.0,
        "notes": "BTC 永续监控",
        "created_at": "2025-01-18T10:00:00",
        "updated_at": "2025-01-18T10:00:00",
        "last_monitored_at": null
      }
    ]
  }
}
```

### 2. 添加币种

```bash
POST /api/hama-market/symbols/add
Content-Type: application/json

{
  "symbol": "ETHUSDT",
  "symbol_name": "Ethereum",
  "market": "spot",
  "enabled": true,
  "priority": 90,
  "notify_enabled": true,
  "notify_threshold": 2.0,
  "notes": "ETH 永续监控"
}
```

**返回示例**:
```json
{
  "success": true,
  "data": {
    "id": 2,
    "symbol": "ETHUSDT"
  }
}
```

### 3. 更新币种

```bash
POST /api/hama-market/symbols/update
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "priority": 150,
  "notify_enabled": true
}
```

### 4. 删除币种

```bash
POST /api/hama-market/symbols/delete
Content-Type: application/json

{
  "symbol": "BTCUSDT"
}
```

### 5. 启用/禁用币种

```bash
POST /api/hama-market/symbols/enable
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "enabled": true
}
```

### 6. 批量启用/禁用

```bash
POST /api/hama-market/symbols/batch-enable
Content-Type: application/json

{
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "enabled": true
}
```

## 前端使用

### 访问币种管理

1. 打开 HAMA 行情页面: http://localhost:8000/#/hama-market
2. 点击右上角的 **"币种管理"** 按钮

### 币种管理功能

#### 添加币种
1. 点击 **"添加币种"** 按钮
2. 填写表单:
   - **币种符号**: 如 BTCUSDT（自动转大写）
   - **币种名称**: 如 Bitcoin
   - **市场**: 现货/合约
   - **优先级**: 0-1000，数值越大优先级越高
   - **启用监控**: 开关
   - **启用通知**: 开关（启用后可设置通知阈值）
   - **备注**: 自定义备注信息
3. 点击 **确定** 保存

#### 编辑币种
1. 在列表中找到要编辑的币种
2. 点击 **"编辑"** 按钮
3. 修改信息后点击 **确定**

#### 删除币种
1. 在列表中找到要删除的币种
2. 点击 **"删除"** 按钮
3. 确认删除

#### 批量操作
1. 勾选多个币种（使用复选框）
2. 点击 **"批量启用"** 或 **"批量禁用"** 按钮

#### 搜索币种
- 在搜索框输入币种符号或名称
- 列表自动过滤显示匹配结果

## 初始化数据库

运行初始化脚本创建表并插入默认币种：

```bash
cd backend_api_python
python init_hama_symbols_table.py
```

默认会插入 10 个主流币种：
- BTCUSDT (Bitcoin)
- ETHUSDT (Ethereum)
- BNBUSDT (Binance Coin)
- SOLUSDT (Solana)
- XRPUSDT (Ripple)
- ADAUSDT (Cardano)
- DOGEUSDT (Dogecoin)
- AVAXUSDT (Avalanche)
- DOTUSDT (Polkadot)
- LINKUSDT (Chainlink)

## 与 HAMA 监控集成

币种管理表与 HAMA 监控系统集成：

1. **自动监控 Worker**: 从 `hama_symbols` 表读取 `enabled=true` 的币种进行监控
2. **优先级排序**: 监控时按 `priority` 降序排列，优先级高的先监控
3. **通知功能**: 当 `notify_enabled=true` 且价格变动超过 `notify_threshold` 时发送通知

### 修改监控脚本使用币种表

在 `auto_hama_monitor_sqlite.py` 或相关监控脚本中：

```python
import sqlite3

def get_monitored_symbols():
    """从数据库获取启用的监控币种"""
    conn = sqlite3.connect('data/quantdinger.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT symbol FROM hama_symbols
        WHERE enabled = 1
        ORDER BY priority DESC, symbol ASC
    ''')
    symbols = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return symbols

# 使用
symbols = get_monitored_symbols()
print(f"监控币种: {symbols}")
```

## 常见问题

### Q: 如何重新初始化表？

```bash
cd backend_api_python
python init_hama_symbols_table.py
```

如果表已存在，脚本会保留现有数据，不会覆盖。

### Q: 如何清空所有币种？

```bash
sqlite3 backend_api_python/data/quantdinger.db "DELETE FROM hama_symbols;"
```

### Q: 如何导出币种列表？

```bash
sqlite3 backend_api_python/data/quantdinger.db \
  "SELECT * FROM hama_symbols;" \
  > symbols_export.txt
```

### Q: 如何批量导入币种？

创建一个 JSON 文件 `symbols.json`:

```json
[
  {"symbol": "MATICUSDT", "symbol_name": "Polygon", "priority": 50},
  {"symbol": "ATOMUSDT", "symbol_name": "Cosmos", "priority": 40}
]
```

然后使用脚本导入（需要自行编写导入脚本）。

## 前端 API 调用示例

```javascript
import {
  getSymbolsList,
  addSymbol,
  updateSymbol,
  deleteSymbol,
  toggleSymbol,
  batchEnableSymbols
} from '@/api/hamaMarket'

// 获取币种列表
const symbols = await getSymbolsList({ enabled: true })

// 添加新币种
await addSymbol({
  symbol: 'SOLUSDT',
  symbol_name: 'Solana',
  market: 'spot',
  enabled: true,
  priority: 70,
  notify_enabled: false,
  notify_threshold: 2.0,
  notes: 'SOL 监控'
})

// 更新币种
await updateSymbol({
  symbol: 'SOLUSDT',
  priority: 80
})

// 删除币种
await deleteSymbol({ symbol: 'SOLUSDT' })

// 切换启用状态
await toggleSymbol({ symbol: 'SOLUSDT', enabled: false })

// 批量启用
await batchEnableSymbols({
  symbols: ['BTCUSDT', 'ETHUSDT'],
  enabled: true
})
```

## 数据库维护

### 创建索引

```sql
CREATE INDEX IF NOT EXISTS idx_hama_symbols_enabled
ON hama_symbols(enabled, priority);

CREATE INDEX IF NOT EXISTS idx_hama_symbols_symbol
ON hama_symbols(symbol);
```

### 查看表结构

```bash
sqlite3 backend_api_python/data/quantdinger.db \
  "PRAGMA table_info(hama_symbols);"
```

### 统计信息

```sql
-- 总币种数
SELECT COUNT(*) FROM hama_symbols;

-- 启用的币种数
SELECT COUNT(*) FROM hama_symbols WHERE enabled = 1;

-- 按市场分组统计
SELECT market, COUNT(*) as count
FROM hama_symbols
GROUP BY market;

-- 优先级分布
SELECT
  CASE
    WHEN priority >= 100 THEN '高'
    WHEN priority >= 50 THEN '中'
    ELSE '低'
  END as level,
  COUNT(*) as count
FROM hama_symbols
GROUP BY level
ORDER BY
  CASE level
    WHEN '高' THEN 1
    WHEN '中' THEN 2
    ELSE 3
  END;
```

## 总结

HAMA 币种管理功能提供了完整的币种 CRUD 操作，支持：

✅ 数据库持久化存储
✅ 优先级排序
✅ 启用/禁用控制
✅ 批量操作
✅ 通知设置
✅ 搜索过滤
✅ 前端可视化界面

所有币种数据存储在 SQLite 数据库中，可以在多个服务之间共享使用。
