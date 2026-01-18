#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 HAMA 币种管理表
用于管理用户监控的 HAMA 指标币种列表
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


def create_hama_symbols_table(db_path):
    """创建 HAMA 币种管理表"""
    print("\n" + "="*80)
    print("创建 HAMA 币种管理表")
    print("="*80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建币种管理表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hama_symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            symbol_name VARCHAR(50),
            market VARCHAR(20) DEFAULT 'spot',
            enabled BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 0,
            notify_enabled BOOLEAN DEFAULT 0,
            notify_threshold DECIMAL(5, 2) DEFAULT 2.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_monitored_at TIMESTAMP
        )
    ''')
    print("✅ hama_symbols 表创建成功")

    # 创建索引
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hama_symbols_enabled ON hama_symbols(enabled, priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hama_symbols_symbol ON hama_symbols(symbol)')
        print("✅ 索引创建成功")
    except Exception as e:
        print(f"⚠️  索引创建警告: {e}")

    # 插入默认币种
    default_symbols = [
        ('BTCUSDT', 'Bitcoin', 'spot', 1, 100, 1, 2.0, 'BTC 永续监控'),
        ('ETHUSDT', 'Ethereum', 'spot', 1, 90, 1, 2.0, 'ETH 永续监控'),
        ('BNBUSDT', 'Binance Coin', 'spot', 1, 80, 1, 2.0, 'BNB 永续监控'),
        ('SOLUSDT', 'Solana', 'spot', 1, 70, 1, 2.0, 'SOL 永续监控'),
        ('XRPUSDT', 'Ripple', 'spot', 1, 60, 1, 2.0, 'XRP 永续监控'),
        ('ADAUSDT', 'Cardano', 'spot', 1, 50, 1, 2.0, 'ADA 永续监控'),
        ('DOGEUSDT', 'Dogecoin', 'spot', 1, 40, 1, 2.0, 'DOGE 永续监控'),
        ('AVAXUSDT', 'Avalanche', 'spot', 1, 30, 1, 2.0, 'AVAX 永续监控'),
        ('DOTUSDT', 'Polkadot', 'spot', 1, 20, 1, 2.0, 'DOT 永续监控'),
        ('LINKUSDT', 'Chainlink', 'spot', 1, 10, 1, 2.0, 'LINK 永续监控'),
    ]

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM hama_symbols")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany('''
            INSERT OR IGNORE INTO hama_symbols
            (symbol, symbol_name, market, enabled, priority, notify_enabled, notify_threshold, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_symbols)
        print(f"✅ 插入 {len(default_symbols)} 个默认币种")
    else:
        print(f"⚠️  表中已有 {count} 条记录，跳过插入默认数据")

    conn.commit()

    # 验证表
    cursor.execute("SELECT * FROM hama_symbols ORDER BY priority DESC")
    symbols = cursor.fetchall()

    if symbols:
        print(f"\n📋 HAMA 币种列表 ({len(symbols)} 个):")
        print("\n{:20} {:20} {:10} {:10} {:10}".format("币种", "名称", "市场", "启用", "优先级"))
        print("-" * 80)
        for s in symbols:
            symbol = s[1]
            name = s[2] or '-'
            market = s[3]
            enabled = '✅' if s[4] else '❌'
            priority = s[5]
            print(f"{symbol:20} {name:20} {market:10} {enabled:10} {priority:10}")

    cursor.close()
    conn.close()

    return True


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🗄️  HAMA 币种管理表初始化工具")
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

    # 创建表
    create_hama_symbols_table(db_path)

    print("\n" + "="*80)
    print("✅ 初始化完成！")
    print("="*80)

    print("\n📝 API 接口:")
    print("  GET    /api/hama-market/symbols/list     - 获取币种列表")
    print("  POST   /api/hama-market/symbols/add      - 添加币种")
    print("  PUT    /api/hama-market/symbols/update   - 更新币种")
    print("  DELETE /api/hama-market/symbols/delete   - 删除币种")
    print("  PUT    /api/hama-market/symbols/enable   - 启用/禁用币种")

    print("\n📝 下一步:")
    print("1. 启动后端服务: python run.py")
    print("2. 访问前端: http://localhost:8000/#/hama-market")
    print("3. 在币种管理页面添加/删除币种")


if __name__ == '__main__':
    main()
