#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA Brave 浏览器监控服务
使用 Playwright + RapidOCR 从 TradingView 图表识别 HAMA 指标
支持 Redis 缓存和 SQLite 缓存
"""
import time
import json
import threading
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 全局单例
_brave_monitor_instance = None


def get_brave_monitor(redis_client=None, cache_ttl: int = 900, use_sqlite: bool = True):
    """
    获取 Brave 监控器单例

    Args:
        redis_client: Redis 客户端
        cache_ttl: 缓存过期时间（秒）
        use_sqlite: 是否使用 SQLite (默认 True)

    Returns:
        HamaBraveMonitor 实例
    """
    global _brave_monitor_instance

    if _brave_monitor_instance is None:
        _brave_monitor_instance = HamaBraveMonitor(redis_client, cache_ttl, use_sqlite)

    return _brave_monitor_instance


class HamaBraveMonitor:
    """HAMA Brave 浏览器监控器"""

    def __init__(self, redis_client=None, cache_ttl: int = 900, use_sqlite: bool = True):
        """
        初始化监控器

        Args:
            redis_client: Redis 客户端
            cache_ttl: 缓存过期时间（秒）
            use_sqlite: 是否使用 SQLite (默认 True)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.prefix = "hama:brave:"
        self.is_monitoring = False
        self.monitor_thread = None
        self.ocr_extractor = None

        # SQLite 支持
        self.use_sqlite = use_sqlite
        self.sqlite_conn = None
        if use_sqlite:
            self._init_sqlite()

        # 初始化 OCR 提取器
        self._init_ocr()

    def _init_sqlite(self):
        """初始化 SQLite 数据库"""
        try:
            # 数据库路径
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            # 确保 data 目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            self.sqlite_conn = sqlite3.connect(db_path)
            self.sqlite_conn.row_factory = sqlite3.Row

            # 创建表
            cursor = self.sqlite_conn.cursor()
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

            self.sqlite_conn.commit()
            logger.info("✅ SQLite 数据库初始化成功")
        except Exception as e:
            logger.error(f"SQLite 初始化失败: {e}")
            self.sqlite_conn = None

    def _init_ocr(self):
        """初始化 OCR 提取器"""
        try:
            from app.services.hama_ocr_extractor import HAMAOCRExtractor
            self.ocr_extractor = HAMAOCRExtractor(ocr_engine='rapidocr')
            logger.info("OCR 提取器初始化成功")
        except Exception as e:
            logger.error(f"OCR 提取器初始化失败: {e}")
            self.ocr_extractor = None

    def get_cached_hama(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取 HAMA 数据 (优先 SQLite,备用 Redis)

        Args:
            symbol: 币种符号

        Returns:
            HAMA 数据或 None
        """
        # 优先从 SQLite 获取 (每次创建新连接以避免线程问题)
        if self.use_sqlite:
            try:
                # 数据库路径
                db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
                db_path = os.path.abspath(db_path)

                # 创建新连接
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM hama_monitor_cache
                    WHERE symbol = ?
                    ORDER BY monitored_at DESC
                    LIMIT 1
                ''', (symbol,))

                row = cursor.fetchone()
                conn.close()

                if row:
                    # 将 Row 对象转换为字典以支持 .get() 方法
                    row_dict = dict(row)
                    return {
                        'hama_trend': row_dict['hama_trend'],
                        'hama_color': row_dict['hama_color'],
                        'hama_value': float(row_dict['hama_value']) if row_dict['hama_value'] else None,
                        'price': float(row_dict['price']) if row_dict['price'] else None,
                        'candle_ma_status': row_dict.get('candle_ma_status'),  # 蜡烛/MA状态
                        'bollinger_status': row_dict.get('bollinger_status'),  # 布林带状态
                        'last_cross_info': row_dict.get('last_cross_info'),  # 最近交叉
                        'screenshot_path': row_dict['screenshot_path'],  # 添加截图路径
                        'cached_at': row_dict['monitored_at'],
                        'cache_source': 'sqlite_brave_monitor'
                    }
            except Exception as e:
                logger.error(f"从 SQLite 获取缓存失败 {symbol}: {e}")

        # 备用: 从 Redis 获取
        if self.redis_client:
            try:
                key = f"{self.prefix}{symbol}"
                cached_data = self.redis_client.get(key)

                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"从 Redis 获取缓存失败 {symbol}: {e}")

        return None

    def set_cached_hama(self, symbol: str, hama_data: Dict[str, Any]) -> bool:
        """
        保存 HAMA 数据到缓存 (SQLite + Redis)

        Args:
            symbol: 币种符号
            hama_data: HAMA 数据

        Returns:
            是否成功
        """
        success = False

        # 保存到 SQLite (每次创建新连接)
        if self.use_sqlite:
            try:
                # 数据库路径
                db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
                db_path = os.path.abspath(db_path)

                # 创建新连接
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO hama_monitor_cache
                    (symbol, hama_trend, hama_color, hama_value, price, ocr_text, screenshot_path, candle_ma_status, bollinger_status, last_cross_info, monitored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    hama_data.get('trend'),  # 修复：使用 'trend' 而不是 'hama_trend'
                    hama_data.get('hama_color'),
                    hama_data.get('hama_value'),
                    hama_data.get('price'),
                    hama_data.get('ocr_text', ''),
                    hama_data.get('screenshot_path', ''),  # 保存截图路径
                    hama_data.get('candle_ma_status', ''),  # 蜡烛/MA状态
                    hama_data.get('bollinger_status', ''),  # 布林带状态
                    hama_data.get('last_cross_info', ''),  # 最近交叉
                    datetime.now()
                ))

                conn.commit()
                conn.close()
                logger.debug(f"{symbol} HAMA 数据已保存到 SQLite (包含截图路径)")
                success = True
            except Exception as e:
                logger.error(f"保存到 SQLite 失败 {symbol}: {e}")

        # 同时保存到 Redis (如果可用)
        if self.redis_client:
            try:
                key = f"{self.prefix}{symbol}"
                hama_data['cached_at'] = datetime.now().isoformat()
                hama_data['cache_source'] = 'brave_browser'

                json_data = json.dumps(hama_data, ensure_ascii=False)
                self.redis_client.setex(key, self.cache_ttl, json_data)

                logger.debug(f"{symbol} HAMA 数据已保存到 Redis (TTL={self.cache_ttl}秒)")
                success = True
            except Exception as e:
                logger.error(f"保存到 Redis 失败 {symbol}: {e}")

        return success

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

            # 截图保存到 screenshots 目录
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_filename = f"hama_brave_{symbol}_{int(time.time())}.png"
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)

            # 步骤 1: 截图
            logger.debug(f"正在截图 {symbol}...")
            result_path = self.ocr_extractor.capture_chart(chart_url, screenshot_path, browser_type)

            if not result_path:
                logger.warning(f"{symbol} 截图失败")
                return None

            # 步骤 2: OCR 识别
            logger.debug(f"正在 OCR 识别 {symbol}...")
            hama_data = self.ocr_extractor.extract_hama_with_ocr(result_path)

            # 保存截图路径到数据中 (只保存文件名，不包含完整路径)
            hama_data['screenshot_path'] = screenshot_filename
            hama_data['screenshot_url'] = f"/screenshot/{screenshot_filename}"
            hama_data['timestamp'] = int(time.time() * 1000)

            # 缓存到 Redis 和 SQLite
            self.set_cached_hama(symbol, hama_data)

            logger.info(f"{symbol} HAMA 状态: {hama_data.get('color', 'unknown')} ({hama_data.get('trend', 'unknown')})")
            return hama_data

        except Exception as e:
            logger.error(f"监控 {symbol} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

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
            'is_monitoring': self.is_monitoring
        }

        # 统计缓存的币种数量
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"{self.prefix}*")
                stats['cached_symbols'] = len(keys)
            except:
                pass

        return stats

    def get_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的币种列表

        Returns:
            币种符号列表
        """
        if not self.redis_client:
            return []

        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            symbols = [key.replace(self.prefix, '') for key in keys]
            return sorted(symbols)
        except Exception as e:
            logger.error(f"获取缓存币种列表失败: {e}")
            return []
