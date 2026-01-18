# 数据库表结构说明

## 📊 QuantDinger 数据库表结构

### 数据库文件
- **路径**: `backend_api_python/data/quantdinger.db`
- **类型**: SQLite
- **表总数**: 15

---

## 📋 完整表结构

### 1. HAMA 监控表（新增）

#### hama_monitor_cache
```
用途: 存储 HAMA 监控缓存数据（每个币种一条最新记录）

字段:
- id (INTEGER PRIMARY KEY)
- symbol (VARCHAR(20) UNIQUE)
- hama_trend (VARCHAR(10)) - HAMA 趋势: up/down/neutral
- hama_color (VARCHAR(10)) - HAMA 颜色: green/red/unknown
- hama_value (DECIMAL(20,8)) - HAMA 数值
- price (DECIMAL(20,8)) - 当前价格
- ocr_text (TEXT) - OCR 识别的原始文本
- screenshot_path (VARCHAR(255)) - 截图文件路径
- monitored_at (TIMESTAMP) - 监控时间
- created_at (TIMESTAMP) - 创建时间
- updated_at (TIMESTAMP) - 更新时间

索引:
- unique_symbol - symbol 唯一索引
- idx_monitored_at - 监控时间索引
- idx_hama_color - 颜色索引

数据示例:
```
BTCUSDT, up, green, 95356.06, 95160.10, "上涨|55.5", 2026-01-18 07:19:00
```

#### hama_monitor_history
```
用途: 存储 HAMA 监控历史数据（所有历史记录）

字段:
- id (INTEGER PRIMARY KEY)
- symbol (VARCHAR(20))
- hama_trend (VARCHAR(10))
- hama_color (VARCHAR(10))
- hama_value (DECIMAL(20,8))
- price (DECIMAL(20,8))
- monitored_at (TIMESTAMP)

索引:
- idx_symbol_monitored - (symbol, monitored_at) 复合索引
- idx_monitored_at - 监控时间索引
```

---

### 2. 核心业务表

#### qd_strategies_trading (交易策略)
```
用途: 存储交易策略配置和状态

主要字段:
- id, symbol, strategy_code, status, parameters
- created_at, updated_at

记录数: 0 条（无策略时）
```

#### qd_indicator_codes (自定义指标)
```
用途: 存储用户自定义的 Python 指标代码

记录数: 1 条
```

#### qd_watchlist (自选股)
```
用途: 存储用户自选股列表

记录数: 1 条（BTCUSDT）
```

#### qd_exchange_credentials (交易所凭证)
```
用途: 存储交易所 API 密钥（加密存储）

记录数: 0 条（未配置）
```

#### qd_backtest_runs (回测结果)
```
记录数: 0 条（未运行回测）
```

---

### 3. AI 分析表

#### qd_ai_decisions (AI 决策)
```
记录数: 0 条（未启动 AI 分析）
```

#### qd_analysis_tasks (分析任务)
```
记录数: 0 条（无分析任务）
```

---

### 4. 待处理订单

#### pending_orders
```
用途: 存储待执行的订单（信号通知）

记录数: 0 条（无待处理订单）
```

---

## 🔄 数据流示例

### 策略运行流程

```
策略启动
    ↓
创建订单 → pending_orders
    ↓
TradingExecutor 处理订单
    ↓
执行结果 → qd_strategy_trades
    ↓
更新持仓 → qd_strategy_positions
```

### HAMA 监控流程

```
自动监控脚本启动
    ↓
监控 7 个币种 → hama_monitor_cache (更新)
    ↓
历史记录 → hama_monitor_history (追加)
```

### AI 代理流程

```
用户请求分析
    ↓
1. 并行分析 5 个代理 → qd_ai_decisions
    ↓
2. 辩论 2 个代理 → qd_ai_decisions (继续更新)
    ↓
3. 决策 1 个代理 → qd_ai_decisions (最终决策)
```

---

## 🛠️ 初始化脚本

### 方法 1: 自动初始化（推荐）

**已执行** - 当启动后端时，SQLAlchemy 会自动创建所有表。

### 方法 2: 手动初始化

```bash
cd backend_api_python
python init_all_tables.py
```

输出：
```
================================================================================
初始化 HAMA 监控表
================================================================================
✅ hama_monitor_cache 表创建成功
✅ hama_monitor_history 表创建成功
✅ 索引创建成功

📋 HAMA 相关表 (2 个):
  - hama_monitor_cache
  - hama_monitor_history
================================================================================
...
================================================================================
系统所有表
================================================================================
总表数: 15
...
```

---

## 📝 表关系说明

### 核心关系

```
qd_strategies_trading (1)
    ├── qd_strategy_notifications (策略通知)
    ├── qd_strategy_trades (交易记录)
    └── qd_strategy_positions (持仓信息)

td_exchange_credentials (0)
    ├── Crypto (API 密钥加密)
    ├── US Stocks (API 密钥)
    ├── Forex (API 密钥)
    └── Futures (API 密钥)
```

---

## 📊 当前状态

**✅ 数据库已初始化**

当前数据库包含：
- **15 个表**
- **2 个 HAMA 监控表**（新增）
- **13 个业务表**
- **2 个 AI 分析表**
- **1 个待处理订单表**

所有表均已就绪，系统可以正常运行！

---

**注意事项**:
1. 表结构由 SQLAlchemy ORM 自动管理
2. 修改模型后运行：`db.create_all()`
3. HAMA 表使用 `INSERT ... ON DUPLICATE KEY UPDATE` 确保数据唯一性
4. 历史表用于历史数据分析，不影响缓存表
