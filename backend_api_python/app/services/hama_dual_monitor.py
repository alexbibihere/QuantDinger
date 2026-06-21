#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 双币种监控服务
专门监控 BTCUSDT 和 ETHUSDT，自动检测趋势变化并发送邮件通知
"""
import threading
import time
import os
from typing import List, Dict, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HamaDualMonitor:
    """HAMA 双币种监控器"""

    def __init__(self):
        self.is_running = False
        self.worker_thread = None
        self.monitor = None
        self.email_notifier = None

        # 监控币种列表（核心币种）
        self.symbols = ['BTCUSDT', 'ETHUSDT']

        # 从环境变量读取监控间隔
        self.interval = int(os.getenv('DUAL_MONITOR_INTERVAL', '300'))  # 默认5分钟

        # 监控方法：browseract 或 brave
        self.monitor_method = os.getenv('DUAL_MONITOR_METHOD', 'browseract')

        logger.info(f"HAMA双币种监控器初始化完成，监控方法: {self.monitor_method}")

    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("HAMA双币种监控已在运行")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._run, daemon=True, name='HamaDualMonitor')
        self.worker_thread.start()
        logger.info("✅ HAMA双币种监控已启动")

    def stop(self):
        """停止监控"""
        if not self.is_running:
            return

        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("⏸️  HAMA双币种监控已停止")

    def _init_monitor(self):
        """初始化监控器"""
        try:
            if self.monitor_method == 'browseract':
                from app.services.hama_browseract_monitor import get_browseract_monitor
                self.monitor = get_browseract_monitor(use_sqlite=True)
                logger.info("✅ 使用 BrowserAct 监控器")
            else:
                from app.services.hama_brave_monitor import get_brave_monitor
                self.monitor = get_brave_monitor(use_sqlite=True)
                logger.info("✅ 使用 Brave 监控器")

            # 初始化邮件通知器
            from app.services.hama_email_notifier import get_hama_email_notifier
            self.email_notifier = get_hama_email_notifier()
            logger.info("✅ 邮件通知器初始化成功")

            return True

        except Exception as e:
            logger.error(f"❌ 监控器初始化失败: {e}")
            return False

    def _run(self):
        """监控主循环"""
        logger.info("🚀 HAMA双币种监控开始运行")

        # 初始化监控器
        if not self._init_monitor():
            self.is_running = False
            return

        # 立即开始首次监控
        logger.info("🚀 立即开始首次监控...")

        round_num = 0
        while self.is_running:
            try:
                round_num += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"第 {round_num} 轮监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                # 监控所有币种
                success_count = 0
                failed_count = 0
                results = {}

                for i, symbol in enumerate(self.symbols):
                    if not self.is_running:
                        break

                    logger.info(f"处理 {i+1}/{len(self.symbols)}: {symbol}")

                    try:
                        # 根据监控器类型调用不同的方法
                        if self.monitor_method == 'browseract':
                            result = self.monitor.monitor_single_symbol(symbol, '15m', check_email=True)
                        else:
                            result = self.monitor.monitor_symbol(symbol, 15, 'brave')

                        if result:
                            success_count += 1
                            results[symbol] = result
                            logger.info(f"  ✅ {symbol}: {result.get('hama_color')} ({result.get('hama_trend')})")
                        else:
                            failed_count += 1
                            logger.warning(f"  ❌ {symbol}: 监控失败")

                    except Exception as e:
                        logger.error(f"  ❌ {symbol}: 出错 - {e}")
                        failed_count += 1

                # 显示统计
                logger.info(f"\n📊 本轮结果:")
                logger.info(f"  成功: {success_count}/{len(self.symbols)}")
                logger.info(f"  失败: {failed_count}/{len(self.symbols)}")

                # 显示趋势摘要
                self._print_trend_summary(results)

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

        logger.info("🛑 HAMA双币种监控已停止")

    def _print_trend_summary(self, results: Dict[str, Any]):
        """打印趋势摘要"""
        logger.info(f"\n{'='*60}")
        logger.info("📈 趋势摘要")
        logger.info(f"{'='*60}")

        for symbol, data in results.items():
            color = data.get('hama_color', 'gray')
            trend = data.get('hama_trend', 'unknown')
            price = data.get('price', 0)

            # 颜色标记
            color_emoji = {
                'green': '🟢',
                'red': '🔴',
                'gray': '⚪'
            }.get(color, '⚪')

            logger.info(f"  {color_emoji} {symbol}: {color} ({trend}) | 价格: ${price:.2f}")

        logger.info(f"{'='*60}")

    def monitor_now(self) -> Dict[str, Any]:
        """立即监控一次"""
        if not self.monitor:
            if not self._init_monitor():
                return {'success': False, 'error': '监控器初始化失败'}

        logger.info(f"🔄 立即监控 {len(self.symbols)} 个币种...")

        results = {
            'total': len(self.symbols),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        for symbol in self.symbols:
            try:
                if self.monitor_method == 'browseract':
                    result = self.monitor.monitor_single_symbol(symbol, '15m', check_email=True)
                else:
                    result = self.monitor.monitor_symbol(symbol, 15, 'brave')

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

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        status = {
            'is_running': self.is_running,
            'symbols': self.symbols,
            'interval': self.interval,
            'monitor_method': self.monitor_method,
            'last_check': None
        }

        if self.monitor:
            try:
                monitor_status = self.monitor.get_status()
                status['monitor_status'] = monitor_status
            except:
                pass

        return status


# 全局单例
_dual_monitor_instance = None


def get_dual_monitor() -> HamaDualMonitor:
    """获取双币种监控器单例"""
    global _dual_monitor_instance
    if _dual_monitor_instance is None:
        _dual_monitor_instance = HamaDualMonitor()
    return _dual_monitor_instance


def start_dual_monitor():
    """启动双币种监控"""
    monitor = get_dual_monitor()
    monitor.start()
    return monitor


def stop_dual_monitor():
    """停止双币种监控"""
    monitor = get_dual_monitor()
    monitor.stop()
