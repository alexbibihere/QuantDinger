# HAMA 趋势邮件通知使用指南

## 功能概述

HAMA 趋势邮件通知功能会在监控到 HAMA 指标形成趋势时自动发送邮件提醒，支持以下场景：

- **颜色变化**: 从红色变为绿色（金叉），或从绿色变为红色（死叉）
- **首次检测**: 首次检测到明确的上涨或下跌趋势
- **趋势变化**: 趋势方向从上涨变为下跌，或从下跌变为上涨

## 快速开始

### 1. 配置 QQ 邮箱

#### 步骤 1: 开启 SMTP 服务
1. 登录 QQ 邮箱 (https://mail.qq.com)
2. 点击「设置」→「账户」
3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」
4. 开启「IMAP/SMTP服务」或「POP3/SMTP服务」
5. 按照提示发送短信验证

#### 步骤 2: 获取授权码
- 开启服务后，系统会显示一个「授权码」
- 这个授权码就是 `SMTP_PASSWORD`
- **重要**: 不是你的 QQ 密码，是授权码！

#### 步骤 3: 配置环境变量

编辑 `backend_api_python/.env` 文件，添加以下配置：

```bash
# SMTP 邮件服务器配置（QQ 邮箱）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your@qq.com
SMTP_PASSWORD=your_qq_authorization_code
SMTP_FROM=your@qq.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# HAMA 邮件通知收件人（多个收件人用逗号分隔）
HAMA_EMAIL_RECIPIENTS=your@qq.com,friend@gmail.com

# HAMA 邮件通知冷却时间（秒），避免频繁发送
# 默认 3600 秒 = 1 小时
HAMA_EMAIL_COOLDOWN=3600
```

### 2. 测试邮件发送

```bash
cd backend_api_python
python test_hama_email.py --test
```

测试脚本会发送 4 封测试邮件：
1. 上涨趋势邮件（BTCUSDT 金叉）
2. 下跌趋势邮件（ETHUSDT 死叉）
3. 冷却机制测试
4. 批量监控完成报告

### 3. 启动 HAMA 监控

#### 方式 1: 使用自动监控脚本

```bash
cd backend_api_python
python auto_hama_monitor_mysql.py
```

监控脚本会自动：
- 每 10 分钟监控一次配置的币种
- 检测 HAMA 趋势变化
- 发送邮件通知（如果在配置的收件人列表中）

#### 方式 2: 手动触发监控

```python
from app.services.hama_brave_monitor_mysql import get_brave_monitor
from app.utils.db import get_db_connection

# 获取数据库连接
db = get_db_connection()

# 获取监控器实例（默认启用邮件通知）
monitor = get_brave_monitor(db_client=db, enable_email=True)

# 监控单个币种
hama_data = monitor.monitor_symbol("BTCUSDT")

# 批量监控
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
results = monitor.monitor_batch(symbols)
```

## 邮件通知示例

### 上涨趋势邮件

```
主题: 🎯 HAMA趋势提醒 | BTCUSDT | 🟢 上涨趋势

内容:
币种: BTCUSDT
时间: 2026-01-18 12:00:00
趋势: 🟢 上涨趋势
颜色: 绿色（看涨）
HAMA 值: 96750.500000
当前价格: $96850.25
信号: 🟢 金叉信号 (HAMA Close 上穿 MA)
```

### 下跌趋势邮件

```
主题: 🎯 HAMA趋势提醒 | ETHUSDT | 🔴 下跌趋势

内容:
币种: ETHUSDT
时间: 2026-01-18 12:05:00
趋势: 🔴 下跌趋势
颜色: 红色（看跌）
HAMA 值: 3250.750000
当前价格: $3245.50
信号: 🔴 死叉信号 (HAMA Close 下穿 MA)
```

## 配置说明

### SMTP 邮件服务器配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| SMTP_HOST | SMTP 服务器地址 | smtp.qq.com |
| SMTP_PORT | SMTP 端口 | 587 (TLS) 或 465 (SSL) |
| SMTP_USER | 邮箱用户名 | your@qq.com |
| SMTP_PASSWORD | 邮箱密码或授权码 | your_qq_authorization_code |
| SMTP_FROM | 发件人地址 | your@qq.com |
| SMTP_USE_TLS | 使用 TLS 加密 | true |
| SMTP_USE_SSL | 使用 SSL 加密 | false |

### HAMA 邮件通知配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| HAMA_EMAIL_RECIPIENTS | 收件人邮箱（逗号分隔） | 无 |
| HAMA_EMAIL_COOLDOWN | 冷却时间（秒） | 3600 (1小时) |

### 常用邮箱配置

#### QQ 邮箱
```bash
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

#### Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```
注意: Gmail 需要开启「两步验证」并生成「应用专用密码」

#### 163 邮箱
```bash
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USE_SSL=true
```

#### Outlook
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

## 冷却机制

为了避免频繁发送邮件，系统实现了冷却机制：

- 同一币种在冷却时间内（默认 1 小时）只会发送一次邮件
- 冷却时间可通过 `HAMA_EMAIL_COOLDOWN` 配置
- 冷却时间是针对每个币种独立的，不同币种互不影响

### 调整冷却时间

```bash
# 30 分钟冷却
HAMA_EMAIL_COOLDOWN=1800

# 2 小时冷却
HAMA_EMAIL_COOLDOWN=7200

# 禁用冷却（不推荐，可能造成邮件轰炸）
HAMA_EMAIL_COOLDOWN=0
```

## 禁用邮件通知

如果不需要邮件通知，可以：

### 方法 1: 不配置收件人
```bash
# .env 文件中留空或不设置
HAMA_EMAIL_RECIPIENTS=
```

### 方法 2: 代码中禁用
```python
monitor = get_brave_monitor(db_client=db, enable_email=False)
```

## 故障排除

### 问题 1: 收不到邮件

**检查清单:**
1. ✅ 确认 SMTP 配置正确
2. ✅ 确认 `HAMA_EMAIL_RECIPIENTS` 已设置
3. ✅ 检查邮箱垃圾箱
4. ✅ 查看后端日志: `backend_api_python/logs/app.log`

### 问题 2: SMTP 认证失败

**QQ 邮箱:**
- 确认使用的是「授权码」而不是 QQ 密码
- 重新生成授权码

**Gmail:**
- 开启「两步验证」
- 生成「应用专用密码」

### 问题 3: 连接超时

**检查:**
1. 网络连接是否正常
2. SMTP 端口是否被防火墙阻止
3. 尝试使用代理（如果有的话）

## 日志查看

邮件通知相关的日志：

```bash
# 查看最新日志
tail -f backend_api_python/logs/app.log

# 搜索邮件相关日志
grep "邮件" backend_api_python/logs/app.log
grep "email" backend_api_python/logs/app.log
```

日志示例：
```
[INFO] 邮件通知器初始化完成 (冷却时间: 3600秒)
[INFO] 📧 BTCUSDT 检测到趋势变化: 颜色变化: red → green，准备发送邮件...
[INFO] ✅ BTCUSDT 邮件通知发送成功
```

## API 路由

如果需要在前端查看截图，需要确保以下路由可用：

```
GET /api/screenshots/:filename
```

该路由在 `app/routes/static_files.py` 中实现。

## 最佳实践

1. **合理设置冷却时间**: 建议至少 30 分钟，避免邮件轰炸
2. **使用多个收件人**: 可以设置团队邮箱，多人接收提醒
3. **定期检查授权码**: 部分邮箱的授权码会过期
4. **监控日志**: 定期查看日志，确保邮件发送正常
5. **测试配置**: 使用测试脚本验证配置后再启用监控

## 技术实现

### 核心文件

- [`app/services/hama_email_notifier.py`](backend_api_python/app/services/hama_email_notifier.py) - 邮件通知服务
- [`app/services/hama_brave_monitor_mysql.py`](backend_api_python/app/services/hama_brave_monitor_mysql.py) - HAMA 监控器（已集成邮件通知）
- [`test_hama_email.py`](backend_api_python/test_hama_email.py) - 测试脚本

### 趋势检测逻辑

```python
# 条件 1: 颜色变化（从红变绿，或从绿变红）
if last_color != current_color and current_color in ['green', 'red']:
    should_notify = True

# 条件 2: 首次检测到明确的趋势
if not last_color and current_color in ['green', 'red']:
    should_notify = True

# 条件 3: 趋势方向变化
if last_trend != current_trend and current_trend in ['up', 'down']:
    should_notify = True
```

### 邮件模板

邮件使用 HTML 模板，包含：
- 头部：币种、趋势标识
- 表格：HAMA 状态、价格、信号
- 截图链接：点击查看 TradingView 截图
- 底部：时间戳、系统信息

## 总结

HAMA 趋势邮件通知功能：
- ✅ 自动检测趋势变化
- ✅ 及时发送邮件提醒
- ✅ 冷却机制避免频繁发送
- ✅ 支持多个收件人
- ✅ 美观的 HTML 邮件模板
- ✅ 完整的日志记录

祝您交易顺利！ 📈
