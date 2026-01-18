import os, sys
sys.path.insert(0, '.')

# 加载环境变量
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    exec(open(env_path).read())

from app.utils.db import get_db_connection

with get_db_connection() as db:
    cursor = db.cursor()

    # 检查表结构
    cursor.execute('PRAGMA table_info(hama_monitor_cache)')
    columns = cursor.fetchall()

    print('Field List:')
    for col in columns:
        print(f'  {col[1]}')

    # 检查email相关字段
    cursor.execute('PRAGMA table_info(hama_monitor_cache)')
    columns = cursor.fetchall()

    has_email_sent = any('email_sent' in str(col) for col in columns)
    has_email_sent_at = any('email_sent_at' in str(col) for col in columns)

    if has_email_sent and has_email_sent_at:
        print('\n[OK] Email fields EXIST')
    else:
        print('\n[INFO] Email fields NOT YET ADDED')

    cursor.close()
