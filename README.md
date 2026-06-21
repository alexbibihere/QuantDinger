# QuantDinger

> 基于HAMA指标的智能量化交易监控系统

[![Python Version](https://img.shields.io/badge/python-3.11.9-blue.svg)](https://www.python.org/)
[![Node Version](https://img.shields.io/badge/node.js-20.18.0-green.svg)](https://nodejs.org/)
[![Vue Version](https://img.shields.io/badge/vue-2.6.14-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📖 项目简介

QuantDinger 是一个功能完善的量化交易监控系统，集成了多项创新技术：

- **🤖 BrowserAct 智能监控**: 新增 BrowserAct 直接数据提取，无需 OCR，速度提升 3 倍
- **🎭 Playwright+OCR 降级方案**: 使用 Playwright 控制浏览器访问 TradingView，通过 RapidOCR 本地识别 HAMA 指标
- **🔄 混合监控模式**: BrowserAct 优先，失败时自动降级，确保系统稳定性
- **📊 多维度数据展示**: Dashboard 仪表盘、K线图表、实时价格推送
- **⚡ 智能监控引擎**: 支持并发监控、缓存预热、智能间隔调整
- **🔔 实时信号通知**: HAMA 交叉信号、订单声音提醒
- **🎯 多市场支持**: 现货、合约市场全覆盖

## ✨ 核心特性

### 1. BrowserAct 智能监控系统 🆕
- ✅ **直接数据提取**: 从 TradingView 直接获取结构化数据，无需 OCR
- ✅ **速度提升 3 倍**: 平均响应时间 < 5 秒（传统方案 > 15 秒）
- ✅ **准确性更高**: 避免图像识别错误，数据精度接近 100%
- ✅ **自动登录**: 支持 TradingView 自动登录和会话保持
- ✅ **Cloudflare 绕过**: 自动处理验证码和反爬机制
- ✅ **混合模式**: BrowserAct 优先，失败时自动降级到传统方案

### 2. Playwright+OCR 监控系统（传统方案）
- ✅ 使用 Brave 浏览器无头模式访问 TradingView
- ✅ RapidOCR 本地识别，完全免费，无需 API 密钥
- ✅ 支持自动登录 TradingView 账号
- ✅ SQLite + Redis 双层缓存
- ✅ 并发监控，提升效率
- ✅ 智能监控间隔（根据市场活跃度调整）

### 2. 前端功能
- 📈 **Dashboard**: KPI指标、收益日历、策略分布、回撤曲线
- 🎯 **HAMA Market**: 实时监控 HAMA 状态，支持自动刷新
- 📊 **Smart Monitor**: 涨幅榜监控、HAMA 信号检测
- 🔍 **TradingView Scanner**: 涨幅榜 TOP10，图表截图懒加载
- 📉 **Indicator Analysis**: K线图表，HAMA 指标回测
- 🤖 **Trading Assistant**: AI 决策记录、持仓管理

### 3. 技术亮点
- ⚡ **实时数据推送**: WebSocket + SSE
- 🎨 **多主题支持**: Light、Dark、RealDark
- 🌍 **国际化**: 支持中英文切换
- 📱 **响应式设计**: 适配桌面和移动端
- 🔐 **安全加密**: API密钥加密存储

## 🚀 快速开始

### 环境要求

- **Python**: 3.11.x (推荐 3.11.9) 或 3.12+ (BrowserAct 需要)
- **Node.js**: 20.x (推荐 20.18.0)
- **Brave 浏览器**: 最新稳定版（可选）
- **Redis**: 5.0+ (可选)
- **uv 包管理器**: 最新版本（BrowserAct 需要）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/alexbibihere/QuantDinger.git
cd QuantDinger
```

#### 2. 后端安装

```bash
cd backend_api_python

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（传统方案）
playwright install chromium

# (可选) 安装 BrowserAct CLI（推荐）
# 运行自动安装脚本
install_browseract.bat

# 或手动安装
uv tool install browser-act-cli --python 3.12

# (可选) 安装 Brave 浏览器
# 下载地址: https://brave.com/download/
```

#### 3. 前端安装

```bash
cd quantdinger_vue

# 安装 npm 依赖
npm install
```

#### 4. 配置文件

创建配置文件 `backend_api_python/.env`:

```env
# Flask 配置
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

# TradingView 配置
TRADINGVIEW_URL=https://cn.tradingview.com/chart/U1FY2qxO/

# Brave 浏览器路径 (Windows)
BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe

# Redis 配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 监控配置
BRAVE_MONITOR_ENABLED=true
HAMA_DEMO_MODE=false
```

配置 TradingView Cookie (可选，用于自动登录):

创建 `backend_api_python/tradingview_cookies.json`:

```json
{
  "cookies": [
    {
      "name": "sessionid",
      "value": "your-cookie-value",
      "domain": ".tradingview.com",
      "path": "/"
    }
  ]
}
```

#### 5. 启动服务

**方式一：一键启动（推荐）**

```bash
# BrowserAct 增强版启动
start_browseract_hama.bat

# 或标准启动
start-all.bat
```

**方式二：分别启动**

**启动后端**:

```bash
cd backend_api_python
python run.py
# 后端运行在 http://localhost:5000
```

**启动前端**:

```bash
cd quantdinger_vue
npm run serve
# 前端运行在 http://localhost:8000
```

**方式三：使用 BrowserAct 集成测试**

```bash
# 测试 BrowserAct 集成
test_browseract.bat

# 安装 BrowserAct CLI
install_browseract.bat
```

#### 6. 访问应用

打开浏览器访问: http://localhost:8000

## 📁 项目结构

```
QuantDinger/
├── backend_api_python/          # Python 后端
│   ├── app/
│   │   ├── routes/             # API 路由
│   │   ├── services/           # 业务逻辑
│   │   │   ├── hama_brave_monitor.py      # Brave 监控器
│   │   │   ├── hama_ocr_extractor.py      # OCR 提取器
│   │   │   └── hama_vision_extractor.py   # 视觉识别提取器
│   │   ├── models/             # 数据模型
│   │   └── utils/              # 工具函数
│   ├── data/                   # SQLite 数据库
│   ├── screenshots/            # HAMA 截图
│   └── run.py                  # Flask 启动文件
│
├── quantdinger_vue/             # Vue 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── dashboard/      # 仪表盘
│   │   │   ├── hama-market/    # HAMA 行情
│   │   │   ├── smart-monitor/  # 智能监控
│   │   │   └── tradingview-scanner/  # TV 扫描器
│   │   ├── components/         # 公共组件
│   │   ├── mixins/             # Mixins
│   │   └── utils/              # 工具函数
│   └── package.json
│
└── docs/                        # 文档
    ├── README.md               # 文档索引
    ├── CLAUDE.md               # 前端架构文档
    ├── TECH_STACK.md           # 技术栈清单
    └── BRAVE_MONITOR_LOGIC.md  # Brave 监控逻辑
```

## 🔧 技术栈

### 前端
- **Vue 2.6.14** - MVVM 框架
- **Vuex 3.6.2** - 状态管理
- **Vue Router 3.5.3** - 路由管理
- **Ant Design Vue 1.7.8** - UI 组件库
- **ECharts 6.0.0** - 图表库
- **Axios 0.26.1** - HTTP 客户端

### 后端
- **Flask 2.3.3** - Web 框架
- **Playwright 1.40.0** - 浏览器自动化
- **RapidOCR 1.3.0** - OCR 识别引擎
- **SQLAlchemy 2.0.0** - ORM
- **APScheduler 3.10.0** - 定时任务

### 数据库
- **SQLite** - 本地数据库
- **Redis** - 缓存（可选）

## 📖 文档

- 📖 [前端架构文档](./docs/CLAUDE.md) - 前端页面技术实现
- 🔧 [技术栈清单](./docs/TECH_STACK.md) - 完整依赖列表
- 🤖 [Brave 监控逻辑](./docs/BRAVE_MONITOR_LOGIC.md) - 监控系统详解

## 🎯 主要功能

### 1. Brave 监控系统

通过 Brave 浏览器自动访问 TradingView，使用 RapidOCR 识别 HAMA 指标：

```python
from app.services.hama_brave_monitor import get_brave_monitor

# 获取监控器实例
monitor = get_brave_monitor(use_sqlite=True)

# 监控单个币种
result = monitor.monitor_symbol('BTCUSDT', browser_type='brave')

# 批量并发监控
results = monitor.monitor_batch_parallel(
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    max_workers=3
)

# 启动持续监控
monitor.start_monitoring(
    symbols=['BTCUSDT', 'ETHUSDT'],
    interval=300,  # 5分钟
    browser_type='brave'
)

# 健康检查
health = monitor.health_check()
print(health)  # {'status': 'healthy', 'checks': {...}}
```

### 2. HAMA 行情 API

```http
# 获取监控列表
GET /api/hama-market/watchlist?market=spot

# 获取单个币种
GET /api/hama-market/symbol?symbol=BTCUSDT&interval=15m

# 获取信号列表
GET /api/hama-market/signals
```

## 🔄 监控流程

```
┌─────────────────┐
│  TradingView    │
│   图表页面      │
└────────┬────────┘
         │
         │ Playwright 访问
         ▼
┌─────────────────┐
│  Brave Browser  │
│  (无头模式)     │
└────────┬────────┘
         │
         │ 截取 HAMA 面板
         ▼
┌─────────────────┐
│  PNG 图片       │
│  (本地文件)     │
└────────┬────────┘
         │
         │ RapidOCR 识别
         ▼
┌─────────────────┐
│  OCR 文本       │
│  (原始数据)     │
└────────┬────────┘
         │
         │ 解析提取
         ▼
┌─────────────────┐
│  HAMA 数据      │
│  (结构化)       │
└────────┬────────┘
         │
         ├──────┐
         │      │
         ▼      ▼
    ┌────────┐ ┌────────┐
    │ SQLite │ │ Redis  │
    │(持久化)│ │ (缓存) │
    └────────┘ └────────┘
```

## 🛠️ 开发指南

### 添加新的监控币种

编辑 `backend_api_python/app/routes/hama_market.py`:

```python
DEFAULT_SYMBOLS = [
    'BTCUSDT',
    'ETHUSDT',
    'YOURLCOINUSDT',  # 添加新币种
]
```

### 调整 OCR 识别参数

编辑 `backend_api_python/app/services/hama_ocr_extractor.py`:

```python
# 截图区域调整 (x, y, width, height)
clip = {
    'x': int(page_width * 0.72),
    'y': int(page_height * 0.45),
    'width': int(page_width * 0.28),
    'height': int(page_height * 0.55)
}
```

### 自定义监控间隔

```python
# 动态间隔 (根据市场活跃度)
interval = monitor.get_dynamic_interval()  # 300或600秒

# 固定间隔
monitor.start_monitoring(symbols, interval=600)
```

## 🐛 故障排除

### 1. Brave 浏览器未找到

```
⚠️ 未找到 Brave 浏览器，回退到 Chromium
```

**解决方法**:
- 安装 Brave 浏览器: https://brave.com/download/
- 或修改 `BRAVE_PATH` 环境变量

### 2. OCR 识别失败

```
❌ RapidOCR 初始化失败
```

**解决方法**:
```bash
pip install rapidocr_onnxruntime
```

### 3. TradingView 登录失败

```
⚠️ 自动登录失败
```

**解决方法**:
1. 手动登录 TradingView 并导出 Cookie
2. 将 Cookie 保存到 `tradingview_cookies.json`
3. 或配置 `file/tradingview.txt` 中的账号密码

### 4. SQLite 数据库锁定

```
sqlite3.OperationalError: database is locked
```

**解决方法**:
- 代码已实现每次创建新连接
- 如果仍有问题，重启后端服务

## 📊 性能优化

### 并发监控

```python
# 串行监控 (默认)
monitor.monitor_batch(symbols)  # 慢

# 并发监控 (快3倍)
monitor.monitor_batch_parallel(symbols, max_workers=3)
```

### 缓存预热

```python
# 启动时预热热门币种
monitor.warmup_cache(hot_symbols=['BTCUSDT', 'ETHUSDT'])
```

### 资源清理

```python
# 清理7天前的数据
monitor.cleanup_old_records(days=7)

# 清理7天前的截图
monitor.cleanup_old_screenshots(max_age_days=7)
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📝 更新日志

### v2.0.0 (2026-01-20)
- ✅ 新增 Brave 浏览器监控系统
- ✅ 集成 RapidOCR 本地识别
- ✅ 实现并发监控和智能间隔
- ✅ 添加缓存预热和健康检查
- ✅ 优化前端页面性能
- ✅ 完善技术文档

### v1.0.0
- 初始版本发布

## 📄 许可证

[MIT License](LICENSE)

## 👥 作者

QuantDinger Team

## 🙏 致谢

- [TradingView](https://www.tradingview.com/) - 图表平台
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - OCR 引擎
- [Ant Design Vue](https://www.antdv.com/) - UI 组件库

## 📮 联系方式

- GitHub Issues: [https://github.com/alexbibihere/QuantDinger/issues](https://github.com/alexbibihere/QuantDinger/issues)
- 邮箱: support@quantdinger.com

---

⭐ 如果这个项目对你有帮助，请点个 Star！
