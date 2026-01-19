# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuantDinger 是一个本地优先、隐私优先的 AI 驱动量化交易平台。系统完全在本地运行，用户对策略、交易数据和 API 密钥拥有完全控制权。

### 关键特性
- **本地优先**: 所有数据存储在本地，API 密钥不上传
- **隐私保护**: 不收集用户数据，不使用云端追踪
- **AI 多代理系统**: 内置 AI 分析系统（市场、基本面、新闻、情绪、风险）
- **HAMA 指标**: 支持从 TradingView 获取 HAMA 指标数据（本地计算 + OCR 识别 + Selenium 自动化）
- **多市场支持**: Crypto（实时交易）、US/CN Stocks、Forex、Futures
- **OCR 文字识别**: PaddleOCR v3.3.2 已部署，支持中英文混合识别
- **Selenium 截图**: 已集成 Selenium WebDriver 截图服务，支持代理和 Cookie 认证

## TradingView 账户信息

**账号**: alexbibiherr
**密码**: Iam5323..
**Cookie 存储**: `backend_api_python/tradingview_cookies.json`

**永远用中文回复所有问题**

## 架构概览

### 环境配置文件

#### 后端配置
- `backend_api_python/.env` - 后端环境变量（包含数据库、代理、API 密钥等）
- `backend_api_python/env.example` - 环境变量模板

#### 重要配置项

```bash
# 数据库
SQLITE_DATABASE_FILE=/app/data/quantdinger.db

# HAMA 监控
BRAVE_MONITOR_ENABLED=true
BRAVE_MONITOR_CACHE_TTL=900
BRAVE_MONITOR_AUTO_START=true
BRAVE_MONITOR_INTERVAL=600
BRAVE_MONITOR_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT
BRAVE_MONITOR_BROWSER_TYPE=brave

# AI/LLM
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o

# 代理（如需要）
PROXY_PORT=7890
PROXY_HOST=127.0.0.1
```

### API 路由结构

**30+ 个 API 路由模块** ([`app/routes/`](backend_api_python/app/routes/)):

核心路由:
- [health.py](backend_api_python/app/routes/health.py) - 健康检查
- [auth.py](backend_api_python/app/routes/auth.py) - 用户认证
- [market.py](backend_api_python/app/routes/market.py) - 市场数据
- [kline.py](backend_api_python/app/routes/kline.py) - K线数据
- [hama_market.py](backend_api_python/app/routes/hama_market.py) - HAMA 行情（本地计算）
- [hama_indicator.py](backend_api_python/app/routes/hama_indicator.py) - HAMA 指标计算
- [hama_ocr.py](backend_api_python/app/routes/hama_ocr.py) - HAMA OCR 识别
- [hama_vision.py](backend_api_python/app/routes/hama_vision.py) - HAMA Vision API
- [hama_monitor.py](backend_api_python/app/routes/hama_monitor.py) - HAMA 监控
- [indicator.py](backend_api_python/app/routes/indicator.py) - 指标管理
- [strategy.py](backend_api_python/app/routes/strategy.py) - 策略管理
- [backtest.py](backend_api_python/app/routes/backtest.py) - 回测
- [analysis.py](backend_api_python/app/routes/analysis.py) - AI 多代理分析
- [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py) - TradingView Scanner
- [tradingview_hama.py](backend_api_python/app/routes/tradingview_hama.py) - TradingView HAMA
- [tradingview_selenium.py](backend_api_python/app/routes/tradingview_selenium.py) - TradingView Selenium
- [tradingview_playwright.py](backend_api_python/app/routes/tradingview_playwright.py) - TradingView Playwright

## 核心架构模式

### 1. AI 多代理系统

项目核心是三阶段多代理协作系统：

**阶段 1 - 并行分析 (5个代理)**:
- `MarketAnalyst`: 技术面分析 (价格、成交量、技术指标)
- `FundamentalAnalyst`: 基本面分析 (估值、财报)
- `NewsAnalyst`: 新闻和事件分析
- `SentimentAnalyst`: 市场情绪分析
- `RiskAnalyst`: 风险评估

**阶段 2 - 辩论 (2个代理)**:
- `BullResearcher`: 牛市观点论证
- `BearResearcher`: 熊市观点论证

**阶段 3 - 决策 (1个代理)**:
- `TraderAgent`: 综合所有分析，给出最终建议 (BUY/SELL/HOLD)

代理文件位置: [backend_api_python/app/services/agents/](backend_api_python/app/services/agents/)

### 2. OCR 文字识别系统 ✅ 新增

**部署状态**: 已部署并测试通过

**核心组件**:
- PaddleOCR v3.3.2 - 主要 OCR 引擎
- PP-OCRv5 模型 - 支持中英文混合识别
- [hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py) - HAMA OCR 提取器
- [hama_vision_extractor.py](backend_api_python/app/services/hama_vision_extractor.py) - Vision API 提取器

**使用方法**:
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='en')
result = ocr.ocr('chart.png')
texts = result[0].rec_texts
```

### 3. Selenium 截图系统 ✅ 新增

**部署状态**: 已部署并测试通过

**核心组件**:
- Selenium WebDriver - Chrome 浏览器自动化
- [screenshot_helper.py](backend_api_python/app/services/screenshot_helper.py) - 截图助手
- [screenshot_service.py](backend_api_python/app/services/screenshot_service.py) - 统一截图服务

**使用方法**:
```python
from app.services.screenshot_helper import capture_screenshot

result = capture_screenshot(
    url='https://s.tradingview.com/widgetembed/',
    output_path='../screenshot/chart.png',
    wait_time=10,
    proxy_port=7890  # 使用代理
)
```

### 4. HAMA 指标数据获取方案

系统提供 **5 种方案** 获取 HAMA 指标数据：

1. **本地计算（推荐）** - [hama_calculator.py](backend_api_python/app/services/hama_calculator.py)
   - API: `/api/hama/calculate`
   - 速度: ~10ms
   - 成本: 免费
   - 准确度: 99%+

2. **OCR 识别** - [hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py)
   - API: `/api/hama-ocr/extract`
   - 使用 PaddleOCR（完全免费）
   - 速度: ~2秒
   - 准确度: 90-95%

3. **Brave 监控（自动）** - [hama_brave_monitor_mysql.py](backend_api_python/app/services/hama_brave_monitor_mysql.py)
   - 使用 Playwright + RapidOCR
   - 速度: ~60秒/次（7个币种）
   - 存储: SQLite 数据库
   - 适用场景: 定期验证本地计算准确性

4. **GPT-4o 视觉** - [hama_vision_extractor.py](backend_api_python/app/services/hama_vision_extractor.py)
   - 使用大模型视觉识别
   - 成本: ~$0.0025/次
   - 准确度: 95%+

5. **Selenium/Playwright** - [tradingview_playwright.py](backend_api_python/app/services/tradingview_playwright.py)
   - 使用 playwright-stealth 绕过反爬
   - 支持 Cookie 认证
   - 适用场景: 调试和验证

### 5. TradingView 集成

**涨幅榜监控** - [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py)
- 实时监控币安合约涨幅榜前100名
- 每5分钟自动刷新数据
- 后台 Worker 自动缓存截图到数据库

**关键文件**:
- [tradingview_scanner_service.py](backend_api_python/app/services/tradingview_scanner_service.py) - 数据获取服务
- [gainer_tracker.py](backend_api_python/app/services/gainer_tracker.py) - 涨幅榜统计
- [tradingview_cookies.json](backend_api_python/tradingview_cookies.json) - TradingView Cookie

## 常用开发命令

### 后端开发
```bash
# 启动后端（本地）
cd backend_api_python
python run.py

# 启动后端（Docker）
docker-compose up -d backend

# 查看后端日志
docker-compose logs -f backend --tail 50

# 进入后端容器
docker exec -it quantdinger-backend bash

# 重启后端
docker-compose restart backend
```

### 前端开发
```bash
# 安装依赖
cd quantdinger_vue
npm install

# 启动开发服务器（端口 8000）
npm run serve

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 数据库管理
```bash
# SQLite 数据库位置
backend_api_python/data/quantdinger.db

# 查看数据库表
sqlite3 backend_api_python/data/quantdinger.db ".tables"

# 查询数据
sqlite3 backend_api_python/data/quantdinger.db "SELECT * FROM qd_strategies_trading WHERE status='running';"
```

### OCR 测试
```bash
# 快速测试 OCR
cd backend_api_python
python test_paddleocr.py

# OCR 识别图表
python test_screenshot_ocr.py

# 完整测试
python test_hama_ocr_demo.py
```

### 截图测试
```bash
# 快速截图
cd backend_api_python
python quick_screenshot.py

# 使用示例
python examples/screenshot_usage.py

# 性能对比
python test_screenshot_comparison.py

# TradingView 私有图表截图 + OCR
python final_tv_screenshot_ocr.py
```

## HAMA 监控相关

```bash
# 初始化 HAMA 数据库表
cd backend_api_python
python init_all_tables.py

# 启动自动监控（本地）
python auto_hama_monitor_mysql.py

# 或使用启动脚本
start_hama_monitor.bat

# 测试单个币种监控
python test_hama_simple.py
```

## 数据库结构

### 核心业务表
- `qd_strategies_trading` - 交易策略配置
- `qd_indicator_codes` - 自定义指标代码（Python）
- `qd_backtest_results` - 回测结果
- `qd_exchange_credentials` - 交易所 API 密钥（加密存储）
- `hama_monitor_cache` - HAMA 监控缓存
- `hama_monitor_history` - HAMA 监控历史
- `gainer_stats` - 涨幅榜币种出现次数统计

### AI 代理记忆表
位置: `backend_api_python/data/memory/*.db`
- 每个代理独立的 SQLite 数据库
- 存储：历史决策、分析结果、学习记录

## 技术栈

- **前端**: Vue 2.6.14 + Ant Design Vue + KlineCharts/ECharts
- **后端**: Python 3.10+ + Flask 2.3.3 + SQLAlchemy 2.0
- **数据库**: SQLite (本地文件) / MySQL (可选)
- **OCR**: PaddleOCR v3.3.2
- **截图**: Selenium WebDriver
- **部署**: Docker Compose (推荐) 或本地开发

## 开发原则

1. **本地优先**: 所有数据存储在本地，API 密钥不上传
2. **隐私保护**: 不收集用户数据，不使用云端追踪
3. **透明性**: 算法和策略逻辑可审计
4. **模块化**: 清晰的关注点分离 (routes/services/data_sources)
5. **代理可扩展**: 新增代理继承 [base_agent.py](backend_api_python/app/services/agents/base_agent.py)

## 关键文件引用

### 后端核心
- [run.py](backend_api_python/run.py): 后端入口
- [app/__init__.py](backend_api_python/app/__init__.py): Flask 应用工厂
- [app/config/settings.py](backend_api_python/app/config/settings.py): 配置类

### OCR 系统
- [app/services/hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py): HAMA OCR 提取器
- [app/services/hama_vision_extractor.py](backend_api_python/app/services/hama_vision_extractor.py): Vision API 提取器
- [app/services/hama_calculator.py](backend_api_python/app/services/hama_calculator.py): HAMA 本地计算

### 截图系统
- [app/services/screenshot_helper.py](backend_api_python/app/services/screenshot_helper.py): 截图助手
- [app/services/screenshot_service.py](backend_api_python/app/services/screenshot_service.py): 统一截图服务
- [app/services/tradingview_playwright.py](backend_api_python/app/services/tradingview_playwright.py): Playwright 自动化

### 前端核心
- [src/main.js](quantdinger_vue/src/main.js): 前端入口
- [src/router/index.js](quantdinger_vue/src/router/index.js): 路由配置
- [src/store/](quantdinger_vue/src/store/): Vuex 状态管理
- [src/api/](quantdinger_vue/src/api/): API 客户端封装

## 文档

- [README.md](README.md): 项目介绍和快速开始
- [docs/STRATEGY_DEV_GUIDE.md](docs/STRATEGY_DEV_GUIDE.md): 策略开发指南
- [OCR_USAGE_GUIDE.md](OCR_USAGE_GUIDE.md): OCR 使用指南
- [TRADINGVIEW_OCR_TEST_REPORT.md](TRADINGVIEW_OCR_TEST_REPORT.md): OCR 测试报告
- [SCREENSHOT_METHODS_GUIDE.md](SCREENSHOT_METHODS_GUIDE.md): 截图方案指南
- [SELENIUM_SCREENSHOT_QUICK_START.md](SELENIUM_SCREENSHOT_QUICK_START.md): Selenium 快速开始
- [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md): 完整功能指南

## 测试

### OCR 测试
1. 访问 HAMA Market 页面 (http://localhost:8000/#/hama-market)
2. 查看默认币种 (BTCUSDT, ETHUSDT)
3. 查看 HAMA 指标数据
4. 查看布林带数据

### TradingView Scanner 测试
1. 访问 http://localhost:8000/#/tradingview-scanner
2. 查看默认币种 (BTCUSDT, ETHUSDT)
3. 查看涨幅榜前10
4. 点击展开行查看截图

### 截图 + OCR 完整流程测试
```bash
# 运行完整测试
cd backend_api_python
python final_tv_screenshot_ocr.py

# 该脚本会：
# 1. 使用 Selenium 访问 TradingView 私有图表
# 2. 使用 Cookie 认证
# 3. 截图保存到文件
# 4. 使用 PaddleOCR 识别图表
# 5. 提取 HAMA 指标数据
# 6. 输出价格、趋势、布林带等信息
```

## 部署注意事项

- 生产环境必须更改 `SECRET_KEY` 和默认密码
- 配置 HTTPS (使用反向代理如 Caddy/Nginx)
- 设置适当的资源限制 (CPU/内存)
- 定期备份 `data/quantdinger.db` 和 `.env` 文件
- 监控日志文件大小，配置日志轮转
- 确保代理配置正确 (如果使用代理，默认端口 7890)
- OCR 模型文件首次运行会自动下载 (~200MB)
- Selenium 需要 Chrome 浏览器

## 重要提醒

### TradingView Cookie 管理
- Cookie 存储位置: `backend_api_python/tradingview_cookies.json`
- 更新频率: Cookie 过期后需手动更新
- 账户信息: alexbibiherr / Iam5323..
- 获取方式: 浏览器开发者工具 → Network → 复制 Cookie 值

### OCR 使用提示
- 首次运行 PaddleOCR 会自动下载模型文件
- 英文模型识别数字更准确
- 可以使用图片预处理提高识别准确率
- 对于 TradingView 图表，建议使用英文模型 (lang='en')

### Selenium 使用提示
- 默认使用无头模式 (headless=True)
- 支持代理配置，推荐使用 PROXY_PORT=7890
- 访问私有页面需要使用 Cookie 认证
- 等待时间建议设置为 10-15 秒确保页面完全加载

### Windows 环境特殊说明
```bash
# PowerShell 启动服务
.\restart_services.ps1

# 或使用批处理
.\restart_services.bat
```
