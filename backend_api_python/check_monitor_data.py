#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查监控数据"""
import sys
import os
import sqlite3

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_monitor_data():
    db_path = os.path.join('data', 'quantdinger.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT symbol, hama_color, hama_value, screenshot_path, monitored_at FROM hama_monitor_cache ORDER BY monitored_at DESC LIMIT 10')

    print('\n=== 最近的监控记录 ===\n')

    for row in cursor.fetchall():
        has_screenshot = '✅' if row['screenshot_path'] else '❌'
        screenshot_info = row['screenshot_path'] if row['screenshot_path'] else '无截图'
        print(f"{row[0]:10} {row[1]:6} {row[2]:>10} {has_screenshot:8} {screenshot_info:30}")

    print('\n截图文件检查:')
    screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    if os.path.exists(screenshot_dir):
        files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
        print(f"截图目录: {screenshot_dir}")
        print(f"截图数量: {len(files)}")
        if files:
            print("最新的截图:")
            for f in sorted(files)[-3:]:
                print(f"  - {f}")
    else:
        print("截图目录不存在")

    conn.close()


if __name__ == '__main__':
    check_monitor_data()
