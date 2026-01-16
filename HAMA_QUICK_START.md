# HAMA 指标快速使用指南

## 🚀 快速开始

### 1. 测试 HAMA API

```bash
# 健康检查
curl http://localhost:5000/api/hama/health

# 预期输出：
# {"success": true, "service": "HAMA Indicator API", "status": "running"}
```

### 2. 计算 HAMA 指标

```bash
# 使用 Python 脚本测试
cd backend_api_python
python test_hama_complete.py
```

### 3. 在代码中使用

```python
import requests

# 准备 OHLCV 数据（格式：[[timestamp, open, high, low, close, volume], ...]）
# 至少需要 100 条数据，推荐 500 条
ohlcv_data = [
    [1705334400000, 3000.0, 3050.0, 2950.0, 3020.0, 1000.0],
    [1705334460000, 3020.0, 3080.0, 3010.0, 3065.0, 1200.0],
    # ... 更多数据
]

# 调用 HAMA 计算 API
response = requests.post(
    'http://localhost:5000/api/hama/calculate',
    json={
        'symbol': 'BTCUSDT',
        'ohlcv': ohlcv_data
    }
)

# 获取结果
result = response.json()

if result['success']:
    hama = result['data']['hama']
    print(f"HAMA 收盘价: {hama['close']}")
    print(f"HAMA 颜色: {hama['color']}")
    print(f"HAMA MA: {hama['ma']}")
    print(f"趋势: {result['data']['trend']['direction']}")

    # 检查交叉信号
    if hama['cross_up']:
        print("🟢 金叉买入信号！")
    elif hama['cross_down']:
        print("🔴 死叉卖出信号！")
```

### 4. 在策略中使用

```python
from app.services.hama_calculator import calculate_hama_from_ohlcv

def my_strategy(ohlcv_data):
    """自定义策略使用 HAMA 指标"""
    # 计算 HAMA
    hama_result = calculate_hama_from_ohlcv(ohlcv_data)

    if not hama_result:
        return None

    hama = hama_result['hama']
    trend = hama_result['trend']

    # 交易逻辑
    if hama['cross_up'] and trend['direction'] == 'up':
        return 'BUY'
    elif hama['cross_down'] and trend['direction'] == 'down':
        return 'SELL'
    else:
        return 'HOLD'
```

## 📊 返回数据说明

### HAMA 蜡烛图数据

```json
{
  "hama": {
    "open": 2995.0,      // HAMA 开盘价
    "high": 3005.0,      // HAMA 最高价
    "low": 2990.0,       // HAMA 最低价
    "close": 3000.0,     // HAMA 收盘价（主要关注）
    "ma": 2998.0,        // HAMA MA 线
    "color": "green",    // 颜色：green（上涨）/ red（下跌）/ gray（中性）
    "cross_up": false,   // 是否金叉
    "cross_down": false  // 是否死叉
  }
}
```

### 趋势数据

```json
{
  "trend": {
    "direction": "up",   // 趋势方向：up / down / neutral
    "rising": true,      // MA 线是否上升
    "falling": false     // MA 线是否下降
  }
}
```

### 布林带数据

```json
{
  "bollinger_bands": {
    "upper": 3100.0,     // 上轨
    "basis": 3000.0,     // 中轨（基准）
    "lower": 2900.0,     // 下轨
    "width": 0.067,      // 带宽（上轨-下轨）/中轨
    "squeeze": false,    // 是否收缩（宽度 < 0.1）
    "expansion": false   // 是否扩张（宽度 > 0.15）
  }
}
```

## 🔧 常见问题

### Q: 需要多少条 OHLCV 数据？

A: 至少 100 条，推荐 500 条。数据越多，计算越准确。

### Q: 时间周期有什么要求？

A: 建议使用统一的时间周期，如 15m、1h、4h 等。不同周期的数据不能混合计算。

### Q: 如何获取实时 OHLCV 数据？

A: 可以从以下数据源获取：
- Binance API: `https://api.binance.com/api/v3/klines`
- OKX API
- 系统现有的 K线接口: `/api/kline`

### Q: HAMA 计算需要多长时间？

A: 500 条数据大约需要 10-50 毫秒。

### Q: 如何调整 HAMA 参数？

A: 修改 `app/services/hama_calculator.py` 中的参数：

```python
self.open_length = 45   # 修改开盘价 EMA 周期
self.high_length = 20   # 修改最高价 EMA 周期
self.low_length = 20    # 修改最低价 EMA 周期
self.close_length = 40  # 修改收盘价 EMA 周期
self.ma_length = 100    # 修改 MA 长度
```

## 📞 技术支持

如有问题，请查看：
- [完整实现文档](TRADINGVIEW_HAMA_IMPLEMENTATION.md)
- HAMA 计算器源码：`app/services/hama_calculator.py`
- API 路由源码：`app/routes/hama_indicator.py`
- Pine Script 参考：`file/hamaAicoin.txt`
