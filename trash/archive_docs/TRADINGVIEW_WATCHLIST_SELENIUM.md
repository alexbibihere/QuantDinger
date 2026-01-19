# ✅ TradingView关注列表 + HAMA指标 - Selenium爬取方案

## 📋 已有服务

**文件**: [backend_api_python/app/services/tradingview_watchlist.py](backend_api_python/app/services/tradingview_watchlist.py)

**现有功能**:
- ✅ 通过TradingView API获取关注列表
- ✅ 使用Cookie认证
- ✅ 过滤USDT交易对
- ✅ 按涨跌幅排序

## 🎯 新方案: Selenium模拟浏览器

### 方案概述

使用Selenium模拟浏览器,可以:
1. ✅ 访问您的TradingView图表页面
2. ✅ 读取页面上的所有指标(HAMA、RSI、MACD等)
3. ✅ 获取关注列表中的所有币种
4. ✅ 绕过API限制

### 使用方法

#### 方法1: 提供TradingView图表URL

```python
from app.services.tradingview_watchlist_selenium import get_tradingview_watchlist_indicators

# 您的TradingView图表URL
watchlist_url = "https://cn.tradingview.com/chart/jvR08dsB/"

# 获取关注列表和HAMA指标
result = get_tradingview_watchlist_indicators(watchlist_url)

for item in result:
    print(f"{item['symbol']}:")
    print(f"  HAMA趋势: {item['indicators']['hama']['trend']}")
    print(f"  交易建议: {item['indicators']['hama']['recommendation']}")
    print(f"  RSI: {item['indicators']['technical']['rsi']}")
```

#### 方法2: 自动登录获取用户关注列表

```python
from app.services.tradingview_watchlist_selenium import get_user_watchlist_indicators

# 自动打开浏览器,等待您登录
result = get_user_watchlist_indicators()

# 程序会提示:
# "⚠️ 需要登录TradingView"
# "请在浏览器中登录,然后按Enter继续..."
```

### 数据获取流程

```
1. 启动Chrome浏览器
   ↓
2. 访问TradingView图表页面
   ↓
3. 检查是否需要登录
   ↓ (如果需要)
4. 等待用户手动登录
   ↓
5. 从页面提取币种列表
   ↓
6. 获取每个币种的HAMA指标
   ↓
7. 返回完整数据
```

### 返回数据格式

```json
[
  {
    "symbol": "BTCUSDT",
    "description": "Bitcoin",
    "exchange": "Binance",
    "market": "futures",
    "indicators": {
      "hama": {
        "trend": "uptrend",
        "recommendation": "BUY",
        "confidence": 0.75,
        "candle_pattern": "bullish_engulfing"
      },
      "technical": {
        "rsi": 65.2,
        "macd": "bullish",
        "ema_20": 45000,
        "ema_50": 43000
      },
      "signals": {
        "ha_close": 45200,
        "ha_open": 44800,
        "trend_strength": "strong"
      }
    },
    "timestamp": "2026-01-09T23:30:00"
  }
]
```

## 🔧 Docker配置

### 需要安装Chrome

修改 `backend_api_python/Dockerfile`:

```dockerfile
# 安装Chrome浏览器
RUN apt-get update && \
    apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 安装ChromeDriver
RUN apt-get update && \
    apt-get install -y chromium-driver \
    && rm -rf /var/lib/apt/lists/*
```

### 重新构建Docker

```bash
cd d:\github\QuantDinger
docker compose build --no-cache backend
docker compose up -d backend
```

## 📝 使用示例

### Python脚本调用

```python
from app.services.tradingview_watchlist_selenium import get_tradingview_watchlist_indicators

# 获取您的TradingView图表数据
url = "https://cn.tradingview.com/chart/jvR08dsB/"
data = get_tradingview_watchlist_indicators(url)

# 按HAMA建议排序
buy_signals = [d for d in data if d['indicators']['hama']['recommendation'] == 'BUY']
sell_signals = [d for d in data if d['indicators']['hama']['recommendation'] == 'SELL']

print(f"买入信号: {len(buy_signals)}个")
print(f"卖出信号: {len(sell_signals)}个")
```

### API端点(可选)

可以创建新的API端点:

```python
# backend_api_python/app/routes/tradingview_watchlist.py

@bp.route('/watchlist/indicators', methods=['GET'])
def get_watchlist_indicators_api():
    """获取TradingView关注列表的HAMA指标"""
    from app.services.tradingview_watchlist_selenium import get_tradingview_watchlist_indicators

    url = request.args.get('url')
    result = get_tradingview_watchlist_indicators(url)

    return jsonify({
        'success': True,
        'count': len(result),
        'data': result
    })
```

## 🎯 优势

✅ **直接读取TradingView数据** - 无需API限制
✅ **获取所有指标** - HAMA、RSI、MACD等
✅ **支持关注列表** - 您关注的币种
✅ **实时数据** - 与TradingView同步
✅ **绕过Binance限制** - 不依赖Binance API

## ⚠️ 注意事项

1. **需要手动登录** - 第一次需要浏览器登录
2. **浏览器窗口** - 会打开Chrome窗口
3. **速度较慢** - 需要加载页面
4. **Docker体积** - 需要安装Chrome

## 📊 快速测试

### 本地测试(无需Docker)

```bash
cd backend_api_python

# 安装依赖
pip install selenium webdriver-manager

# 测试
python -c "
from app.services.tradingview_watchlist_selenium import get_tradingview_watchlist_indicators
result = get_tradingview_watchlist_indicators('https://cn.tradingview.com/chart/jvR08dsB/')
print(f'获取到{len(result)}个币种')
"
```

## 🚀 下一步

需要我帮您:

1. **创建Selenium服务** - 实现模拟浏览器功能
2. **添加API端点** - 前端可以调用
3. **配置Docker** - 安装Chrome
4. **测试功能** - 验证能否读取您的关注列表

**请告诉我您的TradingView图表URL**,我可以立即帮您测试! 🎯

---

**示例URL**: https://cn.tradingview.com/chart/jvR08dsB/
