"""
涨幅榜和 HAMA 指标分析 API 路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.utils.logger import get_logger
from app.services.hama_cache import get_cache_manager

logger = get_logger(__name__)

gainer_analysis_bp = Blueprint('gainer_analysis', __name__)

# HAMA分析缓存 (5分钟有效期) - 备用内存缓存
hama_analysis_cache = {}
CACHE_DURATION = timedelta(minutes=5)

# Redis缓存管理器
hama_redis_cache = get_cache_manager()


@gainer_analysis_bp.route('/top-gainers', methods=['GET'])
def get_top_gainers():
    """
    获取币安涨幅榜并分析 HAMA 指标

    参数:
        limit: 返回数量，默认 20
        market: 市场类型 (spot/futures)，默认 spot
    """
    try:
        # 获取参数
        limit = int(request.args.get('limit', 20))
        market = request.args.get('market', 'spot')  # spot 或 futures

        if limit < 1 or limit > 100:
            return jsonify({
                'code': 0,
                'msg': 'limit must be between 1 and 100',
                'data': None
            }), 400

        from app.services.binance_gainer import BinanceGainerService

        # 直接获取基础数据，不做HAMA分析（更快）
        gainer_service = BinanceGainerService()

        if market == 'futures':
            top_gainers = gainer_service.get_top_gainers_futures(limit)
        else:
            top_gainers = gainer_service.get_top_gainers(limit, market_type='spot')

        if not top_gainers:
            return jsonify({
                'code': 0,
                'msg': 'Failed to fetch top gainers',
                'data': None
            }), 500

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'count': len(top_gainers),
                'timestamp': datetime.now().isoformat(),
                'market': market,
                'symbols': top_gainers
            }
        })

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return jsonify({
            'code': 0,
            'msg': f'Invalid parameter: {str(e)}',
            'data': None
        }), 400
    except Exception as e:
        logger.error(f"Error in get_top_gainers: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/analyze-symbol', methods=['POST'])
def analyze_symbol():
    """
    分析单个币种的 HAMA 指标 (带5分钟缓存)

    请求体:
        {
            "symbol": "BTCUSDT",
            "force_refresh": false  // 可选,强制刷新缓存
        }
    """
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol', '').strip().upper()
        force_refresh = data.get('force_refresh', False)

        if not symbol:
            return jsonify({
                'code': 0,
                'msg': 'symbol is required',
                'data': None
            }), 400

        current_time = datetime.now()

        # 优先使用Redis缓存
        if hama_redis_cache and not force_refresh:
            cached_data = hama_redis_cache.get(symbol)
            if cached_data:
                logger.info(f"使用Redis缓存的HAMA分析数据: {symbol}")
                cached_data['timestamp'] = current_time.isoformat()
                cached_data['cached'] = True
                cached_data['cache_source'] = 'redis'
                return jsonify({
                    'code': 1,
                    'msg': 'success (cached from redis)',
                    'data': cached_data
                })

        # 备用: 检查内存缓存
        if not force_refresh and symbol in hama_analysis_cache:
            cached_data, cached_time = hama_analysis_cache[symbol]
            if current_time - cached_time < CACHE_DURATION:
                logger.info(f"使用内存缓存的HAMA分析数据: {symbol}")
                cached_data['timestamp'] = current_time.isoformat()
                cached_data['cached'] = True
                cached_data['cache_source'] = 'memory'
                return jsonify({
                    'code': 1,
                    'msg': 'success (cached from memory)',
                    'data': cached_data
                })

        # 执行分析
        from app.services.tradingview_service import TradingViewDataService

        tv_service = TradingViewDataService()
        analysis = tv_service.get_hama_cryptocurrency_signals(symbol)
        conditions = tv_service.check_hama_conditions(analysis)

        result_data = {
            'symbol': symbol,
            'hama_analysis': analysis,
            'conditions': conditions,
            'timestamp': current_time.isoformat(),
            'cached': False
        }

        # 存入Redis缓存
        if hama_redis_cache:
            hama_redis_cache.set(symbol, result_data)

        # 备用: 存入内存缓存
        hama_analysis_cache[symbol] = (result_data, current_time)

        # 清理过期缓存
        _clean_expired_cache()

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': result_data
        })

    except Exception as e:
        logger.error(f"Error in analyze_symbol: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


def _clean_expired_cache():
    """清理过期的缓存数据"""
    current_time = datetime.now()
    expired_symbols = []
    for symbol, (data, cached_time) in hama_analysis_cache.items():
        if current_time - cached_time >= CACHE_DURATION:
            expired_symbols.append(symbol)

    for symbol in expired_symbols:
        del hama_analysis_cache[symbol]

    if expired_symbols:
        logger.info(f"清理过期缓存: {len(expired_symbols)} 个币种")


@gainer_analysis_bp.route('/refresh', methods=['POST'])
def refresh_analysis():
    """
    刷新涨幅榜和分析数据

    请求体:
        {
            "limit": 20,
            "market": "spot"
        }
    """
    try:
        data = request.get_json() or {}
        limit = int(data.get('limit', 20))
        market = data.get('market', 'spot')

        from app.services.tradingview_service import get_binance_top_gainers_with_hama_analysis

        result = get_binance_top_gainers_with_hama_analysis(limit)

        if result['success']:
            # 添加是否满足条件的标记
            for item in result['data']:
                item['is_top_gainer'] = item['price_change_percent'] > 5
                item['has_strong_buy_signal'] = item['conditions']['meets_buy_criteria']

            return jsonify({
                'code': 1,
                'msg': 'success',
                'data': {
                    'count': len(result['data']),
                    'timestamp': result['timestamp'],
                    'market': market,
                    'symbols': result['data']
                }
            })
        else:
            return jsonify({
                'code': 0,
                'msg': result.get('error', 'Failed to refresh'),
                'data': None
            }), 500

    except Exception as e:
        logger.error(f"Error in refresh_analysis: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/preload', methods=['POST'])
def preload_symbols():
    """
    预加载指定币种列表的HAMA分析数据

    请求体:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", ...]
        }

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "total": 78,
                "success": 75,
                "failed": 3,
                "failed_symbols": ["XXXUSDT", ...],
                "duration": 120.5
            }
        }
    """
    import time
    from app.services.tradingview_service import TradingViewDataService

    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', [])

        if not symbols:
            return jsonify({
                'code': 0,
                'msg': 'symbols is required',
                'data': None
            }), 400

        logger.info(f"开始预加载 {len(symbols)} 个币种的HAMA分析数据")
        start_time = time.time()

        tv_service = TradingViewDataService()
        success_count = 0
        failed_symbols = []

        for symbol in symbols:
            try:
                # 强制刷新并缓存
                analysis = tv_service.get_hama_cryptocurrency_signals(symbol)
                conditions = tv_service.check_hama_conditions(analysis)

                result_data = {
                    'symbol': symbol,
                    'hama_analysis': analysis,
                    'conditions': conditions,
                    'timestamp': datetime.now().isoformat(),
                    'cached': False
                }

                # 存入缓存
                hama_analysis_cache[symbol] = (result_data, datetime.now())
                success_count += 1

                logger.info(f"预加载成功: {symbol} ({success_count}/{len(symbols)})")

            except Exception as e:
                logger.error(f"预加载失败: {symbol} - {e}")
                failed_symbols.append(symbol)

        # 清理过期缓存
        _clean_expired_cache()

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"预加载完成: 成功 {success_count}/{len(symbols)}, 耗时 {duration:.2f}秒")

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'total': len(symbols),
                'success': success_count,
                'failed': len(failed_symbols),
                'failed_symbols': failed_symbols,
                'duration': round(duration, 2)
            }
        })

    except Exception as e:
        logger.error(f"Error in preload_symbols: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/analyze-batch', methods=['POST'])
def analyze_batch():
    """
    批量分析多个币种的HAMA指标

    请求体:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "force_refresh": false  // 可选
        }

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "results": {
                    "BTCUSDT": {...},
                    "ETHUSDT": {...},
                    ...
                },
                "summary": {
                    "total": 3,
                    "success": 3,
                    "failed": 0,
                    "cached": 2
                }
            }
        }
    """
    from app.services.tradingview_service import TradingViewDataService

    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', [])
        force_refresh = data.get('force_refresh', False)

        if not symbols:
            return jsonify({
                'code': 0,
                'msg': 'symbols is required',
                'data': None
            }), 400

        logger.info(f"批量分析 {len(symbols)} 个币种")

        tv_service = TradingViewDataService()
        results = {}
        success_count = 0
        failed_count = 0
        cached_count = 0

        for symbol in symbols:
            try:
                # 优先使用 Redis 缓存
                if not force_refresh:
                    cached_data = hama_redis_cache.get(symbol)
                    if cached_data and isinstance(cached_data, dict):
                        results[symbol] = cached_data
                        results[symbol]['cached'] = True
                        cached_count += 1
                        success_count += 1
                        logger.debug(f"Redis缓存命中: {symbol}")
                        continue

                # 检查内存缓存 (备用)
                current_time = datetime.now()
                if not force_refresh and symbol in hama_analysis_cache:
                    cached_data, cached_time = hama_analysis_cache[symbol]
                    if current_time - cached_time < CACHE_DURATION:
                        results[symbol] = cached_data
                        results[symbol]['cached'] = True
                        cached_count += 1
                        success_count += 1
                        continue

                # 执行分析
                logger.info(f"计算HAMA指标: {symbol} (无缓存)")
                analysis = tv_service.get_hama_cryptocurrency_signals(symbol)
                conditions = tv_service.check_hama_conditions(analysis)

                result_data = {
                    'symbol': symbol,
                    'hama_analysis': analysis,
                    'conditions': conditions,
                    'timestamp': current_time.isoformat(),
                    'cached': False
                }

                # 存入内存缓存
                hama_analysis_cache[symbol] = (result_data, current_time)

                # 存入 Redis 缓存 (5分钟TTL)
                hama_redis_cache.set(symbol, result_data, ttl=300)

                results[symbol] = result_data
                success_count += 1

            except Exception as e:
                logger.error(f"批量分析失败: {symbol} - {e}")
                results[symbol] = {'error': str(e)}
                failed_count += 1

        # 清理过期缓存
        _clean_expired_cache()

        logger.info(f"批量分析完成: 总数{len(symbols)}, 成功{success_count}, 缓存{cached_count}")

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'results': results,
                'summary': {
                    'total': len(symbols),
                    'success': success_count,
                    'failed': failed_count,
                    'cached': cached_count
                }
            }
        })

    except Exception as e:
        logger.error(f"Error in analyze_batch: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/cache-stats', methods=['GET'])
def get_cache_stats():
    """
    获取缓存统计信息

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "cached_symbols": 78,
                "cache_duration_minutes": 5,
                "oldest_cache": "2026-01-10T05:00:00",
                "newest_cache": "2026-01-10T05:25:00"
            }
        }
    """
    try:
        current_time = datetime.now()

        if not hama_analysis_cache:
            return jsonify({
                'code': 1,
                'msg': 'success',
                'data': {
                    'cached_symbols': 0,
                    'cache_duration_minutes': int(CACHE_DURATION.total_seconds() / 60),
                    'oldest_cache': None,
                    'newest_cache': None,
                    'symbols': []
                }
            })

        # 统计缓存信息
        oldest_time = None
        newest_time = None
        symbols = []

        for symbol, (data, cached_time) in hama_analysis_cache.items():
            symbols.append(symbol)
            if oldest_time is None or cached_time < oldest_time:
                oldest_time = cached_time
            if newest_time is None or cached_time > newest_time:
                newest_time = cached_time

        # 如果Redis可用,优先返回Redis统计
        if hama_redis_cache and hama_redis_cache.is_available():
            redis_stats = hama_redis_cache.get_stats()
            return jsonify({
                'code': 1,
                'msg': 'success',
                'data': {
                    'cache_type': 'redis',
                    'cached_symbols': redis_stats['cached_symbols'],
                    'cache_duration_minutes': redis_stats['cache_ttl_minutes'],
                    'symbols': hama_redis_cache.get_cached_symbols(),
                    'memory_cache_fallback': len(hama_analysis_cache)
                }
            })

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'cache_type': 'memory',
                'cached_symbols': len(hama_analysis_cache),
                'cache_duration_minutes': int(CACHE_DURATION.total_seconds() / 60),
                'oldest_cache': oldest_time.isoformat() if oldest_time else None,
                'newest_cache': newest_time.isoformat() if newest_time else None,
                'symbols': sorted(symbols)
            }
        })

    except Exception as e:
        logger.error(f"Error in get_cache_stats: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """
    启动HAMA定时刷新任务

    请求体:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", ...],  // 可选,默认使用配置的列表
            "interval_minutes": 5  // 可选,默认5分钟
        }

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "status": "started",
                "symbols_count": 78,
                "interval_minutes": 5
            }
        }
    """
    from app.services.hama_scheduler import get_scheduler

    try:
        data = request.get_json() or {}
        symbols = data.get('symbols')
        interval_minutes = data.get('interval_minutes', 5)

        scheduler = get_scheduler()

        if not scheduler:
            return jsonify({
                'code': 0,
                'msg': 'Scheduler not initialized. Please check Redis configuration.',
                'data': None
            }), 500

        # 更新配置
        if symbols:
            scheduler.update_symbols(symbols)
        if interval_minutes != scheduler.interval_minutes:
            scheduler.set_interval(interval_minutes)

        # 启动调度器(如果还未启动)
        if not scheduler.scheduler.running:
            scheduler.start()

        status = scheduler.get_status()

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'status': 'started' if status['running'] else 'running',
                'symbols_count': status['symbols_count'],
                'interval_minutes': status['interval_minutes'],
                'cache_stats': status['cache_stats']
            }
        })

    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """
    停止HAMA定时刷新任务

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "status": "stopped"
            }
        }
    """
    from app.services.hama_scheduler import get_scheduler

    try:
        scheduler = get_scheduler()

        if not scheduler:
            return jsonify({
                'code': 0,
                'msg': 'Scheduler not initialized',
                'data': None
            }), 500

        scheduler.stop()

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'status': 'stopped'
            }
        })

    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@gainer_analysis_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """
    获取定时任务状态

    返回:
        {
            "code": 1,
            "msg": "success",
            "data": {
                "running": true,
                "symbols_count": 78,
                "interval_minutes": 5,
                "cache_stats": {...}
            }
        }
    """
    from app.services.hama_scheduler import get_scheduler

    try:
        scheduler = get_scheduler()

        if not scheduler:
            return jsonify({
                'code': 0,
                'msg': 'Scheduler not initialized',
                'data': None
            }), 500

        status = scheduler.get_status()

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': status
        })

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500

