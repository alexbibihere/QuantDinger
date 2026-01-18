#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建 OCR 识别缓存表
"""
import sqlite3
import os

def create_ocr_cache_table():
    """创建 OCR 识别缓存表"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ocr_cache.db')

    print(f"创建数据库: {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建 OCR 缓存表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            interval VARCHAR(10) DEFAULT '15m',
            trend VARCHAR(10),
            hama_color VARCHAR(10),
            candle_ma VARCHAR(10),
            contraction VARCHAR(10),
            price DECIMAL(20, 8),
            last_cross VARCHAR(20),
            screenshot_path TEXT,
            raw_text TEXT,
            ocr_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, interval)
        )
    ''')

    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ocr_cache_symbol_interval ON ocr_cache(symbol, interval)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ocr_cache_created_at ON ocr_cache(created_at DESC)
    ''')

    conn.commit()
    conn.close()

    print("✅ OCR 缓存表创建完成")

    return db_path


class ORCCache:
    """OCR 识别缓存管理"""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ocr_cache.db')

        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_connection(self):
        """获取数据库连接"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_ocr_result(self, symbol, interval, hama_data, screenshot_path):
        """保存 OCR 识别结果到数据库"""
        import json
        from datetime import datetime

        conn = self.get_connection()
        cursor = conn.cursor()

        # 转换 raw_text 为 JSON 字符串
        raw_text_json = json.dumps(hama_data.get('raw_text', []), ensure_ascii=False)

        # 检查是否存在相同记录（根据 symbol 和 interval）
        cursor.execute('''
            SELECT id FROM ocr_cache
            WHERE symbol = ? AND interval = ?
        ''', (symbol, interval))

        if cursor.fetchone():
            # 更新现有记录
            cursor.execute('''
                UPDATE ocr_cache SET
                trend = ?,
                hama_color = ?,
                candle_ma = ?,
                contraction = ?,
                price = ?,
                last_cross = ?,
                screenshot_path = ?,
                raw_text = ?,
                ocr_data = ?,
                updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ? AND interval = ?
            ''', (
                hama_data.get('trend'),
                hama_data.get('hama_color'),
                hama_data.get('candle_ma'),
                hama_data.get('contraction'),
                hama_data.get('price'),
                hama_data.get('last_cross'),
                screenshot_path,
                raw_text_json,
                json.dumps(hama_data, ensure_ascii=False),
                symbol,
                interval
            ))
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO ocr_cache (
                    symbol, interval,
                    trend, hama_color, candle_ma, contraction,
                    price, last_cross, screenshot_path, raw_text, ocr_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                interval,
                hama_data.get('trend'),
                hama_data.get('hama_color'),
                hama_data.get('candle_ma'),
                hama_cache.get('contraction'),
                hama_data.get('price'),
                hama_data.get('last_cross'),
                screenshot_path,
                raw_text_json,
                json.dumps(hama_data, ensure_ascii=False)
            ))

        conn.commit()
        conn.close()

        print(f"✅ OCR 结果已缓存: {symbol} ({interval})")

    def get_ocr_cache(self, symbol, interval='15m'):
        """从数据库获取 OCR 缓存"""
        import json

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM ocr_cache
            WHERE symbol = ? AND interval = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (symbol, interval))

        row = cursor.fetchone()
        conn.close()

        if row:
            # 转换 raw_text 回列表
            try:
                raw_text = json.loads(row['raw_text'])
            except:
                raw_text = []

            return {
                'symbol': row['symbol'],
                'interval': row['interval'],
                'trend': row['trend'],
                'hama_color': row['hama_color'],
                'candle_ma': row['candle_ma'],
                'contraction': row['contraction'],
                'price': row['price'],
                'last_cross': row['last_cross'],
                'screenshot': row['screenshot_path'],
                'raw_text': raw_text,
                'ocr_data': json.loads(row['ocr_data']) if row['ocr_data'] else None,
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        else:
            return None

    def list_cached_symbols(self):
        """列出所有缓存的币种"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT symbol
            FROM ocr_cache
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]

    def clear_old_cache(self, days=7):
        """清除超过指定天数的旧缓存"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM ocr_cache
            WHERE created_at < datetime('now', '-{} days'.format(days))
        ''')

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count


if __name__ == '__main__':
    # 创建 OCR 缓存表
    db_path = create_ocr_cache_table()

    # 创建实例
    cache = ORCCache(db_path)

    # 测试保存和读取
    test_data = {
        'symbol': 'BTCUSDT',
        'interval': '15m',
        'trend': 'UP',
        'hama_color': 'green',
        'candle_ma': 'above',
        'contraction': 'yes',
        'price': 3310.97,
        'last_cross': '涨（2026-01-1706',
        'screenshot': 'screenshot/hama_panel_20260118_131019.png',
        'raw_text': [['HAMA状态', 0.999], ['上涨趋势', 0.992]]
    }

    cache.save_ocr_result(
        symbol='BTCUSDT',
        interval='15m',
        hama_data=test_data,
        screenshot_path='screenshot/hama_panel_20260118_131019.png'
    )

    # 测试读取
    cached = cache.get_ocr_cache('BTCUSDT', '15m')
    if cached:
        print(f"\n✅ 测试读取缓存:")
        print(f"   币种: {cached['symbol']}")
        print(f"   趋势: {cached['trend']}")
        print(f"   价格: {cached['price']}")
        print(f"   时间: {cached['created_at']}")
        print(f"   截图: {cached['screenshot']}")
