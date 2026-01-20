# Brave 监控系统技术逻辑详解

> 本文档详细说明了 QuantDinger 项目中 Brave 监控系统的技术架构、核心流程和实现细节。

## 目录

- [系统概述](#系统概述)
- [核心架构](#核心架构)
- [工作流程](#工作流程)
- [关键组件](#关键组件)
- [数据流](#数据流)
- [配置管理](#配置管理)
- [错误处理](#错误处理)
- [性能优化](#性能优化)

---

## 系统概述

### 功能定位
Brave 监控系统是 QuantDinger 的核心监控模块，负责：
1. **自动化监控**: 使用 Brave 浏览器自动访问 TradingView 图表
2. **OCR 识别**: 通过 RapidOCR 识别 HAMA 指标数据
3. **数据缓存**: 将识别结果存储到 SQLite/Redis
4. **实时推送**: 通过 API 接口向前端提供数据
5. **持续监控**: 后台线程定时循环监控指定币种

### 技术栈
- **Playwright**: 浏览器自动化控制
- **Playwright Stealth**: 反检测插件
- **RapidOCR**: 本地 OCR 识别引擎
- **SQLite**: 本地数据持久化
- **Redis**: 可选的缓存层
- **Python Threading**: 后台持续监控

---

## 核心架构

### 模块关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│                     (Flask API Routes)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   HamaBraveMonitor                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Monitoring   │  │  Cache       │  │   Thread     │     │
│  │   Control    │  │  Manager     │  │  Management  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 HAMAOCRExtractor                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Browser    │  │   OCR        │  │   Parsing    │     │
│  │  Automation  │  │  Recognition │  │   Logic      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              TradingView Web Platform                        │
│         (https://cn.tradingview.com/chart/)                 │
└─────────────────────────────────────────────────────────────┘
```

### 核心类结构

#### 1. HamaBraveMonitor (监控管理器)
**文件**: `backend_api_python/app/services/hama_brave_monitor.py`

**职责**:
- 监控任务调度和管理
- 缓存读写（SQLite/Redis）
- 后台线程生命周期管理
- 批量监控协调

**关键方法**:
```python
class HamaBraveMonitor:
    def __init__(redis_client, cache_ttl, use_sqlite)
    def get_cached_hama(symbol) -> Dict        # 读取缓存
    def set_cached_hama(symbol, data) -> bool  # 写入缓存
    def monitor_symbol(symbol, browser_type)    # 单次监控
    def monitor_batch(symbols, browser_type)    # 批量监控
    def start_monitoring(symbols, interval)     # 启动持续监控
    def stop_monitoring()                       # 停止监控
```

#### 2. HAMAOCRExtractor (OCR提取器)
**文件**: `backend_api_python/app/services/hama_ocr_extractor.py`

**职责**:
- 浏览器自动化控制
- 页面截图
- OCR 文字识别
- HAMA 数据解析

**关键方法**:
```python
class HAMAOCRExtractor:
    def __init__(ocr_engine='rapidocr')
    def capture_chart(url, save_path, browser_type)  # 截图
    def extract_hama_with_ocr(image_path)            # OCR识别
    def _parse_ocr_result(ocr_text)                  # 解析数据
```

---

## 工作流程

### 1. 初始化流程

```
应用启动
    │
    ├─→ 读取配置文件 (tradingview.txt)
    │   ├─ TradingView 账号密码
    │   └─ Cookie 字符串
    │
    ├─→ 初始化 HamaBraveMonitor
    │   ├─ 创建 SQLite 数据库连接
    │   ├─ 创建 hama_monitor_cache 表
    │   └─ 初始化 HAMAOCRExtractor
    │       ├─ 转换 Cookie 格式
    │       └─ 加载 RapidOCR 引擎
    │
    └─→ 启动后台监控线程
        ├─ 加载监控币种列表 (BTCUSDT, ETHUSDT...)
        └─ 开始监控循环
```

### 2. 单次监控流程

```
monitor_symbol(symbol)
    │
    ├─→ 步骤1: 构建 URL
    │   └─ https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE:XXX&interval=15
    │
    ├─→ 步骤2: 启动浏览器
    │   ├─ 使用 Brave 浏览器路径
    │   ├─ 配置代理 (可选)
    │   └─ 设置 Cookie
    │
    ├─→ 步骤3: 访问页面
    │   ├─ 导航到 TradingView 图表
    │   ├─ 等待页面加载
    │   └─ 检查登录状态
    │       ├─ 如果未登录 → 使用账号密码自动登录
    │       └─ 如果已登录 → 继续
    │
    ├─→ 步骤4: 等待图表渲染
    │   ├─ 等待图表容器出现
    │   ├─ 等待 HAMA 指标面板加载
    │   └─ 额外等待确保数据完整
    │
    ├─→ 步骤5: 截取 HAMA 指标面板
    │   ├─ 计算截图区域 (右下角)
    │   │   ├─ x: 页面宽度的 72% (从右侧28%开始)
    │   │   ├─ y: 页面高度的 45%
    │   │   ├─ width: 28% 页面宽度
    │   │   └─ height: 55% 页面高度
    │   └─ 保存到 screenshots/ 目录
    │
    ├─→ 步骤6: OCR 识别
    │   ├─ 使用 RapidOCR 识别图片文字
    │   └─ 获取 OCR 文本结果
    │
    ├─→ 步骤7: 解析 HAMA 数据
    │   ├─ 识别价格 (Price 标签后的数值)
    │   ├─ 识别 HAMA 状态 (上涨/下跌/盘整)
    │   ├─ 识别颜色 (green/red/gray)
    │   ├─ 识别布林带状态 (收缩/扩张/正常)
    │   ├─ 识别蜡烛/MA状态
    │   └─ 识别最近交叉信息
    │
    ├─→ 步骤8: 缓存数据
    │   ├─ 保存到 SQLite 数据库
    │   └─ (可选) 保存到 Redis
    │
    └─→ 步骤9: 返回结果
        └─ 返回完整的 HAMA 数据字典
```

### 3. 持续监控流程

```
start_monitoring(symbols, interval=600)
    │
    ├─→ 创建后台线程
    │   └─ monitoring_loop()
    │
    └─→ 监控循环
        │
        ├─→ while is_monitoring:
        │   │
        │   ├─→ 批量监控所有币种
        │   │   ├─ for symbol in symbols:
        │   │   │   ├─ monitor_symbol(symbol)
        │   │   │   ├─ 成功 → 统计 +1
        │   │   │   └─ 失败 → 统计失败 +1
        │   │   └─ 输出统计结果
        │   │
        │   ├─→ 等待指定间隔
        │   │   └─ for _ in range(interval):
        │   │       └─ sleep(1) + 检查停止信号
        │   │
        │   └─→ 重复下一轮
        │
        └─→ 停止监控
            └─ stop_monitoring()
                └─ is_monitoring = False
```

---

## 关键组件

### 1. 浏览器自动化 (Playwright)

**初始化配置**:
```python
with sync_playwright() as p:
    # 启动 Brave 浏览器
    browser = p.chromium.launch(
        executable_path="C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        headless=True,  # 无头模式
        args=['--disable-blink-features=AutomationControlled']
    )

    # 创建上下文
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 ...'
    )

    # 注入 Cookie
    if cookies:
        context.add_cookies(cookies)
```

**反检测措施**:
1. 使用 Playwright Stealth 插件
2. 设置真实的 User-Agent
3. 注入 TradingView Cookie
4. 自动登录功能
5. 随机化等待时间

### 2. OCR 识别引擎 (RapidOCR)

**初始化**:
```python
from rapidocr_onnxruntime import RapidOCR

self.ocr = RapidOCR()
logger.info("✅ RapidOCR 初始化成功")
```

**识别流程**:
```python
def extract_hama_with_ocr(self, image_path):
    # 1. 读取图片
    img = cv2.imread(image_path)

    # 2. OCR 识别
    result = self.ocr(img)

    # 3. 提取文本
    ocr_text = '\n'.join([line[1] for line in result])

    # 4. 解析数据
    hama_data = self._parse_ocr_result(ocr_text)

    return hama_data
```

**识别准确率优化**:
- 图片预处理 (灰度化、二值化)
- 调整截图区域大小
- 使用高质量截图 (PNG格式)
- 多次重试机制

### 3. 数据解析逻辑

**价格识别**:
```python
# 方法1: 跨行识别 ("价格" 标签单独一行)
lines = ocr_text.split('\n')
for i, line in enumerate(lines):
    if '价格' in line or 'price' in line.lower():
        if re.match(r'^\s*价格\s*$', line):
            # 检查下一行
            next_line = lines[i+1].strip()
            price_match = re.match(r'^([\d,]+\.?\d*)$', next_line)
            if price_match:
                current_price = float(price_match.group(1).replace(',', ''))

# 方法2: 同行识别 ("价格 3210.82")
price_pattern = r'价格\s+([\d,]+\.?\d*)'
match = re.search(price_pattern, line)
if match:
    current_price = float(match.group(1).replace(',', ''))
```

**HAMA 状态识别**:
```python
# 识别 HAMA 状态关键词
if '上涨' in ocr_text or 'up' in ocr_text.lower():
    hama_trend = 'up'
    hama_color = 'green'
elif '下跌' in ocr_text or 'down' in ocr_text.lower():
    hama_trend = 'down'
    hama_color = 'red'
else:
    hama_trend = 'neutral'
    hama_color = 'gray'
```

**布林带状态识别**:
```python
if '收缩' in ocr_text or 'squeeze' in ocr_text.lower():
    bollinger_status = 'squeeze'
elif '扩张' in ocr_text or 'expansion' in ocr_text.lower():
    bollinger_status = 'expansion'
else:
    bollinger_status = 'normal'
```

### 4. 缓存管理

**SQLite 数据库结构**:
```sql
CREATE TABLE hama_monitor_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,       -- 币种
    hama_trend VARCHAR(10),                    -- 趋势 (up/down/neutral)
    hama_color VARCHAR(10),                    -- 颜色 (green/red/gray)
    hama_value DECIMAL(20, 8),                 -- HAMA 值
    price DECIMAL(20, 8),                      -- 当前价格
    ocr_text TEXT,                             -- OCR 原始文本
    screenshot_path VARCHAR(255),              -- 截图路径
    candle_ma_status TEXT,                     -- 蜡烛/MA状态
    bollinger_status TEXT,                     -- 布林带状态
    last_cross_info TEXT,                      -- 最近交叉
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**缓存策略**:
1. **写入**: 每次监控成功后立即写入
2. **读取**: 优先读取最新一条记录
3. **更新**: 使用 `INSERT OR REPLACE` 覆盖旧数据
4. **TTL**: 默认 900 秒 (15 分钟)

---

## 数据流

### 数据流向图

```
┌─────────────┐
│  TradingView│
│   图表页面  │
└──────┬──────┘
       │
       │ 1. Playwright 访问
       │
       ▼
┌─────────────┐
│ Brave Browser│
│  (自动化)   │
└──────┬──────┘
       │
       │ 2. 截取 HAMA 面板
       │
       ▼
┌─────────────┐
│  PNG 图片   │
│  (本地文件) │
└──────┬──────┘
       │
       │ 3. RapidOCR 识别
       │
       ▼
┌─────────────┐
│  OCR 文本   │
│  (原始数据) │
└──────┬──────┘
       │
       │ 4. 解析提取
       │
       ▼
┌─────────────┐
│ HAMA 数据   │
│ (结构化)    │
│ {           │
│   trend,    │
│   color,    │
│   value,    │
│   ...       │
│ }           │
└──────┬──────┘
       │
       ├──────┐
       │      │
       ▼      ▼
┌────────┐ ┌────────┐
│ SQLite │ │ Redis  │
│(持久化)│ │ (缓存) │
└────────┘ └────────┘
       │
       │ 5. API 接口
       │
       ▼
┌─────────────┐
│   前端页面  │
│(实时展示)   │
└─────────────┘
```

### API 接口

**获取监控列表**:
```http
GET /api/hama-market/watchlist?market=spot

Response:
{
  "success": true,
  "data": {
    "watchlist": [
      {
        "symbol": "BTCUSDT",
        "price": 93060.36,
        "hama_brave": {
          "hama_trend": "neutral",
          "hama_color": "gray",
          "hama_value": 93060.36,
          "candle_ma_status": "蜡烛在MA上",
          "bollinger_status": "squeeze",
          "last_cross_info": "91,500.00",
          "screenshot_path": "hama_brave_BTCUSDT_xxx.png",
          "screenshot_url": "/screenshot/hama_brave_BTCUSDT_xxx.png",
          "cached_at": "2026-01-20 02:54:50",
          "cache_source": "sqlite_brave_monitor"
        }
      }
    ]
  }
}
```

---

## 配置管理

### 配置文件结构

**tradingview.txt**:
```
https://cn.tradingview.com/chart/U1FY2qxO/

cookie:cookiePrivacyPreferenceBannerProduction=notApplicable; ...

账号 ：alexbibiherr
密码：Iam5323..

Brave浏览器路径：C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
```

### 配置加载流程

```python
def _load_tradingview_config(self):
    """加载 TradingView 配置"""
    config_file = '../../file/tradingview.txt'

    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    config = {}
    for line in lines:
        # 解析账号
        if '账号' in line:
            parts = line.split('：')
            config['username'] = parts[1].strip()

        # 解析密码
        elif '密码' in line:
            parts = line.split('：')
            config['password'] = parts[1].strip()

    return config
```

### Cookie 转换逻辑

```python
def _load_cookies(self):
    """加载并转换 Cookie"""
    # 读取字符串格式
    cookie_str = "cookie1=value1; cookie2=value2; ..."

    # 转换为 Playwright 格式
    cookie_list = []
    for cookie in cookie_str.split(';'):
        key, value = cookie.split('=', 1)
        cookie_list.append({
            'name': key.strip(),
            'value': value.strip(),
            'domain': '.tradingview.com',
            'path': '/'
        })

    return cookie_list
```

---

## 错误处理

### 1. 浏览器启动失败

**错误类型**: Brave浏览器路径不存在或启动失败

**处理策略**:
```python
try:
    browser = p.chromium.launch(executable_path=brave_path)
except Exception as e:
    logger.error(f"浏览器启动失败: {e}")
    return None
```

### 2. 页面加载超时

**错误类型**: TradingView 页面加载超时

**处理策略**:
```python
try:
    page.goto(url, timeout=30000)  # 30秒超时
except Exception as e:
    logger.warning(f"页面加载超时: {symbol}")
    return None
```

### 3. OCR 识别失败

**错误类型**: RapidOCR 识别返回空结果

**处理策略**:
```python
ocr_result = self.ocr(img)
if not ocr_result or len(ocr_result) == 0:
    logger.warning(f"OCR 识别失败: {image_path}")
    return None
```

### 4. 数据解析失败

**错误类型**: OCR 文本无法解析出有效数据

**处理策略**:
```python
try:
    hama_data = self._parse_ocr_result(ocr_text)
    if not hama_data.get('hama_value'):
        logger.warning(f"无法从OCR结果中提取价格")
        return None
except Exception as e:
    logger.error(f"数据解析失败: {e}")
    return None
```

### 5. 数据库写入失败

**错误类型**: SQLite 写入失败

**处理策略**:
```python
try:
    cursor.execute('INSERT OR REPLACE ...', values)
    conn.commit()
except Exception as e:
    logger.error(f"数据库写入失败: {e}")
    conn.rollback()
```

---

## 性能优化

### 1. 并发控制

**当前实现**: 串行监控（一次监控一个币种）

**优化建议**:
```python
from concurrent.futures import ThreadPoolExecutor

def monitor_batch_parallel(self, symbols, max_workers=3):
    """并行批量监控"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.monitor_symbol, symbol): symbol
            for symbol in symbols
        }

        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result(timeout=60)
                # 处理结果
            except Exception as e:
                logger.error(f"{symbol} 监控失败: {e}")
```

### 2. 缓存预热

**策略**: 启动时预先监控热门币种

```python
def warmup_cache(self, hot_symbols=['BTCUSDT', 'ETHUSDT']):
    """缓存预热"""
    logger.info("开始缓存预热...")
    self.monitor_batch(hot_symbols)
    logger.info("缓存预热完成")
```

### 3. 智能间隔

**策略**: 根据市场活跃度动态调整监控间隔

```python
def get_dynamic_interval(self):
    """动态获取监控间隔"""
    hour = datetime.now().hour

    # 交易活跃期 (8:00-24:00) - 5分钟
    if 8 <= hour <= 24:
        return 300

    # 交易低迷期 (0:00-8:00) - 10分钟
    else:
        return 600
```

### 4. 资源清理

**策略**: 定期清理过期数据

```python
def cleanup_old_records(self, days=7):
    """清理旧记录"""
    cursor.execute('''
        DELETE FROM hama_monitor_cache
        WHERE monitored_at < datetime('now', '-{} days')
    '''.format(days))
    conn.commit()
    logger.info(f"已清理 {days} 天前的旧数据")
```

### 5. 截图优化

**当前实现**: 每次保存完整截图

**优化建议**:
```python
# 1. 压缩截图质量
page.screenshot(path=image_path, quality=80)  # JPEG

# 2. 只截取必要区域
clip = {
    'x': page_width * 0.72,
    'y': page_height * 0.45,
    'width': page_width * 0.28,
    'height': page_height * 0.55
}
page.screenshot(path=image_path, clip=clip)

# 3. 定期清理旧截图
import os
import time

def cleanup_old_screenshots(screenshot_dir, max_age_days=7):
    """清理旧截图"""
    now = time.time()
    max_age_seconds = max_age_days * 24 * 3600

    for filename in os.listdir(screenshot_dir):
        filepath = os.path.join(screenshot_dir, filename)
        if os.path.getmtime(filepath) < now - max_age_seconds:
            os.remove(filepath)
```

---

## 监控状态管理

### 监控统计

```python
def get_stats(self):
    """获取监控统计"""
    return {
        'available': self.ocr_extractor is not None,
        'cached_symbols': self._get_cached_symbol_count(),
        'cache_ttl_seconds': self.cache_ttl,
        'is_monitoring': self.is_monitoring,
        'monitor_interval': self.interval,
        'total_symbols': len(self.symbols)
    }
```

### 健康检查

```python
def health_check(self):
    """健康检查"""
    checks = {
        'ocr_available': self.ocr_extractor is not None,
        'sqlite_available': self.sqlite_conn is not None,
        'redis_available': self.redis_client is not None,
        'monitoring_active': self.is_monitoring,
        'last_monitor_time': self._get_last_monitor_time()
    }

    # 如果所有关键组件正常
    if all(checks.values()):
        return {'status': 'healthy', 'checks': checks}
    else:
        return {'status': 'degraded', 'checks': checks}
```

---

## 总结

Brave 监控系统是 QuantDinger 项目的核心创新点，通过以下技术实现了高效、稳定的HAMA指标监控：

1. **Playwright 自动化**: 稳定的浏览器控制
2. **RapidOCR 识别**: 高精度的本地OCR
3. **SQLite 缓存**: 可靠的数据持久化
4. **后台线程**: 持续监控不阻塞主程序
5. **智能解析**: 准确提取HAMA指标数据
6. **错误容错**: 完善的异常处理机制

该系统的设计充分考虑了稳定性、可维护性和扩展性，为项目的量化交易功能提供了坚实的数据基础。
