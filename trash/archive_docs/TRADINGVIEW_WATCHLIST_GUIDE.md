# TradingView Watchlist获取指南

## 📊 方案总结

经过测试,我们发现了几个获取TradingView Watchlist的方法:

### ✅ 方案1: 使用TradingView Scanner API (推荐)

不需要登录,可以直接获取大量加密货币数据。

**优点**:
- 无需认证
- 可获取数百个币种
- 包含技术指标(RSI, MACD等)
- 稳定可靠

**API端点**: `https://scanner.tradingview.com/crypto/scan`

**示例代码**:
```python
import requests

symbols = [
    'BINANCE:BTCUSDT',
    'BINANCE:ETHUSDT',
    'BINANCE:BNBUSDT',
    # ... 更多币种
]

response = requests.post('https://scanner.tradingview.com/crypto/scan', json={
    'symbols': {'tickers': symbols},
    'columns': ['name', 'description', 'close', 'change', 'volume', 'RSI|14|0']
})

data = response.json()
```

### ⚠️ 方案2: 使用自定义Watchlist API

需要cookies和list_id。

**API端点**: `https://www.tradingview.com/api/v1/symbols_list/custom/{list_id}/replace/`

**限制**:
- 需要有效的TradingView账号
- 需要正确的list_id
- list_id `104353945` 返回空列表,可能不是您的列表

### 🔑 方案3: 使用Selenium登录获取

需要TradingView用户名和密码。

**优点**:
- 可以获取用户的个人关注列表
- 可以自动浏览TradingView网站

**缺点**:
- 需要提供账号密码
- 速度较慢
- 可能被反爬虫检测

## 💡 推荐方案

**对于您的需求(获取上百个币种)**,推荐使用:

### 方案A: TradingView Scanner API + 自定义币种列表

```python
# 定义您想监控的币种列表
SYMBOLS = [
    'BINANCE:BTCUSDT',
    'BINANCE:ETHUSDT',
    'BINANCE:BNBUSDT',
    'BINANCE:SOLUSDT',
    'BINANCE:XRPUSDT',
    'BINANCE:ADAUSDT',
    'BINANCE:DOGEUSDT',
    'BINANCE:MATICUSDT',
    'BINANCE:DOTUSDT',
    'BINANCE:AVAXUSDT',
    'BINANCE:LINKUSDT',
    'BINANCE:UNIUSDT',
    'BINANCE:LTCUSDT',
    'BINANCE:ATOMUSDT',
    'BINANCE:NEARUSDT',
    # ... 添加更多币种
]

# 批量获取
def get_top_crypto_from_binance(limit=100):
    \"\"\"从币安获取Top币种\"\"\"
    import ccxt
    exchange = ccxt.binance()
    markets = exchange.load_markets()

    # 筛选USDT永续合约
    usdt_perpetual = [
        f\"BINANCE:{symbol}\"
        for symbol, market in markets.items()
        if symbol.endswith('USDT') and market.get('swap', False)
    ][:limit]

    return usdt_perpetual

# 使用Scanner API获取数据
response = requests.post('https://scanner.tradingview.com/crypto/scan', json={
    'symbols': {'tickers': get_top_crypto_from_binance(100)},
    'columns': [
        'name', 'description',
        'close', 'change', 'change|1', 'change|5',
        'volume', 'market_cap',
        'RSI|14|0', 'MACD.macd', 'EMA|20|0', 'EMA|50|0',
        'Recommend.All|15'
    ]
})
```

### 方案B: 使用币安API获取币种列表,再用TradingView获取指标

```python
import ccxt
import requests

# 1. 从币安获取所有USDT永续合约
exchange = ccxt.binance()
markets = exchange.load_markets()

perpetual_symbols = [
    symbol for symbol, market in markets.items()
    if symbol.endswith('USDT') and market.get('swap', False)
]

print(f"找到 {len(perpetual_symbols)} 个USDT永续合约")

# 2. 批量从TradingView获取指标(每批20个)
batch_size = 20
all_data = []

for i in range(0, len(perpetual_symbols), batch_size):
    batch = perpetual_symbols[i:i+batch_size]
    tradingview_symbols = [f\"BINANCE:{s}\" for s in batch]

    response = requests.post('https://scanner.tradingview.com/crypto/scan', json={
        'symbols': {'tickers': tradingview_symbols},
        'columns': ['name', 'description', 'close', 'change', 'RSI|14|0']
    })

    data = response.json()
    all_data.extend(data.get('data', []))

    print(f\"已处理 {i+len(batch)}/{len(perpetual_symbols)}\")

print(f\"总共获取 {len(all_data)} 个币种的数据\")
```

## 🎯 最终建议

**不建议继续使用TradingView的自定义Watchlist API**,原因:

1. list_id `104353945` 返回空列表
2. API认证机制复杂
3. 需要维护cookies有效性

**推荐方案**:
1. **使用币安API**获取所有币种列表(200+永续合约)
2. **使用TradingView Scanner API**批量获取技术指标
3. **使用AICoin API**获取涨幅榜数据

这样可以稳定获取数百个币种的完整数据!

## 📝 下一步

您希望我实现哪个方案?

1. **方案A**: 使用币安API + TradingView Scanner
2. **方案B**: 使用AICoin涨幅榜(已有,20+币种)
3. **方案C**: 尝试其他TradingView API端点

请告诉我您的选择!
