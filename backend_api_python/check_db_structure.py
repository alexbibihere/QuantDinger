#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
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
        result = db.execute("SHOW TABLES LIKE 'hama_monitor_cache'")
        table_exists = result.fetchone()

        if not table_exists:
            print("\n[INFO] 表 hama_monitor_cache 不存在")
            print("\n需要先运行监控来创建表，或者手动执行以下SQL:")
            print("""
CREATE TABLE hama_monitor_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    hama_trend VARCHAR(10),
    hama_color VARCHAR(10),
    hama_value DECIMAL(20, 8),
    price DECIMAL(20, 8),
    ocr_text TEXT,
    screenshot_path VARCHAR(255),
    email_sent TINYINT(1) DEFAULT 0,
    email_sent_at TIMESTAMP NULL,
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol (symbol),
    INDEX idx_monitored_at (monitored_at),
    INDEX idx_email_sent (email_sent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        else:
            print("\n[OK] 表 hama_monitor_cache 已存在")
            print("\n当前表结构:")
            print("-" * 70)

            result = db.execute("DESCRIBE hama_monitor_cache")
            columns = result.fetchall()

            print(f"{'字段名':<20} {'类型':<20} {'允许NULL':<10} {'键'}")
            print("-" * 70)

            has_email_sent = False
            has_email_sent_at = False

            for col in columns:
                field = col[0]
                type_info = col[1]
                null_info = col[2]
                key_info = col[3] if len(col) > 3 else ""

                print(f"{field:<20} {type_info:<20} {null_info:<10} {key_info}")

                if field == 'email_sent':
                    has_email_sent = True
                elif field == 'email_sent_at':
                    has_email_sent_at = True

            print("-" * 70)

            if has_email_sent and has_email_sent_at:
                print("\n[SUCCESS] 邮件发送字段已存在 ✅")
            else:
                print("\n[WARN] 邮件发送字段不存在")
                print("\n需要添加以下字段:")
                print("""
ALTER TABLE hama_monitor_cache
ADD COLUMN email_sent TINYINT(1) DEFAULT 0,
ADD COLUMN email_sent_at TIMESTAMP NULL,
ADD INDEX idx_email_sent (email_sent);
                """)

            # 显示当前数据
            result = db.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            count = result.fetchone()[0]
            print(f"\n当前数据: {count} 条记录")

            if count > 0:
                result = db.execute("""
                    SELECT symbol, hama_trend, hama_color, email_sent, email_sent_at, monitored_at
                    FROM hama_monitor_cache
                    ORDER BY monitored_at DESC
                    LIMIT 5
                """)
                rows = result.fetchall()

                print("\n最近5条记录:")
                print("-" * 70)
                for row in rows:
                    email_status = '已发送' if row[3] else '未发送'
                    email_time = str(row[4]) if row[4] else 'N/A'
                    print(f"  {row[0]:<10} {row[1] or 'N/A':<10} {row[2] or 'N/A':<10} "
                          f"{email_status:<8} {email_time}")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
