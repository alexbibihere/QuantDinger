"""
HAMA 数据健康检查服务

功能：
1. 定期检查 HAMA 监控列表中的数据完整性
2. 检测价格和状态是否缺失
3. 检测缓存状态与截图状态是否一致
4. 当数据异常时触发 longLogic 重启逻辑
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
        self.on_refresh_callback = None

        logger.info(f"HAMA健康检查器初始化: 间隔={check_interval}秒, 阈值={failure_threshold}次")

    def set_failure_callback(self, callback):
        """设置失败回调函数"""
        self.on_failure_callback = callback
        logger.info("已设置HAMA健康检查失败回调函数")

    def set_refresh_callback(self, callback):
        """设置数据刷新回调函数"""
        self.on_refresh_callback = callback
        logger.info("已设置HAMA数据刷新回调函数")

    def set_brave_monitor(self, brave_monitor):
        """设置 Brave 监控器引用（用于状态一致性检查）"""
        self.brave_monitor = brave_monitor
        logger.info("已设置 Brave 监控器引用")

    def check_hama_data(self, watchlist: List[Dict], check_screenshots: bool = True, max_screenshot_age_minutes: int = 30) -> Dict[str, any]:
        """
        检查 HAMA 数据完整性

        Args:
            watchlist: HAMA 监控列表
            check_screenshots: 是否检查截图状态一致性，默认 True
            max_screenshot_age_minutes: 截图最大有效期（分钟），超过此时间强制刷新，默认30分钟

        Returns:
            检查结果: {
                'healthy': bool,
                'symbols': {
                    'ETHUSDT': {'has_price': bool, 'has_status': bool, 'valid': bool, 'screenshot_mismatch': bool},
                    ...
                },
                'failed_symbols': List[str],
                'mismatched_symbols': List[str]
            }
        """
        result = {
            'healthy': True,
            'symbols': {},
            'failed_symbols': [],
            'mismatched_symbols': [],
            'check_time': datetime.now().isoformat()
        }

        for item in watchlist:
            symbol = item.get('symbol', '')
            # 支持多种字段名（price 或 current_price）
            price = item.get('price') or item.get('current_price')
            status = item.get('hama_color') or item.get('hama_trend')

            # 检查价格是否存在且有效
            has_price = price is not None and price != '' and price != 'None'

            # 检查状态是否存在且有效
            valid_statuses = ['green', 'red', 'gray', 'up', 'down', 'neutral']
            has_status = status and status.lower() in valid_statuses

            # 检查蜡烛/MA状态和布林带状态是否存在（新增）
            candle_ma_status = item.get('candle_ma_status')
            bollinger_status = item.get('bollinger_status')
            has_candle_ma = candle_ma_status is not None and candle_ma_status != '' and candle_ma_status != 'None'
            has_bollinger = bollinger_status is not None and bollinger_status != '' and bollinger_status != 'None'

            # 综合判断 - 只检查价格和状态，不强制要求蜡烛/MA状态
            # 放宽条件以减少不必要的重新截图
            is_valid = has_price and has_status

            # 如果缺少蜡烛/MA状态，记录警告
            if not has_candle_ma:
                logger.warning(f"  ⚠️ {symbol} 蜡烛/MA状态缺失: {candle_ma_status}")

            screenshot_mismatch = False

            # 检查截图状态一致性（如果启用）
            if check_screenshots and has_status and hasattr(self, 'brave_monitor'):
                try:
                    # 通过已有截图进行 OCR 提取状态，同时返回截图时间
                    screenshot_status, screenshot_age_minutes = self._ocr_existing_screenshot(symbol)

                    # 判断是否需要刷新：
                    # 1. 状态不一致
                    # 2. 截图过期（超过 max_screenshot_age_minutes）
                    should_refresh = False
                    new_status_from_refresh = None

                    if screenshot_status:
                        if screenshot_status.lower() != status.lower():
                            screenshot_mismatch = True
                            should_refresh = True
                            logger.warning(
                                f"🔍 {symbol} 状态不一致: "
                                f"缓存={status}, 截图={screenshot_status}"
                            )
                        elif screenshot_age_minutes and screenshot_age_minutes > max_screenshot_age_minutes:
                            screenshot_mismatch = True
                            should_refresh = True
                            logger.info(
                                f"⏰ {symbol} 截图过期: "
                                f"{screenshot_age_minutes:.1f}分钟前 > {max_screenshot_age_minutes}分钟阈值"
                            )
                    else:
                        # OCR 失败或没有截图，也应该刷新
                        should_refresh = True
                        logger.info(f"  ⚠️ {symbol} 无法 OCR 已有截图，触发刷新")

                    # 如果需要刷新，调用验证方法（force_refresh=True）并获取新状态
                    if should_refresh:
                        logger.info(f"  🔄 {symbol} 触发刷新（状态不一致或截图过期）")
                        new_status_from_refresh = self._verify_screenshot_status(symbol, force_refresh=True)

                        # 如果刷新成功且返回了新状态，更新 screenshot_status 以反映最新状态
                        if new_status_from_refresh:
                            screenshot_status = new_status_from_refresh
                            logger.info(f"  ✅ {symbol} 刷新后最新状态: {screenshot_status}")

                except Exception as e:
                    logger.debug(f"检查 {symbol} 截图状态失败: {e}")

            # 如果数据不完整（缺少蜡烛/MA状态等），触发重新截图
            if not is_valid and hasattr(self, 'brave_monitor') and self.brave_monitor:
                try:
                    logger.warning(f"  🔄 {symbol} 数据不完整，触发重新截图（has_price={has_price}, has_status={has_status}, has_candle_ma={has_candle_ma}）")
                    self._verify_screenshot_status(symbol, force_refresh=True)
                except Exception as e:
                    logger.error(f"  ❌ {symbol} 重新截图失败: {e}")

            result['symbols'][symbol] = {
                'has_price': has_price,
                'has_status': has_status,
                'valid': is_valid,
                'price': price,
                'status': status,
                'screenshot_mismatch': screenshot_mismatch
            }

            if not is_valid:
                result['healthy'] = False
                result['failed_symbols'].append(symbol)

            if screenshot_mismatch:
                result['healthy'] = False
                result['mismatched_symbols'].append(symbol)

        return result

    def _verify_screenshot_status(self, symbol: str, force_refresh: bool = False) -> Optional[str]:
        """
        通过截图验证 HAMA 状态

        逻辑：
        1. 首先读取本地已保存的截图，进行 OCR 提取状态
        2. 如果状态不一致且 force_refresh=True，则重新截图

        Args:
            symbol: 币种符号
            force_refresh: 是否在状态不一致时强制重新截图，默认 False（仅比对不刷新）

        Returns:
            从截图提取的实际状态，如果验证失败返回 None
        """
        if not self.brave_monitor:
            return None

        try:
            import os
            browser_type = os.getenv('BRAVE_MONITOR_BROWSER_TYPE', 'brave')

            # 第一步：从已有截图进行 OCR 提取状态
            screenshot_status = self._ocr_existing_screenshot(symbol)

            if screenshot_status:
                logger.debug(f"  📸 {symbol} 已有截图 OCR: 状态={screenshot_status}")
                return screenshot_status
            else:
                # 没有已有截图或 OCR 失败，如果 force_refresh 则重新截图
                if force_refresh:
                    logger.info(f"  🔄 {symbol} 没有有效截图，触发重新监控...")
                    result = self.brave_monitor.monitor_symbol(
                        symbol=symbol,
                        interval=15,
                        browser_type=browser_type
                    )

                    if result:
                        actual_status = result.get('hama_color') or result.get('hama_trend')
                        logger.info(f"  📸 {symbol} 重新截图完成: 状态={actual_status}")
                        return actual_status
                    else:
                        logger.warning(f"  ❌ {symbol} 重新监控失败: 无返回数据")
                        return None
                else:
                    logger.debug(f"  ⏭️ {symbol} 跳过重新截图（force_refresh=False）")
                    return None

        except Exception as e:
            logger.error(f"  ❌ {symbol} 截图验证异常: {e}")
            return None

    def _ocr_existing_screenshot(self, symbol: str) -> tuple:
        """
        对已有截图进行 OCR 提取 HAMA 状态

        Args:
            symbol: 币种符号

        Returns:
            (status, age_minutes) 元组
            - status: 从截图提取的状态，如果失败返回 None
            - age_minutes: 截图年龄（分钟），如果无法计算返回 None
        """
        try:
            import os
            import sqlite3

            # 从数据库查询截图路径和监控时间
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT screenshot_path, monitored_at
                FROM hama_monitor_cache
                WHERE symbol = ?
            ''', (symbol,))

            row = cursor.fetchone()
            conn.close()

            if not row or not row['screenshot_path']:
                logger.debug(f"  📁 {symbol} 没有已保存的截图")
                return (None, None)

            screenshot_path = row['screenshot_path']

            # 检查是否是相对路径，如果是则添加默认目录
            if not os.path.isabs(screenshot_path):
                # 默认截图保存在 app/screenshots/ 目录，需要返回到项目根目录
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_file_dir))
                screenshots_dir = os.path.join(project_root, 'app', 'screenshots')
                screenshot_path = os.path.join(screenshots_dir, screenshot_path)
                logger.debug(f"  📂 {symbol} 补全截图路径: {screenshot_path}")

            # 检查文件是否存在
            if not os.path.exists(screenshot_path):
                logger.warning(f"  ❌ {symbol} 截图文件不存在: {screenshot_path}")
                return (None, None)

            # 计算截图年龄
            monitored_at = row['monitored_at'] if 'monitored_at' in row.keys() else None
            age_minutes = None
            if monitored_at:
                from datetime import datetime
                if isinstance(monitored_at, str):
                    monitored_time = datetime.fromisoformat(monitored_at)
                else:
                    monitored_time = monitored_at
                age_seconds = (datetime.now() - monitored_time).total_seconds()
                age_minutes = age_seconds / 60

            # 使用 brave_monitor 的 OCR 提取器进行状态提取
            if not hasattr(self.brave_monitor, 'ocr_extractor') or not self.brave_monitor.ocr_extractor:
                logger.warning(f"  ⚠️ {symbol} OCR 提取器未初始化")
                return (None, age_minutes)

            # 读取截图并提取 HAMA 状态
            from PIL import Image
            image = Image.open(screenshot_path)

            # 调用 OCR 提取（提取 hama_color 和 hama_trend）
            ocr_result = self.brave_monitor.ocr_extractor.extract_hama_with_ocr(screenshot_path)

            if ocr_result:
                status = ocr_result.get('hama_color') or ocr_result.get('hama_trend')
                logger.debug(f"  🔍 {symbol} OCR 提取: {status} (截图: {age_minutes:.1f}分钟前)")
                return (status, age_minutes)
            else:
                logger.warning(f"  ⚠️ {symbol} OCR 提取失败")
                return (None, age_minutes)

        except Exception as e:
            logger.error(f"  ❌ {symbol} 已有截图 OCR 失败: {e}")
            return (None, None)

    def process_check_result(self, check_result: Dict[str, any]):
        """
        处理检查结果

        Args:
            check_result: 检查结果
        """
        failed_symbols = check_result['failed_symbols']
        mismatched_symbols = check_result.get('mismatched_symbols', [])

        # 处理状态不一致的币种（需要刷新）
        if mismatched_symbols:
            logger.info(f"🔄 检测到 {len(mismatched_symbols)} 个币种状态不一致，触发刷新")
            for symbol in mismatched_symbols:
                symbol_info = check_result['symbols'][symbol]
                logger.info(f"  🔄 {symbol}: 缓存={symbol_info['status']} vs 截图不一致，触发刷新")

                # 触发刷新回调
                if self.on_refresh_callback:
                    try:
                        self.on_refresh_callback(symbol, check_result)
                    except Exception as e:
                        logger.error(f"执行刷新回调函数出错: {e}", exc_info=True)

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
