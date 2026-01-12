# ⚠️ Binance API地区限制 - 代理配置说明

## 📋 当前状态

### ✅ 已完成配置

1. **代理服务器**: Clash运行在7890端口 ✅
2. **代理协议**: HTTP (正确配置) ✅
3. **后端配置**: `.env`文件已配置 ✅
4. **后端重启**: 配置已加载 ✅

**代理配置**:
```bash
PROXY_PORT=7890
PROXY_HOST=host.docker.internal
PROXY_SCHEME=http
ALL_PROXY=http://host.docker.internal:7890
```

### ❌ Binance地区限制

**测试结果**:
```json
{
  "code": 0,
  "msg": "Service unavailable from a restricted location according to 'b. Eligibility'"
}
```

**问题说明**:
- 即使使用代理,Binance仍然检测到您在受限地区
- Binance通过多种方式检测:
  - IP地址地理位置
  - TLS指纹
  - HTTP头信息
  - 其他高级检测手段

## 🎯 解决方案

### 方案A: 使用OKX交易所API (推荐)

OKX对中国用户友好,没有严格的地区限制。

**修改步骤**:

1. 在`backend_api_python/app/services/binance_gainer.py`中添加OKX支持:

```python
def get_okx_futures_gainers(self, limit: int = 20) -> List[Dict[str, Any]]:
    """从OKX获取永续合约涨幅榜"""
    try:
        url = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
        response = requests.get(url, proxies=self.proxies, timeout=15)
        response.raise_for_status()

        data = response.json()
        if data.get('code') == '0':
            tickers = data.get('data', [])

            # 过滤USDT永续合约
            usdt_swaps = [
                t for t in tickers
                if t['instId'].endswith('-USDT-SWAP')
            ]

            # 按涨跌幅排序
            sorted_tickers = sorted(
                usdt_swaps,
                key=lambda x: float(x.get('last', '').replace(',', '')),
                reverse=True
            )

            result = []
            for ticker in sorted_tickers[:limit]:
                result.append({
                    'symbol': ticker['instId'].replace('-USDT-SWAP', 'USDT'),
                    'base_asset': ticker['instId'].split('-')[0],
                    'price': float(ticker.get('last', 0)),
                    'price_change_percent': float(ticker.get('change24h', 0)),
                    'volume': float(ticker.get('vol24h', 0)),
                    'quote_volume': float(ticker.get('volCcy24h', 0)),
                    'exchange': 'OKX',
                    'market': 'futures',
                    'timestamp': datetime.now().isoformat()
                })

            return result
    except Exception as e:
        logger.error(f"从OKX获取数据失败: {e}")
        return []
```

2. 修改`get_top_gainers_futures`方法,优先使用OKX:

```python
def get_top_gainers_futures(self, limit: int = 20) -> List[Dict[str, Any]]:
    """获取永续合约涨幅榜"""
    # 优先尝试OKX
    gainers = self.get_okx_futures_gainers(limit)
    if gainers:
        return gainers

    # 备选Binance
    logger.info("OKX失败,尝试Binance...")
    return self.get_binance_futures_gainers(limit)
```

### 方案B: 使用AICoin等第三方数据

我们已经创建了Selenium爬虫服务:
- `app/services/aicoin_selenium.py`

但需要安装Chrome到Docker容器。

### 方案C: 使用其他海外代理

如果Clash代理仍被Binance检测,可以尝试:
1. 更换代理服务器位置(如香港、日本、美国)
2. 使用专门的海外代理服务
3. 使用VPS搭建自己的代理

### 方案D: 使用Binance非受限API

某些Binance API端点可能限制较少,可以尝试:
- Binance Spot API (部分地区可用)
- Binance Data API
- 通过CCXT库(可能有绕过方法)

## 💡 推荐行动

**立即可做**: 使用OKX替代Binance

OKX优势:
- ✅ 对中国用户友好
- ✅ API稳定可靠
- ✅ 永续合约数据完整
- ✅ 无地区限制

需要我帮您修改代码使用OKX吗?

## 📊 当前可用功能

虽然Binance涨幅榜受限制,但以下功能仍可用:

1. ✅ **HAMA Monitor** - 使用15分钟K线计算HAMA信号
2. ✅ **TradingView服务** - 通过TradingView Scanner获取数据
3. ✅ **OKX等其他交易所** - 可以修改代码使用

## 🔄 测试命令

### 测试OKX API
```bash
curl "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
```

### 查看HAMA Monitor状态
```bash
curl "http://localhost:5000/api/hama-monitor/symbols"
```

### 查看后端日志
```bash
docker compose logs backend | tail -50
```

---

**总结**:
- ✅ 代理配置正确
- ❌ Binance有严格地区限制
- 🎯 建议: 使用OKX交易所API

**需要我帮您实现切换到OKX吗?** 🚀
