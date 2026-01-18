#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动配置 HAMA 邮件通知并集成到启动流程
"""
import os
import sys

def setup_email_config():
    """自动配置邮件通知"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')

    # QQ邮箱配置
    config = {
        'SMTP_HOST': 'smtp.qq.com',
        'SMTP_PORT': '587',
        'SMTP_USER': '329731984@qq.com',
        'SMTP_FROM': '329731984@qq.com',
        'SMTP_USE_TLS': 'true',
        'SMTP_USE_SSL': 'false',
        'HAMA_EMAIL_RECIPIENTS': '329731984@qq.com',
        'HAMA_EMAIL_COOLDOWN': '3600'
    }

    print("=" * 70)
    print("Auto Setup HAMA Email Notification")
    print("=" * 70)

    # 读取现有 .env 文件
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
    except FileNotFoundError:
        env_content = ""

    # 检查是否需要配置授权码
    if 'SMTP_PASSWORD=' in env_content and env_content.split('SMTP_PASSWORD=')[1].split('\n')[0].strip():
        print("\n[OK] Email configuration already exists")
        return True

    print("\n[INFO] Please enter your QQ Mail Authorization Code")
    print("[INFO] Get it from: https://mail.qq.com -> Settings -> Account")

    # 提示用户输入授权码
    smtp_password = input("\nEnter Authorization Code: ").strip()

    if not smtp_password:
        print("[ERROR] Authorization Code is required!")
        return False

    config['SMTP_PASSWORD'] = smtp_password

    # 更新 .env 文件
    lines = env_content.split('\n')
    new_lines = []
    skip_section = False
    config_updated = {key: False for key in config.keys()}

    for i, line in enumerate(lines):
        # 检查是否是配置行
        for key in config.keys():
            if line.startswith(f'{key}='):
                # 如果还没更新过，则更新
                if not config_updated[key]:
                    new_lines.append(f'{key}={config[key]}')
                    config_updated[key] = True
                skip_section = False
                break
        else:
            # 检查是否在 Email/SMTP 或 HAMA Email 部分
            if 'Email / SMTP' in line or 'HAMA Email Notification' in line:
                # 检查后续行是否需要更新
                skip_section = False
            new_lines.append(line)

    # 写入文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("\n" + "=" * 70)
    print("[SUCCESS] Email configuration saved")
    print("=" * 70)
    print(f"SMTP Host: {config['SMTP_HOST']}")
    print(f"SMTP User: {config['SMTP_USER']}")
    print(f"Recipients: {config['HAMA_EMAIL_RECIPIENTS']}")
    print("\nYou can now run: python quick_test_email.py")

    return True


def integrate_to_auto_monitor():
    """集成到自动监控启动脚本"""
    auto_monitor_path = os.path.join(os.path.dirname(__file__), 'auto_hama_monitor_mysql.py')

    if not os.path.exists(auto_monitor_path):
        print(f"[WARN] {auto_monitor_path} not found")
        return False

    # 读取文件
    with open(auto_monitor_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经集成了邮件通知
    if 'enable_email=True' in content or 'enable_email = True' in content:
        print("[OK] Email notification already integrated in auto monitor")
        return True

    # 查找 get_brave_monitor 调用并添加 enable_email=True
    import re
    pattern = r'get_brave_monitor\(([^)]*)\)'

    def replace_monitor(match):
        args = match.group(1)
        if 'enable_email' not in args:
            if args.strip():
                args += ', enable_email=True'
            else:
                args = 'enable_email=True'
        return f'get_brave_monitor({args})'

    new_content = re.sub(pattern, replace_monitor, content)

    # 写回文件
    with open(auto_monitor_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("[OK] Email notification integrated to auto monitor")
    return True


def main():
    print("\n" + "=" * 70)
    print(" " * 15 + "HAMA Email Auto Setup")
    print("=" * 70)

    # 1. 配置邮件
    if not setup_email_config():
        print("\n[FAILED] Email configuration failed")
        return False

    # 2. 集成到自动监控
    print("\n" + "-" * 70)
    if not integrate_to_auto_monitor():
        print("[WARN] Failed to integrate to auto monitor (you can do it manually)")

    print("\n" + "=" * 70)
    print("[SUCCESS] Setup completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Test email: python quick_test_email.py")
    print("  2. Start monitor: python auto_hama_monitor_mysql.py")
    print("\nEmail notifications will be sent automatically when HAMA trend changes!")

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Setup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
