#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA Brave 浏览器监控服务（MySQL 版本）
使用 Playwright + RapidOCR 从 TradingView 图表识别 HAMA 指标
数据存储到 MySQL 数据库
"""
import time
import json
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 全局单例
_brave_monitor_instance = None


def get_brave_monitor(db_client=None, cache_ttl: int = 900):
    """
    获取 Brave 监控器单例（MySQL 版本）

    Args:
        db_client: 数据库客户端
        cache_ttl: 缓存过期时间（秒）

    Returns:
        HamaBraveMonitor 实例
    """
    global _brave_monitor_instance

    if _brave_monitor_instance is None:
        _brave_monitor_instance = HamaBraveMonitor(db_client, cache_ttl)

    return _brave_monitor_instance


class HamaBraveMonitor:
    """HAMA Brave 浏览器监控器（MySQL 存储）"""

    def __init__(self, db_client=None, cache_ttl: int = 900, enable_email: bool = True):
        """
        初始化监控器

        Args:
            db_client: 数据库客户端
            cache_ttl: 缓存过期时间（秒）
            enable_email: 是否启用邮件通知
        """
        self.db_client = db_client
        self.cache_ttl = cache_ttl
        self.is_monitoring = False
        self.monitor_thread = None
        self.ocr_extractor = None
        self.enable_email = enable_email

        # 初始化 OCR 提取器
        self._init_ocr()

        # 初始化数据库表
        if db_client:
            self._init_db()

        # 初始化邮件通知器
        if self.enable_email:
            try:
                from app.services.hama_email_notifier import get_hama_email_notifier
                self.email_notifier = get_hama_email_notifier()
                logger.info("邮件通知器初始化成功")
            except Exception as e:
                logger.warning(f"邮件通知器初始化失败: {e}")
                self.email_notifier = None
        else:
            self.email_notifier = None

        # 记录上次状态（用于检测变化）
        self.last_states = {}  # {symbol: {'trend': ..., 'color': ..., 'value': ...}}

    def _init_ocr(self):
        """初始化 OCR 提取器"""
        try:
            from app.services.hama_ocr_extractor import HAMAOCRExtractor
            self.ocr_extractor = HAMAOCRExtractor(ocr_engine='rapidocr')
            logger.info("OCR 提取器初始化成功")
        except Exception as e:
            logger.error(f"OCR 提取器初始化失败: {e}")
            self.ocr_extractor = None

    def _init_db(self):
        """初始化数据库表"""
        try:
            # 创建表
            self.db_client.execute("""
                CREATE TABLE IF NOT EXISTS hama_monitor_cache (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    hama_trend VARCHAR(10),
                    hama_color VARCHAR(10),
                    hama_value DECIMAL(20, 8),
                    price DECIMAL(20, 8),
                    ocr_text TEXT,
                    screenshot_path VARCHAR(255),
                    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_symbol (symbol),
                    INDEX idx_monitored_at (monitored_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            logger.info("数据库表初始化成功")
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}")

    def get_cached_hama(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取缓存的 HAMA 数据

        Args:
            symbol: 币种符号

        Returns:
            HAMA 数据或 None
        """
        if not self.db_client:
            return None

        try:
            # 查询缓存
            result = self.db_client.execute(
                "SELECT * FROM hama_monitor_cache WHERE symbol = %s",
                (symbol,)
            ).fetchone()

            if result:
                # 转换为字典
                columns = ['id', 'symbol', 'hama_trend', 'hama_color', 'hama_value',
                          'price', 'ocr_text', 'screenshot_path', 'monitored_at',
                          'created_at', 'updated_at']
                row = dict(zip(columns, result))

                return {
                    'hama_trend': row['hama_trend'],
                    'hama_color': row['hama_color'],
                    'hama_value': float(row['hama_value']) if row['hama_value'] else None,
                    'price': float(row['price']) if row['price'] else None,
                    'cached_at': row['monitored_at'].isoformat() if row['monitored_at'] else None,
                    'cache_source': 'brave_browser_mysql'
                }

            return None
        except Exception as e:
            logger.error(f"获取缓存失败 {symbol}: {e}")
            return None

    def set_cached_hama(self, symbol: str, hama_data: Dict[str, Any]) -> bool:
        """
        设置币种的 HAMA 状态到数据库

        Args:
            symbol: 币种符号
            hama_data: HAMA 数据

        Returns:
            是否成功
        """
        if not self.db_client:
            logger.warning("数据库客户端未初始化，无法保存数据")
            return False

        try:
            # 使用 INSERT ... ON DUPLICATE KEY UPDATE
            self.db_client.execute("""
                INSERT INTO hama_monitor_cache
                (symbol, hama_trend, hama_color, hama_value, price, ocr_text, monitored_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    hama_trend = VALUES(hama_trend),
                    hama_color = VALUES(hama_color),
                    hama_value = VALUES(hama_value),
                    price = VALUES(price),
                    ocr_text = VALUES(ocr_text),
                    monitored_at = VALUES(monitored_at),
                    updated_at = CURRENT_TIMESTAMP
            """, (
                symbol,
                hama_data.get('hama_trend'),
                hama_data.get('hama_color'),
                hama_data.get('hama_value'),
                hama_data.get('price'),
                hama_data.get('ocr_text', ''),
                datetime.now()
            ))

            self.db_client.commit()
            logger.debug(f"{symbol} HAMA 数据已保存到数据库")
            return True
        except Exception as e:
            logger.error(f"保存数据失败 {symbol}: {e}")
            return False

    def monitor_symbol(self, symbol: str, browser_type: str = 'chromium') -> Optional[Dict[str, Any]]:
        """
        监控单个币种的 HAMA 状态

        Args:
            symbol: 币种符号
            browser_type: 浏览器类型 (chromium, firefox, webkit)

        Returns:
            HAMA 数据或 None
        """
        if not self.ocr_extractor:
            logger.error("OCR 提取器未初始化")
            return None

        try:
            logger.info(f"开始监控 {symbol}, 使用浏览器: {browser_type}")

            # 构建 TradingView 图表 URL
            chart_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}&interval=15"

            # 构建截图保存路径（保存到 app/screenshots/ 目录）
            import os
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            screenshot_dir = os.path.join(app_dir, 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

            screenshot_filename = f"hama_brave_{symbol}_{int(time.time())}.png"
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

            logger.info(f"截图保存路径: {screenshot_path}")

            # 步骤 1: 截图
            logger.debug(f"正在截图 {symbol}...")
            result_path = self.ocr_extractor.capture_chart(chart_url, screenshot_path)

            if not result_path:
                logger.warning(f"{symbol} 截图失败")
                return None

            # 步骤 2: OCR 识别
            logger.debug(f"正在 OCR 识别 {symbol}...")
            hama_data = self.ocr_extractor.extract_hama_with_ocr(result_path)

            # 不删除截图，保留用于前端展示
            logger.debug(f"截图已保留: {result_path}")

            if hama_data:
                # 添加元数据
                hama_data['symbol'] = symbol
                hama_data['monitored_at'] = datetime.now().isoformat()
                hama_data['timestamp'] = int(time.time() * 1000)

                # 添加截图路径（相对路径用于前端访问）
                hama_data['screenshot_path'] = screenshot_filename  # 只保存文件名
                hama_data['screenshot_absolute_path'] = result_path  # 保存完整路径用于调试

                # 检测趋势变化并发送邮件通知
                self._check_and_notify_trend(symbol, hama_data, screenshot_filename)

                # 保存到数据库
                self.set_cached_hama(symbol, hama_data)

                logger.info(f"{symbol} HAMA 状态: {hama_data.get('color', 'unknown')} ({hama_data.get('trend', 'unknown')})")
                return hama_data
            else:
                logger.warning(f"{symbol} OCR 识别失败")
                return None

        except Exception as e:
            logger.error(f"监控 {symbol} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _check_and_notify_trend(self, symbol: str, hama_data: Dict[str, Any], screenshot_filename: str):
        """
        检测趋势变化并发送邮件通知

        Args:
            symbol: 币种符号
            hama_data: HAMA 数据
            screenshot_filename: 截图文件名
        """
        if not self.email_notifier:
            return

        try:
            # 获取当前状态
            current_color = hama_data.get('color', '')
            current_trend = hama_data.get('trend', '')
            current_value = hama_data.get('value', 0)
            current_price = hama_data.get('price', 0)

            # 获取上次状态
            last_state = self.last_states.get(symbol, {})
            last_color = last_state.get('color', '')
            last_trend = last_state.get('trend', '')

            # 检测趋势形成条件
            should_notify = False
            cross_type = None
            notify_reason = ""

            # 条件1: 颜色变化（从无到有，或从红变绿，从绿变红）
            if last_color != current_color and current_color in ['green', 'red']:
                should_notify = True
                notify_reason = f"颜色变化: {last_color or '无'} → {current_color}"
                if current_color == 'green' and last_color == 'red':
                    cross_type = "cross_up"  # 金叉
                elif current_color == 'red' and last_color == 'green':
                    cross_type = "cross_down"  # 死叉

            # 条件2: 首次检测到明确的趋势
            if not last_color and current_color in ['green', 'red']:
                should_notify = True
                notify_reason = f"首次检测到趋势: {current_color}"

            # 条件3: 趋势方向变化
            if last_trend != current_trend and current_trend in ['up', 'down']:
                should_notify = True
                notify_reason = f"趋势变化: {last_trend or '无'} → {current_trend}"

            # 发送邮件通知
            if should_notify:
                logger.info(f"📧 {symbol} 检测到趋势变化: {notify_reason}，准备发送邮件...")

                # 构建截图 URL（假设前端有访问截图的路由）
                # 格式: http://localhost:5000/api/screenshots/filename
                screenshot_url = f"http://localhost:5000/api/screenshots/{screenshot_filename}"

                # 额外数据
                extra_data = {
                    "通知原因": notify_reason,
                    "监控时间": hama_data.get('monitored_at', ''),
                    "OCR 文本": hama_data.get('ocr_text', '')[:100]  # 只取前100字符
                }

                # 发送邮件
                success = self.email_notifier.notify_trend_formed(
                    symbol=symbol,
                    trend=current_trend,
                    hama_color=current_color,
                    hama_value=float(current_value) if current_value else 0.0,
                    price=float(current_price) if current_price else 0.0,
                    cross_type=cross_type,
                    screenshot_url=screenshot_url,
                    extra_data=extra_data
                )

                if success:
                    logger.info(f"✅ {symbol} 邮件通知发送成功")
                else:
                    logger.warning(f"⚠️ {symbol} 邮件通知发送失败")

            # 更新上次状态
            self.last_states[symbol] = {
                'color': current_color,
                'trend': current_trend,
                'value': current_value
            }

        except Exception as e:
            logger.error(f"趋势检测失败 {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def monitor_batch(self, symbols: List[str], browser_type: str = 'chromium') -> Dict[str, Any]:
        """
        批量监控多个币种

        Args:
            symbols: 币种列表
            browser_type: 浏览器类型

        Returns:
            监控结果统计
        """
        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        for i, symbol in enumerate(symbols):
            logger.info(f"处理 {i+1}/{len(symbols)}: {symbol}")

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

        logger.info(f"批量监控完成: 成功 {results['success']}/{results['total']}")
        return results

    def start_monitoring(self, symbols: List[str], interval: int = 600, browser_type: str = 'chromium'):
        """
        启动持续监控（后台线程）

        Args:
            symbols: 币种列表
            interval: 监控间隔（秒）
            browser_type: 浏览器类型
        """
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return

        self.is_monitoring = True

        def monitoring_loop():
            while self.is_monitoring:
                try:
                    logger.info(f"开始新一轮监控，币种数: {len(symbols)}")
                    self.monitor_batch(symbols, browser_type)
                    logger.info(f"监控完成，等待 {interval} 秒后进行下一轮")

                    # 等待指定间隔或直到停止信号
                    for _ in range(interval):
                        if not self.is_monitoring:
                            break
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    time.sleep(60)  # 出错后等待 1 分钟再重试

        self.monitor_thread = threading.Thread(
            target=monitoring_loop,
            daemon=True,
            name='BraveMonitorThread'
        )
        self.monitor_thread.start()

        logger.info(f"✅ Brave持续监控已启动 (间隔: {interval}秒, 币种数: {len(symbols)})")

    def stop_monitoring(self):
        """停止持续监控"""
        if not self.is_monitoring:
            logger.warning("监控未在运行")
            return

        self.is_monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("✅ Brave持续监控已停止")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取监控器统计信息

        Returns:
            统计信息字典
        """
        stats = {
            'available': self.ocr_extractor is not None,
            'cached_symbols': 0,
            'cache_ttl_seconds': self.cache_ttl,
            'is_monitoring': self.is_monitoring,
            'storage_type': 'MySQL'
        }

        # 统计缓存的币种数量
        if self.db_client:
            try:
                result = self.db_client.execute("SELECT COUNT(*) FROM hama_monitor_cache").fetchone()
                stats['cached_symbols'] = result[0] if result else 0
            except:
                pass

        return stats

    def get_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的币种列表

        Returns:
            币种符号列表
        """
        if not self.db_client:
            return []

        try:
            results = self.db_client.execute(
                "SELECT symbol FROM hama_monitor_cache ORDER BY monitored_at DESC"
            ).fetchall()
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"获取缓存币种列表失败: {e}")
            return []
