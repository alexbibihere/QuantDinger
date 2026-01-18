#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断SMTP连接问题
"""
import sys
import os
from pathlib import Path
import smtplib

# 手动加载 .env 文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'

print("=" * 70)
print("SMTP Connection Diagnostics")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Host: {SMTP_HOST}")
print(f"  Port: {SMTP_PORT}")
print(f"  User: {SMTP_USER}")
print(f"  Use SSL: {SMTP_USE_SSL}")
print(f"  Use TLS: {SMTP_USE_TLS}")

if not SMTP_PASSWORD:
    print("\n[ERROR] SMTP_PASSWORD is not set!")
    sys.exit(1)

print(f"\n[INFO] Testing connection to {SMTP_HOST}:{SMTP_PORT}...")

try:
    if SMTP_USE_SSL or SMTP_PORT == 465:
        print("[INFO] Using SMTP_SSL...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
    else:
        print("[INFO] Using SMTP with TLS...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        if SMTP_USE_TLS:
            print("[INFO] Starting TLS...")
            server.starttls()

    print("[OK] Connected to SMTP server")

    print(f"[INFO] Logging in as {SMTP_USER}...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("[OK] Login successful")

    # 发送测试邮件
    print("\n[INFO] Sending test email...")
    from email.message import EmailMessage
    msg = EmailMessage()
    msg['From'] = SMTP_USER
    msg['To'] = SMTP_USER
    msg['Subject'] = 'Test Email from QuantDinger'
    msg.set_content('This is a test email from QuantDinger HAMA notification system.')

    server.send_message(msg)
    print("[OK] Test email sent successfully!")

    server.quit()

    print("\n" + "=" * 70)
    print("[SUCCESS] SMTP configuration is working!")
    print("=" * 70)
    print("\nPlease check your inbox (including spam folder)")

except smtplib.SMTPAuthenticationError as e:
    print(f"\n[ERROR] Authentication failed: {e}")
    print("\nPossible reasons:")
    print("  1. Wrong authorization code")
    print("  2. Authorization code expired")
    print("  3. IMAP/SMTP service not enabled")
    print("\nPlease check: https://mail.qq.com -> Settings -> Account")

except smtplib.SMTPException as e:
    print(f"\n[ERROR] SMTP error: {e}")

except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
