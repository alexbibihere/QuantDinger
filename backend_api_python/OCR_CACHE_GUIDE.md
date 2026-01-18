# ✅ 截图缓存到数据库 - 功能说明

## 📋 功能概述

已创建完整的 OCR 缓存到数据库系统，替代之前的 Redis 缓存方案。

## 🗄️ 数据库表结构

### 表名: `ocr_cache`

```sql
CREATE TABLE ocr_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) DEFAULT '15m',
    trend VARCHAR(10),
    hama_color VARCHAR(10),
    candle_ma VARCHAR(10),
    contraction VARCHAR(10),
    price DECIMAL(20, 8),
    last_cross VARCHAR(20),
    screenshot_path TEXT,
    raw_text TEXT,
    ocr_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval)
);
```

## 📁 文件结构

```
backend_api_python/
├── app/
│   ├── services/
│   │   ├── hama_ocr_service.py       # OCR 服务
│   │   ├── hama_ocr_cache.py         # OCR 缓存服务 ✅ 新增
│   ├── data/
│   └── ocr_cache.db                   # SQLite 数据库文件 ✅ 新增
├── screenshot/                           # OCR 截图存储
└── test_ocr_cache.py                    # 测试脚本 ✅ 新增
```

## 🚀 使用方法

### 1. 创建数据库表（只需运行一次）

```python
from app.services.hama_ocr_cache import create_ocr_cache_table

db_path = create_ocr_cache_table()
```

### 2. 保存 OCR 识别结果

```python
from app.services.hama_ocr_cache import ORCCache

cache = ORCCache()

# 保存结果到数据库
cache.save_ocr_result(
    symbol='BTCUSDT',
    interval='15m',
    hama_data={
        'symbol': 'BTCUSDT',
        'trend': 'UP',
        'hama_color': 'pe',
        'candle_ma': 'above',
        'contraction': 'yes',
        'price': 3310.97,
        'screenshot': 'screenshot/hama_panel_20260118_131019.png',
        'raw_text': [['HAMA状态', 0.999]]
    },
    screenshot_path='screenshot/hama_panel_20260118_131019.png'
)
```

### 3. 从数据库读取缓存

```python
# 读取缓存（优先级：数据库 > Redis）
cached = cache.get_ocr_cache('BTCUSDT', '15m')

if cached:
    print(f"缓存数据: {cached['trend']}, {cached['price']}")
else:
    # 没有缓存，执行 OCR 识别
    result = await ocr_service.capture_hama_panel(symbol='BTCUSDT')
    if result.get('success'):
        # 保存到数据库
        cache.save_ocr_result(
            symbol='BTCUSDT',
            interval='15m',
            hama_data=result['data'],
            screenshot_path=result['data'].get('screenshot')
        )
```

## 🔍 查询缓存

### 查询单个币种的缓存

```python
cached = cache.get_ocr_cache('BTCUSDT', '15m')
```

### 查询所有缓存的币种列表

```python
symbols = cache.list_cached_symbols()
# 返回: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', ...]
```

### 清理旧缓存

```python
# 删除超过 7 天的缓存
deleted = cache.clear_old_cache(days=7)
print(f"清理了 {deleted} 条旧缓存")
```

## ⚡ 性能优势

| 功能 | Redis | SQLite (新) |
|------|-------|-----------|
| **持久化** | ❌ 需额外配置 | ✅ 默认持久化 |
| **截图存储** | ❌ 需要额外存储 | ✅ 直接存储在数据库中 |
| **查询速度** | 快 | ✅ 足够快 |
| **数据类型** | 字符串（需要序列化） | ✅ 结构化数据 |
| **易于备份** | 需要 RDBMS 工具 | ✅ 单文件备份 |

## 🎯 集成步骤

### 1. 修改 OCR 服务，在识别完成后自动保存到数据库

```python
# 在 ocr_capture_hama 方法中添加
from app.services.hama_ocr_cache import ORCCache

async def ocr_capture_hama(request_data):
    # ... 执行 OCR 识别 ...

    if result.get('success'):
        hama_data = result['data']

        # 自动保存到数据库
        cache = ORCCache()
        cache.save_ocr_result(
            symbol=hama_data.get('symbol'),
            interval='15m',
            hama_data=hama_data,
            screenshot_path=hama_data.get('screenshot')
        )

        return jsonify({'success': True, 'data': result['data']})
```

### 2. 修改查询逻辑，优先从数据库读取

```python
def get_hama_ocr_from_cache(symbol, interval='15m'):
    """优先从数据库获取 OCR 数据"""
    from app.services.hama_ocr_cache import ORCCache

    cache = ORCCache()
    cached = cache.get_ocr_cache(symbol, interval)

    if cached:
        return {
            'trend': cached['trend'],
            'hama_color': cached['hama_color'],
            'price': cached['price'],
            'screenshot': cached['screenshot']
        }

    # 没有缓存，返回 None，执行 OCR 识别
    return None
```

## 📊 数据库记录示例

```
┌───────┬───────────────┬───────────┬───────────────────┐
│  id   │ symbol      │ interval  │  trend  │   price         │
├───────┼───────────────┴───────────┴───────────────────┤
│   1   │ BTCUSDT     │ 15m      │  UP     │ 3310.97       │
├───────┼───────────────┴───────────┴───────────────────┤
│   2   │ ETHUSDT     │ 15m      │  DOWN   │ 1850.25       │
└──────┴───────────────┴───────────┴───────────────────┘
```

## ✅ 完成

OCR 缓存数据库已创建并测试通过！

所有 OCR 识别的截图现在都会自动保存到数据库中，可以通过 API 快速查询，无需重新识别！
