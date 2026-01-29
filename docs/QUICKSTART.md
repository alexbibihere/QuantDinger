# QuantDinger 快速开始指南

> 5分钟快速上手 QuantDinger 量化交易监控系统

## 📋 前置要求

在开始之前，请确保你的系统已安装以下软件：

- **Python 3.11.9** - [下载地址](https://www.python.org/downloads/)
- **Node.js 20.18.0** - [下载地址](https://nodejs.org/)
- **Git** - [下载地址](https://git-scm.com/downloads)

可选组件：
- **Brave 浏览器** - [下载地址](https://brave.com/download/)（推荐）
- **Redis 5.0+** - [下载地址](https://redis.io/download)（可选，用于缓存）

## 🚀 快速安装

### 步骤 1: 克隆项目

打开终端（Windows 使用 PowerShell 或 CMD），执行：

```bash
git clone https://github.com/alexbibihere/QuantDinger.git
cd QuantDinger
```

### 步骤 2: 安装后端依赖

```bash
cd backend_api_python

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

**如果遇到安装问题**：

```bash
# 如果 pip 安装失败，尝试升级 pip
python -m pip install --upgrade pip

# 如果 Playwright 安装失败，手动下载
playwright install --with-deps chromium
```

### 步骤 3: 安装前端依赖

打开新的终端窗口：

```bash
cd quantdinger_vue

# 安装依赖
npm install
```

**如果 npm 安装缓慢**：

```bash
# 使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

## ⚙️ 配置文件

### 步骤 4: 创建后端配置文件

在 `backend_api_python` 目录下创建 `.env` 文件：

```bash
cd backend_api_python
# Windows
type nul > .env
# Linux/Mac
touch .env
```

编辑 `.env` 文件，添加以下内容：

```env
# Flask 配置
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this

# TradingView 配置
TRADINGVIEW_URL=https://cn.tradingview.com/chart/U1FY2qxO/

# Brave 浏览器路径（根据你的系统调整）
# Windows:
BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
# Linux:
# BRAVE_PATH=/usr/bin/brave-browser
# Mac:
# BRAVE_PATH=/Applications/Brave Browser.app/Contents/MacOS/Brave Browser

# 监控配置
BRAVE_MONITOR_ENABLED=true
HAMA_DEMO_MODE=false

# 日志级别
LOG_LEVEL=INFO
```

### 步骤 5: 配置 TradingView Cookie（可选）

如果需要自动登录 TradingView，在 `backend_api_python` 目录下创建 `tradingview_cookies.json`：

```json
{
  "cookies": [
    {
      "name": "sessionid",
      "value": "your-session-id-here",
      "domain": ".tradingview.com",
      "path": "/"
    }
  ]
}
```

**如何获取 Cookie**：

1. 打开浏览器，访问 https://cn.tradingview.com/
2. 登录你的账号
3. 按 F12 打开开发者工具
4. 切换到 "Network" 标签
5. 刷新页面，找到任意请求
6. 查看 "Request Headers"，复制 Cookie 值

## 🎯 启动服务

### 步骤 6: 启动后端服务

```bash
cd backend_api_python

# 激活虚拟环境（如果使用）
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 启动后端
python run.py
```

看到以下输出表示启动成功：

```
=======================================================
  QuantDinger 后端服务启动中...
=======================================================
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 123-456-789
 * Running on http://0.0.0.0:5000
```

后端默认运行在 `http://localhost:5000`

### 步骤 7: 启动前端服务

打开新的终端窗口：

```bash
cd quantdinger_vue

# 启动前端
npm run serve
```

看到以下输出表示启动成功：

```
  App running at:
  - Local:   http://localhost:8000
  - Network: http://192.168.1.100:8000

  Note that the development build is not optimized.
  To create a production build, run npm run build.
```

前端默认运行在 `http://localhost:8000`

## 🌐 访问应用

### 步骤 8: 打开浏览器

在浏览器中访问：**http://localhost:8000**

你应该能看到 QuantDinger 的主界面。

## 📸 首次监控设置

### 步骤 9: 测试 Brave 监控

1. 访问 **HAMA Market** 页面
2. 点击右上角的 **刷新** 按钮
3. 等待 1-2 分钟，系统会自动监控 BTCUSDT、ETHUSDT 等币种
4. 查看 HAMA 状态、价格等信息

如果看到数据正常显示，说明 Brave 监控系统工作正常！

### 步骤 10: 启动持续监控（可选）

访问 **Smart Monitor** 页面，点击 **启动监控** 按钮，系统会持续监控你添加的币种。

## 🔧 常见问题

### Q1: 后端启动失败 - 端口被占用

```
Address already in use
```

**解决方案**：

```bash
# Windows: 查找占用端口的进程
netstat -ano | findstr :5000
# 结束进程（PID 替换为实际进程 ID）
taskkill /PID <进程ID> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill -9
```

### Q2: 前端启动失败 - Node 版本过低

```
Error: Node version is too old
```

**解决方案**：

升级到 Node.js 20.x：https://nodejs.org/

### Q3: Brave 浏览器未找到

```
⚠️ 未找到 Brave 浏览器，回退到 Chromium
```

**解决方案**：

1. 安装 Brave 浏览器：https://brave.com/download/
2. 或修改 `.env` 文件中的 `BRAVE_PATH` 为正确的路径

### Q4: OCR 识别失败

```
❌ RapidOCR 初始化失败
```

**解决方案**：

```bash
pip install rapidocr_onnxruntime
```

### Q5: 数据显示为空

**可能原因**：

1. 监控系统还未完成首次监控（等待 2-3 分钟）
2. 数据库文件权限问题
3. Brave 浏览器路径配置错误

**解决方案**：

查看后端日志，检查是否有错误信息。

## 📊 下一步

恭喜！你已经成功运行 QuantDinger。接下来你可以：

1. **添加自定义币种**：在 Smart Monitor 页面添加你想要监控的币种
2. **调整监控间隔**：在代码中修改 `monitor.start_monitoring(interval=600)` 的值
3. **查看文档**：阅读 [完整文档](./README.md) 了解更多功能
4. **自定义配置**：修改 `.env` 文件中的配置项

## 🎓 进阶配置

### 启用 Redis 缓存（可选）

```bash
# 安装 Redis
# Windows: 下载 Redis for Windows
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# 启动 Redis
redis-server

# 修改 .env 文件
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 配置代理（可选）

如果你需要通过代理访问 TradingView：

```env
# .env 文件
PROXY_URL=http://127.0.0.1:7890
```

### 调整监控参数

编辑 `backend_api_python/app/routes/hama_market.py`：

```python
# 修改默认监控币种列表
DEFAULT_SYMBOLS = [
    'BTCUSDT',
    'ETHUSDT',
    'YOURLCOINUSDT',  # 添加你的币种
]

# 修改监控间隔（秒）
DEFAULT_MONITOR_INTERVAL = 300  # 5分钟
```

## 📚 更多资源

- 📖 [完整技术文档](./CLAUDE.md)
- 🔧 [技术栈清单](./TECH_STACK.md)
- 🤖 [Brave 监控逻辑详解](./BRAVE_MONITOR_LOGIC.md)
- 🐛 [问题反馈](https://github.com/alexbibihere/QuantDinger/issues)

## 🆘 获取帮助

如果遇到问题：

1. 查看 [常见问题](#-常见问题)
2. 搜索 [GitHub Issues](https://github.com/alexbibihere/QuantDinger/issues)
3. 提交新的 Issue：描述问题、提供错误日志

---

祝你使用愉快！🎉
