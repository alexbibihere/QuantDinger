# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuantDinger 是一个本地优先、隐私优先的 AI 驱动量化交易平台。系统完全在本地运行，用户对策略、交易数据和 API 密钥拥有完全控制权。

## 架构概览

### 技术栈
- **前端**: Vue 2.6.14 + Ant Design Vue + KlineCharts/ECharts
- **后端**: Python 3.10+ + Flask 2.3.3 + SQLAlchemy 2.0
- **数据库**: SQLite (本地文件)
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

### 4. TradingView 集成与 HAMA 指标

系统实现了完整的 TradingView 数据获取和 HAMA 指标计算功能：

#### TradingView Scanner 功能
- **涨幅榜监控**: 实时监控币安合约涨幅榜前100名
- **自动刷新**: 每5分钟自动刷新数据
- **默认币种**: BTCUSDT、ETHUSDT 固定显示在页面顶部
- **截图缓存**: 后台 Worker 自动缓存涨幅榜前10名币种的15分钟图表截图到 Redis，每10分钟刷新
- **Widget URL**: 使用 `https://s.tradingview.com/widgetembed/` 不需要登录即可显示图表

关键文件:
- [tradingview_scanner.py](backend_api_python/app/routes/tradingview_scanner.py): Scanner API 和截图缓存 Worker
- [tradingview_scanner_service.py](backend_api_python/app/services/tradingview_scanner_service.py): 数据获取服务
- [gainer_tracker.py](backend_api_python/app/services/gainer_tracker.py): 涨幅榜统计

#### HAMA 指标多种实现方案
系统提供 **5 种方案** 获取 HAMA 指标：

1. **本地计算 (推荐)**: [hama_calculator.py](backend_api_python/app/services/hama_calculator.py)
   - API: `/api/hama/calculate`
   - 速度: ~10ms
   - 成本: 免费
   - 适用场景: 生产环境首选

2. **OCR 识别**: [hama_ocr_extractor.py](backend_api_python/app/services/hama_ocr_extractor.py)
   - API: `/api/hama-ocr/extract`
   - 使用 PaddleOCR (完全免费)
   - 速度: ~2秒
   - 适用场景: 日常使用推荐

3. **Playwright**: [tradingview_playwright.py](backend_api_python/app/services/tradingview_playwright.py)
   - 使用 playwright-stealth 绕过反爬
   - 支持 Cookie 认证
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
# 前端: http://localhost:8000
# 后端: http://localhost:5000

# 常用命令
docker-compose ps                    # 查看状态
docker-compose logs -f backend       # 查看后端日志
docker-compose restart backend       # 重启后端
docker-compose down                  # 停止服务
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
- `qd_agent_memory_*`: 各代理的记忆表
- `qd_reflection_records`: 反思验证记录
- `pending_orders`: 待执行订单队列

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
