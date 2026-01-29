#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA Brave 浏览器监控服务
使用 Playwright + RapidOCR 从 TradingView 图表识别 HAMA 指标
支持 Redis 缓存和 SQLite 缓存

优化功能:
- 并发监控
- 缓存预热
- 智能监控间隔
- 资源自动清理
- 健康检查
"""
import time
import json
import threading
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def __init__(self, redis_client=None, cache_ttl: int = 900, use_sqlite: bool = True, enable_email: bool = True):
        """
        初始化监控器

        Args:
            redis_client: Redis 客户端
            cache_ttl: 缓存过期时间（秒）
            use_sqlite: 是否使用 SQLite (默认 True)
            enable_email: 是否启用邮件通知 (默认 True)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.prefix = "hama:brave:"
        self.is_monitoring = False
        self.monitor_thread = None
        self.ocr_extractor = None
        self.symbols = []  # 监控币种列表
        self.interval = 600  # 监控间隔
        self.last_monitor_time = None  # 最后监控时间
        self.enable_email = enable_email

        # 并发配置
        self.max_workers = 3  # 最大并发数

        # SQLite 支持
        self.use_sqlite = use_sqlite
        self.sqlite_conn = None
        if use_sqlite:
            self._init_sqlite()

        # 初始化 OCR 提取器
        self._init_ocr()

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

        # 记录上次状态（用于检测变化）- 从数据库加载
        self.last_states = self._load_last_states_from_db()  # {symbol: {'trend': ..., 'color': ..., 'value': ...}}
        logger.info(f"从数据库加载了 {len(self.last_states)} 个币种的历史状态")

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

            # 创建表 - 使用新的表结构（添加 timeframe 列）
            cursor = self.sqlite_conn.cursor()

            # 先检查表是否存在，如果存在旧表结构，需要迁移数据
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hama_monitor_cache'")
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # 检查是否有 timeframe 列
                cursor.execute("PRAGMA table_info(hama_monitor_cache)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'timeframe' not in columns:
                    logger.info("检测到旧表结构，正在迁移到新结构...")

                    # 创建新表
                    cursor.execute('''
                        CREATE TABLE hama_monitor_cache_new (
                            symbol VARCHAR(20) NOT NULL,
                            timeframe VARCHAR(10) NOT NULL,
                            hama_trend VARCHAR(10),
                            hama_color VARCHAR(10),
                            hama_value DECIMAL(20, 8),
                            price DECIMAL(20, 8),
                            ocr_text TEXT,
                            screenshot_path VARCHAR(255),
                            candle_ma_status TEXT,
                            bollinger_status TEXT,
                            last_cross_info TEXT,
                            email_sent INTEGER DEFAULT 0,
                            email_sent_at TIMESTAMP NULL,
                            monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (symbol, timeframe)
                        )
                    ''')

                    # 迁移数据：将旧数据作为 15m 时间周期迁移
                    cursor.execute('''
                        INSERT INTO hama_monitor_cache_new
                        (symbol, timeframe, hama_trend, hama_color, hama_value, price, ocr_text,
                         screenshot_path, candle_ma_status, bollinger_status, last_cross_info,
                         email_sent, email_sent_at, monitored_at, created_at, updated_at)
                        SELECT symbol, '15m', hama_trend, hama_color, hama_value, price, ocr_text,
                               screenshot_path, candle_ma_status, bollinger_status, last_cross_info,
                               email_sent, email_sent_at, monitored_at, created_at, updated_at
                        FROM hama_monitor_cache
                    ''')

                    # 删除旧表，重命名新表
                    cursor.execute('DROP TABLE hama_monitor_cache')
                    cursor.execute('ALTER TABLE hama_monitor_cache_new RENAME TO hama_monitor_cache')
                    logger.info("数据迁移完成")
                else:
                    logger.info("表结构已是最新版本")
            else:
                # 创建新表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hama_monitor_cache (
                        symbol VARCHAR(20) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        hama_trend VARCHAR(10),
                        hama_color VARCHAR(10),
                        hama_value DECIMAL(20, 8),
                        price DECIMAL(20, 8),
                        ocr_text TEXT,
                        screenshot_path VARCHAR(255),
                        candle_ma_status TEXT,
                        bollinger_status TEXT,
                        last_cross_info TEXT,
                        email_sent INTEGER DEFAULT 0,
                        email_sent_at TIMESTAMP NULL,
                        monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (symbol, timeframe)
                    )
                ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_hama_cache_monitored
                ON hama_monitor_cache(monitored_at)
            ''')

            # 创建邮件发送记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_send_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    email_type VARCHAR(50) NOT NULL,
                    hama_color VARCHAR(10),
                    hama_trend VARCHAR(10),
                    hama_value DECIMAL(20, 8),
                    price DECIMAL(20, 8),
                    cross_type VARCHAR(20),
                    recipients TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    screenshot_path VARCHAR(255),
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建邮件发送记录表的索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_log_symbol
                ON email_send_log(symbol)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_log_sent_at
                ON email_send_log(sent_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_email_log_status
                ON email_send_log(status)
            ''')

            logger.info("✅ 邮件发送记录表初始化成功")

            # 提交更改
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

                # 查询该币种的所有时间周期数据
                cursor.execute('''
                    SELECT * FROM hama_monitor_cache
                    WHERE symbol = ?
                    ORDER BY timeframe
                ''', (symbol,))

                rows = cursor.fetchall()
                conn.close()

                if rows:
                    # 合并多个时间周期的数据
                    timeframes = {}
                    primary_data = None  # 主数据（使用 15m 作为主周期）

                    for row in rows:
                        row_dict = dict(row)
                        timeframe = row_dict.get('timeframe', '15m')

                        # 读取截图并转换为Base64（仅为主周期）
                        screenshot_path = row_dict.get('screenshot_path')
                        screenshot_base64 = None
                        if timeframe == '15m' and screenshot_path:
                            try:
                                import base64
                                from pathlib import Path

                                screenshot_file = Path(screenshot_path)
                                if not screenshot_file.is_absolute():
                                    app_dir = Path(__file__).parent.parent
                                    potential_paths = [
                                        app_dir / 'screenshots' / screenshot_path,
                                        Path(__file__).parent.parent / 'screenshots' / screenshot_path,
                                        Path(__file__).parent.parent.parent / 'app' / 'screenshots' / screenshot_path,
                                    ]
                                    for potential_path in potential_paths:
                                        if potential_path.exists():
                                            screenshot_file = potential_path
                                            break

                                if screenshot_file.exists():
                                    with open(screenshot_file, 'rb') as f:
                                        image_data = f.read()
                                        screenshot_base64 = base64.b64encode(image_data).decode('utf-8')
                            except Exception as e:
                                logger.warning(f"读取截图文件失败: {e}")

                        # 存储该时间周期数据
                        timeframes[timeframe] = {
                            'trend': row_dict['hama_trend'],
                            'color': row_dict['hama_color'],
                            'hama_value': float(row_dict['hama_value']) if row_dict.get('hama_value') else None,
                            'price': float(row_dict['price']) if row_dict.get('price') else None,
                            'candle_ma_status': row_dict.get('candle_ma_status'),
                            'bollinger_status': row_dict.get('bollinger_status'),
                            'last_cross_info': row_dict.get('last_cross_info'),
                            'monitored_at': row_dict.get('monitored_at')
                        }

                        # 使用 15m 作为主数据（向后兼容）
                        if timeframe == '15m':
                            primary_data = timeframes[timeframe]
                            primary_data['screenshot_path'] = screenshot_path
                            primary_data['screenshot_base64'] = screenshot_base64

                    if primary_data:
                        # 构建返回数据（主周期数据在顶层，其他周期在 timeframes 字段）
                        result = {
                            'hama_trend': primary_data.get('trend'),
                            'hama_color': primary_data.get('color'),
                            'hama_value': primary_data.get('hama_value'),
                            'price': primary_data.get('price'),
                            'candle_ma_status': primary_data.get('candle_ma_status'),
                            'bollinger_status': primary_data.get('bollinger_status'),
                            'last_cross_info': primary_data.get('last_cross_info'),
                            'screenshot_path': primary_data.get('screenshot_path'),
                            'screenshot_base64': primary_data.get('screenshot_base64'),
                            'cached_at': primary_data.get('monitored_at'),
                            'cache_source': 'sqlite_brave_monitor',
                            # 所有时间周期数据
                            'timeframes': timeframes,
                            'timeframe_15m': timeframes.get('15m'),
                            'timeframe_1h': timeframes.get('1h'),
                            'timeframe_4h': timeframes.get('4h'),
                        }
                        return result
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

        # 处理截图Base64编码（用于前端展示）
        screenshot_base64 = None
        screenshot_path = hama_data.get('screenshot_path')
        if screenshot_path:
            try:
                import base64
                from pathlib import Path

                # 处理相对路径和绝对路径
                screenshot_file = Path(screenshot_path)
                if not screenshot_file.is_absolute():
                    # 如果是相对路径,尝试从 app/screenshots 目录查找
                    app_dir = Path(__file__).parent.parent  # backend_api_python/app
                    potential_paths = [
                        app_dir / 'screenshots' / screenshot_path,  # app/screenshots/filename.png
                        Path(__file__).parent.parent / 'screenshots' / screenshot_path,  # backend_api_python/screenshots/filename.png
                        Path(__file__).parent.parent.parent / 'app' / 'screenshots' / screenshot_path,  # 从更上层查找
                    ]

                    for potential_path in potential_paths:
                        if potential_path.exists():
                            screenshot_file = potential_path
                            logger.debug(f"找到截图文件: {screenshot_file}")
                            break

                if screenshot_file.exists():
                    # 读取截图文件并转换为Base64
                    with open(screenshot_file, 'rb') as f:
                        image_data = f.read()
                        screenshot_base64 = base64.b64encode(image_data).decode('utf-8')
                        hama_data['screenshot_base64'] = screenshot_base64
                        logger.debug(f"截图已转换为Base64: {symbol}, 大小: {len(screenshot_base64)} 字符")
                else:
                    logger.warning(f"截图文件不存在: {screenshot_path}")
            except Exception as e:
                logger.warning(f"读取截图文件失败: {e}")

        # 保存到 SQLite (每次创建新连接)
        if self.use_sqlite:
            try:
                # 数据库路径
                db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
                db_path = os.path.abspath(db_path)

                # 创建新连接
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                current_time = datetime.now()
                timeframe = hama_data.get('timeframe', '15m')

                # 1. 更新缓存表 (每条记录包含 symbol + timeframe)
                cursor.execute('''
                    INSERT OR REPLACE INTO hama_monitor_cache
                    (symbol, timeframe, hama_trend, hama_color, hama_value, price, ocr_text, screenshot_path,
                     candle_ma_status, bollinger_status, last_cross_info, monitored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    timeframe,
                    hama_data.get('trend'),
                    hama_data.get('color'),  # 注意：OCR返回的是 'color' 不是 'hama_color'
                    hama_data.get('hama_value'),
                    hama_data.get('price'),
                    hama_data.get('ocr_text', ''),
                    hama_data.get('screenshot_path', ''),
                    hama_data.get('candle_ma_status', ''),
                    hama_data.get('bollinger_status', ''),
                    hama_data.get('last_cross_info', ''),
                    current_time
                ))

                # 2. 插入历史表 (每次监控都插入新记录)
                cursor.execute('''
                    INSERT INTO hama_monitor_history
                    (symbol, timeframe, hama_trend, hama_color, hama_value, price, ocr_text, screenshot_path,
                     candle_ma_status, bollinger_status, last_cross_info, monitored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    timeframe,
                    hama_data.get('trend'),
                    hama_data.get('color'),
                    hama_data.get('hama_value'),
                    hama_data.get('price'),
                    hama_data.get('ocr_text', ''),
                    hama_data.get('screenshot_path', ''),
                    hama_data.get('candle_ma_status', ''),
                    hama_data.get('bollinger_status', ''),
                    hama_data.get('last_cross_info', ''),
                    current_time
                ))

                conn.commit()
                conn.close()
                logger.debug(f"{symbol} {timeframe} HAMA 数据已保存到 SQLite (缓存表 + 历史表)")
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

    def _monitor_single_timeframe(self, symbol: str, interval: int, browser_type: str = 'chromium') -> Optional[Dict[str, Any]]:
        """
        监控单个币种的单个时间周期

        Args:
            symbol: 币种符号
            interval: TradingView 时间周期 (15=15m, 60=1h, 240=4h)
            browser_type: 浏览器类型

        Returns:
            该时间周期的 HAMA 数据或 None
        """
        if not self.ocr_extractor:
            logger.error("OCR 提取器未初始化")
            return None

        try:
            timeframe_name = f"{interval}m"
            logger.debug(f"开始监控 {symbol} {timeframe_name} 周期")

            # 构建 TradingView 图表 URL
            chart_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}&interval={interval}"

            # 截图保存目录
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = int(time.time())

            # 准备截图文件名（包含时间周期标识）
            hama_panel_filename = f"hama_brave_{symbol}_{timeframe_name}_{timestamp}.png"
            full_chart_filename = f"full_chart_{symbol}_{timeframe_name}_{timestamp}.png"

            hama_panel_path = os.path.join(screenshot_dir, hama_panel_filename)
            full_chart_path = os.path.join(screenshot_dir, full_chart_filename)

            # 步骤 1: 截取HAMA面板(用于OCR识别)
            logger.debug(f"正在截取 {timeframe_name} HAMA面板 {symbol}...")
            hama_panel_result = self.ocr_extractor.capture_chart(chart_url, hama_panel_path, browser_type)

            if not hama_panel_result:
                logger.warning(f"{symbol} {timeframe_name} HAMA面板截图失败")
                return None

            # 步骤 2: OCR 识别
            logger.debug(f"正在 OCR 识别 {symbol} {timeframe_name}...")
            hama_data = self.ocr_extractor.extract_hama_with_ocr(hama_panel_result)

            if not hama_data:
                logger.warning(f"{symbol} {timeframe_name} OCR 识别失败")
                return None

            # 添加截图路径信息
            hama_data['screenshot_path'] = hama_panel_filename
            hama_data['full_chart_path'] = full_chart_filename
            hama_data['screenshot_url'] = f"/screenshot/{hama_panel_filename}"
            hama_data['full_chart_url'] = f"/screenshot/{full_chart_filename}"
            hama_data['timeframe'] = timeframe_name
            hama_data['timestamp'] = int(time.time() * 1000)

            logger.debug(f"{symbol} {timeframe_name} HAMA: {hama_data.get('color')} ({hama_data.get('trend')})")
            return hama_data

        except Exception as e:
            logger.error(f"监控 {symbol} {interval}m 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def monitor_symbol(self, symbol: str, interval: int = 15, browser_type: str = 'chromium') -> Optional[Dict[str, Any]]:
        """
        监控单个币种的单个时间周期 HAMA 状态

        Args:
            symbol: 币种符号
            interval: 时间周期 (15=15m, 60=1h, 240=4h)
            browser_type: 浏览器类型 (chromium, firefox, webkit)

        Returns:
            HAMA 数据或 None
        """
        if not self.ocr_extractor:
            logger.error("OCR 提取器未初始化")
            return None

        try:
            timeframe_name = f"{interval}m"
            logger.info(f"开始监控 {symbol} {timeframe_name}, 使用浏览器: {browser_type}")

            # 调用单周期监控方法
            hama_data = self._monitor_single_timeframe(symbol, interval, browser_type)

            if hama_data:
                # 缓存到 Redis 和 SQLite（每条记录包含 symbol + timeframe）
                self.set_cached_hama(symbol, hama_data)

                # 仅对 15m 周期检查邮件通知
                if interval == 15 and self.enable_email and self.email_notifier:
                    try:
                        full_chart_path = os.path.join(
                            os.path.dirname(__file__), '..', 'screenshots',
                            hama_data.get('full_chart_path', '')
                        )
                        self._check_and_notify_trend(symbol, hama_data, hama_data.get('full_chart_path'))
                    except Exception as e:
                        logger.warning(f"发送邮件通知失败: {e}")

            return hama_data

        except Exception as e:
            logger.error(f"监控 {symbol} {interval}m 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def monitor_batch(self, symbols: List[str], intervals: List[int] = None, browser_type: str = 'chromium', use_threading: bool = True) -> Dict[str, Any]:
        """
        批量监控多个币种的多个时间周期

        Args:
            symbols: 币种列表
            intervals: 时间周期列表 [15, 60, 240]，默认 [15, 60, 240]
            browser_type: 浏览器类型
            use_threading: 是否使用多线程并行监控

        Returns:
            监控结果统计
        """
        if intervals is None:
            intervals = [15, 60, 240]  # 默认监控 15m, 1h, 4h

        results = {
            'total': len(symbols) * len(intervals),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        def monitor_single_task(symbol: str, interval: int) -> tuple:
            """单个监控任务的包装函数"""
            try:
                hama_data = self.monitor_symbol(symbol, interval, browser_type)
                if hama_data:
                    return (symbol, interval, True, hama_data)
                else:
                    return (symbol, interval, False, None)
            except Exception as e:
                logger.error(f"监控任务失败 {symbol} {interval}m: {e}")
                return (symbol, interval, False, None)

        if use_threading:
            # 使用多线程并行监控
            from concurrent.futures import ThreadPoolExecutor, as_completed

            logger.info(f"使用多线程并行监控 {len(symbols)} 个币种 x {len(intervals)} 个周期 = {results['total']} 个任务")

            with ThreadPoolExecutor(max_workers=3) as executor:  # 最多3个并发浏览器实例
                # 提交所有任务
                futures = {}
                for symbol in symbols:
                    for interval in intervals:
                        future = executor.submit(monitor_single_task, symbol, interval)
                        futures[future] = (symbol, interval)

                # 收集结果
                for future in as_completed(futures):
                    symbol, interval = futures[future]
                    try:
                        symbol, interval_val, success, hama_data = future.result()
                        key = f"{symbol}_{interval_val}m"

                        if success:
                            results['success'] += 1
                            results['symbols'][key] = {
                                'success': True,
                                'symbol': symbol,
                                'interval': interval_val,
                                'data': hama_data
                            }
                        else:
                            results['failed'] += 1
                            results['symbols'][key] = {
                                'success': False,
                                'symbol': symbol,
                                'interval': interval_val
                            }
                    except Exception as e:
                        logger.error(f"任务执行异常 {symbol} {interval}m: {e}")
                        results['failed'] += 1
        else:
            # 顺序执行（用于调试）
            logger.info(f"顺序监控 {len(symbols)} 个币种 x {len(intervals)} 个周期 = {results['total']} 个任务")

            for i, symbol in enumerate(symbols):
                for interval in intervals:
                    logger.info(f"处理 {i+1}/{len(symbols)}: {symbol} {interval}m")

                    symbol, interval_val, success, hama_data = monitor_single_task(symbol, interval)
                    key = f"{symbol}_{interval_val}m"

                    if success:
                        results['success'] += 1
                        results['symbols'][key] = {
                            'success': True,
                            'symbol': symbol,
                            'interval': interval_val,
                            'data': hama_data
                        }
                    else:
                        results['failed'] += 1
                        results['symbols'][key] = {
                            'success': False,
                            'symbol': symbol,
                            'interval': interval_val
                        }

        logger.info(f"批量监控完成: 成功 {results['success']}/{results['total']}")
        return results

    def start_monitoring(self, symbols: List[str], interval: int = 600, browser_type: str = 'chromium', intervals: List[int] = None):
        """
        启动持续监控（后台线程），支持多时间周期并行监控

        Args:
            symbols: 币种列表
            interval: 监控间隔（秒）
            browser_type: 浏览器类型
            intervals: 时间周期列表，默认 [15, 60, 240]
        """
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return

        if intervals is None:
            intervals = [15, 60, 240]

        self.is_monitoring = True

        def monitoring_loop():
            while self.is_monitoring:
                try:
                    logger.info(f"开始新一轮监控，币种数: {len(symbols)}, 周期: {intervals}")
                    # 使用多线程并行监控所有周期
                    self.monitor_batch(symbols, intervals=intervals, browser_type=browser_type, use_threading=True)
                    logger.info(f"监控完成，等待 {interval} 秒后进行下一轮")

                    # 等待指定间隔或直到停止信号
                    for _ in range(interval):
                        if not self.is_monitoring:
                            break
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(60)  # 出错后等待 1 分钟再重试

        self.monitor_thread = threading.Thread(
            target=monitoring_loop,
            daemon=True,
            name='BraveMonitorThread'
        )
        self.monitor_thread.start()

        logger.info(f"✅ Brave持续监控已启动 (间隔: {interval}秒, 币种数: {len(symbols)}, 周期: {intervals}, 并发线程: 3)")

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

    # ==================== 新增优化功能 ====================

    def monitor_batch_parallel(self, symbols: List[str], browser_type: str = 'chromium', max_workers: int = None) -> Dict[str, Any]:
        """
        并行批量监控多个币种（性能优化）

        Args:
            symbols: 币种列表
            browser_type: 浏览器类型
            max_workers: 最大并发数（默认使用 self.max_workers）

        Returns:
            监控结果统计
        """
        if max_workers is None:
            max_workers = self.max_workers

        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'symbols': {}
        }

        logger.info(f"开始并行批量监控 {len(symbols)} 个币种，并发数: {max_workers}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self.monitor_symbol, symbol, browser_type): symbol
                for symbol in symbols
            }

            # 处理完成的任务
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    hama_data = future.result(timeout=90)  # 单个任务最多 90 秒

                    if hama_data:
                        results['success'] += 1
                        results['symbols'][symbol] = {
                            'success': True,
                            'data': hama_data
                        }
                        logger.debug(f"✅ {symbol} 监控成功")
                    else:
                        results['failed'] += 1
                        results['symbols'][symbol] = {
                            'success': False
                        }
                        logger.warning(f"❌ {symbol} 监控失败")

                except Exception as e:
                    results['failed'] += 1
                    results['symbols'][symbol] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"❌ {symbol} 监控异常: {e}")

        logger.info(f"并行批量监控完成: 成功 {results['success']}/{results['total']}, 失败 {results['failed']}")
        return results

    def warmup_cache(self, hot_symbols: List[str] = None, browser_type: str = 'chromium') -> Dict[str, Any]:
        """
        缓存预热：启动时预先监控热门币种

        Args:
            hot_symbols: 热门币种列表（默认 BTC, ETH, BNB, SOL）
            browser_type: 浏览器类型

        Returns:
            预热结果统计
        """
        if hot_symbols is None:
            hot_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']

        logger.info(f"开始缓存预热，币种: {hot_symbols}")

        # 使用串行监控（预热时避免并发压力）
        results = self.monitor_batch(hot_symbols, browser_type)

        logger.info(f"缓存预热完成: 成功 {results['success']}/{results['total']}")
        return results

    def get_dynamic_interval(self) -> int:
        """
        获取动态监控间隔（根据市场活跃度调整）

        Returns:
            监控间隔（秒）
        """
        hour = datetime.now().hour

        # 交易活跃期 (8:00-24:00) - 5分钟
        if 8 <= hour < 24:
            return 300

        # 交易低迷期 (0:00-8:00) - 10分钟
        else:
            return 600

    def cleanup_old_records(self, days: int = 7) -> int:
        """
        清理旧的监控记录（数据库维护）

        Args:
            days: 保留天数（默认 7 天）

        Returns:
            删除的记录数
        """
        if not self.use_sqlite:
            logger.warning("SQLite 未启用，跳过清理")
            return 0

        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 删除旧记录
            cursor.execute('''
                DELETE FROM hama_monitor_cache
                WHERE monitored_at < datetime('now', '-' || ? || ' days')
            ''', (days,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"已清理 {days} 天前的旧数据，删除 {deleted_count} 条记录")
            return deleted_count

        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            return 0

    def cleanup_old_screenshots(self, max_age_days: int = 7) -> int:
        """
        清理旧的截图文件

        Args:
            max_age_days: 保留天数（默认 7 天）

        Returns:
            删除的文件数
        """
        try:
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')

            if not os.path.exists(screenshot_dir):
                logger.warning(f"截图目录不存在: {screenshot_dir}")
                return 0

            now = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            deleted_count = 0

            for filename in os.listdir(screenshot_dir):
                filepath = os.path.join(screenshot_dir, filename)

                # 跳过目录
                if os.path.isdir(filepath):
                    continue

                # 检查文件年龄
                if os.path.getmtime(filepath) < now - max_age_seconds:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.debug(f"删除旧截图: {filename}")
                    except Exception as e:
                        logger.warning(f"删除文件失败 {filename}: {e}")

            logger.info(f"已清理 {max_age_days} 天前的旧截图，删除 {deleted_count} 个文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理旧截图失败: {e}")
            return 0

    def get_history_count(self) -> int:
        """
        获取历史表的总记录数

        Returns:
            记录数
        """
        if not self.use_sqlite:
            return 0

        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM hama_monitor_history')
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            logger.error(f"获取历史记录数失败: {e}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查：监控系统各组件状态

        Returns:
            健康状态字典
        """
        checks = {
            'ocr_available': self.ocr_extractor is not None,
            'sqlite_available': self.sqlite_conn is not None,
            'redis_available': self.redis_client is not None,
            'monitoring_active': self.is_monitoring,
            'last_monitor_time': self.last_monitor_time,
            'cached_symbols_count': self._get_cached_symbol_count(),
            'monitor_interval': self.interval
        }

        # 判断整体状态
        if all([checks['ocr_available'], checks['sqlite_available']]):
            status = 'healthy'
        elif checks['ocr_available']:
            status = 'degraded'
        else:
            status = 'unhealthy'

        return {
            'status': status,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }

    def _get_cached_symbol_count(self) -> int:
        """获取缓存的币种数量"""
        if not self.use_sqlite:
            return 0

        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM hama_monitor_cache')
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            logger.error(f"获取缓存币种数量失败: {e}")
            return 0

    def start_monitoring_smart(self, symbols: List[str], base_interval: int = 600, browser_type: str = 'chromium'):
        """
        启动智能持续监控（动态调整间隔）

        Args:
            symbols: 币种列表
            base_interval: 基础监控间隔（秒）
            browser_type: 浏览器类型
        """
        self.symbols = symbols
        self.interval = base_interval

        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return

        self.is_monitoring = True

        def smart_monitoring_loop():
            while self.is_monitoring:
                try:
                    # 获取动态间隔
                    dynamic_interval = self.get_dynamic_interval()
                    logger.info(f"开始新一轮监控，币种数: {len(symbols)}，动态间隔: {dynamic_interval}秒")

                    # 使用并行监控提升性能
                    self.monitor_batch_parallel(symbols, browser_type)

                    # 更新最后监控时间
                    self.last_monitor_time = datetime.now().isoformat()

                    logger.info(f"监控完成，等待 {dynamic_interval} 秒后进行下一轮")

                    # 等待指定间隔或直到停止信号
                    for _ in range(dynamic_interval):
                        if not self.is_monitoring:
                            break
                        time.sleep(1)

                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(60)  # 出错后等待 1 分钟再重试

        self.monitor_thread = threading.Thread(
            target=smart_monitoring_loop,
            daemon=True,
            name='SmartBraveMonitorThread'
        )
        self.monitor_thread.start()

        logger.info(f"✅ Brave智能持续监控已启动 (基础间隔: {base_interval}秒, 币种数: {len(symbols)})")


    def _check_and_notify_trend(self, symbol: str, hama_data: Dict[str, Any], screenshot_filename: str) -> bool:
        """
        检查趋势并发送邮件通知（使用历史表判断状态变化）

        Args:
            symbol: 币种符号
            hama_data: HAMA 数据
            screenshot_filename: 截图文件名

        Returns:
            是否发送了邮件
        """
        try:
            # 提取当前状态
            current_color = hama_data.get('hama_color', '')
            current_trend = hama_data.get('hama_trend', '')
            current_value = hama_data.get('hama_value', 0)
            price = hama_data.get('price', 0)
            cross_info = hama_data.get('last_cross_info', '')

            # 从历史表查询上一次状态（而不是使用内存中的last_states）
            last_state = self._get_previous_state_from_history(symbol)

            # 检查是否需要发送通知（趋势变化）
            should_notify = False
            cross_type = None

            if last_state:
                # 有历史记录，检查是否变化
                last_color = last_state.get('color', '')
                last_trend = last_state.get('trend', '')

                logger.info(f"{symbol} 状态对比(历史表): 上次={last_color}, 当前={current_color}")

                # 新逻辑: 只有当两个状态都非盘整且状态不同时,才触发邮件
                # 排除盘整状态(null/empty/neutral/gray)
                last_is_valid = last_color and last_color != '' and last_color not in ('neutral', 'gray')
                current_is_valid = current_color and current_color != '' and current_color not in ('neutral', 'gray')

                if last_is_valid and current_is_valid and last_color != current_color:
                    # 两个状态都有效且不同,检测金叉/死叉
                    if current_color == 'green':
                        should_notify = True
                        cross_type = 'cross_up'
                        logger.info(f"✅ 检测到金叉信号: {symbol} (颜色: {last_color} → {current_color})")
                    elif current_color == 'red':
                        should_notify = True
                        cross_type = 'cross_down'
                        logger.info(f"✅ 检测到死叉信号: {symbol} (颜色: {last_color} → {current_color})")
                else:
                    # 状态相同或包含盘整状态,不发送邮件
                    if not last_is_valid or not current_is_valid:
                        logger.info(f"❌ {symbol} 包含盘整状态,不发送邮件 (上次={last_color}, 当前={current_color})")
                    else:
                        logger.info(f"❌ {symbol} 颜色未变化: {last_color} → {current_color}，不发送邮件")
            else:
                # 历史表中没有记录（第一次监控），不发送通知
                logger.info(f"🆕 首次监控 {symbol}（历史表无记录），记录初始状态: {current_color}")

            if not should_notify:
                return False

            # 检查是否在邮件监控白名单中（只有 BTC 和 ETH 才发送邮件）
            email_whitelist = ['BTCUSDT', 'ETHUSDT']
            if symbol not in email_whitelist:
                logger.info(f"{symbol} 不在邮件监控白名单中，跳过发送（仅 BTC/ETH 发送邮件）")
                return False

            # 检查邮件冷却
            if self.email_notifier.is_cooldown_active(symbol):
                logger.info(f"{symbol} 在邮件冷却期内，跳过发送")
                return False

            # 构建截图完整路径
            from pathlib import Path
            screenshot_dir = Path(__file__).parent.parent / 'screenshots'
            screenshot_full_path = str(screenshot_dir / screenshot_filename)

            # 发送邮件通知
            logger.info(f"准备发送邮件通知: {symbol} ({current_color}, {current_trend})")

            # 准备额外数据（包含多时间周期）
            extra_data = {
                'cross_info': cross_info,
                'candle_ma_status': hama_data.get('candle_ma_status', ''),
                'bollinger_status': hama_data.get('bollinger_status', '')
            }

            # 添加多时间周期数据（如果存在）
            if 'timeframes' in hama_data:
                extra_data['timeframes'] = hama_data['timeframes']

            success = self.email_notifier.notify_trend_formed(
                symbol=symbol,
                trend=current_trend,
                hama_color=current_color,
                hama_value=float(current_value) if current_value else 0,
                price=float(price) if price else 0,
                cross_type=cross_type,
                screenshot_url=f"/screenshots/{screenshot_filename}",
                screenshot_path=screenshot_full_path,  # 传递完整的截图文件路径作为附件
                extra_data=extra_data
            )

            # 记录邮件发送日志到数据库
            self._log_email_send(
                symbol=symbol,
                email_type='trend_notification',
                hama_color=current_color,
                hama_trend=current_trend,
                hama_value=current_value,
                price=price,
                cross_type=cross_type,
                screenshot_path=screenshot_full_path,
                success=success,
                recipients=self.email_notifier.default_recipients if self.email_notifier else ''
            )

            if success:
                logger.info(f"✅ {symbol} 邮件通知发送成功")
                # 更新数据库中的邮件发送状态
                try:
                    if self.use_sqlite and self.sqlite_conn:
                        cursor = self.sqlite_conn.cursor()
                        cursor.execute("""
                            UPDATE hama_monitor_cache
                            SET email_sent = 1, email_sent_at = CURRENT_TIMESTAMP
                            WHERE symbol = ?
                        """, (symbol,))
                        self.sqlite_conn.commit()
                        logger.info(f"✅ {symbol} 邮件发送状态已更新到数据库")
                except Exception as e:
                    logger.warning(f"更新邮件发送状态失败: {e}")
                return True
            else:
                logger.warning(f"❌ {symbol} 邮件通知发送失败")
                return False

        except Exception as e:
            logger.error(f"检查趋势并发送邮件失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _get_previous_state_from_history(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从历史表和缓存表查询币种的上一次状态

        逻辑:
        1. 查询历史表最新的一条记录（刚刚插入的）
        2. 查询缓存表的当前记录
        3. 如果两者不同，说明状态有变化，返回缓存表的状态作为"上一次状态"
        4. 如果两者相同或历史表为空，返回历史表的倒数第二条记录

        Args:
            symbol: 币种符号

        Returns:
            {'color': ..., 'trend': ..., 'value': ...} 或 None
        """
        if not self.use_sqlite:
            return None

        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(db_path)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. 查询缓存表当前状态
            cursor.execute('''
                SELECT hama_color, hama_trend, hama_value
                FROM hama_monitor_cache
                WHERE symbol = ?
            ''', (symbol,))

            cache_row = cursor.fetchone()

            # 2. 查询历史表最新的一条记录
            cursor.execute('''
                SELECT hama_color, hama_trend, hama_value
                FROM hama_monitor_history
                WHERE symbol = ?
                ORDER BY monitored_at DESC
                LIMIT 1
            ''', (symbol,))

            history_latest_row = cursor.fetchone()

            # 3. 如果缓存表和历史表的最新记录不同，说明刚刚更新了状态
            # 返回缓存表的状态作为"上一次状态"
            if cache_row and history_latest_row:
                cache_color = cache_row['hama_color'] or ''
                history_color = history_latest_row['hama_color'] or ''

                # 如果颜色相同，说明本次监控没有变化，查询历史表的倒数第二条
                if cache_color == history_color:
                    cursor.execute('''
                        SELECT hama_color, hama_trend, hama_value
                        FROM hama_monitor_history
                        WHERE symbol = ?
                        ORDER BY monitored_at DESC
                        LIMIT 1 OFFSET 1
                    ''', (symbol,))

                    prev_row = cursor.fetchone()
                    conn.close()

                    if prev_row:
                        return {
                            'color': prev_row['hama_color'] or '',
                            'trend': prev_row['hama_trend'] or '',
                            'value': prev_row['hama_value'] or 0
                        }

                    return None
                else:
                    # 颜色不同，返回缓存表状态作为上一次状态
                    conn.close()
                    return {
                        'color': cache_row['hama_color'] or '',
                        'trend': cache_row['hama_trend'] or '',
                        'value': cache_row['hama_value'] or 0
                    }

            # 4. 如果只有历史表记录，查询倒数第二条
            if history_latest_row:
                cursor.execute('''
                    SELECT hama_color, hama_trend, hama_value
                    FROM hama_monitor_history
                    WHERE symbol = ?
                    ORDER BY monitored_at DESC
                    LIMIT 1 OFFSET 1
                ''', (symbol,))

                prev_row = cursor.fetchone()
                conn.close()

                if prev_row:
                    return {
                        'color': prev_row['hama_color'] or '',
                        'trend': prev_row['hama_trend'] or '',
                        'value': prev_row['hama_value'] or 0
                    }

            conn.close()
            return None

        except Exception as e:
            logger.warning(f"从历史表查询上一次状态失败 {symbol}: {e}")
            return None

    def _load_last_states_from_db(self) -> Dict[str, Dict[str, Any]]:
        """
        从数据库加载上次的状态，用于重启后恢复状态判断
        
        Returns:
            {symbol: {'color': ..., 'trend': ..., 'value': ...}}
        """
        states = {}
        
        if not self.use_sqlite or not self.sqlite_conn:
            logger.info("SQLite 未启用，无法从数据库加载历史状态")
            return states
        
        try:
            cursor = self.sqlite_conn.cursor()
            
            # 查询每个币种的最新记录
            cursor.execute("""
                SELECT symbol, hama_color, hama_trend, hama_value
                FROM hama_monitor_cache
                WHERE symbol IS NOT NULL
                ORDER BY monitored_at DESC
            """)
            
            rows = cursor.fetchall()
            
            # 为每个币种只保留最新的状态（用 dict 去重）
            for row in rows:
                symbol = row['symbol']
                if symbol not in states:  # 只保留第一次出现的（最新的）
                    states[symbol] = {
                        'color': row['hama_color'] or '',
                        'trend': row['hama_trend'] or '',
                        'value': row['hama_value'] or 0
                    }
            
            logger.info(f"✅ 从数据库加载了 {len(states)} 个币种的历史状态")
            for symbol, state in states.items():
                logger.debug(f"  {symbol}: {state}")
                
        except Exception as e:
            logger.warning(f"从数据库加载历史状态失败: {e}")
        
        return states

    def _log_email_send(
        self,
        symbol: str,
        email_type: str,
        hama_color: str,
        hama_trend: str,
        hama_value: Any,
        price: Any,
        cross_type: Optional[str],
        screenshot_path: str,
        success: bool,
        recipients: str,
        error_message: Optional[str] = None
    ):
        """
        记录邮件发送日志到数据库
        
        Args:
            symbol: 币种符号
            email_type: 邮件类型 (trend_notification)
            hama_color: HAMA 颜色
            hama_trend: HAMA 趋势
            hama_value: HAMA 值
            price: 当前价格
            cross_type: 交叉类型
            screenshot_path: 截图路径
            success: 是否发送成功
            recipients: 收件人
            error_message: 错误信息（如果失败）
        """
        if not self.use_sqlite or not self.sqlite_conn:
            return
        
        try:
            cursor = self.sqlite_conn.cursor()
            
            # 插入邮件发送记录
            cursor.execute("""
                INSERT INTO email_send_log (
                    symbol, email_type, hama_color, hama_trend, hama_value, price,
                    cross_type, recipients, status, error_message, screenshot_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                email_type,
                hama_color,
                hama_trend,
                float(hama_value) if hama_value else 0,
                float(price) if price else 0,
                cross_type or '',
                recipients,
                'success' if success else 'failed',
                error_message,
                screenshot_path or ''
            ))
            
            self.sqlite_conn.commit()
            logger.info(f"✅ 邮件发送记录已保存: {symbol} - {email_type} - {'成功' if success else '失败'}")
            
        except Exception as e:
            logger.error(f"记录邮件发送日志失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
