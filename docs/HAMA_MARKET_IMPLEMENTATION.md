# HAMA 行情实现完整文档

> 版本: 1.0
> 更新时间: 2025-01-19
> 作者: QuantDinger Team

---

## 目录

- [一、系统概述](#一系统概述)
- [二、整体架构](#二整体架构)
- [三、核心组件](#三核心组件)
- [四、API 接口文档](#四api-接口文档)
- [五、数据库设计](#五数据库设计)
- [六、前端展示逻辑](#六前端展示逻辑)
- [七、数据流程](#七数据流程)
- [八、配置说明](#八配置说明)
- [九、使用场景](#九使用场景)
- [十、关键文件清单](#十关键文件清单)
- [十一、故障排查](#十一故障排查)
- [十二、开发指南](#十二开发指南)

---

## 一、系统概述

### 1.1 系统简介

HAMA 行情系统是 QuantDinger 平台的核心功能之一，用于获取和展示基于 TradingView HAMA（Heiken Ashi Moving Average）指标的市场行情数据。

### 1.2 设计理念

- **本地优先**: 主要数据来自本地计算，确保速度和隐私
- **双重验证**: 本地计算 + TradingView OCR 识别，确保准确性
- **完全免费**: 使用开源 OCR 引擎，无需付费 API
- **可扩展性**: 支持多种 OCR 引擎和浏览器类型

### 1.3 技术栈

| 组件 | 技术选型 |
|------|---------|
| **后端框架** | Flask 2.3.3 |
| **数据库** | SQLite / MySQL |
| **浏览器自动化** | Playwright + playwright-stealth |
| **OCR 引擎** | RapidOCR / PaddleOCR / Tesseract / EasyOCR |
| **指标计算** | Pandas + NumPy |
| **邮件通知** | SMTP |

---

## 二、整体架构

### 2.1 双数据源架构

```
┌─────────────────────────────────────────────────────────────┐
│                      HAMA 行情系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌─────────────────────────┐ │
│  │   本地计算（主要）    │      │   Brave监控（验证）      │ │
│  │                      │      │                         │ │
│  │ • 速度: 2-5秒        │      │ • 速度: ~60秒/次        │ │
│  │ • 成本: 免费         │      │ • 成本: 免费            │ │
│  │ • 准确度: 99%+       │      │ • 准确度: 90-95%        │ │
│  │ • 数据源: Binance    │      │ • 数据源: TradingView   │ │
│  │ • API: /symbol       │      │ • API: /brave/monitor   │ │
│  └──────────────────────┘      └─────────────────────────┘ │
│            ↓                            ↓                   │
│      前端优先展示              数据库缓存                    │
│      (完整HAMA数据)           (辅助验证)                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 系统层次

```
┌────────────────────────────────────────────────────────────┐
│                        前端展示层                            │
│  • HAMA 行情页面                                            │
│  • 监控列表 (Brave 数据优先)                                │
│  • 信号扫描页面                                             │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                        API 路由层                            │
│  • /api/hama-market/*                                      │
│  • 请求验证、参数解析、响应封装                              │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                        服务层                                │
│  ┌──────────────────┐      ┌──────────────────────────┐   │
│  │  本地计算服务     │      │   Brave 监控服务          │   │
│  │  • HAMA计算器    │      │   • OCR 提取器            │   │
│  │  • 布林带计算    │      │   • 邮件通知器            │   │
│  │  • 趋势判断      │      │   • 数据库缓存            │   │
│  └──────────────────┘      └──────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│                        数据层                                │
│  • SQLite / MySQL 数据库                                    │
│  • Binance API (K线数据)                                    │
│  • TradingView (图表截图)                                   │
└────────────────────────────────────────────────────────────┘
```

---

## 三、核心组件

### 3.1 本地计算服务

**文件位置**: [`app/services/hama_calculator.py`](../backend_api_python/app/services/hama_calculator.py)

#### 3.1.1 功能说明

基于 TradingView Pine Script 代码实现 HAMA 指标的本地计算，完全复现 TradingView 的算法逻辑。

#### 3.1.2 核心算法

```python
class HAMACalculator:
    """HAMA 指标计算器"""

    # HAMA 参数（与 Pine Script 完全一致）
    open_length = 45    # 开盘价 EMA 周期
    high_length = 20    # 最高价 EMA 周期
    low_length = 20     # 最低价 EMA 周期
    close_length = 40   # 收盘价 WMA 周期（注意：WMA）
    ma_length = 100     # MA WMA 长度（注意：WMA）

    # 布林带参数
    bb_length = 400     # 布林带 SMA 周期（注意：SMA）
    bb_mult = 2.0       # 标准差倍数
```

#### 3.1.3 计算流程

```python
def calculate_hama(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算 HAMA 指标

    步骤:
    1. 计算 HAMA 源数据
    2. 计算 HAMA 蜡烛图
    3. 计算 HAMA MA 线
    4. 判断颜色/趋势
    5. 判断交叉信号
    6. 计算布林带
    7. 判断布林带状态
    8. 判断 MA 趋势
    """

    # 步骤 1: 计算 HAMA 源数据
    df['source_open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
    df['source_high'] = df[['high', 'close']].max(axis=1)
    df['source_low'] = df[['low', 'close']].min(axis=1)
    df['source_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    # 步骤 2: 计算 HAMA 蜡烛图
    df['hama_open'] = EMA(df['source_open'], 45)
    df['hama_high'] = EMA(df['source_high'], 20)
    df['hama_low'] = EMA(df['source_low'], 20)
    df['hama_close'] = WMA(df['source_close'], 40)  # 注意：WMA

    # 步骤 3: 计算 HAMA MA 线
    df['hama_ma'] = WMA(df['close'], 100)  # 注意：WMA

    # 步骤 4: 判断颜色/趋势
    df['hama_color'] = df['hama_open'] > df['hama_open'].shift(1) ? 'green' : 'red'

    # 步骤 5: 判断交叉信号
    df['hama_cross_up'] = (hama_close > hama_ma) & (前一根hama_close <= 前一根hama_ma)
    df['hama_cross_down'] = (hama_close < hama_ma) & (前一根hama_close >= 前一根hama_ma)

    # 步骤 6: 计算布林带
    df['bb_basis'] = SMA(df['close'], 400)  # 注意：SMA
    df['bb_dev'] = STD(df['close'], 400)
    df['bb_upper'] = bb_basis + bb_dev * 2.0
    df['bb_lower'] = bb_basis - bb_dev * 2.0

    # 步骤 7: 布林带状态
    df['bb_width'] = (bb_upper - bb_lower) / bb_basis
    df['bb_squeeze'] = bb_width < 0.1   # 收缩
    df['bb_expansion'] = bb_width > 0.15  # 扩张

    # 步骤 8: MA 趋势
    df['hama_rising'] = hama_ma > 前一根hama_ma
    df['hama_falling'] = hama_ma < 前一根hama_ma
```

#### 3.1.4 返回数据格式

```json
{
    "symbol": "BTCUSDT",
    "timestamp": 1737265200000,
    "open": 33100.50,
    "high": 33250.00,
    "low": 33000.00,
    "close": 33150.00,
    "hama": {
        "open": 33120.00,
        "high": 33200.00,
        "low": 33050.00,
        "close": 33140.00,
        "ma": 33080.00,
        "color": "green",
        "cross_up": true,
        "cross_down": false
    },
    "bollinger_bands": {
        "upper": 33500.00,
        "basis": 33150.00,
        "lower": 32800.00,
        "width": 0.021,
        "squeeze": false,
        "expansion": true
    },
    "trend": {
        "direction": "up",
        "rising": true,
        "falling": false
    }
}
```

---

### 3.2 Brave 监控服务

**文件位置**: [`app/services/hama_brave_monitor_mysql.py`](../backend_api_python/app/services/hama_brave_monitor_mysql.py)

#### 3.2.1 功能说明

使用 Playwright + RapidOCR 从 TradingView 图表自动识别 HAMA 指标，并保存到数据库。

#### 3.2.2 工作流程

```
1. 启动无头浏览器
   ├─ 支持 Chromium/Firefox/WebKit/Brave
   ├─ 加载代理配置（可选）
   └─ 加载 TradingView Cookie（自动登录）

2. 访问 TradingView 图表
   └─ URL: https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3ABTCUSDT&interval=15

3. 精确定位截图
   └─ 截取右下角 HAMA 信息面板（右侧 28%, 底部 40%）

4. RapidOCR 识别
   ├─ 提取面板结构化文本
   └─ 解析: 价格、HAMA状态、趋势、布林带状态、最近交叉

5. 保存到数据库
   └─ 表: hama_monitor_cache

6. 邮件通知（可选）
   ├─ 检测趋势变化
   └─ 发送邮件通知
```

#### 3.2.3 邮件通知规则

```python
"""
邮件发送逻辑：
1. 只有第一次检测到明确趋势（green/red）时才发送邮件
2. 如果已发送过邮件，就不再发送
3. 除非：HAMA状态变为盘整（neutral/gray）以外状态，才重置并发送新邮件

触发条件：
- 首次检测到明确趋势
- 从盘整变为明确趋势
- 趋势方向发生变化（up ↔ down）
- 颜色变化（green ↔ red）
"""

def _check_and_notify_trend(symbol, hama_data, screenshot_filename):
    # 获取当前状态
    current_color = hama_data.get('color')
    current_trend = hama_data.get('trend')

    # 获取上次状态
    last_state = self.last_states.get(symbol, {})

    # 获取邮件发送状态
    email_status = self.get_email_status(symbol)
    email_already_sent = email_status['email_sent']

    # 判断是否为明确的趋势状态
    has_clear_trend = current_color in ['green', 'red'] and current_trend in ['up', 'down']

    # 判断是否为盘整状态
    is_neutral = current_color not in ['green', 'red'] or current_trend not in ['up', 'down']

    should_notify = False

    # 情况1：当前是盘整状态，重置邮件状态
    if is_neutral and email_already_sent:
        self.reset_email_status(symbol)

    # 情况2：首次检测到明确趋势 → 发送邮件
    if has_clear_trend and not last_color:
        should_notify = True

    # 情况3：从盘整变为明确趋势 → 发送邮件
    elif has_clear_trend and last_color not in ['green', 'red']:
        should_notify = True

    # 情况4：趋势方向发生变化 → 发送邮件
    elif last_trend in ['up', 'down'] and current_trend in ['up', 'down'] and last_trend != current_trend:
        should_notify = True

    # 情况5：颜色变化 → 发送邮件
    elif last_color in ['green', 'red'] and current_color in ['green', 'red'] and last_color != current_color:
        should_notify = True

    # 检查是否已发送过邮件（避免重复发送）
    if should_notify and email_already_sent:
        should_notify = False

    # 发送邮件
    if should_notify:
        success = self.email_notifier.notify_trend_formed(...)
        if success:
            self.update_email_status(symbol)
```

#### 3.2.4 监控器状态管理

```python
class HamaBraveMonitor:
    """HAMA Brave 浏览器监控器"""

    def __init__(self, db_client=None, cache_ttl: int = 900, enable_email: bool = True):
        self.db_client = db_client
        self.cache_ttl = cache_ttl
        self.is_monitoring = False
        self.monitor_thread = None
        self.ocr_extractor = None
        self.email_notifier = None

        # 记录上次状态（用于检测变化）
        self.last_states = {}  # {symbol: {'trend': ..., 'color': ..., 'value': ...}}

    def start_monitoring(self, symbols: List[str], interval: int = 600, browser_type: str = 'chromium'):
        """启动持续监控（后台线程）"""
        # 每 interval 秒执行一次监控
        # 后台线程自动运行

    def stop_monitoring(self):
        """停止持续监控"""

    def monitor_batch(self, symbols: List[str], browser_type: str = 'chromium'):
        """批量监控多个币种"""
        # 返回监控结果统计
```

---

### 3.3 OCR 提取器

**文件位置**: [`app/services/hama_ocr_extractor.py`](../backend_api_python/app/services/hama_ocr_extractor.py)

#### 3.3.1 支持的 OCR 引擎

| OCR 引擎 | 速度 | 准确度 | 成本 | 推荐度 | 安装命令 |
|---------|------|--------|------|--------|---------|
| **RapidOCR** | ⚡⚡⚡ | 90-95% | 免费 | ⭐⭐⭐⭐⭐ | `pip install rapidocr-onnxruntime` |
| **PaddleOCR** | ⚡⚡ | 90-95% | 免费 | ⭐⭐⭐⭐ | `pip install paddleocr paddlepaddle` |
| **Tesseract** | ⚡ | 80-85% | 免费 | ⭐⭐⭐ | `pip install pytesseract` |
| **EasyOCR** | ⚡ | 85-90% | 免费 | ⭐⭐⭐ | `pip install easyocr` |

#### 3.3.2 OCR 解析逻辑

```python
def _parse_ocr_result(text_lines: List[str]) -> Dict[str, Any]:
    """
    从右下角 HAMA 面板提取数据

    面板格式:
    ┌─────────────────────┐
    │ 价格: 3311.73       │
    │ HAMA状态: 上涨      │
    │ 状态: 收缩          │
    │ 最近交叉: 涨 5根前  │
    └─────────────────────┘
    """

    # 1. 识别价格
    price_patterns = [
        r'价格\s*[:：]?\s*([\d,]+\.?\d*)',
        r'Price\s*[:：]?\s*([\d,]+\.?\d*)',
    ]

    # 2. 识别 HAMA 状态
    hama_status_patterns = [
        r'HAMA状态\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
        r'HAMA\s*Status\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
    ]

    # 3. 识别布林带状态
    bb_status_patterns = [
        r'状态\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
        r'Status\s*[:：]?\s*([^\s]+(?:\s+[^\s]+)?)',
    ]

    # 4. 识别最近交叉
    cross_patterns = [
        r'最近交叉\s*[:：]?\s*([^\n]+)',
        r'Last\s*Cross\s*[:：]?\s*([^\n]+)',
    ]

    # 5. 如果仍未识别出趋势，尝试从全局文本中查找
    # 6. 构建返回结果
```

#### 3.3.3 截图区域配置

```python
# 计算截图区域: 精确定位到右下角 HAMA 指标面板
clip = {
    'x': int(page_width * 0.72),   # 从页面 72% 处开始（右侧28%）
    'y': int(page_height * 0.60),  # 从页面 60% 处开始（底部40%）
    'width': int(page_width * 0.28),   # 截取右侧28%宽度
    'height': int(page_height * 0.40)  # 截取底部40%高度
}
```

---

## 四、API 接口文档

**基础路径**: `/api/hama-market`

### 4.1 监控列表接口

#### 4.1.1 获取监控列表

```http
GET /api/hama-market/watchlist
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbols | string | 否 | 币种列表，逗号分隔（默认: DEFAULT_SYMBOLS） |
| market | string | 否 | 市场（spot/futures，默认: spot） |

**响应示例**:
```json
{
    "success": true,
    "data": {
        "watchlist": [
            {
                "symbol": "BTCUSDT",
                "price": 3311.73,
                "hama_brave": {
                    "hama_trend": "up",
                    "hama_color": "green",
                    "hama_value": 3311.73,
                    "screenshot_path": "hama_brave_BTCUSDT_1234567890.png",
                    "screenshot_url": "/screenshot/hama_brave_BTCUSDT_1234567890.png",
                    "cached_at": "2025-01-19T10:30:00",
                    "cache_source": "brave_browser"
                }
            }
        ]
    }
}
```

**数据源**: SQLite 数据库（Brave 监控缓存）

---

### 4.2 单个币种接口

#### 4.2.1 获取单个币种 HAMA 指标

```http
GET /api/hama-market/symbol
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 币种（如: BTCUSDT） |
| interval | string | 否 | K线周期（默认: 15m） |
| limit | integer | 否 | K线数量（默认: 500） |

**响应示例**:
```json
{
    "success": true,
    "data": {
        "symbol": "BTCUSDT",
        "timestamp": 1737265200000,
        "open": 33100.50,
        "high": 33250.00,
        "low": 33000.00,
        "close": 33150.00,
        "hama": {
            "open": 33120.00,
            "high": 33200.00,
            "low": 33050.00,
            "close": 33140.00,
            "ma": 33080.00,
            "color": "green",
            "cross_up": true,
            "cross_down": false
        },
        "bollinger_bands": {
            "upper": 33500.00,
            "basis": 33150.00,
            "lower": 32800.00,
            "width": 0.021,
            "squeeze": false,
            "expansion": true
        },
        "trend": {
            "direction": "up",
            "rising": true,
            "falling": false
        }
    }
}
```

**数据源**: 本地计算

---

### 4.3 信号扫描接口

#### 4.3.1 获取 HAMA 信号列表

```http
GET /api/hama-market/signals
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbols | string | 否 | 币种列表，逗号分隔（默认: DEFAULT_SYMBOLS） |

**响应示例**:
```json
{
    "success": true,
    "data": {
        "signals": [
            {
                "symbol": "BTCUSDT",
                "signal_type": "UP",
                "price": 33150.00,
                "hama_close": 33140.00,
                "ma": 33080.00,
                "timestamp": 1737265200000
            }
        ]
    }
}
```

**信号类型**:
- `UP`: 金叉（买入信号）
- `DOWN`: 死叉（卖出信号）

**数据源**: 本地计算

---

### 4.4 Brave 监控接口

#### 4.4.1 获取 Brave 监控器状态

```http
GET /api/hama-market/brave/status
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "available": true,
        "cached_symbols": 10,
        "cache_ttl_seconds": 900,
        "is_monitoring": true,
        "storage_type": "MySQL",
        "cached_symbols_list": ["BTCUSDT", "ETHUSDT", ...]
    }
}
```

---

#### 4.4.2 手动触发 Brave 监控

```http
POST /api/hama-market/brave/monitor
```

**请求体**:
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "browser_type": "chromium"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total": 2,
        "success": 2,
        "failed": 0,
        "symbols": {
            "BTCUSDT": {
                "success": true,
                "data": {
                    "symbol": "BTCUSDT",
                    "trend": "up",
                    "hama_color": "green",
                    ...
                }
            }
        }
    }
}
```

---

#### 4.4.3 启动持续监控

```http
POST /api/hama-market/brave/start
```

**请求体**:
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "interval": 600,
    "browser_type": "chromium"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "持续监控已启动, 间隔: 600秒"
}
```

---

#### 4.4.4 停止持续监控

```http
POST /api/hama-market/brave/stop
```

**响应示例**:
```json
{
    "success": true,
    "message": "持续监控已停止"
}
```

---

### 4.5 OCR 接口

#### 4.5.1 OCR 识别 HAMA 指标

```http
POST /api/hama-market/ocr/capture
```

**请求体**:
```json
{
    "symbol": "BTCUSDT",
    "tv_url": "https://cn.tradingview.com/chart/U1FY2qxO/"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "symbol": "BTCUSDT",
        "trend": "UP",
        "hama_color": "green",
        "candle_ma": "above",
        "contraction": "yes",
        "last_cross": null,
        "price": 3311.73,
        "screenshot": "screenshot/hama_panel_20260118_081620.png",
        "timestamp": "20260118_081620"
    }
}
```

---

#### 4.5.2 批量 OCR 识别

```http
POST /api/hama-market/ocr/batch
```

**请求体**:
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total": 2,
        "success": 2,
        "failed": 0,
        "results": [
            {
                "symbol": "BTCUSDT",
                "success": true,
                "data": {...}
            }
        ]
    }
}
```

---

### 4.6 币种管理接口

#### 4.6.1 获取监控币种列表

```http
GET /api/hama-market/symbols/list
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| enabled | boolean | 否 | 是否只返回启用的币种 |
| market | string | 否 | 市场类型（spot/futures） |

**响应示例**:
```json
{
    "success": true,
    "data": {
        "symbols": [
            {
                "id": 1,
                "symbol": "BTCUSDT",
                "symbol_name": "Bitcoin",
                "market": "spot",
                "enabled": true,
                "priority": 100,
                "notify_enabled": true,
                "notify_threshold": 2.0,
                "notes": "BTC 永续监控",
                "created_at": "2025-01-18T10:00:00",
                "updated_at": "2025-01-18T10:00:00",
                "last_monitored_at": null
            }
        ]
    }
}
```

---

#### 4.6.2 添加监控币种

```http
POST /api/hama-market/symbols/add
```

**请求体**:
```json
{
    "symbol": "MATICUSDT",
    "symbol_name": "Polygon",
    "market": "spot",
    "enabled": true,
    "priority": 0,
    "notify_enabled": false,
    "notify_threshold": 2.0,
    "notes": ""
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "id": 11,
        "symbol": "MATICUSDT"
    }
}
```

---

#### 4.6.3 更新监控币种

```http
PUT /api/hama-market/symbols/update
```

**请求体**:
```json
{
    "symbol": "BTCUSDT",
    "enabled": true,
    "priority": 100,
    "notify_enabled": true
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "updated": true
    }
}
```

---

#### 4.6.4 删除监控币种

```http
DELETE /api/hama-market/symbols/delete
```

**请求体**:
```json
{
    "symbol": "MATICUSDT"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "deleted": true
    }
}
```

---

#### 4.6.5 启用/禁用币种

```http
POST /api/hama-market/symbols/enable
```

**请求体**:
```json
{
    "symbol": "BTCUSDT",
    "enabled": true
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "symbol": "BTCUSDT",
        "enabled": true
    }
}
```

---

#### 4.6.6 批量启用/禁用币种

```http
POST /api/hama-market/symbols/batch-enable
```

**请求体**:
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "enabled": true
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "total": 2,
        "updated": 2
    }
}
```

---

### 4.7 其他接口

#### 4.7.1 获取热门币种

```http
GET /api/hama-market/hot-symbols
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", ...]
    }
}
```

---

#### 4.7.2 健康检查

```http
GET /api/hama-market/health
```

**响应示例**:
```json
{
    "success": true,
    "service": "HAMA Market API",
    "status": "running"
}
```

---

## 五、数据库设计

### 5.1 HAMA 监控缓存表

**表名**: `hama_monitor_cache`

**用途**: 存储 Brave 监控的 HAMA 数据（MySQL / SQLite）

```sql
CREATE TABLE hama_monitor_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    hama_trend VARCHAR(10),          -- up/down/neutral
    hama_color VARCHAR(10),          -- green/red/gray
    hama_value DECIMAL(20, 8),
    price DECIMAL(20, 8),
    ocr_text TEXT,
    screenshot_path VARCHAR(255),
    email_sent TINYINT(1) DEFAULT 0,
    email_sent_at TIMESTAMP NULL,
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol (symbol),
    INDEX idx_monitored_at (monitored_at),
    INDEX idx_email_sent (email_sent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| symbol | VARCHAR(20) | 币种符号（唯一） |
| hama_trend | VARCHAR(10) | HAMA 趋势（up/down/neutral） |
| hama_color | VARCHAR(10) | HAMA 颜色（green/red/gray） |
| hama_value | DECIMAL(20,8) | HAMA 数值 |
| price | DECIMAL(20,8) | 当前价格 |
| ocr_text | TEXT | OCR 识别的原始文本 |
| screenshot_path | VARCHAR(255) | 截图文件路径 |
| email_sent | TINYINT(1) | 是否已发送邮件（0=否，1=是） |
| email_sent_at | TIMESTAMP | 邮件发送时间 |
| monitored_at | TIMESTAMP | 监控时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

### 5.2 HAMA 监控币种表

**表名**: `hama_symbols`

**用途**: 管理监控币种列表

```sql
CREATE TABLE hama_symbols (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    symbol_name VARCHAR(100),
    market VARCHAR(20) DEFAULT 'spot',
    enabled TINYINT(1) DEFAULT 1,
    priority INT DEFAULT 0,
    notify_enabled TINYINT(1) DEFAULT 0,
    notify_threshold DECIMAL(5,2) DEFAULT 2.0,
    notes TEXT,
    last_monitored_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY unique_symbol (symbol),
    INDEX idx_enabled (enabled),
    INDEX idx_market (market),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| symbol | VARCHAR(20) | 币种符号（唯一） |
| symbol_name | VARCHAR(100) | 币种名称 |
| market | VARCHAR(20) | 市场（spot/futures） |
| enabled | TINYINT(1) | 是否启用（0=否，1=是） |
| priority | INT | 优先级（越大越优先） |
| notify_enabled | TINYINT(1) | 是否启用通知（0=否，1=是） |
| notify_threshold | DECIMAL(5,2) | 通知阈值（百分比） |
| notes | TEXT | 备注 |
| last_monitored_at | TIMESTAMP | 最后监控时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

### 5.3 数据库初始化

**脚本位置**: [`init_all_tables.py`](../backend_api_python/init_all_tables.py)

**使用方法**:
```bash
cd backend_api_python
python init_all_tables.py
```

---

## 六、前端展示逻辑

### 6.1 HAMA 行情页面

**路由**: `/#/hama-market`

**展示策略**:

```javascript
// 1. 优先显示 Brave 监控数据（OCR 识别）
if (watchlistItem.hama_brave) {
    // 显示 Brave 监控数据
    显示: hama_brave.hama_trend
          hama_brave.hama_color
          hama_brave.hama_value
          hama_brave.screenshot_url  // 截图
          hama_brave.cached_at       // 缓存时间
}

// 2. 无 Brave 数据时，显示为"暂无数据"
// （不显示本地计算数据，只展示通过 Brave 监控 OCR 识别的数据）
```

**数据来源**:
- API: `GET /api/hama-market/watchlist`
- 数据源: SQLite 数据库（Brave 监控缓存）

---

### 6.2 信号扫描页面

**路由**: `/#/hama-signals`

**展示内容**:
- 当前金叉/死叉信号
- 信号类型、价格、时间
- 点击可查看详情

**数据来源**:
- API: `GET /api/hama-market/signals`
- 数据源: 本地计算

---

### 6.3 截图展示

**访问路径**: `/screenshot/{filename}`

**示例**: `/screenshot/hama_brave_BTCUSDT_1234567890.png`

**存储位置**: `backend_api_python/app/screenshots/`

---

## 七、数据流程

### 7.1 本地计算流程

```
前端请求 (/api/hama-market/symbol?symbol=BTCUSDT)
    ↓
后端接收请求
    ↓
获取 Binance K线数据 (500根, 15分钟)
    ↓
本地计算 HAMA 指标
    ├─ 计算 HAMA 源数据
    ├─ 计算 HAMA 蜡烛图
    ├─ 计算 HAMA MA 线
    ├─ 判断颜色/趋势
    ├─ 判断交叉信号
    ├─ 计算布林带
    └─ 判断布林带状态
    ↓
返回完整 JSON 数据
    ⚡ 耗时: 2-5秒
```

---

### 7.2 Brave 监控流程

```
自动监控脚本 (auto_hama_monitor_mysql.py)
    ↓
每 10 分钟执行一次
    ↓
遍历监控币种列表
    ↓
对于每个币种:
    ├─ 启动 Playwright 无头浏览器
    ├─ 加载 TradingView Cookie
    ├─ 访问 TradingView 图表
    │   └─ URL: https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3ABTCUSDT&interval=15
    ├─ 等待图表渲染 (50秒)
    ├─ 精确定位截图 (右下角面板)
    ├─ RapidOCR 识别文本
    ├─ 解析 HAMA 数据
    ├─ 保存到数据库
    └─ 检测趋势变化 → 发送邮件通知（可选）
    ↓
前端从数据库读取缓存
    ⚡ 耗时: ~60秒/次
```

---

### 7.3 OCR 识别流程

```
用户触发 OCR 识别 (/api/hama-market/ocr/capture)
    ↓
后端接收请求
    ↓
启动 Playwright 浏览器
    ├─ 加载 TradingView Cookie
    └─ 支持自动登录
    ↓
访问 TradingView 图表
    ↓
等待图表渲染 (50秒)
    ↓
精确定位截图
    └─ 右下角面板 (右侧 28%, 底部 40%)
    ↓
RapidOCR 识别文本
    ├─ 提取结构化文本
    └─ 置信度过滤 (> 0.5)
    ↓
解析 OCR 结果
    ├─ 识别价格
    ├─ 识别 HAMA 状态
    ├─ 识别布林带状态
    └─ 识别最近交叉
    ↓
返回 HAMA 数据
    ⚡ 耗时: ~60秒
```

---

### 7.4 邮件通知流程

```
Brave 监控检测到数据
    ↓
解析 HAMA 数据
    ├─ 获取当前状态 (color, trend, value)
    └─ 获取上次状态
    ↓
检测趋势变化
    ├─ 首次检测到明确趋势？
    ├─ 从盘整变为明确趋势？
    ├─ 趋势方向发生变化？
    └─ 颜色变化？
    ↓
判断是否应该发送邮件
    ├─ 检查是否已发送过邮件
    └─ 避免重复发送
    ↓
构建邮件内容
    ├─ 币种信息
    ├─ 趋势变化
    ├─ 价格信息
    ├─ 截图链接
    └─ 额外数据
    ↓
发送邮件通知
    └─ SMTP 协议
    ↓
更新邮件发送状态
    └─ email_sent = 1
```

---

## 八、配置说明

### 8.1 环境变量

**配置文件**: [`.env`](../backend_api_python/.env)

```bash
# ==================== HAMA 监控配置 ====================

# 是否启用 Brave 监控
BRAVE_MONITOR_ENABLED=true

# 缓存过期时间（秒）
BRAVE_MONITOR_CACHE_TTL=900

# 是否自动启动监控
BRAVE_MONITOR_AUTO_START=true

# 监控间隔（秒）
BRAVE_MONITOR_INTERVAL=600

# 监控币种列表（逗号分隔）
BRAVE_MONITOR_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT

# 浏览器类型（chromium/firefox/webkit/brave）
BRAVE_MONITOR_BROWSER_TYPE=brave

# ==================== 邮件通知配置（可选）====================

# SMTP 服务器
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# 发件人邮箱
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# 收件人邮箱（多个邮箱用逗号分隔）
EMAIL_TO=alert@example.com,trading@example.com

# 是否启用 TLS
SMTP_USE_TLS=true

# ==================== 代理配置（可选）====================

# 代理服务器
PROXY_HOST=127.0.0.1
PROXY_PORT=7890

# 或使用代理 URL
PROXY_URL=socks5h://127.0.0.1:7890

# ==================== 数据库配置 ====================

# 数据库类型（sqlite/mysql）
DB_TYPE=sqlite

# SQLite 数据库文件路径
SQLITE_DATABASE_FILE=data/quantdinger.db

# MySQL 配置（如果使用 MySQL）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=quantdinger
```

---

### 8.2 TradingView 配置

#### 8.2.1 TradingView Cookie

**文件位置**: [`tradingview_cookies.json`](../backend_api_python/tradingview_cookies.json)

**格式**:
```json
{
    "cookies": "cookiePrivacyPreferenceBannerProduction=notApplicable; _ga=GA1.1.1866852168.1760819691; ..."
}
```

**获取方法**:
1. 打开浏览器，访问 TradingView
2. 登录账号
3. 按 F12 打开开发者工具
4. 切换到 Network 标签
5. 刷新页面
6. 找到任意请求，查看 Request Headers
7. 复制 Cookie 值

---

#### 8.2.2 TradingView 账号密码

**文件位置**: [`file/tradingview.txt`](../backend_api_python/file/tradingview.txt)

**格式**:
```
账号：your_username
密码：your_password
```

**用途**: 自动登录 TradingView（Cookie 过期时使用）

---

### 8.3 邮件通知配置

#### 8.3.1 Gmail 配置

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # 使用应用专用密码
SMTP_USE_TLS=true
```

**获取应用专用密码**:
1. 访问 https://myaccount.google.com/security
2. 开启两步验证
3. 生成应用专用密码
4. 复制密码到配置文件

---

#### 8.3.2 QQ 邮箱配置

```bash
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_authorization_code  # 使用授权码
SMTP_USE_TLS=true
```

**获取授权码**:
1. 登录 QQ 邮箱
2. 设置 → 账户
3. 开启 SMTP 服务
4. 生成授权码

---

## 九、使用场景

### 9.1 场景对比

| 场景 | 推荐方案 | API | 数据源 | 速度 | 准确度 |
|------|---------|-----|--------|------|--------|
| **生产环境** | 本地计算 | `/api/hama-market/symbol` | Binance | 2-5秒 | 99%+ |
| **验证准确性** | Brave监控 | `/api/hama-market/brave/monitor` | TradingView | ~60秒 | 90-95% |
| **日常使用** | 本地计算 | `/api/hama-market/symbol` | Binance | 2-5秒 | 99%+ |
| **高精度需求** | GPT-4o视觉 | `/api/hama-vision/extract` | TradingView | ~30秒 | 95%+ |
| **信号扫描** | 本地计算 | `/api/hama-market/signals` | Binance | 5-10秒 | 99%+ |

---

### 9.2 使用示例

#### 9.2.1 获取 BTCUSDT 的 HAMA 指标

```bash
curl "http://localhost:5000/api/hama-market/symbol?symbol=BTCUSDT&interval=15m&limit=500"
```

**响应**:
```json
{
    "success": true,
    "data": {
        "symbol": "BTCUSDT",
        "hama": {
            "open": 33120.00,
            "close": 33140.00,
            "ma": 33080.00,
            "color": "green",
            "cross_up": true
        },
        "trend": {
            "direction": "up"
        }
    }
}
```

---

#### 9.2.2 获取监控列表

```bash
curl "http://localhost:5000/api/hama-market/watchlist?symbols=BTCUSDT,ETHUSDT"
```

---

#### 9.2.3 手动触发 Brave 监控

```bash
curl -X POST "http://localhost:5000/api/hama-market/brave/monitor" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT"], "browser_type": "chromium"}'
```

---

#### 9.2.4 获取信号列表

```bash
curl "http://localhost:5000/api/hama-market/signals?symbols=BTCUSDT,ETHUSDT,BNBUSDT"
```

---

#### 9.2.5 启动持续监控

```bash
curl -X POST "http://localhost:5000/api/hama-market/brave/start" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT"], "interval": 600}'
```

---

## 十、关键文件清单

### 10.1 核心服务

| 文件 | 功能 |
|------|------|
| [`app/services/hama_calculator.py`](../backend_api_python/app/services/hama_calculator.py) | HAMA 本地计算服务 |
| [`app/services/hama_brave_monitor_mysql.py`](../backend_api_python/app/services/hama_brave_monitor_mysql.py) | Brave 监控器（MySQL 版本） |
| [`app/services/hama_ocr_extractor.py`](../backend_api_python/app/services/hama_ocr_extractor.py) | OCR 提取器 |
| [`app/services/hama_email_notifier.py`](../backend_api_python/app/services/hama_email_notifier.py) | 邮件通知器 |
| [`app/services/hama_monitor_worker.py`](../backend_api_python/app/services/hama_monitor_worker.py) | 监控 Worker |

---

### 10.2 API 路由

| 文件 | 功能 |
|------|------|
| [`app/routes/hama_market.py`](../backend_api_python/app/routes/hama_market.py) | HAMA 行情 API 路由 |
| [`app/routes/hama_ocr.py`](../backend_api_python/app/routes/hama_ocr.py) | OCR API 路由 |
| [`app/routes/hama_indicator.py`](../backend_api_python/app/routes/hama_indicator.py) | HAMA 指标 API 路由 |

---

### 10.3 自动监控

| 文件 | 功能 |
|------|------|
| [`auto_hama_monitor_mysql.py`](../backend_api_python/auto_hama_monitor_mysql.py) | 自动监控脚本（MySQL 版本） |
| [`auto_hama_monitor_sqlite.py`](../backend_api_python/auto_hama_monitor_sqlite.py) | 自动监控脚本（SQLite 版本） |

---

### 10.4 数据库初始化

| 文件 | 功能 |
|------|------|
| [`init_all_tables.py`](../backend_api_python/init_all_tables.py) | 初始化所有数据库表 |
| [`init_hama_symbols_table.py`](../backend_api_python/init_hama_symbols_table.py) | 初始化 HAMA 币种表 |

---

### 10.5 配置文件

| 文件 | 功能 |
|------|------|
| [`.env`](../backend_api_python/.env) | 环境变量配置 |
| [`tradingview_cookies.json`](../backend_api_python/tradingview_cookies.json) | TradingView Cookie |
| [`file/tradingview.txt`](../backend_api_python/file/tradingview.txt) | TradingView 账号密码 |

---

### 10.6 测试脚本

| 文件 | 功能 |
|------|------|
| [`test_hama_simple.py`](../backend_api_python/test_hama_simple.py) | 简单测试脚本 |
| [`test_hama_market_api.py`](../backend_api_python/test_hama_market_api.py) | API 测试脚本 |
| [`test_batch_hama_monitor.py`](../backend_api_python/test_batch_hama_monitor.py) | 批量监控测试 |

---

## 十一、故障排查

### 11.1 常见问题

#### 问题 1: Brave 监控无法启动

**症状**: `Brave 监控器未初始化`

**排查步骤**:

1. 检查环境变量:
```bash
echo $BRAVE_MONITOR_ENABLED
```

2. 检查 Playwright 是否安装:
```bash
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

3. 检查 RapidOCR 是否安装:
```bash
python -c "from rapidocr_onnxruntime import RapidOCR; print('OK')"
```

4. 检查数据库连接:
```bash
python -c "from app import create_app; app = create_app(); print('OK')"
```

**解决方案**:

```bash
# 安装 Playwright
pip install playwright playwright-stealth
playwright install chromium

# 安装 RapidOCR
pip install rapidocr-onnxruntime
```

---

#### 问题 2: OCR 识别不准确

**症状**: OCR 识别结果错误或置信度低

**排查步骤**:

1. 检查截图是否正确:
```bash
ls -lh backend_api_python/app/screenshots/
```

2. 手动测试 OCR:
```bash
cd backend_api_python
python test_hama_ocr_demo.py
```

3. 尝试不同的 OCR 引擎:
```bash
# PaddleOCR
pip install paddleocr paddlepaddle

# EasyOCR
pip install easyocr
```

**解决方案**:

1. 调整截图区域（修改 `hama_ocr_extractor.py`）:
```python
clip = {
    'x': int(page_width * 0.72),   # 调整这个值
    'y': int(page_height * 0.60),  # 调整这个值
    'width': int(page_width * 0.28),
    'height': int(page_height * 0.40)
}
```

2. 增加等待时间（确保图表完全渲染）:
```python
page.wait_for_timeout(50000)  # 增加到 60 秒
```

---

#### 问题 3: 邮件通知发送失败

**症状**: `邮件通知发送失败`

**排查步骤**:

1. 检查 SMTP 配置:
```bash
grep SMTP .env
```

2. 测试邮件发送:
```bash
cd backend_api_python
python test_hama_email.py
```

3. 检查防火墙:
```bash
telnet smtp.gmail.com 587
```

**解决方案**:

1. 确认使用应用专用密码（Gmail）
2. 检查 SMTP 端口是否正确
3. 确认防火墙允许 SMTP 连接
4. 尝试使用 TLS 而非 SSL

---

#### 问题 4: 数据库连接失败

**症状**: `数据库连接失败`

**排查步骤**:

1. 检查数据库文件是否存在:
```bash
ls -lh backend_api_python/data/quantdinger.db
```

2. 检查数据库权限:
```bash
chmod 664 backend_api_python/data/quantdinger.db
```

3. 检查数据库表是否存在:
```bash
sqlite3 backend_api_python/data/quantdinger.db ".tables"
```

**解决方案**:

```bash
# 重新初始化数据库
cd backend_api_python
python init_all_tables.py
```

---

#### 问题 5: Playwright 浏览器无法启动

**症状**: `Browser not found`

**排查步骤**:

1. 检查 Playwright 浏览器是否安装:
```bash
playwright install --help
```

2. 检查系统依赖:
```bash
# Linux
sudo apt-get install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# macOS
# 无需额外依赖

# Windows
# 无需额外依赖
```

**解决方案**:

```bash
# 重新安装 Playwright 浏览器
playwright install chromium
playwright install firefox
playwright install webkit
```

---

### 11.2 日志调试

#### 启用调试日志

```bash
# 修改 .env
LOG_LEVEL=DEBUG

# 重启服务
python run.py
```

#### 查看日志文件

```bash
# 查看最新日志
tail -f backend_api_python/logs/app.log

# 查看错误日志
grep ERROR backend_api_python/logs/app.log

# 查看 HAMA 相关日志
grep "HAMA" backend_api_python/logs/app.log
```

---

## 十二、开发指南

### 12.1 添加新的 OCR 引擎

#### 步骤 1: 实现 OCR 接口

在 [`hama_ocr_extractor.py`](../backend_api_python/app/services/hama_ocr_extractor.py) 中添加:

```python
class HAMAOCRExtractor:
    def _init_ocr(self):
        # 添加新的 OCR 引擎
        elif self.ocr_engine == 'your_engine':
            try:
                import your_ocr_lib
                self.ocr = your_ocr_lib.Engine()
                logger.info("✅ YourOCR 初始化成功")
            except Exception as e:
                logger.error(f"YourOCR 初始化失败: {e}")
                self.ocr = None

    def _ocr_with_your_engine(self, image_path: str) -> List[str]:
        """使用 YourOCR 识别图片"""
        result = self.ocr.recognize(image_path)
        text_lines = []
        for item in result:
            text = item.get('text', '')
            confidence = item.get('confidence', 0)
            if confidence > 0.5:
                text_lines.append(text)
        return text_lines

    def extract_hama_with_ocr(self, image_path: str):
        # 添加新的 OCR 引擎分支
        elif self.ocr_engine == 'your_engine':
            text_lines = self._ocr_with_your_engine(image_path)
```

---

#### 步骤 2: 测试 OCR 引擎

创建测试脚本 `test_your_ocr.py`:

```python
from app.services.hama_ocr_extractor import HAMAOCRExtractor

# 测试 OCR 引擎
extractor = HAMAOCRExtractor(ocr_engine='your_engine')
result = extractor.extract_hama_with_ocr('test_screenshot.png')
print(result)
```

---

### 12.2 自定义 HAMA 指标参数

#### 步骤 1: 修改 HAMA 计算器

在 [`hama_calculator.py`](../backend_api_python/app/services/hama_calculator.py) 中修改:

```python
class HAMACalculator:
    def __init__(self, open_length=45, high_length=20, low_length=20,
                 close_length=40, ma_length=100, bb_length=400, bb_mult=2.0):
        """初始化 HAMA 计算器（自定义参数）"""
        self.open_length = open_length
        self.high_length = high_length
        self.low_length = low_length
        self.close_length = close_length
        self.ma_length = ma_length
        self.bb_length = bb_length
        self.bb_mult = bb_mult
```

---

#### 步骤 2: 更新 API 接口

在 [`hama_market.py`](../backend_api_python/app/routes/hama_market.py) 中添加参数:

```python
@hama_market_bp.route('/symbol', methods=['GET'])
def get_hama_symbol():
    # 获取自定义参数
    open_length = int(request.args.get('open_length', 45))
    high_length = int(request.args.get('high_length', 20))
    # ...

    # 创建自定义计算器
    from app.services.hama_calculator import HAMACalculator
    calculator = HAMACalculator(
        open_length=open_length,
        high_length=high_length,
        # ...
    )

    # 计算指标
    result = calculator.get_latest_hama(df)
```

---

### 12.3 添加新的监控币种

#### 方法 1: 通过 API 添加

```bash
curl -X POST "http://localhost:5000/api/hama-market/symbols/add" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "MATICUSDT",
    "symbol_name": "Polygon",
    "market": "spot",
    "enabled": true,
    "priority": 50
  }'
```

---

#### 方法 2: 通过数据库添加

```sql
INSERT INTO hama_symbols (symbol, symbol_name, market, enabled, priority)
VALUES ('MATICUSDT', 'Polygon', 'spot', 1, 50);
```

---

#### 方法 3: 通过环境变量添加

修改 `.env`:

```bash
BRAVE_MONITOR_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT,MATICUSDT
```

---

### 12.4 自定义邮件通知

#### 步骤 1: 创建邮件通知器

在 [`hama_email_notifier.py`](../backend_api_python/app/services/hama_email_notifier.py) 中修改:

```python
class HamaEmailNotifier:
    def notify_trend_formed(self, symbol, trend, hama_color, hama_value,
                            price, cross_type, screenshot_url, extra_data):
        """自定义邮件内容"""

        subject = f"🔔 HAMA 趋势提醒: {symbol} - {trend.upper()}"
        body = f"""
        <h2>HAMA 趋势提醒</h2>
        <p><strong>币种:</strong> {symbol}</p>
        <p><strong>趋势:</strong> {trend}</p>
        <p><strong>颜色:</strong> {hama_color}</p>
        <p><strong>价格:</strong> {price}</p>
        <p><strong>截图:</strong> <a href="{screenshot_url}">查看</a></p>

        <h3>额外数据</h3>
        <pre>{json.dumps(extra_data, indent=2, ensure_ascii=False)}</pre>
        """

        # 发送邮件
        self.send_email(subject, body)
```

---

#### 步骤 2: 添加新的通知渠道

例如：Telegram 通知、Webhook 通知

```python
class HamaTelegramNotifier:
    def notify_trend_formed(self, symbol, trend, ...):
        """发送 Telegram 通知"""
        message = f"🔔 HAMA 趋势提醒: {symbol} - {trend.upper()}"
        self.send_telegram(message)

    def send_telegram(self, message):
        """发送 Telegram 消息"""
        import requests
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': message
        })
```

---

### 12.5 性能优化

#### 优化 1: 缓存 K线数据

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_kline_cached(symbol, interval, limit):
    """缓存 K线数据"""
    return kline_service.get_kline(symbol=symbol, timeframe=interval, limit=limit)
```

---

#### 优化 2: 并发监控

```python
from concurrent.futures import ThreadPoolExecutor

def monitor_batch_parallel(self, symbols, browser_type='chromium', max_workers=3):
    """并发监控多个币种"""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.monitor_symbol, symbol, browser_type): symbol
            for symbol in symbols
        }
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                results[symbol] = future.result()
            except Exception as e:
                logger.error(f"{symbol} 监控失败: {e}")
                results[symbol] = None
    return results
```

---

#### 优化 3: 数据库连接池

```python
from DBUtils.PooledDB import PooledDB

# 创建数据库连接池
db_pool = PooledDB(
    creator=sqlite3,
    database='data/quantdinger.db',
    maxconnections=10,
    mincached=2,
    maxcached=5
)

# 获取连接
conn = db_pool.connection()
```

---

## 附录

### A. 默认监控币种列表

```python
DEFAULT_SYMBOLS = [
    'BTCUSDT',   # Bitcoin
    'ETHUSDT',   # Ethereum
    'BNBUSDT',   # Binance Coin
    'SOLUSDT',   # Solana
    'XRPUSDT',   # XRP
    'ADAUSDT',   # Cardano
    'DOGEUSDT',  # Dogecoin
    'AVAXUSDT',  # Avalanche
    'DOTUSDT',   # Polkadot
    'LINKUSDT'   # Chainlink
]
```

---

### B. HAMA 指标参数说明

| 参数 | 默认值 | 说明 | 计算方法 |
|------|--------|------|----------|
| open_length | 45 | 开盘价 EMA 周期 | EMA(source_open, 45) |
| high_length | 20 | 最高价 EMA 周期 | EMA(source_high, 20) |
| low_length | 20 | 最低价 EMA 周期 | EMA(source_low, 20) |
| close_length | 40 | 收盘价 WMA 周期 | WMA(source_close, 40) |
| ma_length | 100 | MA WMA 长度 | WMA(close, 100) |
| bb_length | 400 | 布林带 SMA 周期 | SMA(close, 400) |
| bb_mult | 2.0 | 标准差倍数 | basis ± dev * 2.0 |

---

### C. 支持的时间周期

| 周期 | 参数 | 说明 |
|------|------|------|
| 1分钟 | 1m | 短线交易 |
| 3分钟 | 3m | 短线交易 |
| 5分钟 | 5m | 短线交易 |
| 15分钟 | 15m | 日内交易（推荐） |
| 30分钟 | 30m | 日内交易 |
| 1小时 | 1h | 波段交易 |
| 2小时 | 2h | 波段交易 |
| 4小时 | 4h | 波段交易 |
| 1天 | 1d | 长线交易 |
| 1周 | 1w | 长线交易 |

---

### D. 邮件通知模板

#### 趋势形成通知

```
主题: 🔔 HAMA 趋势提醒: BTCUSDT - UP

HAMA 趋势提醒

币种: BTCUSDT
趋势: UP (上涨)
颜色: GREEN
价格: 3311.73
HAMA 值: 3311.73
截图: http://localhost:5000/screenshot/hama_brave_BTCUSDT_1234567890.png

通知原因: 首次检测到趋势: green (up)
监控时间: 2025-01-19 10:30:00
上次状态: 无
当前状态: green (up)
是否首次: 是

---
QuantDinger HAMA 智能监控系统
```

---

### E. 常用命令速查

```bash
# 启动后端服务
cd backend_api_python
python run.py

# 初始化数据库
python init_all_tables.py

# 启动自动监控
python auto_hama_monitor_mysql.py

# 测试 HAMA 计算
python test_hama_simple.py

# 测试 OCR 识别
python test_hama_ocr_demo.py

# 测试邮件通知
python test_hama_email.py

# 查看日志
tail -f logs/app.log

# 查看数据库
sqlite3 data/quantdinger.db ".tables"
sqlite3 data/quantdinger.db "SELECT * FROM hama_monitor_cache"

# 备份数据库
cp data/quantdinger.db data/quantdinger.db.backup

# 恢复数据库
cp data/quantdinger.db.backup data/quantdinger.db
```

---

### F. 参考资源

- **TradingView HAMA 指标**: https://www.tradingview.com/script/
- **Playwright 文档**: https://playwright.dev/python/
- **RapidOCR 文档**: https://github.com/RapidAI/RapidOCR
- **PaddleOCR 文档**: https://github.com/PaddlePaddle/PaddleOCR
- **Flask 文档**: https://flask.palletsprojects.com/

---

## 更新日志

### v1.0 (2025-01-19)
- 初始版本
- 完整的 HAMA 行情实现文档
- 包含所有核心组件、API 接口、数据库设计
- 包含故障排查和开发指南

---

**文档维护**: QuantDinger Team
**最后更新**: 2025-01-19
**文档版本**: 1.0
