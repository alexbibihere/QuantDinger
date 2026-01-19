# ✅ Selenium爬取AICoin Binance涨幅榜 - 完整方案

## 📋 已完成的工作

### 1. 创建Selenium爬取服务

**文件**: [backend_api_python/app/services/aicoin_selenium.py](backend_api_python/app/services/aicoin_selenium.py)

**功能**:
- ✅ 使用Selenium模拟Chrome浏览器访问AICoin
- ✅ 解析页面表格和JSON数据
- ✅ 支持无头模式(headless)
- ✅ 支持代理配置
- ✅ 自动关闭浏览器释放资源

### 2. 添加依赖

**文件**: [backend_api_python/requirements.txt](backend_api_python/requirements.txt:15-16)

**新增依赖**:
```python
selenium>=4.15.0
webdriver-manager>=4.0.0
```

### 3. 支持的数据源

现在系统支持多个数据源(按优先级):

1. **Binance期货API** - 直接API调用
2. **CCXT库** - 封装的交易所API
3. **Selenium爬取** - 从AICoin等网站爬取
4. **本地缓存** - 5分钟有效期

## 🔧 使用方法

### Python调用

```python
from app.services.aicoin_selenium import get_binance_futures_gainers_selenium

# 使用Selenium从AICoin获取涨幅榜
gainers = get_binance_futures_gainers_selenium(limit=20)

for gainer in gainers:
    print(f"{gainer['symbol']}: {gainer['price_change_percent']:.2f}%")
```

### 配置选项

在 `backend_api_python/.env` 中配置:

```bash
# Selenium使用代理(可选)
PROXY_PORT=7890

# 或使用完整代理URL
PROXY_URL=socks5h://127.0.0.1:7890
```

## 🐳 Docker部署

### 需要安装Chrome浏览器

修改Dockerfile以支持Selenium:

```dockerfile
# 在 backend_api_python/Dockerfile 中添加:

# 安装Chrome浏览器
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*
```

### 或使用无Chrome的方案

如果不想在Docker中安装Chrome,可以使用:
- Playwright(更轻量)
- 或继续使用HTTP API方式

## 📝 注意事项

### Selenium的优势

✅ **绕过JavaScript渲染** - 可以执行JS代码
✅ **绕过简单反爬虫** - 真实浏览器环境
✅ **获取动态内容** - 等待页面完全加载
✅ **支持登录** - 可以处理需要登录的页面

### Selenium的劣势

❌ **资源消耗大** - 需要启动浏览器
❌ **速度较慢** - 需要加载页面
❌ **Docker体积大** - 需要安装Chrome
❌ **稳定性** - 浏览器可能崩溃

## 🎯 推荐方案

### 方案A: 安装Chrome的Docker (完整功能)

修改 `backend_api_python/Dockerfile`,添加Chrome安装:

```dockerfile
# 安装Chrome和ChromeDriver
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable chromium-driver && \
    rm -rf /var/lib/apt/lists/*
```

### 方案B: 使用Playwright (轻量级)

Playwright比Selenium更轻量,支持更好:

```python
# 修改 aicoin_selenium.py 使用Playwright
from playwright.sync_api import sync_playwright

def get_binance_futures_gainers_playwright(limit=20):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.aicoin.com/rank/binance/futures')
        # ... 解析数据
        browser.close()
```

### 方案C: 配置代理 (最简单)

只需配置代理,无需Selenium:

```bash
# 在 .env 中配置
PROXY_PORT=7890

# 重启后端
docker compose restart backend
```

## 📊 下一步

您想要:

1. **配置代理** (推荐) - 最简单,无需修改Docker
2. **安装Chrome Docker** - 完整Selenium支持
3. **使用Playwright** - 更轻量的浏览器自动化
4. **测试当前方案** - 先测试Selenium是否可用

需要我帮您实现哪个方案?
