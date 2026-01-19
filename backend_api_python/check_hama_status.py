#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from app import get_hama_brave_monitor

print("=" * 80)
print("Brave 监控状态检查")
print("=" * 80)

# 1. 检查监控器状态
monitor = get_hama_brave_monitor()
if monitor:
    stats = monitor.get_stats()
    print(f"\n[监控器状态]")
    print(f"  - 可用: {stats.get('available', False)}")
    print(f"  - 运行中: {stats.get('is_monitoring', False)}")
    print(f"  - 缓存币种数: {stats.get('cached_symbols', 0)}")
    print(f"  - 缓存TTL: {stats.get('cache_ttl_seconds', 0)}秒")
else:
    print("\n[监控器状态] 未初始化")

# 2. 检查数据库记录
conn = sqlite3.connect('data/quantdinger.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM hama_monitor_cache')
count = cursor.fetchone()[0]
print(f"\n[数据库统计]")
print(f"  - 总记录数: {count}")

if count > 0:
    cursor.execute('''
        SELECT symbol, hama_trend, hama_color, hama_value, price, monitored_at
        FROM hama_monitor_cache
        ORDER BY monitored_at DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()

    print(f"\n[最新10条记录]")
    print("-" * 80)
    for r in rows:
        symbol = r[0]
        trend = r[1] or 'N/A'
        color = r[2] or 'N/A'
        value = f"{r[3]:.6f}" if r[3] else 'N/A'
        price = f"${r[4]:.6f}" if r[4] else 'N/A'
        time = r[5]
        print(f"{symbol:12} | 趋势: {trend:6} | 颜色: {color:6} | HAMA: {value:12} | 价格: {price:15} | {time}")

conn.close()

print("\n" + "=" * 80)
