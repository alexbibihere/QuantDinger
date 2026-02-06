# HAMA 数据健康检查与 LongLogic 自动重载

## 功能概述

当 HAMA 监控列表检测不到价格和状态时，系统会自动重新读取 `longLogic.txt` 配置文件并应用更新。

---

## 核心功能

### 1. HAMA 数据健康检查

系统会定期检查 HAMA 监控列表中的数据完整性：

- **检查内容**：
  - 价格是否有效（非空、非 'None'）
  - HAMA 状态是否有效（green/red/gray/up/down/neutral）

- **检查机制**：
  - 默认每 60 秒检查一次
  - 连续失败 3 次后触发重载逻辑

### 2. LongLogic 自动重载

当检测到 HAMA 数据异常时：

1. 自动重新读取 `backend_api_python/file/longLogic.txt`
2. 解析配置文件内容
3. 应用更新后的配置
4. 记录配置变更

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HAMA_HEALTH_CHECK_ENABLED` | `true` | 是否启用健康检查 |
| `HAMA_HEALTH_CHECK_INTERVAL` | `60` | 检查间隔（秒） |
| `HAMA_HEALTH_CHECK_THRESHOLD` | `3` | 失败阈值（连续N次失败后重载） |

### longLogic.txt 配置格式

```
https://cn.tradingview.com/chart/U1FY2qxO/

cookie: 你的cookie字符串

账号 ：alexbibiherr
密码：Iam5323..

前端端口永远使用8000,如果有端口占用，就停止服务再启动

Brave浏览器路径：C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe

hama指标访问流程：
启动worker  Brave监控 启动brave无头浏览器 使用账号密码自动登录 访问tradingview页面 截图右下角的hama指标
然后进行OCR识别，保存结果到数据库，前端调用接口 查询数据库展示


QQ邮件
邮箱：32319731984@qq.com
授权码： agwnmwaexbytbicf
收件人：329731984@qq.com,845848958@qq.com

所有新创建的都按规则放入分别的文件夹，md放docs文件夹，bat放bat文件夹


如果hama列表检测不到价格和状态，就重新读取longLogic.txt，把这个设为轮训任务
```

---

## 日志说明

### 正常日志

```
✅ HAMA 数据健康检查通过
健康检查完成: 1 个币种, 健康: True, 失败: 0
```

### 异常日志

```
⚠️ ETHUSDT 数据异常 (价格=None, 状态=gray), 失败次数: 1/3
⚠️ ETHUSDT 数据异常 (价格=None, 状态=gray), 失败次数: 2/3
❌ ETHUSDT 连续失败 3 次，触发重启逻辑
```

### 重载日志

```
🔄 触发 LongLogic 配置重载 (原因: ETHUSDT 数据异常)
✅ 成功读取 longLogic.txt (最后修改: 2026-02-07 02:00:00)
⚠️ 配置已发生变化: 1 项
  - tradingview_url: https://cn.tradingview.com/chart/NEW/ -> https://cn.tradingview.com/chart/U1FY2qxO/
📝 应用 longLogic 配置...
  TradingView URL: https://cn.tradingview.com/chart/U1FY2qxO/
  Brave 路径: C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
  邮件发送者: 32319731984@qq.com
  邮件收件人: 2 个
✅ 配置应用完成
```

---

## 使用方法

### 方法1: 使用启动脚本（推荐）

直接运行启动脚本：

```bash
# Windows
cd backend_api_python
cd bat
restart_backend_with_health_check.bat
```

脚本会自动：
1. 停止现有的后端服务
2. 清理临时文件
3. 启动后端服务并启用健康检查

### 方法2: 手动启动

```bash
cd backend_api_python

# 设置环境变量
set HAMA_HEALTH_CHECK_ENABLED=true
set HAMA_HEALTH_CHECK_INTERVAL=60
set HAMA_HEALTH_CHECK_THRESHOLD=3

# 启动后端
python run.py
```

---

## 核心代码文件

### 1. 健康检查服务

**文件**: [app/services/hama_health_checker.py](../backend_api_python/app/services/hama_health_checker.py)

**主要类**: `HAMAHealthChecker`

**核心方法**:
- `check_hama_data(watchlist)` - 检查数据完整性
- `process_check_result(check_result)` - 处理检查结果
- `start(get_watchlist_func)` - 启动健康检查线程

### 2. LongLogic 读取服务

**文件**: [app/services/long_logic_reader.py](../backend_api_python/app/services/long_logic_reader.py)

**主要类**: `LongLogicReader`

**核心方法**:
- `read_config()` - 读取配置文件
- `_parse_config(content)` - 解析配置内容
- `reload_config()` - 重新加载配置
- `apply_config()` - 应用配置

### 3. 应用工厂集成

**文件**: [app/__init__.py](../backend_api_python/app/__init__.py)

**新增全局单例**:
- `_hama_health_checker` - 健康检查器
- `_long_logic_reader` - LongLogic 读取器

**新增函数**:
- `init_hama_health_checker()` - 初始化健康检查器
- `init_long_logic_reader()` - 初始化 LongLogic 读取器
- `start_hama_health_checker()` - 启动健康检查

---

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    1. 系统启动                               │
│  └─> 初始化健康检查器 + LongLogic 读取器                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    2. 健康检查轮询                            │
│  └─> 每 60 秒检查一次 HAMA 监控列表                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    3. 数据验证                               │
│  ├─> 价格有效？                                              │
│  ├─> 状态有效？                                              │
│  └─> 综合判断：通过 / 失败                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    ↓               ↓
                ✅ 通过           ❌ 失败
                    ↓               ↓
            重置失败计数    累计失败次数 +1
                                    ↓
                            达到阈值（3次）？
                                    ↓
                            ┌───────┴───────┐
                            ↓               ↓
                        ❌ 否            ✅ 是
                            ↓               ↓
                        继续监控      🔄 触发重载
                                            ↓
                                重新读取 longLogic.txt
                                            ↓
                                        应用新配置
```

---

## 配置项详解

### longLogic.txt 支持的配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `tradingview_url` | TradingView 图表 URL | `https://cn.tradingview.com/chart/U1FY2qxO/` |
| `cookie` | TradingView Cookie 字符串 | `sessionid=xxx; sessionid_sign=yyy;` |
| `账号` | TradingView 账号 | `alexbibiherr` |
| `密码` | TradingView 密码 | `Iam5323..` |
| `前端端口` | 前端服务端口 | `8000` |
| `Brave浏览器路径` | Brave 浏览器完整路径 | `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe` |
| `hama指标访问流程` | HAMA 工作流程描述 | 多行文本 |
| `QQ邮件` | 邮件配置块 | 发件人、授权码、收件人 |
| `新创建` | 文件组织规则 | 描述性文本 |
| `hama列表检测不到` | 健康检查规则 | 描述性文本 |

---

## 故障排查

### 1. 健康检查未启动

**检查日志**:
```
HAMA 健康检查已禁用 (HAMA_HEALTH_CHECK_ENABLED=false)
```

**解决方案**:
```bash
# 确保环境变量设置正确
set HAMA_HEALTH_CHECK_ENABLED=true
```

### 2. LongLogic.txt 文件未找到

**检查日志**:
```
配置文件不存在: backend_api_python/file/longLogic.txt
```

**解决方案**:
- 确认文件存在于正确位置
- 检查文件路径是否正确

### 3. 配置重载后未生效

**检查日志**:
```
⚠️ 配置未发生变化
```

**原因**:
- 配置文件内容未更改
- 系统已使用最新配置

**解决方案**:
- 修改 `longLogic.txt` 中的配置项
- 保存文件后等待下次健康检查触发重载

---

## API 接口

### 获取健康检查状态

```http
GET /api/health-check/status
```

**响应示例**:
```json
{
  "is_running": true,
  "check_interval": 60,
  "failure_threshold": 3,
  "last_check_time": "2026-02-07T02:00:00",
  "failure_count": {
    "ETHUSDT": 0
  }
}
```

### 手动触发健康检查

```http
POST /api/health-check/check-now
```

### 手动重载 LongLogic

```http
POST /api/longlogic/reload
```

**响应示例**:
```json
{
  "success": true,
  "message": "配置已重新加载",
  "changes": ["tradingview_url: ... -> ..."]
}
```

---

## 最佳实践

### 1. 调整检查频率

根据实际需求调整检查间隔：

```bash
# 高频检查（适合测试）
set HAMA_HEALTH_CHECK_INTERVAL=30

# 低频检查（减少资源消耗）
set HAMA_HEALTH_CHECK_INTERVAL=120
```

### 2. 调整失败阈值

根据网络稳定性调整阈值：

```bash
# 不稳定网络环境
set HAMA_HEALTH_CHECK_THRESHOLD=5

# 稳定网络环境
set HAMA_HEALTH_CHECK_THRESHOLD=2
```

### 3. 监控日志

定期检查日志文件，确保健康检查正常运行：

```bash
# 查看最近的健康检查日志
tail -f logs/app.log | grep "健康检查"
```

---

## 总结

通过 HAMA 数据健康检查与 LongLogic 自动重载功能，系统可以：

1. ✅ 自动检测 HAMA 数据异常
2. ✅ 自动重新加载配置文件
3. ✅ 自动应用最新配置
4. ✅ 无需手动干预

这大大提高了系统的稳定性和可维护性！
