#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 HAMA 邮件通知
使用示例收件人: 329731984@qq.com
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.hama_email_notifier import get_hama_email_notifier


def main():
    print("=" * 70)
    print(" " * 15 + "HAMA Email Notification Quick Test")
    print("=" * 70)

    # 获取邮件通知器
    notifier = get_hama_email_notifier()

    # 显示当前配置
    print("\n[Current Config]")
    print(f"  SMTP Host: {notifier.smtp_host or 'Not configured'}")
    print(f"  SMTP Port: {notifier.smtp_port}")
    print(f"  From: {notifier.smtp_from or 'Not configured'}")
    print(f"  To: {notifier.default_recipients or 'Not configured'}")
    print(f"  Cooldown: {notifier.cooldown_seconds} sec ({notifier.cooldown_seconds // 60} min)")

    # 检查配置
    if not notifier.smtp_host:
        print("\n[ERROR] SMTP_HOST not configured")
        print("\nPlease follow the configuration steps:")
        print_config_guide()
        return

    if not notifier.smtp_user or not notifier.smtp_password:
        print("\n[ERROR] SMTP_USER or SMTP_PASSWORD not configured")
        print("\nPlease follow the configuration steps:")
        print_config_guide()
        return

    if not notifier.default_recipients:
        print("\n[ERROR] HAMA_EMAIL_RECIPIENTS not configured")
        print("\nPlease add to .env file:")
        print("  HAMA_EMAIL_RECIPIENTS=329731984@qq.com")
        return

    print("\n[OK] Configuration check passed")

    # 发送测试邮件
    print("\n" + "=" * 70)
    print("Sending test emails...")
    print("=" * 70)

    test_cases = [
        {
            "name": "Test 1: BTCUSDT Uptrend (Golden Cross)",
            "symbol": "BTCUSDT",
            "trend": "up",
            "color": "green",
            "value": 96750.50,
            "price": 96850.25,
            "cross": "cross_up",
            "reason": "Golden Cross: HAMA Close crosses above MA"
        },
        {
            "name": "Test 2: ETHUSDT Downtrend (Death Cross)",
            "symbol": "ETHUSDT",
            "trend": "down",
            "color": "red",
            "value": 3250.75,
            "price": 3245.50,
            "cross": "cross_down",
            "reason": "Death Cross: HAMA Close crosses below MA"
        }
    ]

    success_count = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\n{test['name']}")
        print("-" * 70)

        success = notifier.notify_trend_formed(
            symbol=test['symbol'],
            trend=test['trend'],
            hama_color=test['color'],
            hama_value=test['value'],
            price=test['price'],
            cross_type=test['cross'],
            screenshot_url=f"http://localhost:5000/api/screenshots/test_{test['symbol']}.png",
            extra_data={
                "Reason": test['reason'],
                "Monitored at": "2026-01-18 12:00:00",
                "Data Source": "Brave Browser OCR"
            }
        )

        if success:
            print(f"[OK] {test['symbol']} email sent successfully")
            success_count += 1
        else:
            print(f"[FAIL] {test['symbol']} email send failed")

    # 测试冷却机制
    print("\n" + "=" * 70)
    print("Test 3: Cooldown Mechanism (Send BTCUSDT again, should be blocked)")
    print("=" * 70)

    success = notifier.notify_trend_formed(
        symbol="BTCUSDT",
        trend="up",
        hama_color="green",
        hama_value=96750.50,
        price=96850.25,
    )

    if not success:
        print("[OK] Cooldown mechanism working (email not sent as expected)")
        success_count += 1
    else:
        print("[WARN] Cooldown mechanism may not work (email sent)")

    # 总结
    print("\n" + "=" * 70)
    print(f"Test completed: {success_count}/{len(test_cases) + 1} passed")
    print("=" * 70)

    print(f"\n[Recipient] {notifier.default_recipients}")
    print("Please check your email (including spam folder)")

    if success_count == len(test_cases) + 1:
        print("\n[SUCCESS] All tests passed! HAMA email notification is working")
        print("\nNext steps:")
        print("  1. Start HAMA auto monitor: python auto_hama_monitor_mysql.py")
        print("  2. Email will be sent automatically when trend changes detected")
    else:
        print("\n[WARN] Some tests failed, please check:")
        print("  1. SMTP configuration is correct")
        print("  2. Authorization code is valid (use QQ mail auth code, not password)")
        print("  3. Network connection is normal")
        print("  4. Check backend log: logs/app.log")


def print_config_guide():
    """打印配置指南"""
    print("\n" + "=" * 70)
    print("QQ Mail Configuration Steps")
    print("=" * 70)
    print("""
Step 1: Enable QQ Mail SMTP Service
   - Visit https://mail.qq.com
   - Click Settings -> Account
   - Find POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV Services
   - Enable IMAP/SMTP Service
   - Verify with SMS

Step 2: Get Authorization Code
   - After enabling, an authorization code will be displayed
   - Copy this code (NOT your QQ password!)

Step 3: Configure .env file
   Edit backend_api_python/.env, add:

   SMTP_HOST=smtp.qq.com
   SMTP_PORT=587
   SMTP_USER=329731984@qq.com
   SMTP_PASSWORD=your_qq_authorization_code
   SMTP_FROM=329731984@qq.com
   SMTP_USE_TLS=true

   HAMA_EMAIL_RECIPIENTS=329731984@qq.com
   HAMA_EMAIL_COOLDOWN=3600

Step 4: Run test again
   python quick_test_email.py
""")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
