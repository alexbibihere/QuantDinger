#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化邮件发送记录表"""
import sys
import os

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.services.hama_brave_monitor import get_brave_monitor

def main():
    print("=" * 60)
    print("初始化邮件发送记录表")
    print("=" * 60)

    # 初始化监控器（会自动创建表）
    monitor = get_brave_monitor(use_sqlite=True)

    print("\n✅ 数据库表初始化完成！")

    # 验证表是否创建成功
    import sqlite3
    db_path = os.path.join(
        os.path.dirname(__file__), 'data', 'quantdinger.db'
    )
    db_path = os.path.abspath(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    if 'email_send_log' in tables:
        print("\n✅ email_send_log 表已创建")

        # 查看表结构
        cursor.execute('PRAGMA table_info(email_send_log)')
        print("\n表结构:")
        for row in cursor.fetchall():
            print(f"  {row[1]:20} {row[2]:20}")

        # 查询记录数
        cursor.execute('SELECT COUNT(*) FROM email_send_log')
        count = cursor.fetchone()[0]
        print(f"\n当前记录数: {count}")
    else:
        print("\n❌ email_send_log 表未创建")

    conn.close()

if __name__ == '__main__':
    main()
