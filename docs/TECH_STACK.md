# QuantDinger 技术栈清单

> 本文档详细列出了 QuantDinger 项目使用的所有技术栈、框架、库及其版本信息。

**最后更新**: 2026-01-20
**项目版本**: v2.0.0

---

## 目录

- [运行时环境](#运行时环境)
- [前端技术栈](#前端技术栈)
- [后端技术栈](#后端技术栈)
- [数据库与缓存](#数据库与缓存)
- [浏览器自动化](#浏览器自动化)
- [OCR 识别](#ocr-识别)
- [数据分析](#数据分析)
- [API 集成](#api-集成)
- [开发工具](#开发工具)
- [系统要求](#系统要求)

---

## 运行时环境

### 核心运行时
- **Node.js**: v20.18.0
- **npm**: 10.8.2
- **Python**: 3.11.9

### 包管理器
- **npm**: ^8.0.0 (前端)
- **pip**: 自动 (Python)

---

## 前端技术栈

### 核心框架
| 库名 | 版本 | 用途 |
|------|------|------|
| **Vue** | ^2.6.14 | 核心MVVM框架 |
| **Vue Router** | ^3.5.3 | 路由管理 (Hash模式) |
| **Vuex** | ^3.6.2 | 状态管理 |
| **Vue Template Compiler** | ^2.6.14 | 模板编译 |

### UI 组件库
| 库名 | 版本 | 用途 |
|------|------|------|
| **Ant Design Vue** | ^1.7.8 | 主UI组件库 |
| **@ant-design-vue/pro-layout** | ^1.0.12 | 布局组件 |
| **@ant-design/colors** | ^3.2.2 | 颜色工具 |

### 图表可视化
| 库名 | 版本 | 用途 |
|------|------|------|
| **ECharts** | ^6.0.0 | 主要图表库 (饼图、折线图、柱状图等) |
| **Lightweight Charts** | ^5.0.8 | TradingView轻量级图表 |
| **KlineCharts** | ^9.8.0 | K线图表 |
| **@antv/data-set** | ^0.10.2 | 数据处理 |
| **viser-vue** | ^2.4.8 | 可视化组件 |

### HTTP 客户端
| 库名 | 版本 | 用途 |
|------|------|------|
| **Axios** | ^0.26.1 | HTTP请求 |

### 工具库
| 库名 | 版本 | 用途 |
|------|------|------|
| **Moment.js** | ^2.29.2 | 时间处理 |
| **Crypto-js** | ^4.2.0 | 加密解密 |
| **Lodash** (多个包) | ^4.4.x | 数据处理工具 |
| **MD5** | ^2.3.0 | MD5哈希 |
| **Store** | ^2.0.12 | 本地存储 |

### 表单与编辑器
| 库名 | 版本 | 用途 |
|------|------|------|
| **Vue Quill Editor** | ^3.0.6 | 富文本编辑器 |
| **WangEditor** | ^3.1.1 | 富文本编辑器 |
| **CodeMirror** | ^5.65.16 | 代码编辑器 |
| **Vue Cropper** | 0.4.9 | 图片裁剪 |

### 其他功能库
| 库名 | 版本 | 用途 |
|------|------|------|
| **Vue i18n** | ^8.27.1 | 国际化 |
| **Vue Clipboard2** | ^0.2.1 | 剪贴板操作 |
| **NProgress** | ^0.2.0 | 进度条 |
| **Enquire.js** | ^2.1.6 | 响应式媒体查询 |
| **Mockjs2** | 1.0.8 | 数据模拟 |
| **@iconify/vue2** | ^2.1.0 | 图标组件 |
| **Vue SVG Component Runtime** | ^1.0.1 | SVG组件 |

### 构建工具
| 库名 | 版本 | 用途 |
|------|------|------|
| **Vue CLI** | ~5.0.8 | 项目脚手架 |
| **@vue/cli-service** | ~5.0.8 | 构建服务 |
| **@vue/cli-plugin-babel** | ~5.0.8 | Babel集成 |
| **@vue/cli-plugin-eslint** | ~5.0.8 | ESLint集成 |
| **@vue/cli-plugin-router** | ~5.0.8 | Router集成 |
| **@vue/cli-plugin-vuex** | ~5.0.8 | Vuex集成 |
| **@vue/cli-plugin-unit-jest** | ~5.0.8 | 单元测试 |

### 编译器与转译器
| 库名 | 版本 | 用途 |
|------|------|------|
| **Babel** | Core | JavaScript编译 |
| **Babel Core** | ^7.x | Babel核心 |
| **Babel Loader** | 8 | Webpack Babel加载器 |
| **Babel Plugin Import** | ^1.13.3 | 按需引入 |
| **Babel ESLint** | ^10.1.0 | Babel ESLint |
| **Regenerator Runtime** | ^0.13.9 | async/await支持 |

### CSS 预处理器
| 库名 | 版本 | 用途 |
|------|------|------|
| **Less** | ^3.13.1 | CSS预处理器 |
| **Less Loader** | ^5.0.0 | Webpack Less加载器 |
| **Sass** | ^1.97.2 | CSS预处理器 |
| **Sass Loader** | ^10.5.2 | Webpack Sass加载器 |
| **PostCSS** | ^8.3.5 | CSS转换工具 |
| **PostCSS Less** | ^6.0.0 | Less PostCSS支持 |

### 代码规范
| 库名 | 版本 | 用途 |
|------|------|------|
| **ESLint** | ^7.0.0 | JavaScript代码检查 |
| **Babel ESLint** | ^10.1.0 | Babel ESLint |
| **ESLint Plugin Vue** | ^5.2.3 | Vue文件检查 |
| **ESLint Plugin HTML** | ^5.0.5 | HTML检查 |
| **Stylelint** | ^14.8.5 | CSS/Less检查 |
| **Lint Staged** | ^12.5.0 | Git暂存文件检查 |

### Git 工具
| 库名 | 版本 | 用途 |
|------|------|------|
| **Husky** | ^6.0.0 | Git hooks管理 |
| **Commitizen** | ^4.2.4 | 规范化提交 |
| **Commitlint** | ^12.1.4 | 提交信息检查 |
| **CZ Conventional Changelog** | ^3.3.0 | 提交规范 |
| **Git Revision Webpack Plugin** | ^3.0.6 | Git版本信息 |

### 测试工具
| 库名 | 版本 | 用途 |
|------|------|------|
| **@vue/test-utils** | ^1.3.0 | Vue组件测试 |
| **Jest** | (内置) | 单元测试框架 |

### Webpack 插件
| 库名 | 版本 | 用途 |
|------|------|------|
| **Webpack Theme Color Replacer** | ^1.3.26 | 主题色替换 |
| **File Loader** | ^6.2.0 | 文件加载 |
| **Vue SVG Icon Loader** | ^2.1.1 | SVG图标加载 |
| **Vue SVG Loader** | 0.16.0 | SVG加载 |

---

## 后端技术栈

### 核心框架
| 库名 | 版本 | 用途 |
|------|------|------|
| **Flask** | 2.3.3 | Web框架 |
| **Flask-CORS** | 4.0.0 | 跨域支持 |

### 数据验证与安全
| 库名 | 版本 | 用途 |
|------|------|------|
| **PyJWT** | 2.8.0 | JWT令牌生成和验证 |
| **python-dotenv** | ^1.0.1 | 环境变量管理 |

### 任务调度
| 库名 | 版本 | 用途 |
|------|------|------|
| **APScheduler** | ^3.10.0 | 定时任务调度 |

### WebSocket
| 库名 | 版本 | 用途 |
|------|------|------|
| **WebSockets** | ^12.0 | WebSocket支持 |

---

## 数据库与缓存

### ORM
| 库名 | 版本 | 用途 |
|------|------|------|
| **SQLAlchemy** | ^2.0.0 | Python ORM |
| **PyMySQL** | ^1.0.2 | MySQL驱动 |

### 缓存
| 库名 | 版本 | 用途 |
|------|------|------|
| **Redis** | ^5.0.0 | 缓存和消息队列 |

### 本地数据库
| 库名 | 版本 | 用途 |
|------|------|------|
| **SQLite** | (Python内置) | 轻量级本地数据库 |

---

## 浏览器自动化

### Playwright 方案
| 库名 | 版本 | 用途 |
|------|------|------|
| **Playwright** | ^1.40.0 | 浏览器自动化 (推荐) |
| **Playwright Stealth** | ^1.0.5 | 反检测插件 |

### Selenium 方案
| 库名 | 版本 | 用途 |
|------|------|------|
| **Selenium** | ^4.15.0 | 浏览器自动化 (备用) |
| **WebDriver Manager** | ^4.0.0 | 驱动管理 |

### 浏览器支持
- **Chromium** (Chrome/Edge)
- **Brave** (主要使用)
- **Firefox** (可选)
- **WebKit** (可选)

---

## OCR 识别

### 主要引擎
| 库名 | 版本 | 用途 |
|------|------|------|
| **RapidOCR** | ^1.3.0 (rapidocr_onnxruntime) | 主要OCR引擎 (推荐) |
| **PaddleOCR** | ^2.7.0 | 备用OCR引擎 |
| **PaddlePaddle** | ^2.6.0 | PaddleOCR依赖 |

### 识别能力
- 中文识别
- 英文识别
- 数字识别
- 混合文本识别

---

## 数据分析

### 核心库
| 库名 | 版本 | 用途 |
|------|------|------|
| **Pandas** | ^1.5.0 | 数据处理和分析 |
| **NumPy** | ^1.24.0 | 数值计算 |

---

## API 集成

### 金融数据 API
| 库名 | 版本 | 用途 |
|------|------|------|
| **yfinance** | ^0.2.18 | Yahoo Finance数据 |
| **Finnhub Python** | ^2.4.18 | Finnhub数据 |
| **AKShare** | ^1.12.0 | 金融数据接口 (中文) |
| **CCXT** | ^4.0.0 | 加密货币交易所API |

### HTTP 工具
| 库名 | 版本 | 用途 |
|------|------|------|
| **Requests** | ^2.28.0 | HTTP客户端 |
| **PySocks** | ^1.7.1 | SOCKS代理支持 |

### HTML 解析
| 库名 | 版本 | 用途 |
|------|------|------|
| **BeautifulSoup4** | ^4.7.1 | HTML解析 |
| **lxml** | ^4.3.2 | XML/HTML解析引擎 |

### 异步支持
| 库名 | 版本 | 用途 |
|------|------|------|
| **nest-asyncio** | ^1.0.0 | 嵌套事件循环支持 |

---

## 开发工具

### 前端开发工具
| 工具 | 用途 |
|------|------|
| **Vue DevTools** | Vue调试 |
| **Chrome DevTools** | 浏览器调试 |
| **ESLint** | 代码检查 |
| **Stylelint** | 样式检查 |

### 后端开发工具
| 工具 | 用途 |
|------|------|
| **pytest** | 单元测试 (可选) |
| **black** | 代码格式化 (可选) |
| **flake8** | 代码检查 (可选) |

---

## 系统要求

### 开发环境
- **操作系统**: Windows 10/11, macOS, Linux
- **内存**: 最低 8GB，推荐 16GB
- **磁盘**: 最低 10GB 可用空间
- **网络**: 稳定的互联网连接

### 浏览器要求
- **Brave Browser** (推荐): 最新稳定版
- **Google Chrome**: 最新稳定版
- **Chromium**: 最新版本

### Python 环境
- **Python**: 3.11.x (推荐 3.11.9)
- **pip**: 最新版本

### Node.js 环境
- **Node.js**: 20.x (推荐 20.18.0)
- **npm**: 10.x (推荐 10.8.2)

---

## 依赖安装

### 前端依赖安装
```bash
cd quantdinger_vue
npm install
```

### 后端依赖安装
```bash
cd backend_api_python
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 安装 Brave 浏览器 (手动)
# 下载地址: https://brave.com/download/
```

---

## 版本管理策略

### 依赖版本锁定
- **前端**: 使用 package-lock.json 锁定确切版本
- **后端**: 使用 requirements.txt 指定版本范围

### 版本更新策略
- **主版本**: 重大更新，可能包含破坏性变更
- **次版本**: 功能更新，向后兼容
- **补丁版本**: Bug修复，向后兼容

### 推荐更新频率
- **安全更新**: 立即更新
- **主版本更新**: 评估后谨慎更新
- **次版本更新**: 每季度检查一次
- **补丁版本更新**: 每月更新一次

---

## 技术栈总结

### 前端技术栈
- **核心**: Vue 2.6 + Vuex + Vue Router
- **UI**: Ant Design Vue 1.7
- **图表**: ECharts 6.0 + Lightweight Charts 5.0 + KlineCharts 9.8
- **构建**: Vue CLI 5.0 + Webpack
- **工具**: Axios, Moment.js, Lodash

### 后端技术栈
- **框架**: Flask 2.3
- **自动化**: Playwright 1.40 + Playwright Stealth
- **OCR**: RapidOCR 1.3 + PaddleOCR 2.7
- **数据**: Pandas 1.5 + NumPy 1.24
- **API**: CCXT 4.0 + yfinance 0.2

### 特色技术
- ✅ **无头浏览器自动化**: Playwright + Stealth
- ✅ **本地OCR识别**: RapidOCR (完全免费)
- ✅ **多图表库集成**: 3个专业图表库
- ✅ **实时数据推送**: WebSocket + SSE
- ✅ **多数据源支持**: 5个金融数据API

---

## 附录

### A. 常用命令

**前端**:
```bash
npm run serve          # 启动开发服务器 (端口8000)
npm run build          # 构建生产版本
npm run lint           # 代码检查
npm run lint:nofix     # 代码检查 (不自动修复)
```

**后端**:
```bash
python run.py          # 启动Flask服务器 (端口5000)
pytest                 # 运行测试 (可选)
```

### B. 环境变量

**前端**: `.env.development`, `.env.production`
**后端**: `.env` 或通过 `python-dotenv` 加载

### C. 配置文件

**前端**:
- `vue.config.js` - Vue CLI配置
- `.eslintrc.js` - ESLint配置
- `.stylelintrc.js` - Stylelint配置

**后端**:
- `requirements.txt` - Python依赖
- `config.py` - 应用配置
- `file/tradingview.txt` - TradingView配置

---

## 维护说明

### 依赖更新检查
```bash
# 前端: 检查过时的依赖
npm outdated

# 后端: 检查过时的依赖
pip list --outdated
```

### 安全漏洞扫描
```bash
# 前端: npm audit
npm audit

# 后端: 使用 pip-audit (需安装)
pip install pip-audit
pip-audit
```

---

## 技术支持

如有技术问题，请参考：
1. 项目文档: `CLAUDE.md`, `BRAVE_MONITOR_LOGIC.md`
2. API文档: 启动后端后访问 http://localhost:5000/docs
3. GitHub Issues: https://github.com/alexbibihere/QuantDinger/issues

---

**文档版本**: v1.0
**最后更新**: 2026-01-20
**维护者**: QuantDinger Team
