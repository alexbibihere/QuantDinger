#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终邮件测试 - 正确加载环境变量
"""
import sys
import os
from pathlib import Path

# 第一步：手动加载 .env 文件到环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    print(f"[INFO] Loading environment from {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print("[OK] Environment loaded")
else:
    print(f"[WARN] .env file not found at {env_path}")

# 第二步：添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 第三步：导入并使用邮件通知器
from app.services.hama_email_notifier import get_hama_email_notifier

print("\n" + "=" * 70)
print(" " * 20 + "Final Email Test")
print("=" * 70)

notifier = get_hama_email_notifier()

print("\n[Configuration Check]")
print(f"  SMTP Host: {notifier.smtp_host}")
print(f"  SMTP Port: {notifier.smtp_port} (type: {type(notifier.smtp_port)})")
print(f"  SMTP User: {notifier.smtp_user}")
print(f"  SMTP From: {notifier.smtp_from}")
print(f"  Use SSL: {notifier.smtp_use_ssl}")
print(f"  Use TLS: {notifier.smtp_use_tls}")
print(f"  Recipients: {notifier.default_recipients}")

if not notifier.smtp_host or not notifier.smtp_password:
    print("\n[ERROR] Missing required configuration!")
    sys.exit(1)

print("\n[OK] All configuration loaded")

# 发送测试邮件
print("\n" + "=" * 70)
print("Sending Test Email...")
print("=" * 70)

success = notifier.notify_trend_formed(
    symbol="BTCUSDT",
    trend="up",
    hama_color="green",
    hama_value=96750.50,
    price=96850.25,
    cross_type="cross_up",
    screenshot_url="http://localhost:5000/api/screenshots/test.png",
    extra_data={
        "Reason": "Test Email - Golden Cross Detected",
        "Monitored at": "2026-01-18 12:00:00",
        "Data Source": "Brave Browser OCR"
    }
)

if success:
    print("\n" + "=" * 70)
    print("[SUCCESS] Test email sent successfully!")
    print("=" * 70)
    print(f"\nPlease check your inbox: {notifier.default_recipients}")
    print("(including spam folder)")
    print("\nEmail notification is ready for HAMA monitoring!")
else:
    print("\n[FAILED] Email send failed")
    print("Please check the logs for details")
    sys.exit(1)
