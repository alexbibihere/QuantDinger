# HAMA 监控服务完整启动指南

## 配置信息

根据 `backend_api_python/file/tradingview.txt` 配置：

**TradingView 账号：**
- 账号：alexbibiherr
- 密码：Iam5323..
- Cookie：已配置（2026-01-20 更新）

**Brave 浏览器：**
- 路径：`C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`
- 模式：无头模式（Headless）

**QQ 邮件配置：**
- 邮箱：32319731984@qq.com
- 授权码：agwnmwaexbytbicf

## 工作流程

```
启动 Worker
    ↓
Brave 监控服务
    ↓
启动 Brave 无头浏览器 ✅
    ↓
使用 Cookie 自动登录 TradingView ✅
    ↓
访问 TradingView 图表页面 ✅
    ↓
截图右下角 HAMA 指标区域 ✅
    ↓
PaddleOCR 识别指标数据 ✅
    ↓
保存结果到 SQLite 数据库 ✅
    ↓
QQ 邮件发送通知（可选）✅
    ↓
前端 API 调用查询数据库 ✅
```

## 启动方式

### 方式 1：使用批处理脚本（推荐）

```bash
bat\启动HAMA监控.bat
```

### 方式 2：使用 Python 脚本

```bash
python start_hama_monitor_simple.py
```

### 方式 3：一键启动所有服务

```bash
python start_all_services.py
```

这会启动：
1. 后端 API 服务（端口 5000）
2. HAMA Brave 监控服务（使用 Brave 无头浏览器）
3. 邮件通知服务（QQ 邮箱）
4. 前端 Vue 应用（端口 8000）

## 监控配置

**监控币种：**
- BTCUSDT
- ETHUSDT
- BNBUSDT
- SOLUSDT
- XRPUSDT
- ADAUSDT
- DOGEUSDT

**监控间隔：** 10分钟（600秒）

**浏览器：** Brave 无头模式

**OCR 引擎：** PaddleOCR v3.3.2

**数据存储：** SQLite 数据库（`backend_api_python/data/quantdinger.db`）

**截图保存：** `backend_api_python/app/screenshots/`

## 测试监控

### 快速测试单个币种

```bash
python test_hama_quick.py
```

这会立即执行一次 BTCUSDT 的监控并显示结果。

### 调试 OCR 识别

```bash
python debug_ocr.py
```

这会显示 OCR 识别的详细文本内容。

## 查看日志

**监控日志：**
```bash
tail -f logs/hama_monitor_brave.log
```

**后端日志：**
```bash
tail -f logs/backend.log
```

**前端日志：**
```bash
tail -f logs/frontend.log
```

## 查看数据库

```bash
cd backend_api_python
python -c "
import sqlite3
conn = sqlite3.connect('data/quantdinger.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM hama_monitor_cache ORDER BY rowid DESC LIMIT 10')
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
"
```

## 访问应用

**前端首页：** http://localhost:8000

**HAMA Market：** http://localhost:8000/#/hama-market

**后端 API：** http://localhost:5000/api/health

## 停止服务

按 `Ctrl+C` 停止监控服务。

如果需要停止所有服务：

```bash
taskkill //F //IM python.exe
taskkill //F //IM node.exe
```

## 文件组织

**Markdown 文档：** 放在 `docs/` 文件夹

**批处理脚本：** 放在 `bat/` 文件夹

**日志文件：** 放在 `logs/` 文件夹

**截图文件：** 放在 `backend_api_python/app/screenshots/` 文件夹

## 故障排除

### Brave 浏览器未找到

如果日志显示"未找到 Brave 浏览器"，请确认 Brave 安装路径：
- 默认路径：`C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`

### OCR 识别失败

1. 检查截图是否正确生成
2. 查看日志中的 OCR 文本输出
3. 尝试调整截图区域参数

### Cookie 过期

如果无法访问 TradingView，更新 `backend_api_python/tradingview_cookies.json` 中的 Cookie。

获取 Cookie 方式：
1. 浏览器登录 TradingView
2. F12 打开开发者工具
3. Network → 复制 Cookie 值
4. 更新到配置文件

## 邮件通知

邮件通知会在以下情况自动发送：
- HAMA 趋势发生变化（上涨 ↔ 下跌）
- 首次识别到新的趋势

配置位置：
- 文件：`backend_api_python/.env`
- 参数：
  - `EMAIL_ENABLED=true`
  - `EMAIL_SMTP_HOST=smtp.qq.com`
  - `EMAIL_SMTP_PORT=587`
  - `EMAIL_FROM=32319731984@qq.com`
  - `EMAIL_PASSWORD=agwnmwaexbytbicf`

## 性能优化

**监控间隔调整：**
修改 `start_hama_monitor_simple.py` 中的 `interval` 参数（默认 600 秒 = 10 分钟）

**并发监控：**
支持同时监控多个币种，默认 7 个。

**截图缓存：**
OCR 识别结果会缓存 15 分钟（TTL=900），避免重复识别。

## 状态检查

```bash
# 检查服务端口
netstat -ano | findstr ":5000 :8000"

# 检查进程
tasklist | findstr "python.exe node.exe"

# 检查最新截图
ls -lth backend_api_python/app/screenshots/*.png | head -5
```
