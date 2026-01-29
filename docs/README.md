# QuantDinger 技术栈快速参考

## 运行时环境
- **Node.js**: v20.18.0
- **Python**: 3.11.9
- **npm**: 10.8.2

## 前端核心
```
Vue 2.6.14
├── Vuex 3.6.2 (状态管理)
├── Vue Router 3.5.3 (路由)
├── Ant Design Vue 1.7.8 (UI组件)
├── ECharts 6.0.0 (图表)
├── Lightweight Charts 5.0.8 (TradingView图表)
├── KlineCharts 9.8.0 (K线图)
├── Axios 0.26.1 (HTTP)
├── Moment.js 2.29.2 (时间)
└── Vue i18n 8.27.1 (国际化)
```

## 后端核心
```
Flask 2.3.3
├── SQLAlchemy 2.0.0 (ORM)
├── Redis 5.0.0 (缓存)
├── Playwright 1.40.0 (浏览器自动化)
├── Playwright Stealth 1.0.5 (反检测)
├── RapidOCR 1.3.0 (OCR识别)
├── PaddleOCR 2.7.0 (备用OCR)
├── APScheduler 3.10.0 (定时任务)
├── Pandas 1.5.0 (数据分析)
├── CCXT 4.0.0 (交易所API)
├── yfinance 0.2.18 (金融数据)
└── AkShare 1.12.0 (中文金融数据)
```

## 数据库
- **SQLite**: 本地开发/缓存
- **MySQL**: 生产数据库 (可选)
- **Redis**: 缓存和消息队列

## 浏览器
- **Brave**: 主要使用 (无头模式)
- **Chromium**: 备用
- **Firefox**: 可选

## 开发工具
- **Vue CLI 5.0**: 前端脚手架
- **Webpack**: 模块打包
- **ESLint**: 代码检查
- **Stylelint**: 样式检查
- **Husky**: Git hooks

## 项目端口
- **前端**: http://localhost:8000
- **后端**: http://localhost:5000

## 📚 文档导航

### 快速开始
- 🚀 [快速开始指南](./QUICKSTART.md) - 5分钟快速上手
- 📖 [项目总览](../README.md) - 项目介绍和核心特性

### 技术文档
- 🎨 [前端架构技术文档](./CLAUDE.md) - Vue前端各页面技术实现
- 🔧 [技术栈清单](./TECH_STACK.md) - 完整依赖和版本信息
- 🤖 [Brave监控系统逻辑](./BRAVE_MONITOR_LOGIC.md) - 监控系统架构和实现细节

### 文档目录
- [README.md](../README.md) - 项目根目录
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始指南
- [CLAUDE.md](./CLAUDE.md) - 前端架构文档（含7大页面详解）
- [TECH_STACK.md](./TECH_STACK.md) - 技术栈清单
- [BRAVE_MONITOR_LOGIC.md](./BRAVE_MONITOR_LOGIC.md) - Brave监控逻辑详解

## 🔥 快速链接

- [快速安装](./QUICKSTART.md#-快速安装)
- [核心特性](../README.md#-核心特性)
- [前端页面](./CLAUDE.md#技术栈概览)
- [监控流程](../README.md#-监控流程)
- [常见问题](./QUICKSTART.md#-常见问题)
