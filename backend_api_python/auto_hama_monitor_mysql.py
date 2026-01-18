#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地自动监控脚本（MySQL 版本）
定期从 TradingView 获取 HAMA 数据并保存到 MySQL 数据库
"""
import sys
import os
import time
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_mysql_connection():
    """获取 MySQL 数据库连接"""
    try:
        import pymysql
        from app.config.database import get_db_connection

        conn = get_db_connection()
        print("✅ MySQL 连接成功")
        return conn
    except Exception as e:
        print(f"⚠️  MySQL 连接失败: {e}")
        print("  将使用内存模式（数据不会持久化）")
        return None


def auto_monitor():
    """自动监控主函数"""
    print("\n" + "="*80)
    print("🤖 HAMA 自动监控服务（MySQL 存储）")
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
    print(f"  存储方式: MySQL 数据库")

    # 导入模块
    try:
        from app.services.hama_brave_monitor_mysql import HamaBraveMonitor
        print("\n✅ 监控器模块导入成功（MySQL 版本）")
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return

    # 初始化 MySQL 连接
    print("\n正在连接 MySQL...")
    db_client = get_mysql_connection()

    # 初始化监控器
    print("\n正在初始化 Brave 监控器...")
    monitor = HamaBraveMonitor(db_client=db_client, cache_ttl=900, enable_email=True)

    if not monitor.ocr_extractor:
        print("❌ OCR 提取器未初始化，无法继续")
        return

    print("✅ 监控器初始化成功")
    print(f"  可用: {monitor.ocr_extractor is not None}")
    print(f"  存储: {'MySQL' if db_client else '内存'}")
    print(f"  邮件通知: {'✅ 已启用' if monitor.email_notifier else '❌ 未启用'}")

    # 显示数据库统计
    if db_client:
        try:
            cursor = db_client.cursor()
            cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
            count = cursor.fetchone()[0]
            print(f"  当前缓存: {count} 个币种")
            cursor.close()
        except:
            pass

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
            if db_client:
                try:
                    cursor = db_client.cursor()
                    cursor.execute("SELECT COUNT(*) FROM hama_monitor_cache")
                    cached_count = cursor.fetchone()[0]
                    print(f"\n💾 数据库缓存: {cached_count} 个币种")
                    cursor.close()
                except:
                    pass

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
        if db_client:
            try:
                cursor = db_client.cursor()

                # 缓存的币种
                cursor.execute("SELECT symbol, hama_trend, hama_color, monitored_at FROM hama_monitor_cache ORDER BY monitored_at DESC")
                cached_symbols = cursor.fetchall()

                if cached_symbols:
                    print(f"\n💾 数据库缓存 ({len(cached_symbols)} 个币种):")
                    for row in cached_symbols:
                        print(f"  - {row[0]}: {row[1]} / {row[2]} / {row[3]}")

                cursor.close()
            except:
                pass

    except Exception as e:
        print(f"\n❌ 监控出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    auto_monitor()
