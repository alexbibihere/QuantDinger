#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动 HAMA 监控服务
使用 Brave 浏览器监控 TradingView 图表并自动识别 HAMA 指标
"""
import sys
import os
import time
import io

# Windows 控制台编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend_api_python'))

def main():
    print("\n" + "="*80)
    print("🤖 HAMA 监控服务启动")
    print("="*80)
    print(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 配置
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT']
    interval = 600  # 10分钟

    print("📋 配置:")
    print(f"  监控币种: {', '.join(symbols)}")
    print(f"  监控间隔: {interval}秒 ({interval//60}分钟)")
    print(f"  浏览器: Brave (无头模式)")
    print(f"  OCR引擎: PaddleOCR")
    print(f"  存储: SQLite 数据库")
    print()
    print("⚠️  按 Ctrl+C 停止监控")
    print("="*80)
    print()

    try:
        # 导入监控模块
        from app.services.hama_brave_monitor_mysql import get_brave_monitor

        # 初始化监控器（不使用数据库连接，监控器会自动初始化）
        print("🔧 正在初始化监控器...")
        monitor = get_brave_monitor(db_client=None, cache_ttl=900)
        print("✅ 监控器初始化成功")
        print()

        # 开始监控
        print("🚀 开始监控...")
        print()
        monitor.start_monitoring(symbols=symbols, interval=interval, browser_type='brave')

    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
