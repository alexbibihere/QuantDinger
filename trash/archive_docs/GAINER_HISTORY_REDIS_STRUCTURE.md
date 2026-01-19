# 涨幅榜历史 - Redis数据结构说明

## 新的数据结构

### Key格式
```
gainer_appearance:symbol:{币种符号}
```

### Value格式 (JSON)
```json
{
  "appearances": [
    {
      "date": "2026-01-13",
      "price": 42500.50,
      "change_percentage": 5.2,
      "volume": 1000000,
      "rank": 1,
      "timestamp": "2026-01-13T10:30:00"
    },
    {
      "date": "2026-01-12",
      "price": 41800.00,
      "change_percentage": 3.1,
      "volume": 950000,
      "rank": 2,
      "timestamp": "2026-01-12T10:30:00"
    }
  ]
}
```

## 数据结构特点

### 1. 以币种为Key
- **优势**: 快速查询单个币种的所有历史记录
- **用途**: 涨幅榜历史页面、币种详情分析

### 2. 完整的涨幅信息
每次出现记录包含：
- **date**: 日期
- **price**: 当天价格
- **change_percentage**: 涨跌幅
- **volume**: 成交量
- **rank**: 当天排名
- **timestamp**: 记录时间

### 3. 自动排序
- 记录按日期降序排列（最新的在前）
- 最多保留30天的数据

## 辅助数据结构

### 统计Key
```
gainer_appearance:stats
```
**类型**: Hash
**字段**: `{symbol}: {出现次数}`

### 每日索引
```
gainer_appearance:daily:{date}
```
**类型**: Set
**值**: 币种符号列表
**用途**: 快速查询某天有哪些币种出现在涨幅榜

## 使用示例

### 记录涨幅数据
```python
from app.services.gainer_tracker import record_gainer_appearance

gainer_data = [
    {
        'symbol': 'BTCUSDT',
        'price': 42500.50,
        'change_percentage': 5.2,
        'volume': 1000000,
        'rank': 1
    },
    {
        'symbol': 'ETHUSDT',
        'price': 2500.00,
        'change_percentage': 4.1,
        'volume': 800000,
        'rank': 2
    }
]

record_gainer_appearance(gainer_data)
```

### 查询单个币种历史
```python
from app.services.gainer_tracker import get_gainer_tracker

tracker = get_gainer_tracker()
history = tracker.get_symbol_history('BTCUSDT', days=7)

# 返回:
# {
#     'symbol': 'BTCUSDT',
#     'total_appearances': 15,
#     'appearances': [
#         {'date': '2026-01-13', 'price': 42500.50, ...},
#         ...
#     ]
# }
```

### 查询所有币种历史
```python
all_history = tracker.get_all_symbols_history(days=7, min_appearances=1)

# 返回所有币种的历史记录，按出现次数降序排序
```

## API接口

### 获取历史数据
```
GET /api/gainer-stats/history?days=7
```

**响应**:
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "daily": [
      {
        "date": "2026-01-13",
        "count": 10,
        "symbols": ["BTCUSDT", "ETHUSDT", ...],
        "symbolDetails": [
          {
            "symbol": "BTCUSDT",
            "count": 15,
            "price": 42500.50,
            "changePercentage": 5.2,
            "volume": 1000000,
            "rank": 1
          },
          ...
        ]
      }
    ],
    "ranking": [
      {
        "symbol": "BTCUSDT",
        "total_count": 15,
        "percentage": 75.0
      },
      ...
    ]
  }
}
```

## 前端展示

### 涨幅榜历史页面 (`/gainer-history`)

**统计概览**:
- 记录天数
- 涉及币种数
- 最高出现次数
- 平均出现次数

**排行榜**:
- 按出现次数排序
- 显示进度条
- 颜色标记（红/橙/蓝/绿）

**每日详情**:
- 可折叠面板
- 显示当天的币种列表
- 包含价格、涨跌幅、排名等完整信息

## 数据流程

1. **TradingView Scanner获取涨幅榜**
   ```python
   gainers = get_top_gainers(limit=10)
   ```

2. **自动记录到Redis**（包含完整信息）
   ```python
   record_gainer_appearance(gainer_data)
   ```

3. **Redis存储**
   ```
   Key: gainer_appearance:symbol:BTCUSDT
   Value: {"appearances": [...]}
   ```

4. **前端查询**
   ```
   GET /api/gainer-stats/history?days=7
   ```

5. **显示数据**
   - 统计概览
   - 排行榜
   - 每日详情

## 优势

1. **查询效率高**: 以币种为Key，快速查询单个币种的所有历史
2. **数据完整**: 包含价格、涨跌幅、成交量、排名等完整信息
3. **自动排序**: 按日期降序，最新的在前
4. **空间优化**: 只保留30天数据，自动过期
5. **灵活扩展**: 可以轻松添加更多字段

## 注意事项

1. **数据过期**: 30天后自动过期，需要定期重新记录
2. **内存占用**: 每个币种约占用1-2KB（取决于出现次数）
3. **并发安全**: 使用Redis事务保证数据一致性
4. **备份建议**: 定期导出重要数据到数据库

## 性能指标

- **写入**: 每个币种约1ms
- **读取单个币种**: 约2ms
- **读取所有币种历史**: 约50-100ms（取决于币种数量）
- **内存占用**: 100个币种 × 30天 ≈ 100-200MB
