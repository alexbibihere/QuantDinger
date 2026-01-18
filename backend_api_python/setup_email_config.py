#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速配置 HAMA 邮件通知
"""
import os

# 读取 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '.env')

print("=" * 70)
print("HAMA Email Configuration Setup")
print("=" * 70)
print("\nPlease enter your QQ mail configuration:")
print("(Press Enter to use default value)\n")

# 获取用户输入
smtp_host = input("SMTP Host [smtp.qq.com]: ").strip() or "smtp.qq.com"
smtp_port = input("SMTP Port [587]: ").strip() or "587"
smtp_user = input("SMTP User (your QQ email) [329731984@qq.com]: ").strip() or "329731984@qq.com"
smtp_password = input("SMTP Password (authorization code): ").strip()
smtp_from = input("SMTP From [329731984@qq.com]: ").strip() or "329731984@qq.com"
recipients = input("Recipients [329731984@qq.com]: ").strip() or "329731984@qq.com"
cooldown = input("Cooldown seconds [3600]: ").strip() or "3600"

if not smtp_password:
    print("\n[ERROR] SMTP Password (authorization code) is required!")
    print("Please get it from: https://mail.qq.com -> Settings -> Account")
    exit(1)

# 构建 .env 配置
config_lines = [
    f"\n# =========================",
    f"# Email / SMTP (QQ Mail)",
    f"# =========================",
    f"SMTP_HOST={smtp_host}",
    f"SMTP_PORT={smtp_port}",
    f"SMTP_USER={smtp_user}",
    f"SMTP_PASSWORD={smtp_password}",
    f"SMTP_FROM={smtp_from}",
    f"SMTP_USE_TLS=true",
    f"SMTP_USE_SSL=false",
    f"",
    f"# =========================",
    f"# HAMA Email Notification",
    f"# =========================",
    f"HAMA_EMAIL_RECIPIENTS={recipients}",
    f"HAMA_EMAIL_COOLDOWN={cooldown}",
    f"\n"
]

# 读取现有 .env 文件
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
except FileNotFoundError:
    env_content = ""

# 检查是否已存在配置
if "SMTP_HOST=smtp.qq.com" in env_content:
    print("\n[WARN] SMTP configuration already exists in .env file")
    choice = input("Do you want to overwrite? (y/n): ").strip().lower()
    if choice != 'y':
        print("Configuration cancelled.")
        exit(0)

# 更新配置
lines = env_content.split('\n')
new_lines = []
skip_smtp = False
skip_hama = False

for line in lines:
    if line.startswith('SMTP_HOST='):
        skip_smtp = True
        continue
    if line.startswith('SMTP_PORT='):
        continue
    if line.startswith('SMTP_USER='):
        continue
    if line.startswith('SMTP_PASSWORD='):
        continue
    if line.startswith('SMTP_FROM='):
        continue
    if line.startswith('SMTP_USE_TLS='):
        continue
    if line.startswith('SMTP_USE_SSL='):
        skip_smtp = False
        continue
    if line.startswith('HAMA_EMAIL_RECIPIENTS='):
        skip_hama = True
        continue
    if line.startswith('HAMA_EMAIL_COOLDOWN='):
        skip_hama = False
        continue

    if not skip_smtp and not skip_hama:
        new_lines.append(line)

# 添加新配置
new_lines.extend(config_lines)

# 写入文件
with open(env_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("\n" + "=" * 70)
print("[SUCCESS] Configuration saved to .env file")
print("=" * 70)
print(f"\nSMTP Host: {smtp_host}")
print(f"SMTP User: {smtp_user}")
print(f"SMTP From: {smtp_from}")
print(f"Recipients: {recipients}")
print(f"Cooldown: {cooldown} seconds")
print("\nNext step: Run 'python quick_test_email.py' to test email sending")
