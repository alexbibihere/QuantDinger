# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuantDinger 是一个本地优先、隐私优先的 AI 驱动量化交易平台。系统完全在本地运行，用户对策略、交易数据和 API 密钥拥有完全控制权。

### 关键特性
- **本地优先**: 所有数据存储在本地，API 密钥不上传
- **隐私保护**: 不收集用户数据，不使用云端追踪
- **AI 多代理系统**: 内置 AI 分析系统（市场、基本面、新闻、情绪、风险）
- **HAMA 指标**: 支持从 TradingView 获取 HAMA 指标数据（本地计算 + OCR 识别 + Playwright 自动化）
- **多市场支持**: Crypto（实时交易）、US/CN Stocks、Forex、Futures

## TradingView Cookie
```
cookiePrivacyPreferenceBannerProduction=notApplicable; _ga=GA1.1.1866852168.1760819691; cookiesSettings={"analytics":true,"advertising":true}; device_t=OThMTjowLDRibHJCUTow.albLE7WBs_dZ5drzD6kWjXsL7iQmttVDo3lvzVFUq90; sessionid=ki9qy7vvfk3h19qp0qd64exhonzapfrd; sessionid_sign=v3:cBmutdL9L5e4Y27C8skCR/dCbqBKOzvhheZiwjOQqOc=; tv_ecuid=2f707cb5-e0fd-457d-a12e-af14f34bee79; __gads=ID=14f07cdc5b671962:T=1767987209:RT=1768623944:S=ALNI_MYMXuccOjaGeS7V3qeAdjzkcw9H7w; __gpi=UID=000011e07ded39b9:T=1767987209:RT=1768623944:S=ALNI_MZvLD6OWj01o8fzaR8AwA3B6hMakg; __eoi=ID=94061d16f7692d1d:T=1767987209:RT=1768623944:S=AA-AfjbJz4kBsqzI2qydEXWmmZ2m; _ga_YVVRYGL0E0=GS2.1.s1768635293$o39$g0$t1768635293$j60$l0$h0; _sp_id.cf1a=4ae0f691-127b-49ab-b10b-1895c52c78ba.1760819689.31.1768635294.1768627525.a86976df-8efe-4226-b331-f53bab04cb2b.aed6ac03-dab9-4ea2-999e-d51dc101efba.57d2806a-6505-417b-b17c-d2f86fa0dd3c.1768635293698.1; _sp_ses.cf1a=*
```

## tv account

账号 alexbibiherr
密码 Iam5323..

永远用中文回复


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

#### TradingView 配置
- `backend_api_python/tradingview_cookies.json` - TradingView Cookie 和账户信息
- `backend_api_python/file/tradingview.txt` - TradingView 图表链接和账户

### API 路由结构

**30 个 API 路由模块** ([`app/routes/`](backend_api_python/app/routes/)):

核心路由:
- [health.py](backend_api_python/app/routes/health.py) - 健康检查
- [auth.py](backend_api_python/app/routes/auth.py) - 用户认证
- [market.py](backend_api_python/app/routes/market.py) - 市场数据
- [kline.py](backend_api_python/app/routes/kline.py) - K线数据
- [hama_market.py](backend_api_python/app/routes/hama_market.py) - HAMA 行情（本地计算 + Brave 监控）
- [indicator.py](backend_api_python/app/routes/indicator.py) - 指标管理
- [strategy.py](backend_api_python/app/routes/strategy.py) - 策略管理
- [backtest.py](backend/python/app/routes/backtest.py) - 回测
- [analysis.py](backend_api_python/app/routes/analysis.py) - AI 多代理分析
- [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py) - TradingView Scanner

### 工作流程说明

#### 策略开发流程

```
1. 编写 Python 指标代码
2. 创建策略配置（风险管理：Stop-Loss/TP/MACD）
3. 回测 + AI 参数优化
4. 实时交易（Crypto）或信号通知（Stock/Forex）
```

#### HAMA 数据流程（当前架构）

```
主要数据源: 本地计算（2-5秒）
    ↓
验证数据源: Brave 监控（每10分钟）
    ├─ Playwright 访问 TradingView
    ├─ 截图 HAMA 面板
    ├─ RapidOCR 识别
    └─ 保存到 SQLite
```

#### 数据存储

```
本地数据库: backend_api_python/data/quantdinger.db
    ├─ 业务表（16个表）
    ├─ HAMA 表（2个表）
    └─ AI 代理记忆表（独立数据库）

AI 代理记忆: backend_api_python/data/memory/*.db
    ├─ 每个代理独立的数据库
    └─ 存储：历史决策、分析结果
```

### 常用开发命令

#### 后端开发
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

#### 前端开发
```bash
# 安装依赖
cd quantdinger_vue
npm install

# 启动开发服务器
npm run serve

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

#### 数据库管理
```bash
# SQLite 数据库位置
backend_api_python/data/quantdinger.db

# 查看数据库表
sqlite3 backend_api_python/data/quantdinger.db ".tables"

# 查看特定表结构
sqlite3 backend_api_python/data/quantdinger.db ".schema qd_strategies_trading"

# 查询数据
sqlite3 backend_api_python/data/quantdinger.db "SELECT * FROM qd_strategies_trading WHERE status='running';"
```

#### HAMA 监控相关
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

### 数据库结构

#### 核心业务表
- `qd_strategies_trading` - 交易策略配置
- `qd_indicator_codes` - 自定义指标代码（Python）
- `qd_backtest_results` - 回测结果
- `qd_exchange_credentials` - 交易所 API 密钥（加密存储）
- `hama_monitor_cache` - HAMA 监控缓存（新增）
- `hama_monitor_history` - HAMA 监控历史（新增）

#### AI 代理记忆表
位置: `backend_api_python/data/memory/*.db`
- 每个代理独立的 SQLite 数据库
- 存储：历史决策、分析结果、学习记录

### 技术栈

- **前端**: Vue 2.6.14 + Ant Design Vue + KlineCharts/ECharts
- **后端**: Python 3.10+ + Flask 2.3.3 + SQLAlchemy 2.0
- **数据库**: SQLite (本地文件) / MySQL (可选)
- **部署**: Docker Compose (推荐) 或本地开发

### 目录结构
```
QuantDinger/
├── backend_api_python/          # Python Flask 后端
│   ├── app/
│   │   ├── routes/              # API 路由 (14个模块)
│   │   ├── services/            # 核心业务逻辑
│   │   │   ├── agents/          # AI 多代理系统
│   │   │   ├── live_trading/    # 实时交易执行
│   │   │   ├── analysis.py      # 市场分析服务
│   │   │   ├── backtest.py      # 回测引擎
│   │   │   ├── strategy.py      # 策略管理
│   │   │   └── llm.py           # LLM 接口
│   │   ├── data_sources/        # 统一数据源接口
│   │   ├── config/              # 配置管理
│   │   └── utils/               # 工具函数
│   ├── data/                    # 数据存储目录
│   ├── logs/                    # 日志目录
│   ├── run.py                   # 后端启动入口
│   ├── requirements.txt         # Python 依赖
│   └── env.example              # 环境变量模板
├── quantdinger_vue/             # Vue 2 前端
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── api/                 # API 封装
│   │   ├── components/          # 公共组件
│   │   ├── store/               # Vuex 状态管理
│   │   ├── router/              # 路由配置
│   │   └── locales/             # 国际化 (10种语言)
│   ├── vue.config.js            # 前端配置 (开发代理到后端 5000)
│   └── package.json             # Node 依赖
└── docker-compose.yml           # Docker 部署配置
```

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
- [coordinator.py](backend_api_python/app/services/agents/coordinator.py): 代理编排器
- [analyst_agents.py](backend_api_python/app/services/agents/analyst_agents.py): 分析代理
- [researcher_agents.py](backend_api_python/app/services/agents/researcher_agents.py): 研究代理
- [trader_agent.py](backend_api_python/app/services/agents/trader_agent.py): 决策代理

### 2. 本地记忆增强 (RAG + Reflection)

每个代理都有独立的 SQLite 记忆存储 ([data/memory/](backend_api_python/data/memory/))，支持：
- **检索**: 基于相似度和时间衰减的历史经验检索
- **反思**: 自动验证历史决策并学习 (可选 Worker)
- **注入**: 检索到的经验作为上下文注入到代理提示词

关键文件:
- [memory.py](backend_api_python/app/services/agents/memory.py): 记忆管理
- [reflection.py](backend_api_python/app/services/agents/reflection.py): 反思服务
- [reflection_worker.py](backend_api_python/app/services/agents/reflection_worker.py): 后台验证 Worker

### 3. 策略生命周期

```
指标开发 (Python) → 策略配置 (风险管理) → 回测 + AI 优化 → 执行
                                    ↓
                        实时交易 (Crypto) 或 信号通知 (Stock/Forex)
```

关键服务:
- [strategy.py](backend_api_python/app/services/strategy.py): 策略 CRUD 和状态管理
- [strategy_compiler.py](backend_api_python/app/services/strategy_compiler.py): Python 指标编译
- [backtest.py](backend_api_python/app/services/backtest.py): 回测引擎
- [trading_executor.py](backend_api_python/app/services/trading_executor.py): 策略执行器
- [signal_notifier.py](backend_api_python/app/services/signal_notifier.py): 信号通知 (Telegram/Email/Webhook)

### 4. HAMA 指标监控与数据获取

#### HAMA 数据获取方案（5种实现）

系统提供 **5 种方案** 获取 HAMA 指标数据：

1. **本地计算（推荐）** - [hama_calculator.py](backend_api_python/app/services/hama_calculator.py)
   - API: `/api/hama/calculate`
   - 速度: ~10ms
   - 成本: 免费
   - 准确度: 99%+
   - 适用场景: 生产环境首选

2. **OCR 识别** - [hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py)
   - API: `/api/hama-ocr/extract`
   - 使用 RapidOCR（完全免费）
   - 速度: ~2秒
   - 准确度: 90-95%（依赖 OCR 质量）
   - 适用场景: 日常使用推荐

3. **Brave 监控（自动）** - [hama_brave_monitor.py](backend_api_python/app/services/hama_brave_monitor.py)
   - API: `/api/hama-market/brave/status`, `/api/hama-market/brave/monitor`
   - 使用 Playwright + RapidOCR
   - 速度: ~60秒/次（7个币种）
   - 存储: SQLite 数据库
   - 适用场景: 定期验证本地计算准确性

4. **GPT-4o 视觉** - [hama_vision_extractor.py](backend_api_python/app/services/hama_vision_extractor.py)
   - 使用大模型视觉识别
   - 成本: ~$0.0025/次
   - 准确度: 95%+
   - 适用场景: 高精度需求

5. **Playwright** - [tradingview_playwright.py](backend_api_python/app/services/tradingview_playwright.py)
   - 使用 playwright-stealth 绕过反爬
   - 支持 Cookie 认证
   - 适用场景: 调试和验证

#### HAMA 监控架构

**本地计算（主要）**:
```
前端请求
    ↓
后端 API (/api/hama-market/symbol)
    ↓
本地计算 HAMA (hama_calculator.py)
    ↓
返回完整数据（HAMA + 趋势 + 布林带）
    ⚡ 2-5秒
```

**Brave 监控（验证）**:
```
本地自动监控脚本（auto_hama_monitor_mysql.py）
    ↓
每 10 分钟自动执行:
    ├─ 启动无头浏览器（Chromium）
    ├─ 访问 TradingView 图表（用户图表）
    ├─ 截图 HAMA 面板
    ├─ OCR 识别 HAMA 数据
    └─ 保存到 SQLite 数据库
    ↓
前端从数据库读取
```

**关键文件**:
- [hama_calculator.py](backend_api_python/app/services/hama_calculator.py) - HAMA 本地计算
- [hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py) - OCR 提取器
- [hama_brave_monitor.py](backend_api_python/app/services/hama_brave_monitor.py) - Brave 监控器（Redis 版本）
- [hama_brave_monitor_mysql.py](backend_api_python/app/services/hama_brave_monitor_mysql.py) - Brave 监控器（MySQL 版本）
- [auto_hama_monitor_mysql.py](backend_api_python/auto_hama_monitor_mysql.py) - 自动监控脚本（MySQL）
- [init_all_tables.py](backend_api_python/init_all_tables.py) - 数据库初始化脚本

#### TradingView 集成

**涨幅榜监控** - [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py)
- 实时监控币安合约涨幅榜前100名
- 每5分钟自动刷新数据
- 后台 Worker 自动缓存截图到数据库

**关键文件**:
- [tradingview_scanner_service.py](backend_api_python/app/services/tradingview_scanner_service.py) - 数据获取服务
- [gainer_tracker.py](backend_api_python/app/services/gainer_tracker.py) - 涨幅榜统计
- [tradingview_cookies.json](backend_api_python/tradingview_cookies.json) - TradingView Cookie（用户账户）
   - 适用场景: 验证/调试

4. **GPT-4o 视觉**: [hama_vision_extractor.py](backend_api_python/app/services/hama_vision_extractor.py)
   - 使用大模型视觉识别
   - 成本: ~$0.0025/次
   - 适用场景: 高精度需求

5. **Pyppeteer**: [tradingview_pyppeteer.py](backend_api_python/app/services/tradingview_pyppeteer.py)
   - 备用浏览器自动化方案

### 5. 统一数据源接口

支持多市场数据，通过 [data_sources/](backend_api_python/app/data_sources/) 统一接口：
- **加密货币**: CCXT (100+ 交易所)
- **美股**: yfinance, Finnhub, Tiingo
- **港股/中股**: AkShare, 东方财富
- **外汇/期货**: OANDA

代理支持: `PROXY_PORT` 或 `PROXY_URL` (支持 socks5h)

## 常用开发命令

### Docker 部署 (推荐)
```bash
# 首次启动
git clone https://github.com/brokermr810/QuantDinger.git
cd QuantDinger
cp backend_api_python/env.example backend_api_python/.env
docker-compose up -d --build

# 访问
# 后端: http://localhost:5000
# 前端: 需要单独运行 (见下方本地开发)

# 常用命令
docker-compose ps                      # 查看状态
docker-compose logs -f backend         # 查看后端日志
docker-compose restart backend         # 重启后端
docker-compose down                    # 停止服务
docker-compose exec backend bash       # 进入容器

# 注意事项
# - Redis 服务默认注释，如需启用请取消 docker-compose.yml 中的 redis 注释
# - 前端服务默认注释，推荐使用本地开发模式运行前端
# - 代理配置使用 host.docker.internal 访问宿主机代理
# - 数据库路径: /app/data/quantdinger.db (容器内) = ./backend_api_python/data/quantdinger.db (宿主机)
```

### 本地开发
```bash
# 后端 (Flask API)
cd backend_api_python
pip install -r requirements.txt
cp env.example .env
python run.py                        # 启动在 http://localhost:5000

# 前端 (Vue UI)
cd quantdinger_vue
npm install
npm run serve                        # 启动在 http://localhost:8000
                                    # 自动代理 /api 到后端 5000

# 构建
npm run build                        # 生产构建
npm run lint                         # 代码检查
```

## 关键配置文件

### 后端配置: [backend_api_python/.env](backend_api_python/env.example)

核心配置项:
```bash
# 认证
SECRET_KEY=                          # Flask session 密钥 (生产环境必须更改)
ADMIN_USER=quantdinger
ADMIN_PASSWORD=123456

# AI/LLM (必需用于 AI 分析功能)
OPENROUTER_API_KEY=                  # OpenRouter API 密钥
OPENROUTER_MODEL=openai/gpt-4o       # 使用的模型

# 代理设置 (网络受限时推荐)
PROXY_PORT=7890                      # 或使用 PROXY_URL=socks5h://127.0.0.1:7890

# 代理记忆 (可选)
ENABLE_AGENT_MEMORY=true             # 启用 RAG 记忆
ENABLE_REFLECTION_WORKER=false       # 启用自动反思验证

# 数据库
SQLITE_DATABASE_FILE=/app/data/quantdinger.db  # Docker 路径
```

### 前端配置: [quantdinger_vue/vue.config.js](quantdinger_vue/vue.config.js)

开发环境自动代理 `/api` 到 `http://localhost:5000`

## API 路由结构

所有 API 路由在 [backend_api_python/app/routes/](backend_api_python/app/routes/):
- [auth.py](backend_api_python/app/routes/auth.py): 登录/登出 (`/api/user/login`, `/api/user/logout`)
- [health.py](backend_api_python/app/routes/health.py): 健康检查 (`/api/health`)
- [market.py](backend_api_python/app/routes/market.py): 市场数据 (行情、搜索)
- [kline.py](backend_api_python/app/routes/kline.py): K线数据
- [indicator.py](backend_api_python/app/routes/indicator.py): 指标管理
- [strategy.py](backend_api_python/app/routes/strategy.py): 策略 CRUD 和控制
- [backtest.py](backend_api_python/app/routes/backtest.py): 回测 API
- [analysis.py](backend_api_python/app/routes/analysis.py): AI 多代理分析 (`/api/analysis/multi`)
- [ai_chat.py](backend_api_python/app/routes/ai_chat.py): AI 聊天助手
- [dashboard.py](backend_api_python/app/routes/dashboard.py): 仪表板数据
- [credentials.py](backend_api_python/app/routes/credentials.py): 交易所凭证管理
- [settings.py](backend_api_python/app/routes/settings.py): 系统设置

## 数据库模式

SQLite 数据库默认位置: `backend_api_python/data/quantdinger.db`

核心表:
- `qd_users`: 用户表
- `qd_indicators`: 技术指标 (Python 代码)
- `qd_strategies_trading`: 交易策略配置
- `qd_backtest_results`: 回测结果
- `qd_exchange_credentials`: 交易所 API 密钥 (加密存储)
- `qd_agent_memory_*`: 各代理的记忆表 (单独的 SQLite 数据库在 `data/memory/`)
- `qd_reflection_records`: 反思验证记录
- `pending_orders`: 待执行订单队列
- `gainer_stats`: 涨幅榜币种出现次数统计
- `hama_cache`: HAMA 指标缓存 (可选，使用 Redis)

### 数据库访问
```bash
# 使用 SQLite 客户端查看
sqlite3 backend_api_python/data/quantdinger.db
.tables
.schema qd_strategies_trading
SELECT * FROM qd_strategies_trading;

# Docker 容器内
docker-compose exec backend sqlite3 /app/data/quantdinger.db
```

## 实时交易执行

支持 10+ 加密货币交易所直接 API 交易:
- [live_trading/base.py](backend_api_python/app/services/live_trading/base.py): 基类接口
- [live_trading/binance.py](backend_api_python/app/services/live_trading/binance.py): Binance
- [live_trading/okx.py](backend_api_python/app/services/live_trading/okx.py): OKX
- [live_trading/bitget.py](backend_api_python/app/services/live_trading/bitget.py): Bitget
- [live_trading/execution.py](backend_api_python/app/services/live_trading/execution.py): 执行引擎
- [live_trading/records.py](backend_api_python/app/services/live_trading/records.py): 交易记录

## 策略执行流程

1. **策略启动**: [trading_executor.py](backend_api_python/app/services/trading_executor.py) 启动独立线程
2. **Tick 循环**: 每个 `STRATEGY_TICK_INTERVAL_SEC` (默认 10s) 执行一次:
   - 获取当前价格 (带缓存)
   - 运行用户 Python 指标代码
   - 检查触发条件
   - 发送订单到 `pending_orders` 表
3. **订单执行**: [pending_order_worker.py](backend_api_python/app/services/pending_order_worker.py) 后台 Worker:
   - 轮询 `pending_orders`
   - 根据模式执行:
     - **live**: 调用交易所 API (Crypto)
     - **signal**: 发送通知 (Telegram/Email/Webhook)
4. **状态恢复**: 重启后自动恢复 `status='running'` 的策略

## 国际化 (i18n)

前端支持 10 种语言，文件在 [quantdinger_vue/src/locales/](quantdinger_vue/src/locales/):
- 简体中文、繁体中文、英语、日语、韩语、德语、法语、泰语、越南语、阿拉伯语

TradingView 行情页面配置:
- **默认币种区块**: BTCUSDT、ETHUSDT (固定显示在顶部，蓝色标签，★排名)
- **涨幅榜区块**: 涨幅前10币种 (绿色标签，正常排名)
- **截图缓存**: 自动缓存到 Redis，TTL 600秒 (10分钟)

## 开发原则

1. **本地优先**: 所有数据存储在本地，API 密钥不上传
2. **隐私保护**: 不收集用户数据，不使用云端追踪
3. **透明性**: 算法和策略逻辑可审计
4. **模块化**: 清晰的关注点分离 (routes/services/data_sources)
5. **代理可扩展**: 新增代理继承 [base_agent.py](backend_api_python/app/services/agents/base_agent.py)

## 关键文件引用

### 后端核心
- [run.py](backend_api_python/run.py): 后端入口 (处理 .env 加载、代理配置、UTF-8)
- [app/__init__.py](backend_api_python/app/__init__.py): Flask 应用工厂
- [app/config/settings.py](backend_api_python/app/config/settings.py): 配置类

### 前端核心
- [src/main.js](quantdinger_vue/src/main.js): 前端入口
- [src/router/index.js](quantdinger_vue/src/router/index.js): 路由配置
- [src/store/](quantdinger_vue/src/store/): Vuex 状态管理
- [src/api/](quantdinger_vue/src/api/): API 客户端封装

### 文档
- [README.md](README.md): 项目介绍和快速开始
- [docs/STRATEGY_DEV_GUIDE.md](docs/STRATEGY_DEV_GUIDE.md): 策略开发指南

## 常见任务

### 添加新的交易所
1. 在 [live_trading/](backend_api_python/app/services/live_trading/) 创建新文件继承 `BaseExchange`
2. 实现必需方法: `create_order`, `cancel_order`, `get_balance`, `get_position`
3. 在 [factory.py](backend_api_python/app/services/live_trading/factory.py) 注册
4. 更新前端交易所列表

### 添加新的 AI 代理
1. 在 [agents/](backend_api_python/app/services/agents/) 创建新文件
2. 继承 `BaseAgent` (来自 [base_agent.py](backend_api_python/app/services/agents/base_agent.py))
3. 在 [coordinator.py](backend_api_python/app/services/agents/coordinator.py) 注册代理
4. 在 [memory.py](backend_api_python/app/services/agents/memory.py) 添加记忆表

### 调试代理流程
- 查看 [backend_api_python/logs/](backend_api_python/logs/) 日志文件
- 检查 `data/memory/*.db` 中的代理记忆
- 使用 SQLite 客户端查看 `quantdinger.db` 中的分析结果

## 测试

当前项目未包含自动化测试。手动测试流程:
1. 启动后端和前端
2. 登录 (默认: quantdinger/123456)
3. 创建指标并测试可视化
4. 配置策略并运行回测
5. 启用 AI 代理分析 (需 OPENROUTER_API_KEY)
6. (谨慎) 在测试网启动实时交易

### 测试 TradingView Scanner
1. 访问 http://localhost:8000/#/tradingview-scanner
2. 查看默认币种 (BTCUSDT, ETHUSDT)
3. 查看涨幅榜前10
4. 点击展开行查看截图

### 测试 HAMA 指标
```bash
# 本地计算 (推荐)
curl -X POST http://localhost:5000/api/hama/calculate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "ohlcv": [[...], ...]}'

# OCR 识别 (免费)
curl -X POST http://localhost:5000/api/hama-ocr/extract \
  -H "Content-Type: application/json" \
  -d '{"chart_url": "https://cn.tradingview.com/chart/xxx/", "symbol": "ETHUSD", "interval": "15"}'

# 获取图表截图
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&interval=15m"
```

## 部署注意事项

- 生产环境必须更改 `SECRET_KEY` 和默认密码
- 配置 HTTPS (使用反向代理如 Caddy/Nginx)
- 设置适当的资源限制 (CPU/内存)
- 定期备份 `data/quantdinger.db` 和 `.env` 文件
- 监控日志文件大小，配置日志轮转
- 确保代理配置正确 (如果使用代理)
- Redis 可选但推荐用于生产环境

## 重要提醒

### TradingView Cookie 管理
如果需要访问 TradingView 高级功能或受保护的内容，需要更新 Cookie：
- Cookie 存储位置: 后端配置或环境变量
- 更新频率: Cookie 过期后需手动更新
- 获取方式: 浏览器开发者工具 → Network → 复制 Cookie 值

### Windows 环境特殊说明
```bash
# PowerShell 启动服务
.\restart_services.ps1

# 或使用批处理
.\restart_services.bat
```

## 截图缓存系统详细说明

### 架构
- 后台 Worker: 服务启动时自动启动
- 缓存范围: 涨幅榜前10个币种
- 刷新周期: 每10分钟
- TTL: 600秒 (10分钟)
- 图表周期: 15分钟
- URL 格式: TradingView Widget Embed (不需要登录)

### API 使用
```bash
# 获取截图 (优先从缓存)
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&interval=15m"

# 强制刷新 (忽略缓存)
curl "http://localhost:5000/api/tradingview-scanner/chart-screenshot?symbol=BTCUSDT&interval=15m&force_refresh=true"
```

### 前端展示
- TradingView Scanner 页面: http://localhost:8000/#/tradingview-scanner
- 默认币种区块: BTCUSDT, ETHUSDT (固定在顶部)
- 涨幅榜区块: 动态显示涨幅前10
- 点击展开行显示截图

### 配置修改
修改 [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py):
- 第 240 行: `get_top_gainers(limit=10)` - 修改缓存数量
- 第 117 行: `_SCREENSHOT_CACHE_TTL = 600` - 修改 TTL
- `interval_mapping`: 修改时间周期映射 (15m->15, 1h->60, 1d->D 等)
