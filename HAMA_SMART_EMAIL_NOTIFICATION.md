# HAMA 智能邮件通知系统更新说明

## 更新内容

### 1. 数据库表结构更新

在 `hama_monitor_cache` 表中添加了邮件发送状态字段：

```sql
ALTER TABLE hama_monitor_cache
ADD COLUMN email_sent TINYINT(1) DEFAULT 0,
ADD COLUMN email_sent_at TIMESTAMP NULL,
ADD INDEX idx_email_sent (email_sent);
```

**字段说明**：
- `email_sent`: 是否已发送邮件（0=未发送，1=已发送）
- `email_sent_at`: 邮件发送时间

### 2. 新增方法

#### `get_email_status(symbol: str)`
获取币种的邮件发送状态

**返回**：
```python
{
    'email_sent': bool,      # 是否已发送
    'email_sent_at': datetime  # 发送时间
}
```

#### `update_email_status(symbol: str)`
更新币种的邮件发送状态为"已发送"

#### `reset_email_status(symbol: str)`
重置币种的邮件发送状态（用于状态变为盘整时）

### 3. 邮件发送逻辑优化

#### 原逻辑问题
- 每次检测到趋势变化都会发送邮件
- 没有记录是否已发送过
- 容易造成邮件轰炸

#### 新逻辑（智能邮件通知）

**发送规则**：

1. **首次检测到明确趋势**
   - 第一次检测到 green/red 趋势时发送邮件
   - 标记 `email_sent = 1`

2. **已发送邮件后的处理**
   - 如果 `email_sent = 1`，则不再发送邮件
   - **除非**检测到趋势反转（金叉/死叉）

3. **盘整状态处理**
   - 当HAMA状态变为盘整（neutral/gray）时
   - 自动重置 `email_sent = 0`
   - 为下次趋势形成做好准备

4. **趋势反转（重要信号）**
   - 从上涨变为下跌（死叉）
   - 从下跌变为上涨（金叉）
   - **即使已发送过邮件，也会再次发送提醒**

**流程图**：

```
监控到新数据
    ↓
判断状态
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│  明确趋势        │  盘整状态        │  趋势反转        │
│  (green/red)    │  (neutral/gray)  │  (up↔down)       │
└────────┬────────┴────────┬────────┴────────┬────────┘
         │                 │                 │
         ↓                 ↓                 ↓
    是否已发送?      重置邮件状态      发送邮件
         │             email_sent=0   (重要信号)
         ↓
    否 → 发送邮件
    是 → 检查是否反转
         ↓
    是反转 → 发送邮件
    否反转 → 跳过发送
```

## 触发条件总结

| 场景 | 是否发送邮件 | 说明 |
|------|------------|------|
| 首次检测到 green/red 趋势 | ✅ 发送 | 第一次提醒 |
| 继续保持 same 趋势 | ❌ 不发送 | 避免重复 |
| 状态变为盘整 (neutral) | ❌ 不发送 | 重置状态为下次准备 |
| 从盘整变为明确趋势 | ✅ 发送 | 新趋势形成 |
| 趋势反转 (up→down 或 down→up) | ✅ 发送 | 重要信号，必须提醒 |
| 颜色变化 (green↔red) | ✅ 发送 | 交叉信号 |

## 使用示例

### 启动监控

```bash
cd backend_api_python
python auto_hama_monitor_mysql.py
```

### 查看邮件状态

```sql
SELECT
    symbol,
    hama_trend,
    hama_color,
    email_sent,
    email_sent_at,
    monitored_at
FROM hama_monitor_cache;
```

**示例输出**：

| symbol | hama_trend | hama_color | email_sent | email_sent_at |
|--------|-----------|------------|------------|---------------|
| BTCUSDT | up | green | 1 | 2026-01-18 12:00:00 |
| ETHUSDT | down | red | 1 | 2026-01-18 12:05:00 |
| BNBUSDT | neutral | gray | 0 | NULL |

### 手动重置邮件状态

如果需要重新发送某个币种的邮件：

```python
from app.services.hama_brave_monitor_mysql import get_brave_monitor
from app.utils.db import get_db_connection

db = get_db_connection()
monitor = get_brave_monitor(db)

# 重置 BTCUSDT 的邮件状态
monitor.reset_email_status('BTCUSDT')
```

## 日志示例

```
[INFO] BTCUSDT 首次检测到趋势: green (up)
[INFO] 📧 BTCUSDT 检测到趋势变化: 首次检测到趋势: green (up)，准备发送邮件...
[INFO] ✅ BTCUSDT 邮件通知发送成功
[DEBUG] BTCUSDT 邮件状态已更新为已发送

[INFO] BTCUSDT 状态变为盘整，邮件状态已重置

[INFO] BTCUSDT 从盘整变为趋势: red (down)
[INFO] 📧 BTCUSDT 检测到趋势变化: 从盘整变为趋势: red (down)，准备发送邮件...
[INFO] ✅ BTCUSDT 邮件通知发送成功

[INFO] BTCUSDT 已发送过邮件，跳过发送 (首次检测到趋势: red (down))

[INFO] BTCUSDT 趋势反转: down → up
[INFO] 📧 BTCUSDT 检测到趋势变化: 趋势反转: down → up，准备发送邮件...
[INFO] ✅ BTCUSDT 邮件通知发送成功（金叉信号）
```

## 优势

1. **避免邮件轰炸**：同一趋势只发送一次邮件
2. **重要信号不遗漏**：趋势反转时必定发送邮件
3. **自动重置机制**：盘整后自动准备下次发送
4. **状态可追踪**：数据库记录每个币种的邮件发送状态
5. **智能判断**：根据不同场景决定是否发送

## 配置要求

无需额外配置，系统会自动：
- 检测数据库表结构
- 自动添加新字段（如果不存在）
- 按新逻辑运行

## 总结

新的邮件通知系统更加智能和高效：
- ✅ 减少不必要的邮件发送
- ✅ 确保重要信号及时通知
- ✅ 自动管理邮件发送状态
- ✅ 支持趋势反转重复提醒

现在你可以安心启动监控，不用担心收到过多重复邮件了！
