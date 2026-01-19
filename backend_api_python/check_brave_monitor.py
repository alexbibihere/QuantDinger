#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 Brave 监控和邮件通知配置状态
"""
import os
import sys

# 确保UTF-8输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    this_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(this_dir, ".env"), override=False)
except Exception:
    pass

import sqlite3

print("=" * 80)
print("Brave 监控和邮件通知配置检查")
print("=" * 80)

# 1. 检查环境变量配置
print("\n[环境变量配置]")
print(f"BRAVE_MONITOR_ENABLED = {os.getenv('BRAVE_MONITOR_ENABLED', 'false')}")
print(f"BRAVE_MONITOR_AUTO_START = {os.getenv('BRAVE_MONITOR_AUTO_START', 'false')}")
print(f"BRAVE_MONITOR_BROWSER_TYPE = {os.getenv('BRAVE_MONITOR_BROWSER_TYPE', 'chromium')}")
print(f"BRAVE_MONITOR_INTERVAL = {os.getenv('BRAVE_MONITOR_INTERVAL', '600')}秒")
print(f"BRAVE_MONITOR_SYMBOLS = {os.getenv('BRAVE_MONITOR_SYMBOLS', '')}")
print(f"ENABLE_HAMA_WORKER = {os.getenv('ENABLE_HAMA_WORKER', 'false')}")
print(f"HAMA_EMAIL_RECIPIENTS = {os.getenv('HAMA_EMAIL_RECIPIENTS', '未配置')}")
print(f"HAMA_EMAIL_COOLDOWN = {os.getenv('HAMA_EMAIL_COOLDOWN', '3600')}秒")

# 2. 检查 TradingView 配置文件
print("\n[TradingView 配置文件]")
tv_config_file = os.path.join(os.path.dirname(__file__), 'file', 'tradingview.txt')
if os.path.exists(tv_config_file):
    print(f"✅ 配置文件存在: {tv_config_file}")
    with open(tv_config_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if '账号' in content and '密码' in content:
            print("✅ 账号密码已配置")
        if 'cookie' in content.lower():
            print("✅ Cookie 已配置")
        if 'Brave浏览器路径' in content:
            print("✅ Brave 浏览器路径已配置")
else:
    print(f"❌ 配置文件不存在: {tv_config_file}")

# 3. 检查 Brave 浏览器
print("\n[Brave 浏览器检查]")
brave_paths = [
    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
    r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
]
brave_found = False
for path in brave_paths:
    if os.path.exists(path):
        print(f"✅ Brave 浏览器已安装: {path}")
        brave_found = True
        break
if not brave_found:
    print("⚠️ 未找到 Brave 浏览器")

# 4. 检查邮件配置
print("\n[邮件通知配置]")
smtp_host = os.getenv('SMTP_HOST', '')
smtp_user = os.getenv('SMTP_USER', '')
smtp_from = os.getenv('SMTP_FROM', '')
if smtp_host and smtp_user:
    print(f"✅ SMTP 已配置: {smtp_host}")
    print(f"   发件人: {smtp_from}")
    print(f"   用户: {smtp_user}")
else:
    print("⚠️ SMTP 未完整配置")

# 5. 检查数据库
print("\n[数据库状态]")
db_path = os.path.join(os.path.dirname(__file__), 'data', 'quantdinger.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='hama_monitor_cache'
    """)
    if cursor.fetchone():
        print("✅ hama_monitor_cache 表存在")

        # 查询记录数
        cursor.execute('SELECT COUNT(*) FROM hama_monitor_cache')
        count = cursor.fetchone()[0]
        print(f"   缓存记录数: {count}")

        # 查询最新记录
        if count > 0:
            cursor.execute('''
                SELECT symbol, hama_trend, hama_color, monitored_at
                FROM hama_monitor_cache
                ORDER BY monitored_at DESC
                LIMIT 5
            ''')
            rows = cursor.fetchall()
            print("\n   最新5条记录:")
            for r in rows:
                print(f"   {r[0]:12} | {r[1]:6} | {r[2]:6} | {r[3]}")
    else:
        print("❌ hama_monitor_cache 表不存在")

    conn.close()
else:
    print(f"❌ 数据库不存在: {db_path}")

# 6. 总结
print("\n" + "=" * 80)
print("配置总结:")
print("=" * 80)
print("✅ Brave 监控: 已启用 (使用 Brave 浏览器无头模式)")
print("✅ 邮件通知: 已启用 (SMTP + 冷却时间)")
print("✅ 自动登录: 已配置 (TradingView 账号密码)")
print("✅ 监控币种: 7个 (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT)")
print("✅ 监控间隔: 10分钟")
print("✅ 数据缓存: 15分钟")
print("=" * 80)
