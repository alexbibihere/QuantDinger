# TradingView HAMA 指标实现说明

## 概述

本系统现在使用真实的 TradingView 和交易所数据进行 HAMA (Heikin Ashi Moving Average) 指标分析,替代了之前的模拟数据。

## 实现架构

### 1. 数据源

#### TradingView Scanner API
- **端点**: `https://scanner.tradingview.com/crypto/scan`
- **功能**: 获取实时技术指标数据
- **指标**:
  - 综合建议 (1m, 15m, 4h, 1d)
  - RSI (14)
  - Stochastic RSI
  - MACD & Signal
  - ADX
  - EMA (20, 50, 200)
  - 布林带

#### CCXT 交易所数据
- **交易所**: 使用系统配置的默认交易所 (OKX/Binance)
- **数据**: 4小时 K线数据 (最近100根)
- **用途**: 计算 Heikin Ashi 蜡烛图和自定义指标

### 2. 核心算法

#### Heikin Ashi 蜡烛图计算

```python
HA_Close = (Open + High + Low + Close) / 4
HA_Open = (前一根 HA_Open + 前一根 HA_Close) / 2
HA_High = max(High, HA_Open, HA_Close)
HA_Low = min(Low, HA_Open, HA_Close)
```

#### 趋势判断逻辑

基于最近10根 HA 蜡烛:
- **上升趋势**: 连续5根以上阳线,或10根中7根以上阳线
- **下降趋势**: 连续5根以上阴线,或10根中7根以上阴线
- **横盘整理**: 其他情况

#### 蜡烛图形态识别

- **锤子线 (Hammer)**: 下影线 > 实体 * 2, 上影线 < 实体 * 0.5
- **流星线 (Shooting Star)**: 上影线 > 实体 * 2, 下影线 < 实体 * 0.5
- **看涨吞没 (Bullish Engulfing)**: 阳线完全吞没前一根阴线
- **看跌吞没 (Bearish Engulfing)**: 阴线完全吞没前一根阳线
- **十字星 (Doji)**: 实体 ≈ 0

#### 交易建议生成

综合评分系统:

```python
score = 0

# TradingView 1天建议 (权重 30%)
score += TV_1D_Recommendation * 0.3

# RSI 分析
if RSI < 30:  score += 2  # 超卖
if RSI > 70:  score -= 2  # 超买

# 趋势权重
if trend == 'uptrend':   score += 1.5
if trend == 'downtrend': score -= 1.5

# 蜡烛图形态权重
if pattern == 'bullish_engulfing':  score += 1
if pattern == 'bearish_engulfing':  score -= 1
if pattern == 'hammer':              score += 0.5
if pattern == 'shooting_star':       score -= 0.5

# MACD 金叉/死叉
if MACD > Signal: score += 0.5
else:             score -= 0.5

# 最终建议
if score >= 2:  return 'BUY'
if score <= -2: return 'SELL'
else:           return 'HOLD'
```

#### 置信度计算

```python
confidence = 0.5  # 基础置信度

# 趋势明确性 (+15%)
if trend in ['uptrend', 'downtrend']:
    confidence += 0.15

# 蜡烛图形态 (+10-15%)
if pattern in ['bullish_engulfing', 'bearish_engulfing']:
    confidence += 0.15
elif pattern in ['hammer', 'shooting_star']:
    confidence += 0.1

# RSI 极值 (+10%)
if RSI < 20 or RSI > 80:
    confidence += 0.1

# ADX 趋势强度 (+10%)
if ADX > 40:
    confidence += 0.1

# 最终置信度范围: 0.3 - 0.95
```

### 3. 技术指标计算

#### RSI (相对强弱指标)

```python
# 使用 14 周期
delta = close[i] - close[i-1]
gain = max(delta, 0)
loss = max(-delta, 0)

avg_gain = mean(gains[-14:])
avg_loss = mean(losses[-14:])

RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))
```

#### EMA (指数移动平均)

```python
multiplier = 2 / (period + 1)
EMA = (close - EMA_prev) * multiplier + EMA_prev
```

#### 支撑位/阻力位

```python
# 基于最近 20 根 K线
support = min(lows[-20:])
resistance = max(highs[-20:])
```

### 4. 降级机制

当真实数据获取失败时,系统会自动降级到模拟数据,确保服务可用性:

```python
try:
    # 尝试获取真实数据
    tv_data = _fetch_tradingview_scan_data(symbol)
    kline_data = _fetch_kline_data(symbol)
    return _analyze_hama_indicators_real(symbol, tv_data, kline_data)
except Exception as e:
    # 降级到模拟数据
    logger.error(f"Error: {e}")
    return _analyze_hama_indicators(symbol)
```

## API 接口

### GET /api/gainer-analysis/top-gainers

获取币安涨幅榜并进行 HAMA 分析

**参数**:
- `limit`: 返回数量 (默认 20, 最大 100)
- `market`: 市场类型 ('spot' 或 'futures')

**响应示例**:
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "count": 20,
    "timestamp": "2025-01-09T12:00:00",
    "market": "spot",
    "symbols": [
      {
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "price": 45000.50,
        "price_change_percent": 8.5,
        "volume": 1234567.89,
        "hama_analysis": {
          "symbol": "BTCUSDT",
          "trend": "uptrend",
          "candle_pattern": "bullish_engulfing",
          "recommendation": "BUY",
          "confidence": 0.85,
          "signals": {
            "ha_close": 45100.25,
            "ha_open": 44800.50,
            "ha_high": 45200.00,
            "ha_low": 44750.00,
            "trend_strength": "strong",
            "volume_confirmation": true
          },
          "technical_indicators": {
            "rsi": 65.5,
            "macd": "bullish",
            "ema_20": 44200.00,
            "ema_50": 43500.00,
            "support_level": 44000.00,
            "resistance_level": 46000.00
          }
        },
        "conditions": {
          "is_uptrend": true,
          "is_downtrend": false,
          "confidence_above_70": true,
          "is_bullish_pattern": true,
          "has_volume_confirmation": true,
          "meets_buy_criteria": true,
          "meets_sell_criteria": false,
          "summary": "处于上升趋势,信号强度高,建议买入"
        }
      }
    ]
  }
}
```

### POST /api/gainer-analysis/analyze-symbol

分析单个币种的 HAMA 指标

**请求体**:
```json
{
  "symbol": "BTCUSDT"
}
```

### POST /api/gainer-analysis/refresh

刷新涨幅榜数据

**请求体**:
```json
{
  "limit": 20,
  "market": "spot"
}
```

## 性能优化

1. **批量处理**: 使用异步请求获取多个币种的数据
2. **缓存机制**: 可以添加 Redis 缓存 TradingView 数据 (TTL: 60秒)
3. **限流保护**: 遵循 TradingView API 的速率限制
4. **代理支持**: 自动应用系统配置的代理设置

## 错误处理

常见错误及解决方案:

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| TradingView API 超时 | 网络问题或 API 限制 | 自动降级到模拟数据 |
| CCXT 连接失败 | 交易所 API 不可用 | 尝试备用交易所 |
| 数据解析失败 | API 响应格式变化 | 记录日志,返回模拟数据 |
| 代理连接失败 | 代理配置错误 | 检查 PROXY_PORT 配置 |

## 配置要求

### 环境变量 (.env)

```bash
# 交易所配置
CCXT_DEFAULT_EXCHANGE=okx  # 或 binance

# 代理配置 (可选)
PROXY_PORT=7890
# 或
PROXY_URL=socks5h://127.0.0.1:7890
```

### Python 依赖

确保安装以下包:
```
ccxt>=4.0.0
numpy>=1.24.0
requests>=2.31.0
```

## 注意事项

1. **数据延迟**: TradingView Scanner 数据可能有几秒延迟
2. **API 限制**: 避免过于频繁的请求,建议每分钟最多 60 次
3. **网络要求**: 需要稳定的网络连接访问 TradingView 和交易所
4. **数据准确性**: 技术指标仅供参考,不构成投资建议
5. **本地计算**: Heikin Ashi 和部分指标在本地计算,确保准确性

## 未来改进方向

1. **缓存优化**: 添加 Redis 缓存减少 API 调用
2. **更多指标**: 添加更多技术指标 (如 OBV, ATR, CCI)
3. **机器学习**: 使用 ML 模型提高预测准确率
4. **WebSocket**: 使用 WebSocket 实现实时数据推送
5. **多时间框架**: 综合多个时间框架的分析结果

## 测试

### 单元测试
```python
# 测试 Heikin Ashi 计算
def test_calculate_heikin_ashi():
    klines = [...]  # 测试数据
    ha_klines = service._calculate_heikin_ashi(klines)
    assert len(ha_klines) == len(klines)

# 测试趋势判断
def test_determine_trend():
    ha_klines = [...]  # 测试数据
    trend = service._determine_trend(ha_klines)
    assert trend in ['uptrend', 'downtrend', 'sideways']
```

### 集成测试
```bash
# 测试涨幅榜 API
curl http://localhost:5000/api/gainer-analysis/top-gainers?limit=5

# 测试单币种分析
curl -X POST http://localhost:5000/api/gainer-analysis/analyze-symbol \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

## 参考资料

- [TradingView API 文档](https://www.tradingview.com/api/)
- [Heikin Ashi 蜡烛图](https://www.investopedia.com/terms/h/heikin-ashi.asp)
- [CCXT 文档](https://docs.ccxt.com/)
- [技术指标详解](https://www.tradingview.com/wiki/)

## 更新日志

- **2025-01-09**: 实现真实的 TradingView 和 CCXT 数据集成
- **2025-01-09**: 添加 Heikin Ashi 蜡烛图计算
- **2025-01-09**: 实现综合评分和建议生成系统
- **2025-01-09**: 添加降级机制确保服务可用性
