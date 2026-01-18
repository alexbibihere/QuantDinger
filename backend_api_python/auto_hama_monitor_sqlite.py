#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地自动监控脚本（SQLite 版本）
定期从 TradingView 获取 HAMA 数据并保存到 SQLite 数据库
"""
import sys
import os
import time
import sqlite3
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_sqlite_connection():
    """获取 SQLite 数据库连接"""
    try:
        # 数据库路径
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'quantdinger.db')

        # 确保 data 目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        print(f"✅ SQLite 连接成功: {db_path}")

        # 初始化表
        init_database(conn)

        return conn
    except Exception as e:
        print(f"⚠️  SQLite 连接失败: {e}")
        return None


def init_database(conn):
    """初始化数据库表"""
    try:
        cursor = conn.cursor()

        # 创建 HAMA 监控缓存表
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

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hama_cache_monitored
            ON hama_monitor_cache(monitored_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hama_cache_symbol
            ON hama_monitor_cache(symbol)
        ''')

        conn.commit()
        print("✅ 数据库表初始化成功")
    except Exception as e:
        print(f"⚠️  数据库表初始化失败: {e}")


class SQLiteHamaMonitor:
    """SQLite HAMA 监控器适配器"""

    def __init__(self, conn):
        self.conn = conn
        self.ocr_extractor = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化 OCR 提取器"""
        try:
            from app.services.hama_ocr_extractor import HAMAOCRExtractor
            self.ocr_extractor = HAMAOCRExtractor(ocr_engine='rapidocr')
            print("✅ OCR 提取器初始化成功")
        except Exception as e:
            print(f"❌ OCR 提取器初始化失败: {e}")

    def get_cached_hama(self, symbol: str):
        """从数据库获取缓存的 HAMA 数据"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM hama_monitor_cache
                WHERE symbol = ?
                ORDER BY monitored_at DESC
                LIMIT 1
            ''', (symbol,))

            row = cursor.fetchone()

            if row:
                return {
                    'hama_trend': row['hama_trend'],
                    'hama_color': row['hama_color'],
                    'hama_value': float(row['hama_value']) if row['hama_value'] else None,
                    'price': float(row['price']) if row['price'] else None,
                    'cached_at': row['monitored_at'],
                    'cache_source': 'sqlite_brave_monitor'
                }

            return None
        except Exception as e:
            print(f"❌ 获取缓存失败 {symbol}: {e}")
            return None

    def set_cached_hama(self, symbol: str, hama_data: dict):
        """保存 HAMA 数据到数据库"""
        try:
            cursor = self.conn.cursor()

            # 使用 INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO hama_monitor_cache
                (symbol, hama_trend, hama_color, hama_value, price, ocr_text, monitored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                hama_data.get('hama_trend'),
                hama_data.get('hama_color'),
                hama_data.get('hama_value'),
                hama_data.get('price'),
                hama_data.get('ocr_text', ''),
                datetime.now()
            ))

            self.conn.commit()
            print(f"✅ {symbol} HAMA 数据已保存到 SQLite")
            return True
        except Exception as e:
            print(f"❌ 保存数据失败 {symbol}: {e}")
            return False

    def monitor_symbol(self, symbol: str, browser_type: str = 'chromium'):
        """监控单个币种"""
        if not self.ocr_extractor:
            print("❌ OCR 提取器未初始化")
            return None

        try:
            print(f"🔄 正在监控 {symbol}...")

            # 构建 TradingView 图表 URL
            chart_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}&interval=15"
            screenshot_path = f"hama_brave_{symbol}_{int(time.time())}.png"

            # 步骤 1: 截图
            print(f"   正在截图...")
            result_path = self.ocr_extractor.capture_chart(chart_url, screenshot_path)

            if not result_path:
                print(f"   ❌ {symbol} 截图失败")
                return None

            # 步骤 2: OCR 识别
            print(f"   正在 OCR 识别...")
            hama_data = self.ocr_extractor.extract_hama_with_ocr(result_path)

            # 清理截图
            try:
                if os.path.exists(result_path):
                    os.remove(result_path)
            except:
                pass

            if hama_data:
                # 添加元数据
                hama_data['symbol'] = symbol
                hama_data['monitored_at'] = datetime.now().isoformat()
                hama_data['timestamp'] = int(time.time() * 1000)

                # 保存到数据库
                self.set_cached_hama(symbol, hama_data)

                print(f"   ✅ {symbol} HAMA 状态: {hama_data.get('hama_color', 'unknown')} ({hama_data.get('hama_trend', 'unknown')})")
                return hama_data
            else:
                print(f"   ❌ {symbol} OCR 识别失败")
                return None

        except Exception as e:
            print(f"❌ 监控 {symbol} 失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def monitor_batch(self, symbols: list, browser_type: str = 'chromium'):
        """批量监控多个币种"""
        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        for i, symbol in enumerate(symbols):
            print(f"\n处理 {i+1}/{len(symbols)}: {symbol}")

            hama_data = self.monitor_symbol(symbol, browser_type)

            if hama_data:
                results['success'] += 1
                results['symbols'][symbol] = {
                    'success': True,
                    'data': hama_data
                }
            else:
                results['failed'] += 1
                results['symbols'][symbol] = {
                    'success': False
                }

        return results

    def get_stats(self):
        """获取统计信息"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            count = cursor.fetchone()[0]

            return {
                'cached_symbols': count,
                'storage_type': 'SQLite'
            }
        except:
            return {'cached_symbols': 0, 'storage_type': 'SQLite'}


def auto_monitor():
    """自动监控主函数"""
    print("\n" + "="*80)
    print("🤖 HAMA 自动监控服务（SQLite 存储）")
    print("="*80)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 配置
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT']
    interval = 600  # 10分钟
    browser_type = 'chromium'

    print(f"\n📋 配置:")
    print(f"  监控币种: {', '.join(symbols)}")
    print(f"  监控间隔: {interval}秒 ({interval//60}分钟)")
    print(f"  浏览器类型: {browser_type}")
    print(f"  存储方式: SQLite 数据库")

    # 初始化 SQLite 连接
    print("\n正在连接 SQLite...")
    conn = get_sqlite_connection()

    if not conn:
        print("\n❌ 无法连接数据库，退出")
        return

    # 初始化监控器
    print("\n正在初始化 Brave 监控器...")
    monitor = SQLiteHamaMonitor(conn)

    if not monitor.ocr_extractor:
        print("❌ OCR 提取器未初始化，无法继续")
        return

    print("✅ 监控器初始化成功")

    # 显示数据库统计
    stats = monitor.get_stats()
    print(f"  当前缓存: {stats['cached_symbols']} 个币种")

    # 监控循环
    print("\n" + "="*80)
    print("🔄 开始监控循环（按 Ctrl+C 停止）")
    print("="*80)

    round_num = 0

    try:
        while True:
            round_num += 1
            print(f"\n{'='*80}")
            print(f"第 {round_num} 轮监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")

            # 批量监控
            results = monitor.monitor_batch(symbols, browser_type)

            # 显示结果
            print(f"\n📊 本轮结果:")
            print(f"  总数: {results['total']}")
            print(f"  成功: {results['success']}")
            print(f"  失败: {results['failed']}")

            if results['success'] > 0:
                print(f"\n✅ 成功的币种:")
                for symbol, data in results['symbols'].items():
                    if data.get('success'):
                        hama = data.get('data', {})
                        trend = hama.get('hama_trend', 'unknown')
                        color = hama.get('hama_color', 'unknown')
                        value = hama.get('hama_value', 0)
                        print(f"  - {symbol}: {trend} / {color} / {value}")

            # 检查数据库缓存
            stats = monitor.get_stats()
            print(f"\n💾 数据库缓存: {stats['cached_symbols']} 个币种")

            # 等待下一轮
            print(f"\n⏰ 等待 {interval} 秒后进行下一轮...")
            print(f"   (当前时间: {datetime.now().strftime('%H:%M:%S')})")
            print(f"   (下一轮: {datetime.fromtimestamp(time.time() + interval).strftime('%H:%M:%S')})")

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("⏸️  监控已停止")
        print("="*80)
        print(f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总轮数: {round_num}")

        # 显示统计
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, hama_trend, hama_color, monitored_at
                FROM hama_monitor_cache
                ORDER BY monitored_at DESC
            ''')
            cached_symbols = cursor.fetchall()

            if cached_symbols:
                print(f"\n💾 数据库缓存 ({len(cached_symbols)} 个币种):")
                for row in cached_symbols:
                    print(f"  - {row[0]}: {row[1]} / {row[2]} / {row[3]}")

            cursor.close()
        except Exception as e:
            print(f"查询缓存失败: {e}")

        finally:
            conn.close()

    except Exception as e:
        print(f"\n❌ 监控出错: {e}")
        import traceback
        traceback.print_exc()
        conn.close()


if __name__ == '__main__':
    auto_monitor()
