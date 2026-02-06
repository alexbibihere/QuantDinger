"""
HAMA 数据健康检查服务

功能：
1. 定期检查 HAMA 监控列表中的数据完整性
2. 检测价格和状态是否缺失
3. 当数据异常时触发 longLogic 重启逻辑
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HAMAHealthChecker:
    """HAMA 数据健康检查器"""

    def __init__(self, check_interval: int = 60, failure_threshold: int = 3):
        """
        初始化健康检查器

        Args:
            check_interval: 检查间隔（秒），默认60秒
            failure_threshold: 失败阈值，连续N次失败才触发重启，默认3次
        """
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.failure_count = {}  # {symbol: count}
        self.last_check_time = None
        self.is_running = False
        self.check_thread = None

        # 回调函数
        self.on_failure_callback = None

        logger.info(f"HAMA健康检查器初始化: 间隔={check_interval}秒, 阈值={failure_threshold}次")

    def set_failure_callback(self, callback):
        """设置失败回调函数"""
        self.on_failure_callback = callback
        logger.info("已设置HAMA健康检查失败回调函数")

    def check_hama_data(self, watchlist: List[Dict]) -> Dict[str, any]:
        """
        检查 HAMA 数据完整性

        Args:
            watchlist: HAMA 监控列表

        Returns:
            检查结果: {
                'healthy': bool,
                'symbols': {
                    'ETHUSDT': {'has_price': bool, 'has_status': bool, 'valid': bool},
                    ...
                },
                'failed_symbols': List[str]
            }
        """
        result = {
            'healthy': True,
            'symbols': {},
            'failed_symbols': [],
            'check_time': datetime.now().isoformat()
        }

        for item in watchlist:
            symbol = item.get('symbol', '')
            price = item.get('current_price')
            status = item.get('hama_color') or item.get('hama_trend')

            # 检查价格是否存在且有效
            has_price = price is not None and price != '' and price != 'None'

            # 检查状态是否存在且有效
            valid_statuses = ['green', 'red', 'gray', 'up', 'down', 'neutral']
            has_status = status and status.lower() in valid_statuses

            # 综合判断
            is_valid = has_price and has_status

            result['symbols'][symbol] = {
                'has_price': has_price,
                'has_status': has_status,
                'valid': is_valid,
                'price': price,
                'status': status
            }

            if not is_valid:
                result['healthy'] = False
                result['failed_symbols'].append(symbol)

        return result

    def process_check_result(self, check_result: Dict[str, any]):
        """
        处理检查结果

        Args:
            check_result: 检查结果
        """
        failed_symbols = check_result['failed_symbols']

        if not failed_symbols:
            # 所有币种都正常，重置失败计数
            self.failure_count.clear()
            logger.info("✅ HAMA 数据健康检查通过")
            return

        # 处理失败的币种
        for symbol in failed_symbols:
            if symbol not in self.failure_count:
                self.failure_count[symbol] = 0

            self.failure_count[symbol] += 1

            symbol_info = check_result['symbols'][symbol]
            logger.warning(
                f"⚠️ {symbol} 数据异常 "
                f"(价格={symbol_info['price']}, 状态={symbol_info['status']}), "
                f"失败次数: {self.failure_count[symbol]}/{self.failure_threshold}"
            )

            # 达到阈值，触发失败回调
            if self.failure_count[symbol] >= self.failure_threshold:
                logger.error(f"❌ {symbol} 连续失败 {self.failure_count[symbol]} 次，触发重启逻辑")

                # 重置该币种的失败计数
                self.failure_count[symbol] = 0

                # 触发回调
                if self.on_failure_callback:
                    try:
                        self.on_failure_callback(symbol, check_result)
                    except Exception as e:
                        logger.error(f"执行失败回调函数出错: {e}", exc_info=True)

    def check_once(self, get_watchlist_func):
        """
        执行一次健康检查

        Args:
            get_watchlist_func: 获取监控列表的函数
        """
        try:
            self.last_check_time = datetime.now()

            # 获取监控列表
            watchlist = get_watchlist_func()

            if not watchlist:
                logger.warning("获取 HAMA 监控列表为空")
                return

            # 执行健康检查
            check_result = self.check_hama_data(watchlist)

            # 处理检查结果
            self.process_check_result(check_result)

            logger.info(f"健康检查完成: {len(watchlist)} 个币种, "
                       f"健康: {check_result['healthy']}, "
                       f"失败: {len(check_result['failed_symbols'])}")

        except Exception as e:
            logger.error(f"健康检查执行失败: {e}", exc_info=True)

    def start(self, get_watchlist_func):
        """
        启动健康检查线程

        Args:
            get_watchlist_func: 获取监控列表的函数
        """
        if self.is_running:
            logger.warning("健康检查已在运行中")
            return

        self.is_running = True

        def check_loop():
            logger.info(f"🚀 HAMA 健康检查线程已启动 (间隔: {self.check_interval}秒)")

            while self.is_running:
                try:
                    self.check_once(get_watchlist_func)
                except Exception as e:
                    logger.error(f"健康检查出错: {e}", exc_info=True)

                # 等待下一次检查
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)

            logger.info("HAMA 健康检查线程已停止")

        self.check_thread = threading.Thread(target=check_loop, daemon=True)
        self.check_thread.start()

        logger.info("✅ HAMA 健康检查器已启动")

    def stop(self):
        """停止健康检查"""
        if not self.is_running:
            return

        logger.info("正在停止 HAMA 健康检查...")
        self.is_running = False

        if self.check_thread:
            self.check_thread.join(timeout=5)

        logger.info("✅ HAMA 健康检查已停止")

    def get_status(self) -> Dict:
        """获取健康检查状态"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'failure_threshold': self.failure_threshold,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'failure_count': self.failure_count.copy()
        }
