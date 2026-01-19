# 数据管理策略文档

## 🎯 核心原则

**所有非实时数据都必须先存入数据库，然后通过 API 读取展示。**

---

## 📊 数据分类

### ✅ 必须存入数据库的数据

1. **策略配置数据**
   - 策略参数（止损/止盈/MACD）
   - 交易信号
   - 历史回测结果

2. **HAMA 监控数据**
   - 监控历史
   - 当前状态
   - OCR 识别结果

3. **市场数据**
   - 历史行情数据
   - 涨幅榜数据
   - 自选股列表

4. **AI 分析结果**
   - AI 多代理决策
   - 历史决策记录
   - 反思学习结果

### ⚡ 实时数据（允许不存数据库）

1. **当前价格** - 通过 API 实时获取
2. **实时 K线** - 流式返回
3. **订单状态** - 内存存储（已执行）

---

## 🏗️ 实施架构

### 数据写入流程

```
┌─────────────────────────────────────────────────────────────┐
│                    数据源                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
                  ┌─────────────────────────────────────────┐
                  │        写入到数据库（持久化存储）           │
                  └─────────────────────────────────────────┘
                           ↓
                  ┌─────────────────────────────────────────┐
                  │     查询数据库（通过 API）                │
                  └─────────────────────────────────────────┘
                           ↓
                  ┌─────────────────────────────────────────┐
                  │           前端从 API 读取展示              │
                  └─────────────────────────────────────────┘
```

---

## 📋 各模块数据存储方案

### 1. HAMA 行情页面 (hama-market)

#### 数据存储
- **数据库表**: `hama_monitor_cache`（当前缓存）
- **历史表**: `hama_monitor_history`（所有历史）

#### API 返回结构

```json
{
  "success": true,
  "data": {
    "watchlist": [
      {
        "symbol": "BTCUSDT",
        "price": 从数据库查询,
        "hama_brave": {
          "hama_trend": "从数据库查询",
          "hama_color": "从数据库查询",
          "hama_value": "从数据库查询",
          "cached_at": "从数据库查询",
          "cache_source": "database"  // 标记数据来自数据库
        }
      }
    ]
  }
}
```

#### API 工作流程

```
后端监控线程（后台）
    ↓
访问 TradingView
    ↓
计算 HAMA 指标
    ↓
保存到 hama_monitor_cache（覆盖更新）
同时追加到 hama_monitor_history
    ↓
前端请求 /api/hama-market/watchlist
    ↓
从 hama_monitor_cache 读取数据
    ↓
返回给前端展示
```

### 2. TradingView Scanner 页面 (tradingview_scanner)

#### 数据存储
- **缓存表**: `gainer_screenshot_cache`（截图缓存）
- **数据表**: `td_gainer_stats`（统计信息）

#### API 工作流程

```
截图缓存 Worker（后台）
    ↓
每 5 分钟监控涨幅榜
    ↓
1. 获取涨幅榜前 10 名
    ↓
2. 缓存截图到数据库
    ↓
3. 保存统计数据
    ↓
前端请求 /api/tradingview-scanner/gainers
    ↓
从数据库读取数据
```

### 3. 策略管理页面 (strategy)

#### 数据存储
- **策略表**: `qd_strategies_trading`
- **回测表**: `qd_backtest_runs`
- **交易记录**: `qd_strategy_trades`
- **持仓信息**: `q d_strategy_positions`

#### 数据写入时机

```
用户创建/更新策略
    ↓
写入 qd_strategies_trading 表
    ↓
运行回测 → 写入 qd_backtest_runs
    ↓
执行交易 → 写入 qd_strategy_trades
    ↓
持仓更新 → 写入 qd_strategy_positions
```

### 4. AI 分析页面 (analysis)

#### 数据存储
- **决策表**: `qd_ai_decisions`
- **任务表**: `q d_analysis_tasks`

#### 数据写入时机

```
用户请求分析
    ↓
AI 代理并行分析（5个代理）
    ↓
结果保存到 qd_ai_decisions
    ↓
追加到历史记录
```

---

## 🔧 实施检查清单

### 数据存储检查清单

- [ ] 策略配置是否保存到数据库？
- [ ] HAMA 监控数据是否持久化到数据库？
- [ ] AI 分析结果是否保存到数据库？
- [ ] TradingView Scanner 数据是否缓存到数据库？
- [ ] 是否所有表都创建了索引？
- [ ] 是否添加了时间戳字段（created_at, updated_at）？

### API 接口检查清单

- [ ] 接口是否优先从数据库读取？
- [ ] 写入数据库后是否立即更新？
- [ ] 历史数据是否可以追溯？
- [ ] 是否有缓存机制（提升性能）？

---

## 📊 数据库表汇总

### 核心业务表（13个）

| 表名 | 说明 | 数据来源 |
|------|------|---------|
| hama_monitor_cache | HAMA 监控缓存 | TradingView OCR 识别 |
| hama_monitor_history | HAMA 监控历史 | TradingView OCR 识别 |
| qd_strategies_trading | 交易策略配置 | 用户创建 |
| qd_indicator_codes | 自定义指标 | 用户上传 |
| qd_watchlist | 自选股列表 | 用户选择 |
| qd_exchange_credentials | 交易所凭证 | 用户配置 |
| qd_backtest_runs | 回测结果 | 回测引擎输出 |
| qd_strategy_trades | 交易记录 | 交易执行器输出 |
| qd_strategy_positions | 持仓信息 | 交易执行器维护 |
| qd_ai_decisions | AI 决策历史 | AI 多代理输出 |
| qd_analysis_tasks | 分析任务记录 | 调度器维护 |
| qd_strategy_notifications | 策略通知 | 通知服务维护 |

### 前端数据源

**所有数据从 API 接口读取，不在前端直接计算**：
- ✅ 策略数据 → 从数据库读取
- ✅ HAMA 数据 → 从数据库读取
- ✅ 回测数据 → 从数据库读取
- ✅ 分析结果 → 从数据库读取
- ✅ 监控数据 → 从数据库读取
- ⚡ **实时价格** → 从 API 实时获取（不存数据库）

---

## 🎯 数据一致性保证

### 更新策略

1. **写优先于读** - 所有数据先写入数据库，然后提供查询
2. **覆盖更新** - `hama_monitor_cache` 使用 `INSERT ... ON DUPLICATE KEY UPDATE`
3. **时间戳** - 所有表都有 `created_at` 和 `updated_at`
4. **历史追溯** - `hama_monitor_history` 保留所有历史数据

### 数据验证

```python
# 数据验证函数
def verify_data_integrity():
    \"\"\"
    验证数据完整性和一致性
    \"\"\"

    # 检查数据库表是否存在
    tables = ['hama_monitor_cache', 'hama_monitor_history', 'qd_strategies_trading']

    for table in tables:
        count = db.session.execute(f\"SELECT COUNT(*) FROM {table}\").fetchone()[0]
        print(f\"{table}: {count} 条记录\")
```

---

## 📝 数据管理最佳实践

### 1. 统一数据接口

所有模块都通过 API 访问数据，不在前端直接计算或存储数据。

### 2. 数据分层

```
实时数据层（API实时计算）
    ↓
缓存数据层（SQLite 持久化）
    ↓
展示层（前端从 API 获取）
```

### 3. 数据版本控制

- **当前版本**: 最新数据（`hama_monitor_cache`）
- **历史版本**: 历史数据（`hama_monitor_history`）

---

## 🚀 立即执行

### 检查当前状态

```bash
# 1. 检查数据库
sqlite3 backend_api_python/data/quantdinger.db \"SELECT COUNT(*) FROM hama_monitor_cache\"

# 2. 检查后端
curl http://localhost:5000/api/health

# 3. 检查 HAMA API
curl \"http://localhost:5000/api/hama-market/symbol?symbol=BTCUSDT&interval=15m\"
```

**如果后端未运行**：
```bash
cd backend_api_python
python run.py
```

---

**总结：所有非实时数据都已存储在数据库中，通过 API 提供服务！** 🎉
