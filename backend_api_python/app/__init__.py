"""
QuantDinger Python API - Flask application factory.
"""
from flask import Flask
from flask_cors import CORS
import logging
import traceback

from app.utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

# Global singletons (avoid duplicate strategy threads).
_trading_executor = None
_pending_order_worker = None
_reflection_worker = None
_redis_client = None
_hama_scheduler = None
_tv_cache_manager = None
_tv_scheduler = None
_hama_brave_monitor = None
_hama_health_checker = None
_long_logic_reader = None


def get_trading_executor():
    """Get the trading executor singleton."""
    global _trading_executor
    if _trading_executor is None:
        from app.services.trading_executor import TradingExecutor
        _trading_executor = TradingExecutor()
    return _trading_executor


def get_pending_order_worker():
    """Get the pending order worker singleton."""
    global _pending_order_worker
    if _pending_order_worker is None:
        from app.services.pending_order_worker import PendingOrderWorker
        _pending_order_worker = PendingOrderWorker()
    return _pending_order_worker


def get_reflection_worker():
    """Get the reflection verification worker singleton."""
    global _reflection_worker
    if _reflection_worker is None:
        from app.services.agents.reflection_worker import ReflectionWorker
        _reflection_worker = ReflectionWorker()
    return _reflection_worker


def start_reflection_worker():
    """
    Start the reflection worker if enabled.

    To enable it, set ENABLE_REFLECTION_WORKER=true.
    """
    import os
    enabled = os.getenv("ENABLE_REFLECTION_WORKER", "false").lower() == "true"
    if not enabled:
        logger.info("Reflection worker is disabled. Set ENABLE_REFLECTION_WORKER=true to enable.")
        return

    # Avoid running twice with Flask reloader
    debug = os.getenv("PYTHON_API_DEBUG", "false").lower() == "true"
    if debug:
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            return

    try:
        get_reflection_worker().start()
    except Exception as e:
        logger.error(f"Failed to start reflection worker: {e}")


def start_pending_order_worker():
    """Start the pending order worker (disabled by default in paper mode).

    To enable it, set ENABLE_PENDING_ORDER_WORKER=true.
    """
    import os
    # Local deployment: default to enabled so queued orders can be dispatched automatically.
    # To disable it, set ENABLE_PENDING_ORDER_WORKER=false explicitly.
    if os.getenv('ENABLE_PENDING_ORDER_WORKER', 'true').lower() != 'true':
        logger.info("Pending order worker is disabled (paper mode). Set ENABLE_PENDING_ORDER_WORKER=true to enable.")
        return
    try:
        get_pending_order_worker().start()
    except Exception as e:
        logger.error(f"Failed to start pending order worker: {e}")


def restore_running_strategies():
    """
    Restore running strategies on startup.
    Local deployment: only restores IndicatorStrategy.
    """
    import os
    # You can disable auto-restore to avoid starting many threads on low-resource hosts.
    if os.getenv('DISABLE_RESTORE_RUNNING_STRATEGIES', 'false').lower() == 'true':
        logger.info("Startup strategy restore is disabled via DISABLE_RESTORE_RUNNING_STRATEGIES")
        return
    try:
        from app.services.strategy import StrategyService

        strategy_service = StrategyService()
        trading_executor = get_trading_executor()

        running_strategies = strategy_service.get_running_strategies_with_type()

        if not running_strategies:
            logger.info("No running strategies to restore.")
            return

        logger.info(f"Restoring {len(running_strategies)} running strategies...")

        restored_count = 0
        for strategy_info in running_strategies:
            strategy_id = strategy_info['id']
            strategy_type = strategy_info.get('strategy_type', '')

            try:
                if strategy_type and strategy_type != 'IndicatorStrategy':
                    logger.info(f"Skip restore unsupported strategy type: id={strategy_id}, type={strategy_type}")
                    continue

                success = trading_executor.start_strategy(strategy_id)
                strategy_type_name = 'IndicatorStrategy'

                if success:
                    restored_count += 1
                    logger.info(f"[OK] {strategy_type_name} {strategy_id} restored")
                else:
                    logger.warning(f"[FAIL] {strategy_type_name} {strategy_id} restore failed (state may be stale)")
            except Exception as e:
                logger.error(f"Error restoring strategy {strategy_id}: {str(e)}")
                logger.error(traceback.format_exc())

        logger.info(f"Strategy restore completed: {restored_count}/{len(running_strategies)} restored")

    except Exception as e:
        logger.error(f"Failed to restore running strategies: {str(e)}")
        logger.error(traceback.format_exc())
        # Do not raise; avoid breaking app startup.


def init_redis_client():
    """
    初始化Redis客户端
    """
    import os

    # 检查是否启用Redis
    redis_enabled = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'

    if not redis_enabled:
        logger.info("Redis已禁用 (REDIS_ENABLED=false)")
        return None

    try:
        import redis

        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD', None)

        logger.info(f"连接Redis: {redis_host}:{redis_port}")

        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False,  # 保持二进制模式,JSON处理
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # 测试连接
        client.ping()
        logger.info("Redis连接成功")

        return client

    except Exception as e:
        logger.warning(f"Redis连接失败,将使用内存缓存: {e}")
        return None


def init_hama_scheduler():
    """
    初始化HAMA定时任务调度器(使用默认币种列表,不阻塞启动)
    """
    import os

    # 检查是否启用定时任务
    scheduler_enabled = os.getenv('HAMA_SCHEDULER_ENABLED', 'true').lower() == 'true'

    if not scheduler_enabled:
        logger.info("HAMA定时任务已禁用 (HAMA_SCHEDULER_ENABLED=false)")
        return None

    try:
        from app.services.hama_scheduler import init_scheduler
        from app.services.hama_cache import init_cache_manager

        # 初始化缓存管理器
        redis_client = get_redis_client()
        cache_ttl = int(os.getenv('HAMA_CACHE_TTL', 300))  # 默认5分钟
        init_cache_manager(redis_client, cache_ttl)

        # 使用默认币种列表(避免启动时获取永续合约列表,阻塞启动)
        # 调度器启动后会自动获取完整的币种列表
        symbols = []

        # 刷新间隔
        interval_minutes = int(os.getenv('HAMA_SCHEDULER_INTERVAL', 5))  # 默认5分钟

        # 缓存有效期 (超过这个时间才更新)
        cache_ttl_minutes = int(os.getenv('HAMA_CACHE_VALIDITY_MINUTES', 15))  # 默认15分钟

        # 初始化调度器 (传入 cache_ttl_minutes 参数)
        scheduler = init_scheduler(symbols, interval_minutes, cache_ttl_minutes)

        logger.info(f"HAMA调度器初始化完成, 币种数: {len(symbols)}, 间隔: {interval_minutes}分钟, 缓存有效期: {cache_ttl_minutes}分钟")

        return scheduler

    except Exception as e:
        logger.error(f"初始化HAMA调度器失败: {e}")
        return None


def get_redis_client():
    """获取Redis客户端"""
    global _redis_client
    return _redis_client


def get_hama_brave_monitor():
    """获取HAMA Brave监控器"""
    global _hama_brave_monitor
    return _hama_brave_monitor


def init_hama_brave_monitor():
    """
    初始化HAMA Brave监控器
    """
    import os

    # 检查是否启用Brave监控
    brave_monitor_enabled = os.getenv('BRAVE_MONITOR_ENABLED', 'true').lower() == 'true'

    if not brave_monitor_enabled:
        logger.info("HAMA Brave监控已禁用 (BRAVE_MONITOR_ENABLED=false)")
        return None

    try:
        from app.services.hama_brave_monitor import get_brave_monitor

        # 缓存有效期
        cache_ttl = int(os.getenv('BRAVE_MONITOR_CACHE_TTL', 900))  # 默认15分钟

        # 初始化监控器 (使用 SQLite)
        _brave_monitor = get_brave_monitor(redis_client=_redis_client, cache_ttl=cache_ttl, use_sqlite=True)

        logger.info(f"HAMA Brave监控器初始化完成, TTL={cache_ttl}秒, SQLite=启用")

        # 检查是否自动启动持续监控
        auto_start = os.getenv('BRAVE_MONITOR_AUTO_START', 'false').lower() == 'true'

        if auto_start:
            # 监控间隔（秒）
            interval = int(os.getenv('BRAVE_MONITOR_INTERVAL', '600'))  # 默认10分钟

            # 监控币种列表
            symbols_str = os.getenv('BRAVE_MONITOR_SYMBOLS', '')
            symbols = [s.strip() for s in symbols_str.split(',') if s.strip()] if symbols_str else None

            # 浏览器类型
            browser_type = os.getenv('BRAVE_MONITOR_BROWSER_TYPE', 'brave')

            # 使用默认币种列表（如果未指定）
            if not symbols:
                symbols = [
                    'BTCUSDT',
                    'ETHUSDT'
                ]

            logger.info(f"自动启动Brave持续监控: 币种={len(symbols)}个, 间隔={interval}秒")

            # 启动持续监控（后台线程）
            import threading
            monitor_thread = threading.Thread(
                target=_brave_monitor.start_monitoring,
                args=(symbols, interval, browser_type),
                daemon=True,
                name='BraveMonitorThread'
            )
            monitor_thread.start()

            logger.info("✅ Brave持续监控已在后台启动")

        return _brave_monitor

    except Exception as e:
        logger.error(f"初始化HAMA Brave监控器失败: {e}")
        return None


def get_hama_scheduler():
    """获取HAMA调度器"""
    global _hama_scheduler
    return _hama_scheduler


def start_hama_scheduler():
    """启动HAMA定时任务(后台线程,不阻塞Flask启动)"""
    import os
    import threading

    # 检查是否自动启动
    auto_start = os.getenv('HAMA_SCHEDULER_AUTO_START', 'true').lower() == 'true'

    if not auto_start:
        logger.info("HAMA定时任务自动启动已禁用 (HAMA_SCHEDULER_AUTO_START=false)")
        return

    scheduler = get_hama_scheduler()

    if not scheduler:
        logger.info("HAMA调度器未初始化")
        return

    # 在后台线程中启动,避免阻塞Flask应用
    def start_schedulerInBackground():
        try:
            scheduler.start()
            logger.info("HAMA定时任务已启动(后台)")
        except Exception as e:
            logger.error(f"启动HAMA定时任务失败: {e}")

    thread = threading.Thread(target=start_schedulerInBackground, daemon=True)
    thread.start()
    logger.info("HAMA定时任务正在后台启动...")


def stop_hama_scheduler():
    """停止HAMA定时任务"""
    scheduler = get_hama_scheduler()

    if scheduler and scheduler.scheduler.running:
        try:
            scheduler.stop()
            logger.info("HAMA定时任务已停止")
        except Exception as e:
            logger.error(f"停止HAMA定时任务失败: {e}")


def init_tv_cache_manager():
    """初始化TradingView缓存管理器"""
    global _tv_cache_manager, _redis_client

    if _tv_cache_manager is not None:
        return _tv_cache_manager

    if _redis_client is None:
        logger.warning("Redis客户端未初始化,跳过TradingView缓存管理器初始化")
        return None

    try:
        from app.services.tradingview_cache import init_cache_manager
        _tv_cache_manager = init_cache_manager(_redis_client, default_ttl=300)
        logger.info("TradingView缓存管理器已初始化")
    except Exception as e:
        logger.error(f"初始化TradingView缓存管理器失败: {e}")
        _tv_cache_manager = None

    return _tv_cache_manager


def get_tv_cache_manager():
    """获取TradingView缓存管理器"""
    global _tv_cache_manager
    return _tv_cache_manager


def init_tv_scheduler():
    """初始化TradingView定时任务(使用空列表,不阻塞启动)"""
    global _tv_scheduler, _tv_cache_manager

    if _tv_scheduler is not None:
        return _tv_scheduler

    # 先初始化缓存管理器
    if _tv_cache_manager is None:
        init_tv_cache_manager()

    if _tv_cache_manager is None:
        logger.warning("TradingView缓存管理器未初始化,跳过TradingView定时任务初始化")
        return None

    try:
        from app.services.tradingview_scheduler import init_scheduler
        # 使用空列表初始化,避免启动时获取币种列表阻塞
        _tv_scheduler = init_scheduler(_tv_cache_manager, refresh_interval=300)
        logger.info("TradingView定时任务已初始化")
    except Exception as e:
        logger.error(f"初始化TradingView定时任务失败: {e}")
        _tv_scheduler = None

    return _tv_scheduler


def get_tv_scheduler():
    """获取TradingView定时任务"""
    global _tv_scheduler
    return _tv_scheduler


def start_tv_scheduler():
    """启动TradingView定时任务(后台线程,不阻塞Flask启动)"""
    import threading
    global _tv_scheduler

    if _tv_scheduler is not None and _tv_scheduler.is_running:
        logger.warning("TradingView定时任务已在运行中")
        return

    # 在后台线程中启动,避免阻塞Flask应用
    def start_schedulerInBackground():
        try:
            init_tv_scheduler()
            if _tv_scheduler:
                _tv_scheduler.start()
                logger.info("TradingView定时任务已启动(后台)")
        except Exception as e:
            logger.error(f"启动TradingView定时任务失败: {e}")

    thread = threading.Thread(target=start_schedulerInBackground, daemon=True)
    thread.start()
    logger.info("TradingView定时任务正在后台启动...")


def stop_tv_scheduler():
    """停止TradingView定时任务"""
    scheduler = get_tv_scheduler()

    if scheduler and scheduler.is_running:
        try:
            scheduler.stop()
            logger.info("TradingView定时任务已停止")
        except Exception as e:
            logger.error(f"停止TradingView定时任务失败: {e}")


def get_long_logic_reader():
    """获取 LongLogic 读取器单例"""
    global _long_logic_reader
    return _long_logic_reader


def get_hama_health_checker():
    """获取 HAMA 健康检查器单例"""
    global _hama_health_checker
    return _hama_health_checker


def init_long_logic_reader():
    """
    初始化 LongLogic 配置读取器
    """
    try:
        from app.services.long_logic_reader import get_long_logic_reader as get_reader
        global _long_logic_reader
        _long_logic_reader = get_reader()
        logger.info("✅ LongLogic 配置读取器已初始化")
        return _long_logic_reader
    except Exception as e:
        logger.error(f"初始化 LongLogic 读取器失败: {e}", exc_info=True)
        return None


def init_hama_health_checker(long_logic_reader=None):
    """
    初始化 HAMA 数据健康检查器

    Args:
        long_logic_reader: LongLogic 读取器实例
    """
    try:
        from app.services.hama_health_checker import HAMAHealthChecker
        import os

        global _hama_health_checker

        # 检查间隔（秒），默认60秒
        check_interval = int(os.getenv('HAMA_HEALTH_CHECK_INTERVAL', '60'))

        # 失败阈值，默认3次
        failure_threshold = int(os.getenv('HAMA_HEALTH_CHECK_THRESHOLD', '3'))

        _hama_health_checker = HAMAHealthChecker(
            check_interval=check_interval,
            failure_threshold=failure_threshold
        )

        # 设置失败回调：重新读取 longLogic.txt
        if long_logic_reader:
            def reload_long_logic_on_failure(symbol, check_result):
                """HAMA 数据失败时重新加载 longLogic.txt"""
                try:
                    logger.info(f"🔄 触发 LongLogic 配置重载 (原因: {symbol} 数据异常)")
                    long_logic_reader.reload_config()
                    long_logic_reader.apply_config()
                except Exception as e:
                    logger.error(f"重载 LongLogic 配置失败: {e}", exc_info=True)

            _hama_health_checker.set_failure_callback(reload_long_logic_on_failure)

        logger.info(f"✅ HAMA 健康检查器已初始化 (间隔={check_interval}秒, 阈值={failure_threshold}次)")
        return _hama_health_checker

    except Exception as e:
        logger.error(f"初始化 HAMA 健康检查器失败: {e}", exc_info=True)
        return None


def start_hama_health_checker():
    """
    启动 HAMA 数据健康检查（后台线程）
    """
    import os

    # 检查是否启用健康检查
    health_check_enabled = os.getenv('HAMA_HEALTH_CHECK_ENABLED', 'true').lower() == 'true'

    if not health_check_enabled:
        logger.info("HAMA 健康检查已禁用 (HAMA_HEALTH_CHECK_ENABLED=false)")
        return

    health_checker = get_hama_health_checker()
    brave_monitor = get_hama_brave_monitor()

    if not health_checker:
        logger.warning("HAMA 健康检查器未初始化")
        return

    # 定义获取监控列表的函数
    def get_watchlist_func():
        try:
            if brave_monitor:
                import sqlite3
                import os

                # 从SQLite数据库获取最新的HAMA数据
                # 数据库路径固定为 backend_api_python/data/quantdinger.db
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'quantdinger.db')
                db_path = os.path.abspath(db_path)

                if not os.path.exists(db_path):
                    logger.warning(f"数据库文件不存在: {db_path}")
                    return []

                watchlist = []
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # 查询每个币种的最新记录（使用正确的列名）
                cursor.execute('''
                    SELECT symbol, price, hama_trend, hama_color, monitored_at
                    FROM hama_monitor_cache
                    WHERE symbol IN (
                        SELECT DISTINCT symbol FROM hama_monitor_cache
                    )
                    ORDER BY symbol, monitored_at DESC
                ''')

                rows = cursor.fetchall()

                # 使用字典跟踪已处理的币种（只取每个币种的最新记录）
                symbol_data = {}
                for row in rows:
                    symbol, price, trend, color, monitored_at = row
                    if symbol not in symbol_data:
                        symbol_data[symbol] = {
                            'symbol': symbol,
                            'current_price': price,
                            'hama_color': color,
                            'hama_trend': trend,
                            'timestamp': monitored_at
                        }

                watchlist = list(symbol_data.values())
                conn.close()

                logger.debug(f"从SQLite获取到 {len(watchlist)} 个币种的监控数据")
                return watchlist
            else:
                logger.warning("Brave 监控器未初始化，无法获取监控列表")
                return []
        except Exception as e:
            logger.error(f"获取监控列表失败: {e}", exc_info=True)
            return []

    # 启动健康检查
    try:
        health_checker.start(get_watchlist_func)
        logger.info("✅ HAMA 健康检查已启动 (后台轮询)")
    except Exception as e:
        logger.error(f"启动 HAMA 健康检查失败: {e}", exc_info=True)


def create_app(config_name='default'):
    """
    Flask application factory.

    Args:
        config_name: config name

    Returns:
        Flask app
    """
    global _redis_client, _hama_scheduler, _tv_cache_manager, _tv_scheduler, _hama_brave_monitor

    app = Flask(__name__, static_folder=None)  # 禁用默认静态文件夹

    app.config['JSON_AS_ASCII'] = False

    CORS(app)

    setup_logger()

    from app.routes import register_routes
    register_routes(app)

    # Startup hooks.
    with app.app_context():
        # 1. 初始化Redis客户端
        _redis_client = init_redis_client()

        # 2. 初始化HAMA调度器
        _hama_scheduler = init_hama_scheduler()

        # 3. 启动HAMA定时任务
        start_hama_scheduler()

        # 4. 初始化HAMA Brave监控器
        _hama_brave_monitor = init_hama_brave_monitor()

        # 5. 初始化邮件通知器
        import os
        try:
            from app.services.hama_email_notifier import get_hama_email_notifier
            email_notifier = get_hama_email_notifier()
            logger.info("✅ HAMA 邮件通知器已初始化")
        except Exception as e:
            logger.error(f"初始化 HAMA 邮件通知器失败: {e}")

        # 6. 启动 HAMA 监控 Worker (后台自动监控 + 邮件通知)
        enable_hama_worker = os.getenv('ENABLE_HAMA_WORKER', 'true').lower() == 'true'
        if enable_hama_worker and _hama_brave_monitor:
            try:
                from app.services.hama_monitor_worker import get_hama_monitor_worker
                worker = get_hama_monitor_worker()
                worker.start()
                logger.info("✅ HAMA 监控 Worker 已启动 (后台自动监控 + 邮件通知)")
            except Exception as e:
                logger.error(f"启动 HAMA 监控 Worker 失败: {e}")

        # 6. 初始化并启动TradingView定时任务（暂时禁用）
        # init_tv_cache_manager()
        # start_tv_scheduler()

        # 6. 启动实时价格服务(暂时禁用)
        import os
        # 暂时禁用实时价格服务和 SSE
        enable_realtime_price = False  # os.getenv('ENABLE_REALTIME_PRICE', 'true').lower() == 'true'
        if False:  # enable_realtime_price
            try:
                from app.services.realtime_price import start_realtime_price_service
                from app.services.price_broadcaster import get_price_broadcaster

                # 启动价格广播器
                redis_host = os.getenv('REDIS_HOST', 'host.docker.internal')
                redis_port = int(os.getenv('REDIS_PORT', 6379))
                broadcaster = get_price_broadcaster()
                broadcaster.start(redis_host=redis_host, redis_port=redis_port)

                # 使用默认的热门币种列表,避免启动时获取永续合约列表阻塞
                realtime_symbols = [
                    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
                    'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
                    'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'ATOMUSDT',
                    'UNIUSDT', 'LTCUSDT', 'BCHUSDT', 'FILUSDT',
                    # 添加涨幅榜常见币种
                    'GMTUSDT', 'EGLDUSDT', 'IDUSDT', 'XTZUSDT',
                    'FLOWUSDT', '1INCHUSDT', 'NEARUSDT', 'APEUSDT',
                    'SANDUSDT', 'MANAUSDT', 'AXSUSDT', 'SHIBUSDT',
                    'TRXUSDT', 'ETCUSDT', 'XLMUSDT', 'VETUSDT'
                ]

                start_realtime_price_service(realtime_symbols)
                logger.info(f"实时价格服务已启动, 监控 {len(realtime_symbols)} 个币种 (默认列表)")
            except Exception as e:
                logger.warning(f"启动实时价格服务失败: {e}")

        # 6. 启动其他后台任务
        start_pending_order_worker()
        start_reflection_worker()
        restore_running_strategies()

        # 7. 初始化 LongLogic 配置读取器
        _long_logic_reader = init_long_logic_reader()

        # 8. 初始化并启动 HAMA 健康检查（自动重载 longLogic.txt）
        _hama_health_checker = init_hama_health_checker(long_logic_reader=_long_logic_reader)
        start_hama_health_checker()

        # 9. 启动截图缓存 Worker (已暂停)
        try:
            logger.info("⏸️  截图缓存 Worker 已禁用 (如需启用，请取消注释)")
            # from app.routes.tradingview_scanner import start_screenshot_worker
            # start_screenshot_worker()
            # logger.info("✅ 截图缓存 Worker 已启动")
        except Exception as e:
            logger.error(f"❌ 启动截图缓存 Worker 失败: {e}", exc_info=True)

    return app

