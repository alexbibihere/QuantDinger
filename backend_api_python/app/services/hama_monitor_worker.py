#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 监控 Worker 集成服务
作为后台线程运行,自动监控币种并保存到数据库
"""
import threading
import time
import logging
import os
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)


class HamaMonitorWorker:
    """HAMA 监控 Worker 服务"""

    def __init__(self):
        self.is_running = False
        self.worker_thread = None
        self.monitor = None
        # 从环境变量读取监控币种列表
        symbols_str = os.getenv('BRAVE_MONITOR_SYMBOLS', '')
        self.symbols = [s.strip() for s in symbols_str.split(',') if s.strip()] if symbols_str else ['ETHUSDT']
        # 从环境变量读取监控间隔
        self.interval = int(os.getenv('BRAVE_MONITOR_INTERVAL', '3600'))
        # 从环境变量读取浏览器类型，默认使用 brave
        self.browser_type = os.getenv('BRAVE_MONITOR_BROWSER_TYPE', 'brave')

    def start(self):
        """启动监控 Worker"""
        if self.is_running:
            logger.warning("HAMA 监控 Worker 已在运行")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._run, daemon=True, name='HamaMonitorWorker')
        self.worker_thread.start()
        logger.info("✅ HAMA 监控 Worker 已启动")

    def stop(self):
        """停止监控 Worker"""
        if not self.is_running:
            return

        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("⏸️  HAMA 监控 Worker 已停止")

    def _run(self):
        """Worker 主循环"""
        logger.info("🚀 HAMA 监控 Worker 开始运行")

        # 初始化监控器
        try:
            from app.services.hama_brave_monitor import get_brave_monitor
            self.monitor = get_brave_monitor(use_sqlite=True)
            logger.info("✅ 监控器初始化成功")
        except Exception as e:
            logger.error(f"❌ 监控器初始化失败: {e}")
            self.is_running = False
            return

        # 立即开始监控，无需等待
        logger.info("🚀 立即开始首次监控...")

        # 监控循环
        round_num = 0
        while self.is_running:
            try:
                round_num += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"第 {round_num} 轮监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                # 批量监控
                success_count = 0
                failed_count = 0

                for i, symbol in enumerate(self.symbols):
                    if not self.is_running:
                        break

                    logger.info(f"处理 {i+1}/{len(self.symbols)}: {symbol}")

                    try:
                        result = self.monitor.monitor_symbol(symbol, 15, self.browser_type)

                        if result:
                            success_count += 1
                            logger.info(f"  ✅ {symbol}: {result.get('hama_color')} ({result.get('hama_trend')})")
                        else:
                            failed_count += 1
                            logger.warning(f"  ❌ {symbol}: 监控失败")

                    except Exception as e:
                        logger.error(f"  ❌ {symbol}: 出错 - {e}")
                        failed_count += 1

                    # 避免请求过快
                    time.sleep(2)

                # 显示统计
                logger.info(f"\n📊 本轮结果:")
                logger.info(f"  成功: {success_count}/{len(self.symbols)}")
                logger.info(f"  失败: {failed_count}/{len(self.symbols)}")

                # 获取数据库统计
                try:
                    stats = self.monitor.get_stats()
                    logger.info(f"  数据库缓存: {stats.get('cached_symbols', 0)} 个币种")
                except:
                    pass

                # 等待下一轮
                if self.is_running:
                    logger.info(f"\n⏰ 等待 {self.interval} 秒后进行下一轮...")
                    for _ in range(self.interval):
                        if not self.is_running:
                            break
                        time.sleep(1)

            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                # 出错后等待1分钟再重试
                for _ in range(60):
                    if not self.is_running:
                        break
                    time.sleep(1)

        logger.info("🛑 HAMA 监控 Worker 已停止")

    def get_status(self):
        """获取 Worker 状态"""
        status = {
            'is_running': self.is_running,
            'symbols': self.symbols,
            'interval': self.interval,
            'browser_type': self.browser_type
        }

        if self.monitor:
            try:
                stats = self.monitor.get_stats()
                status['cached_symbols'] = stats.get('cached_symbols', 0)
                status['storage_type'] = stats.get('storage_type', 'Unknown')
            except:
                status['cached_symbols'] = 0
                status['storage_type'] = 'Unknown'

        return status

    def monitor_now(self, symbols: List[str] = None):
        """立即监控指定币种"""
        if not self.monitor:
            logger.error("监控器未初始化")
            return None

        if symbols is None:
            symbols = self.symbols

        logger.info(f"🔄 立即监控 {len(symbols)} 个币种...")

        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        for symbol in symbols:
            try:
                result = self.monitor.monitor_symbol(symbol, self.browser_type)

                if result:
                    results['success'] += 1
                    results['symbols'][symbol] = {
                        'success': True,
                        'data': result
                    }
                else:
                    results['failed'] += 1
                    results['symbols'][symbol] = {
                        'success': False
                    }
            except Exception as e:
                logger.error(f"监控 {symbol} 失败: {e}")
                results['failed'] += 1
                results['symbols'][symbol] = {
                    'success': False,
                    'error': str(e)
                }

        logger.info(f"✅ 立即监控完成: 成功 {results['success']}/{results['total']}")
        return results


# 全局单例
_hama_monitor_worker = None


def get_hama_monitor_worker():
    """获取 HAMA 监控 Worker 单例"""
    global _hama_monitor_worker
    if _hama_monitor_worker is None:
        _hama_monitor_worker = HamaMonitorWorker()
    return _hama_monitor_worker
