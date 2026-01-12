"""
TradingView Scanner API路由
提供无需登录的大规模加密货币数据获取接口
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.services.tradingview_scanner_service import (
    TradingViewScannerAPI,
    get_top_perpetuals,
    get_default_watchlist,
    get_top_gainers
)
from app.services.tradingview_cache import get_cache_manager as get_tv_cache_manager_impl
from app import get_tv_cache_manager
from app.utils.logger import get_logger
from app import get_redis_client
import json

logger = get_logger(__name__)

tradingview_scanner_bp = Blueprint('tradingview_scanner', __name__)


def _redis_available():
    """检查Redis是否可用"""
    redis_client = get_redis_client()
    if not redis_client:
        return False
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def _redis_get(key):
    """从Redis获取数据"""
    if not _redis_available():
        return None
    try:
        redis_client = get_redis_client()
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Redis获取失败: {e}")
        return None


def _redis_set(key, data, ttl=300):
    """设置数据到Redis"""
    if not _redis_available():
        return False
    try:
        redis_client = get_redis_client()
        redis_client.setex(key, ttl, json.dumps(data))
        return True
    except Exception as e:
        logger.warning(f"Redis设置失败: {e}")
        return False


# 内存缓存 (备用,当Redis不可用时)
_top_gainers_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=3)
}

_perpetuals_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=5)
}

_watchlist_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=5)
}


@tradingview_scanner_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    """
    获取默认关注列表 (带5分钟缓存)

    查询参数:
    - limit: 限制返回数量 (默认20)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 20,
        "data": [...],
        "cached": true
    }
    """
    global _watchlist_cache

    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 最多100个

        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'
        current_time = datetime.now()

        # 检查缓存
        if not force_refresh and _watchlist_cache['data'] is not None:
            cache_age = current_time - _watchlist_cache['timestamp']
            if cache_age < _watchlist_cache['duration']:
                logger.info(f"使用缓存的watchlist数据 (缓存时间: {cache_age.seconds}秒)")
                watchlist = _watchlist_cache['data'][:limit]

                return jsonify({
                    'success': True,
                    'count': len(watchlist),
                    'data': watchlist,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Default Watchlist (Cached)'
                })

        # 重新获取数据
        logger.info(f"获取默认关注列表, limit={limit}")

        # 获取完整数据并缓存
        full_watchlist = get_default_watchlist(limit=100)
        _watchlist_cache['data'] = full_watchlist
        _watchlist_cache['timestamp'] = current_time

        watchlist = full_watchlist[:limit]

        return jsonify({
            'success': True,
            'count': len(watchlist),
            'data': watchlist,
            'cached': False,
            'source': 'TradingView Default Watchlist'
        })

    except Exception as e:
        logger.error(f"获取默认关注列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/perpetuals', methods=['GET'])
def get_perpetuals():
    """
    获取币安永续合约列表 (使用Redis缓存)

    查询参数:
    - limit: 限制返回数量 (默认50)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 50,
        "data": [...],
        "cached": true
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # 最多200个

        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'
        current_time = datetime.now()

        # 获取币种级别缓存管理器
        tv_cache = get_tv_cache_manager() or get_tv_cache_manager_impl()

        # 优先使用币种级别 Redis 缓存
        if not force_refresh and tv_cache and tv_cache.is_available():
            try:
                # 获取所有已缓存的币种
                cached_symbols = tv_cache.get_all_cached_symbols()

                if cached_symbols and len(cached_symbols) > 0:
                    # 批量获取币种数据
                    cached_coins = tv_cache.get_coins(cached_symbols)

                    if cached_coins and len(cached_coins) > 0:
                        # 转换为列表
                        perpetuals = list(cached_coins.values())

                        # 按成交量排序
                        perpetuals.sort(key=lambda x: x.get('volume', 0), reverse=True)

                        # 限制返回数量
                        perpetuals = perpetuals[:limit]

                        logger.info(f"使用币种级别 Redis 缓存: {len(perpetuals)} 个币种")

                        return jsonify({
                            'success': True,
                            'count': len(perpetuals),
                            'data': perpetuals,
                            'cached': True,
                            'cache_age_seconds': 0,
                            'source': 'TradingView Perpetuals (Coin-level Redis Cache)'
                        })
            except Exception as e:
                logger.warning(f"读取币种级别缓存失败: {e}")

        # 检查内存缓存 (备用)
        if not force_refresh and _perpetuals_mem_cache['data'] is not None:
            cache_age = current_time - _perpetuals_mem_cache['timestamp']
            if cache_age < _perpetuals_mem_cache['duration']:
                logger.info(f"使用内存缓存的永续合约数据 (缓存时间: {cache_age.seconds}秒)")
                perpetuals = _perpetuals_mem_cache['data'][:limit]

                return jsonify({
                    'success': True,
                    'count': len(perpetuals),
                    'data': perpetuals,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Perpetuals (Memory Cache)'
                })

        # 重新获取数据
        logger.info(f"获取永续合约列表, limit={limit}")

        # 获取完整数据并缓存(最多200个)
        full_perpetuals = get_top_perpetuals(limit=200)

        # 存入币种级别 Redis 缓存
        try:
            if tv_cache and tv_cache.is_available():
                cached_count = tv_cache.set_coins(full_perpetuals, ttl=300)
                logger.info(f"永续合约数据已存入币种级别 Redis 缓存: {cached_count} 个币种")
            else:
                logger.warning("币种级别缓存管理器不可用")
        except Exception as e:
            logger.warning(f"存入币种级别 Redis 缓存失败: {e}")

        # 存入内存缓存
        _perpetuals_mem_cache['data'] = full_perpetuals
        _perpetuals_mem_cache['timestamp'] = current_time

        perpetuals = full_perpetuals[:limit]

        return jsonify({
            'success': True,
            'count': len(perpetuals),
            'data': perpetuals,
            'cached': False,
            'source': 'TradingView Perpetuals'
        })

    except Exception as e:
        logger.error(f"获取永续合约列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/top-gainers', methods=['GET'])
def get_gainers():
    """
    获取涨幅榜 (使用Redis缓存)

    查询参数:
    - limit: 限制返回数量 (默认20)
    - min_change: 最小涨跌幅百分比 (可选)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 20,
        "data": [...],
        "cached": true
    }
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 最多100个

        min_change = request.args.get('min_change', type=float)
        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'

        current_time = datetime.now()

        # 获取币种级别缓存管理器
        tv_cache = get_tv_cache_manager() or get_tv_cache_manager_impl()

        # 优先使用币种级别 Redis 缓存
        if not force_refresh and tv_cache and tv_cache.is_available():
            try:
                # 获取所有已缓存的币种
                cached_symbols = tv_cache.get_all_cached_symbols()

                if cached_symbols and len(cached_symbols) > 0:
                    # 批量获取币种数据
                    cached_coins = tv_cache.get_coins(cached_symbols)

                    if cached_coins and len(cached_coins) > 0:
                        # 转换为列表
                        gainers = list(cached_coins.values())

                        # 按涨跌幅排序
                        gainers.sort(key=lambda x: x.get('change_percentage', 0), reverse=True)

                        # 应用过滤
                        if min_change is not None:
                            gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

                        # 限制返回数量
                        gainers = gainers[:limit]

                        logger.info(f"使用币种级别 Redis 缓存: {len(gainers)} 个币种")

                        return jsonify({
                            'success': True,
                            'count': len(gainers),
                            'data': gainers,
                            'cached': True,
                            'cache_age_seconds': 0,
                            'source': 'TradingView Scanner - Top Gainers (Coin-level Redis Cache)'
                        })
            except Exception as e:
                logger.warning(f"读取币种级别缓存失败: {e}")

        # 检查内存缓存 (备用)
        if not force_refresh and _top_gainers_mem_cache['data'] is not None:
            cache_age = current_time - _top_gainers_mem_cache['timestamp']
            if cache_age < _top_gainers_mem_cache['duration']:
                logger.info(f"使用内存缓存的涨幅榜数据 (缓存时间: {cache_age.seconds}秒)")
                gainers = _top_gainers_mem_cache['data'].copy()

                # 应用过滤
                if min_change is not None:
                    gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

                gainers = gainers[:limit]

                return jsonify({
                    'success': True,
                    'count': len(gainers),
                    'data': gainers,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Scanner - Top Gainers (Memory Cache)'
                })

        # 缓存失效或强制刷新,重新获取数据
        logger.info(f"获取涨幅榜, limit={limit}, min_change={min_change}")

        gainers = get_top_gainers(limit=100)  # 获取更多然后过滤

        # 存入币种级别 Redis 缓存
        try:
            if tv_cache and tv_cache.is_available():
                cached_count = tv_cache.set_coins(gainers, ttl=180)
                logger.info(f"涨幅榜数据已存入币种级别 Redis 缓存: {cached_count} 个币种")
            else:
                logger.warning("币种级别缓存管理器不可用")
        except Exception as e:
            logger.warning(f"存入币种级别 Redis 缓存失败: {e}")

        # 存入内存缓存
        _top_gainers_mem_cache['data'] = gainers
        _top_gainers_mem_cache['timestamp'] = current_time

        # 应用过滤
        if min_change is not None:
            gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

        gainers = gainers[:limit]

        return jsonify({
            'success': True,
            'count': len(gainers),
            'data': gainers,
            'cached': False,
            'source': 'TradingView Scanner - Top Gainers'
        })

    except Exception as e:
        logger.error(f"获取涨幅榜失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/symbols', methods=['POST'])
def get_symbols_data():
    """
    获取指定币种的数据

    请求体:
    {
        "symbols": ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", ...]
    }

    返回:
    {
        "success": true,
        "count": 2,
        "data": [...]
    }
    """
    try:
        data = request.get_json()

        if not data or 'symbols' not in data:
            return jsonify({
                'success': False,
                'error': '请提供symbols列表'
            }), 400

        symbols = data['symbols']

        if not isinstance(symbols, list):
            return jsonify({
                'success': False,
                'error': 'symbols必须是数组'
            }), 400

        symbols = symbols[:100]  # 最多100个

        logger.info(f"获取指定币种数据, 数量={len(symbols)}")

        api = TradingViewScannerAPI()
        result = api.get_crypto_data(symbols)

        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'source': 'TradingView Scanner'
        })

    except Exception as e:
        logger.error(f"获取指定币种数据失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    获取统计信息

    返回:
    {
        "success": true,
        "data": {
            "total_perpetuals": 200,
            "top_gainers": [...]
        }
    }
    """
    try:
        logger.info("获取统计信息")

        # 获取一些统计数据
        api = TradingViewScannerAPI()

        # 获取前20个作为样本
        sample = api.get_default_watchlist(limit=20)

        # 计算统计
        if sample:
            avg_change = sum(c.get('change_percentage', 0) for c in sample) / len(sample)
            gainers_count = sum(1 for c in sample if c.get('change_percentage', 0) > 0)
            losers_count = sum(1 for c in sample if c.get('change_percentage', 0) < 0)

            stats_data = {
                'sample_size': len(sample),
                'avg_change': round(avg_change, 2),
                'gainers_count': gainers_count,
                'losers_count': losers_count,
                'top_gainer': max(sample, key=lambda x: x.get('change_percentage', 0)) if sample else None,
                'top_loser': min(sample, key=lambda x: x.get('change_percentage', 0)) if sample else None
            }
        else:
            stats_data = {}

        return jsonify({
            'success': True,
            'data': stats_data,
            'source': 'TradingView Scanner'
        })

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
