#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化系统所有数据库表
包括 HAMA 监控相关的表
"""
import sys
import os
import sqlite3
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_hama_tables(db_path):
    """创建 HAMA 监控相关的表"""
    print("\n" + "="*80)
    print("创建 HAMA 监控表")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. HAMA 监控缓存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hama_monitor_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            hama_trend VARCHAR(10),
            hama_color VARCHAR(10),
            hama_value DECIMAL(20, 8),
            price DECIMAL(20, 8),
            ocr_text TEXT,
            screenshot_path VARCHAR(255),
            monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ hama_monitor_cache 表创建成功")

    # 2. HAMA 监控历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hama_monitor_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            hama_trend VARCHAR(10),
            hama_color VARCHAR(10),
            hama_value DECIMAL(20, 8),
            price DECIMAL(20, 8),
            monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ hama_monitor_history 表创建成功")

    # 创建索引
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hama_cache_monitored ON hama_monitor_cache(monitored_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hama_cache_symbol ON hama_monitor_cache(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hama_history_symbol_monitored ON hama_monitor_history(symbol, monitored_at)')
        print("✅ 索引创建成功")
    except Exception as e:
        print(f"⚠️  索引创建警告: {e}")

    conn.commit()

    # 验证表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hama_%'")
    tables = cursor.fetchall()

    if tables:
        print(f"\n📋 HAMA 相关表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table[0]}")

    cursor.close()
    conn.close()

    return True


def show_all_tables(db_path):
    """显示所有数据库表"""
    print("\n" + "="*80)
    print("系统所有表")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\n总表数: {len(tables)}")

    # 按类别分组
    system_tables = []
    hama_tables = []
    trading_tables = []
    other_tables = []

    for table in tables:
        name = table[0]
        if name.startswith('hama_'):
            hama_tables.append(name)
        elif name.startswith('td_') or name.startswith('kline_') or name.startswith('strategy_'):
            trading_tables.append(name)
        else:
            system_tables.append(name)

    if system_tables:
        print(f"\n📋 系统表 ({len(system_tables)} 个):")
        for name in system_tables:
            print(f"  - {name}")

    if trading_tables:
        print(f"\n📊 交易表 ({len(trading_tables)} 个):")
        for name in trading_tables:
            print(f"  - {name}")

    if hama_tables:
        print(f"\n🎯 HAMA 表 ({len(hama_tables)} 个):")
        for name in hama_tables:
            print(f"  - {name}")

    cursor.close()
    conn.close()

    return True


def get_table_info(db_path, table_name):
    """获取表的详细信息"""
    print("\n" + "="*80)
    print(f"表结构: {table_name}")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    if columns:
        print(f"\n字段数: {len(columns)}")
        print("\n{:20} {:20} {:10} {:10}".format("字段名", "类型", "NOT NULL", "PRIMARY KEY"))
        print("-" * 70)

        for col in columns:
            cid, name, type_, notnull, pk = col
            print(f"{name:20} {type_:20} {str(notnull):10} {str(pk):10}")

    # 获取行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n记录数: {count}")

    cursor.close()
    conn.close()


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🗄️  系统数据库初始化工具")
    print("="*80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 数据库路径
    db_path = 'data/quantdinger.db'

    if not os.path.exists(db_path):
        print(f"\n❌ 数据库文件不存在: {db_path}")
        print(f"\n请先启动后端服务创建数据库:")
        print("  cd backend_api_python")
        print("  python run.py")
        return

    print(f"\n✅ 数据库文件: {db_path}")

    # 1. 创建 HAMA 表
    create_hama_tables(db_path)

    # 2. 显示所有表
    show_all_tables(db_path)

    # 3. 显示 HAMA 表结构
    get_table_info(db_path, 'hama_monitor_cache')

    print("\n" + "="*80)
    print("✅ 初始化完成！")
    print("="*80)

    print("\n📝 下一步:")
    print("1. 运行自动监控: python auto_hama_monitor.py")
    print("2. 或双击启动: start_hama_monitor.bat")
    print("3. 访问前端: http://localhost:8000/#/hama-market")


if __name__ == '__main__':
    main()
