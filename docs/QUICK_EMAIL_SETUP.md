# 快速配置 QQ 邮件通知

## 步骤 1: 获取 QQ 邮箱授权码

1. 访问 https://mail.qq.com
2. 登录你的账号: 329731984@qq.com
3. 点击「设置」→「账户」
4. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」
5. 点击「开启」IMAP/SMTP服务
6. 按照提示发送短信验证
7. 验证成功后，会显示一个「授权码」（16位字符）
8. **复制这个授权码**（不是QQ密码！）

## 步骤 2: 编辑 .env 文件

打开 `backend_api_python/.env` 文件，找到以下部分：

```bash
# Email / SMTP (required if you enable email channel)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

修改为：

```bash
# Email / SMTP (required if you enable email channel)
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=329731984@qq.com
SMTP_PASSWORD=你在步骤1获得的授权码
SMTP_FROM=329731984@qq.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

## 步骤 3: 添加收件人配置

在同一 `.env` 文件中，找到或添加：

```bash
# HAMA Email Notification (optional)
# HAMA 邮件通知收件人（多个收件人用逗号分隔）
# 示例: user1@qq.com,user2@gmail.com
HAMA_EMAIL_RECIPIENTS=329731984@qq.com

# HAMA 邮件通知冷却时间（秒），避免频繁发送
# 默认 3600 秒 = 1小时，同一币种在冷却期内只发送一次邮件
HAMA_EMAIL_COOLDOWN=3600
```

## 步骤 4: 保存文件并测试

保存 `.env` 文件，然后运行测试：

```bash
cd backend_api_python
python quick_test_email.py
```

## 完整配置示例

`.env` 文件中应该包含：

```bash
# =========================
# Email / SMTP
# =========================
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=329731984@qq.com
SMTP_PASSWORD=你的授权码（16位字符）
SMTP_FROM=329731984@qq.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# =========================
# HAMA Email Notification
# =========================
HAMA_EMAIL_RECIPIENTS=329731984@qq.com
HAMA_EMAIL_COOLDOWN=3600
```

## 常见问题

### Q: 授权码在哪里？
A: QQ邮箱 → 设置 → 账户 → 开启IMAP/SMTP服务 → 验证后显示

### Q: 为什么不能用QQ密码？
A: QQ邮箱为了安全，使用授权码代替密码登录第三方客户端

### Q: 授权码忘记了怎么办？
A: 在QQ邮箱设置中重新生成授权码

### Q: 测试失败怎么办？
A:
1. 检查授权码是否正确（16位字符）
2. 检查网络连接
3. 检查QQ邮箱是否开启了IMAP/SMTP服务
4. 查看后端日志: `logs/app.log`

## 下一步

配置完成后：

1. **测试邮件**: `python quick_test_email.py`
2. **启动监控**: `python auto_hama_monitor_mysql.py`
3. **查看日志**: `tail -f logs/app.log`

当HAMA监控检测到趋势变化时，会自动发送邮件到 329731984@qq.com
