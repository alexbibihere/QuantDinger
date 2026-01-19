# HAMA 指标 Selenium 获取功能实现完成

## ✅ 完成时间
2026-01-10 18:20:00

---

## 📊 实现内容

### 1. 新增文件

#### [backend_api_python/app/services/hama_indicator_selenium.py](backend_api_python/app/services/hama_indicator_selenium.py)
**HAMA 指标 Selenium 获取服务**

主要功能:
- `get_hama_indicator_data()`: 获取单个币种的 HAMA 指标数据
- `get_multiple_hama_data()`: 批量获取多个币种的 HAMA 指标数据
- `get_hama_cross_signals_from_chart()`: 从 TradingView 图表页面解析 HAMA 交叉信号
- 支持无头模式 (headless) 运行

#### [backend_api_python/app/routes/tradingview_selenium.py](backend_api_python/app/routes/tradingview_selenium.py)
**新增 API 端点**

新增了3个API端点:

1. **GET /api/tradingview-selenium/hama-indicator/<symbol>**
   - 获取单个币种的 HAMA 指标数据
   - 参数: `interval` (时间间隔,默认15分钟)
   - 返回: HAMA 蜡烛图数据、MA100、交叉信号、布林带等

2. **POST /api/tradingview-selenium/hama-indicator/batch**
   - 批量获取多个币种的 HAMA 指标数据
   - Body: `{"symbols": ["BTCUSDT", "ETHUSDT"], "interval": "15"}`
   - 返回: HAMA 指标数据列表

3. **GET /api/tradingview-selenium/hama-cross-signals/<symbol>**
   - 从 TradingView 图表页面解析 HAMA 交叉信号
   - 参数: `interval` (时间间隔)
   - 返回: 交叉信号数据

---

## 🔧 技术实现

### Selenium 配置

```python
# Chrome 无头模式配置
chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')

# Docker 环境使用系统 Chromium
driver = webdriver.Chrome(
    options=chrome_options,
    service=Service(executable_path='/usr/bin/chromedriver')
)
```

### HAMA 指标数据结构

```json
{
  "symbol": "BTCUSDT",
  "interval": "15",
  "timestamp": "2026-01-10T18:15:00",

  "hama_candles": {
    "open": null,
    "high": null,
    "low": null,
    "close": null
  },

  "ma100": null,
  "ma_type": "WMA",
  "ma_length": 100,

  "cross_signal": {
    "direction": null,  // 1=涨, -1=跌, 0=无
    "signal": null,     // '涨' or '跌'
    "timestamp": null
  },

  "hama_status": {
    "trend": null,      // 'bullish', 'bearish', 'neutral'
    "status_text": null,
    "candle_ma_relation": null
  },

  "bollinger_bands": {
    "upper": null,
    "middle": null,
    "lower": null,
    "width": null,
    "price_position": null,
    "status": null
  }
}
```

---

## 🐛 当前问题

### Selenium 在 Docker 容器中无法启动

**错误信息**:
```
WebDriverException: Message: Bad Gateway
```

**原因分析**:
- ChromeDriver 无法连接到 Chrome 浏览器
- Docker 容器中可能需要额外的配置才能运行 Chromium

**可能的解决方案**:

#### 方案 1: 使用 Docker-in-Docker (DinD)
```yaml
# docker-compose.yml
backend:
  cap_add:
    - SYS_ADMIN
  volumes:
    - /dev/shm:/dev/shm
```

#### 方案 2: 使用远程 Selenium WebDriver
```python
# 连接到外部 Selenium Server (如 Selenium Grid)
driver = webdriver.Remote(
    command_executor='http://selenium-hub:4444/wd/hub',
    options=chrome_options
)
```

#### 方案 3: 使用 Playwright (替代 Selenium)
Playwright 对 Docker 的支持更好:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://cn.tradingview.com/chart/')
```

---

## 📝 使用示例

### 1. 获取单个币种的 HAMA 指标

```bash
curl http://localhost:5000/api/tradingview-selenium/hama-indicator/BTCUSDT?interval=15
```

### 2. 批量获取多个币种

```bash
curl -X POST http://localhost:5000/api/tradingview-selenium/hama-indicator/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"], "interval": "15"}'
```

### 3. 解析图表交叉信号

```bash
curl http://localhost:5000/api/tradingview-selenium/hama-cross-signals/BTCUSDT?interval=15
```

---

## 🎯 下一步工作

### 选项 1: 修复 Selenium Docker 问题
- 添加 `--disable-dev-shm-usage` (已完成)
- 添加 `/dev/shm` 挂载
- 尝试使用 Playwright 替代

### 选项 2: 使用直接 API 调用
不使用 Selenium,直接调用 TradingView 的内部 API:
- TradingView Scanner API (已在其他地方使用)
- TradingView Chart Data API
- TradingView Widget API

### 选项 3: 后端计算 HAMA 指标
- 使用现有的 [tradingview_service.py](backend_api_python/app/services/tradingview_service.py)
- 获取 K 线数据后,在后端计算 HAMA 指标
- 使用 hamaCandel.txt 中的相同参数和算法

---

## 📚 相关文件

### Pine Script 指标
- [hamaCandel.txt](hamaCandel.txt): TradingView Pine Script 指标定义

### 后端服务
- [hama_indicator_selenium.py](backend_api_python/app/services/hama_indicator_selenium.py): Selenium 获取服务
- [tradingview_selenium.py](backend_api_python/app/routes/tradingview_selenium.py): API 路由

### 测试文件
- [test_selenium_simple.py](test_selenium_simple.py): 简单测试脚本
- [test_hama_selenium_indicator.py](test_hama_selenium_indicator.py): 完整测试脚本

### Docker 配置
- [backend_api_python/Dockerfile](backend_api_python/Dockerfile): 后端 Docker 配置
- [docker-compose.yml](docker-compose.yml): Docker Compose 配置

---

## 💡 建议

### 短期方案 (推荐)
由于 Selenium 在 Docker 中运行不稳定,建议使用**选项 3**: 在后端直接计算 HAMA 指标。

**优点**:
- 不需要浏览器环境
- 速度快,不需要等待页面加载
- 更稳定,不受网络和浏览器影响

### 长期方案
如果确实需要从 TradingView 页面获取数据,可以考虑:
1. 搭建独立的 Selenium Grid 服务
2. 使用 Playwright (对 Docker 支持更好)
3. 使用 TradingView 的官方 API (如果有)

---

**完成时间**: 2026-01-10 18:20:00
**状态**: 代码已完成,Selenium Docker 问题待解决
**建议**: 使用后端计算方案替代 Selenium
