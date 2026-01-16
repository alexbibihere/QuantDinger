# TradingView Cookies 配置文件

## 说明

此文件用于存储 TradingView 的登录 Cookies，以便系统可以通过 Selenium 模拟浏览器访问 TradingView 并读取 HAMA 指标数据。

## 如何获取 Cookies

### 步骤：

1. **登录 TradingView**
   - 在浏览器中打开 https://cn.tradingview.com/
   - 使用您的账号登录

2. **打开开发者工具**
   - Windows/Linux: 按 `F12` 或 `Ctrl + Shift + I`
   - Mac: 按 `Cmd + Option + I`

3. **找到 Cookies**
   - 切换到 `Application` (应用) 或 `Storage` (存储) 标签
   - 在左侧找到 `Cookies` -> `https://cn.tradingview.com`

4. **复制重要的 Cookies**
   复制以下 cookies 的值：
   - `sessionid`
   - `sessionid_sign`
   - `uid`

5. **更新配置文件**
   将复制的值更新到下面的 `cookies.json` 文件中

## Cookies 格式示例

创建文件 `backend_api_python/config/tradingview_cookies.json`:

```json
{
  "sessionid": "您的sessionid值",
  "sessionid_sign": "您的sessionid_sign值",
  "uid": "您的uid值"
}
```

## 环境变量配置

在 `backend_api_python/.env` 文件中添加：

```bash
# TradingView Cookies 配置
TRADINGVIEW_SESSIONID=您的sessionid值
TRADINGVIEW_SESSIONID_SIGN=您的sessionid_sign值
TRADINGVIEW_UID=您的uid值
```

## API 使用示例

### 1. 从 TradingView 获取 HAMA 指标

```bash
POST /api/tradingview-hama/get-hama
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "interval": "15",
  "headless": true,
  "cookies": {
    "sessionid": "从配置文件读取",
    "sessionid_sign": "从配置文件读取",
    "uid": "从配置文件读取"
  }
}
```

### 2. 批量获取多个币种的 HAMA 指标

```bash
POST /api/tradingview-hama/batch-get-hama
Content-Type: application/json

{
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "interval": "15",
  "headless": true,
  "cookies": {
    "sessionid": "...",
    "sessionid_sign": "...",
    "uid": "..."
  }
}
```

### 3. 从 TradingView 获取价格

```bash
POST /api/tradingview-hama/get-price
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "headless": true,
  "cookies": {
    "sessionid": "...",
    "sessionid_sign": "...",
    "uid": "..."
  }
}
```

## 注意事项

1. **Cookie 过期**
   - TradingView 的 cookies 有过期时间
   - 如果获取失败，请重新获取 cookies 并更新配置

2. **安全性**
   - 不要将 `config/tradingview_cookies.json` 提交到版本控制
   - 将其添加到 `.gitignore` 文件中
   - 使用环境变量存储敏感信息

3. **无头模式**
   - `headless: true` - 不显示浏览器窗口（推荐用于生产环境）
   - `headless: false` - 显示浏览器窗口（推荐用于调试）

4. **性能考虑**
   - Selenium 需要启动浏览器，首次请求较慢（约 5-10 秒）
   - 批量请求建议分批处理，避免同时打开过多浏览器

## 前端集成示例

在 Vue 组件中调用：

```javascript
import { axios } from '@/utils/request'

async function getHamaFromTradingView(symbol) {
  try {
    const response = await axios.post('/api/tradingview-hama/get-hama', {
      symbol: symbol,
      interval: '15',
      headless: true,
      cookies: {
        sessionid: this.$cookies.get('tv_sessionid'),
        sessionid_sign: this.$cookies.get('tv_sessionid_sign'),
        uid: this.$cookies.get('tv_uid')
      }
    })

    if (response.data.success) {
      return response.data.data
    }
  } catch (error) {
    console.error('获取HAMA指标失败:', error)
  }
}
```

## 故障排除

### 问题：获取失败，提示未登录

**解决方案：**
1. 检查 cookies 是否正确
2. 尝试在浏览器中重新登录 TradingView
3. 重新获取并更新 cookies

### 问题：浏览器启动失败

**解决方案：**
1. 检查 Docker 容器中是否安装了 Chromium
2. 查看后端日志：`docker-compose logs backend`
3. 确认 ChromeDriver 版本匹配

### 问题：加载超时

**解决方案：**
1. 增加 `wait_for_load` 参数（默认 10 秒）
2. 检查网络连接
3. 使用非无头模式 (`headless: false`) 调试

## 相关文件

- `backend_api_python/app/services/tradingview_hama_selenium.py` - Selenium 服务实现
- `backend_api_python/app/routes/tradingview_hama.py` - API 路由定义
- `backend_api_python/config/tradingview_cookies.json` - Cookies 配置文件（需创建）
- `backend_api_python/.env` - 环境变量配置
