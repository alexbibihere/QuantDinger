#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 HAMA 监控数据库表（SQLite 版本）
"""
import sys
import os
import sqlite3

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init_database():
    """初始化 SQLite 数据库表"""
    print("\n" + "="*80)
    print("初始化 HAMA 监控数据库表（SQLite）")
    print("="*80)

    # 数据库文件路径
    db_path = 'data/quantdinger.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        print(f"  提示: 请先启动后端服务创建数据库")
        return False

    print(f"✅ 找到数据库: {db_path}")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 读取 SQL 文件
    sql_file = 'sql/hama_monitor_schema.sql'

    if not os.path.exists(sql_file):
        print(f"❌ SQL 文件不存在: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"✅ 已读取 SQL 文件: {sql_file}")

    # 修改 SQL 使其兼容 SQLite
    sql_content = sql_content.replace('ENGINE=InnoDB DEFAULT CHARSET=utf8mb4', '')
    sql_content = sql_content.replace('AUTO_INCREMENT', 'AUTOINCREMENT')

    # 分割并执行 SQL 语句
    statements = []
    for statement in sql_content.split(';'):
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            statements.append(statement)

    print(f"\n正在执行 {len(statements)} 个 SQL 语句...")

    success_count = 0
    for i, statement in enumerate(statements, 1):
        try:
            cursor.execute(statement)
            print(f"  {i}/{len(statements)} ✅")
            success_count += 1
        except Exception as e:
            error_msg = str(e).strip()
            if 'already exists' in error_msg:
                print(f"  {i}/{len(statements)} ⚠️  表已存在")
                success_count += 1
            else:
                print(f"  {i}/{len(statements)} ❌ {error_msg[:50]}")

    # 提交事务
    conn.commit()

    print(f"\n✅ 成功执行 {success_count}/{len(statements)} 个语句")

    # 验证表是否创建
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hama_%'")
    tables = cursor.fetchall()

    if tables:
        print(f"\n📋 已创建/存在的表:")
        for table in tables:
            print(f"  - {table[0]}")

        # 查询缓存数据
        cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
        count = cursor.fetchone()[0]
        print(f"\n💾 当前缓存: {count} 条记录")
    else:
        print("\n⚠️  未找到 hama_ 开头的表")

    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("✅ 初始化完成！")
    print("="*80)

    return True


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
