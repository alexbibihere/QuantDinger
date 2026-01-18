#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构（支持SQLite和MySQL）
"""
import sys
import os
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.db import get_db_connection

print("=" * 70)
print("检查 hama_monitor_cache 表结构")
print("=" * 70)

try:
    with get_db_connection() as db:
        # 检查表是否存在
        cursor = db.cursor()

        # 判断数据库类型
        db_type = os.getenv('DB_TYPE', 'sqlite')

        if db_type == 'sqlite':
            # SQLite语法
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hama_monitor_cache'")
            table_exists = cursor.fetchone()
        else:
            # MySQL语法
            cursor.execute("SHOW TABLES LIKE 'hama_monitor_cache'")
            table_exists = cursor.fetchone()

        if not table_exists:
            print("\n[INFO] 表 hama_monitor_cache 不存在")
            print("\n下次运行监控时会自动创建表，包含以下字段:")
            print("""
- email_sent TINYINT(1) DEFAULT 0      -- 是否已发送邮件
- email_sent_at TIMESTAMP NULL          -- 邮件发送时间
            """)
        else:
            print("\n[OK] 表 hama_monitor_cache 已存在")
            print("\n当前表结构:")
            print("-" * 70)

            # 获取表结构
            if db_type == 'sqlite':
                cursor.execute("PRAGMA table_info(hama_monitor_cache)")
                columns = cursor.fetchall()
                print(f"{'字段名':<20} {'类型':<20} {'允许NULL':<10}")
                print("-" * 70)
                for col in columns:
                    print(f"{col[1]:<20} {col[2]:<20} {col[3]:<10}")
            else:
                cursor.execute("DESCRIBE hama_monitor_cache")
                columns = cursor.fetchall()
                print(f"{'字段名':<20} {'类型':<20} {'允许NULL':<10} {'键'}")
                print("-" * 70)
                for col in columns:
                    key_info = col[3] if len(col) > 3 else ""
                    print(f"{col[0]:<20} {col[1]:<20} {col[2]:<10} {key_info}")

            print("-" * 70)

            # 检查是否有 email_sent 字段
            has_email_fields = False
            if db_type == 'sqlite':
                cursor.execute("PRAGMA table_info(hama_monitor_cache)")
                columns = cursor.fetchall()
                for col in columns:
                    if col[1] in ['email_sent', 'email_sent_at']:
                        has_email_fields = True
                        print(f"[FOUND] 字段: {col[1]}")
            else:
                cursor.execute("SHOW COLUMNS FROM hama_monitor_cache LIKE 'email_sent%'")
                email_columns = cursor.fetchall()
                if email_columns:
                    has_email_fields = True
                    print("\n[SUCCESS] 邮件发送字段已存在 ✅")
                    for col in email_columns:
                        print(f"  - {col[0]}")

            if not has_email_fields:
                print("\n[WARN] 邮件发送字段不存在")
                print("\n下次运行监控时会自动添加这些字段")

            # 显示当前数据
            if db_type == 'sqlite':
                cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            else:
                cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            count = cursor.fetchone()[0]
            print(f"\n当前数据: {count} 条记录")

            if count > 0:
                if db_type == 'sqlite':
                    cursor.execute("""
                        SELECT symbol, hama_trend, hama_color, monitored_at
                        FROM hama_monitor_cache
                        ORDER BY monitored_at DESC
                        LIMIT 5
                    """)
                else:
                    cursor.execute("""
                        SELECT symbol, hama_trend, hama_color, email_sent, email_sent_at, monitored_at
                        FROM hama_monitor_cache
                        ORDER BY monitored_at DESC
                        LIMIT 5
                    """)
                rows = cursor.fetchall()

                print("\n最近5条记录:")
                print("-" * 70)
                for row in rows:
                    if len(row) > 4:  # MySQL有email_sent字段
                        email_status = '已发送' if row[3] else '未发送'
                        email_time = str(row[4]) if row[4] else 'N/A'
                        print(f"  {row[0]:<10} {row[1] or 'N/A':<10} {row[2] or 'N/A':<10} "
                              f"{email_status:<8} {email_time}")
                    else:  # SQLite没有email_sent字段
                        print(f"  {row[0]:<10} {row[1] or 'N/A':<10} {row[2] or 'N/A':<10} "
                              f"{str(row[3]) if row[3] else 'N/A'}")

            cursor.close()

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("提示: 运行监控后会自动创建/更新表结构")
print("启动命令: python auto_hama_monitor_mysql.py")
print("=" * 70)
