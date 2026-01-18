#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 HAMA 监控数据库
"""
import sys
import os

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database():
    """检查数据库"""
    print("\n" + "="*80)
    print("🔍 检查 HAMA 监控数据库")
    print("="*80)

    try:
        import sqlite3

        # 数据库路径
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'quantdinger.db')

        if not os.path.exists(db_path):
            print(f"\n❌ 数据库文件不存在: {db_path}")
            return

        print(f"\n✅ 数据库文件存在: {db_path}")
        print(f"   文件大小: {os.path.getsize(db_path) / 1024:.2f} KB")

        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 检查表
        print("\n📋 数据库表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hama%'")
        tables = cursor.fetchall()

        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  ⚠️  没有找到 HAMA 相关表")

        # 检查 hama_monitor_cache 表
        print("\n📊 hama_monitor_cache 表:")
        try:
            cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            count = cursor.fetchone()[0]
            print(f"  总记录数: {count}")

            if count > 0:
                cursor.execute('''
                    SELECT symbol, hama_trend, hama_color, hama_value, monitored_at
                    FROM hama_monitor_cache
                    ORDER BY monitored_at DESC
                    LIMIT 10
                ''')
                rows = cursor.fetchall()

                print(f"\n  最新 {len(rows)} 条记录:")
                for row in rows:
                    print(f"  - {row[0]}: {row[1]} / {row[2]} / {row[3]} / {row[4]}")
            else:
                print("  ⚠️  暂无数据 (监控脚本正在运行中...)")

        except sqlite3.OperationalError:
            print("  ❌ 表不存在")

        conn.close()

        print("\n" + "="*80)
        print("✅ 检查完成!")
        print("="*80)

        if count == 0:
            print("\n💡 提示:")
            print("  监控脚本正在后台运行,首次监控需要几分钟时间")
            print("  请稍后重新运行此脚本查看数据")

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_database()
