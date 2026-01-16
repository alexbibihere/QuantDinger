#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 行情 API 路由

提供类似 TradingView 的 HAMA 行情数据接口
"""
from flask import Blueprint, request, jsonify
import traceback
import random
from app.services.kline import KlineService
from app.services.hama_calculator import calculate_hama_from_ohlcv
from app.utils.logger import get_logger
from app.data.market_symbols_seed import get_hot_symbols
import os

logger = get_logger(__name__)

hama_market_bp = Blueprint('hama_market', __name__, url_prefix='/api/hama-market')
kline_service = KlineService()

# 模拟数据模式（用于演示）
DEMO_MODE = os.getenv('HAMA_DEMO_MODE', 'false').lower() == 'true'

# 默认监控币种列表
DEFAULT_SYMBOLS = [
    'BTCUSDT',
    'ETHUSDT',
    'BNBUSDT',
    'SOLUSDT',
    'XRPUSDT',
    'ADAUSDT',
    'DOGEUSDT',
    'AVAXUSDT',
    'DOTUSDT',
    'LINKUSDT'
]


def generate_demo_hama_data(symbol):
    """
    生成演示用的 HAMA 数据
    """
    # 基础价格（根据币种不同）
    base_prices = {
        'BTCUSDT': 95000,
        'ETHUSDT': 3200,
        'BNBUSDT': 650,
        'SOLUSDT': 145,
        'XRPUSDT': 2.5,
        'ADAUSDT': 0.95,
        'DOGEUSDT': 0.32,
        'AVAXUSDT': 38,
        'DOTUSDT': 7.5,
        'LINKUSDT': 14.5
    }

    base_price = base_prices.get(symbol, 100)

    # 生成随机波动
    price_change = random.uniform(-0.05, 0.05)
    current_price = base_price * (1 + price_change)

    # 生成 HAMA 数据
    hama_open = current_price * random.uniform(0.998, 1.002)
    hama_close = current_price * random.uniform(0.998, 1.002)
    hama_high = max(hama_open, hama_close) * random.uniform(1.0, 1.005)
    hama_low = min(hama_open, hama_close) * random.uniform(0.995, 1.0)
    hama_ma = current_price * random.uniform(0.98, 1.02)

    # 判断颜色
    color = 'green' if hama_close > hama_open else 'red'

    # 生成布林带
    bb_basis = current_price
    bb_width = random.uniform(0.03, 0.08)
    bb_upper = bb_basis * (1 + bb_width)
    bb_lower = bb_basis * (1 - bb_width)

    # 判断趋势
    direction = 'up' if hama_close > hama_ma else 'down'
    is_rising = hama_close > hama_ma

    # 生成交叉信号（5%概率）
    cross_up = random.random() < 0.05
    cross_down = random.random() < 0.05 if not cross_up else False

    return {
        'symbol': symbol,
        'price': current_price,
        'change_percentage': price_change * 100,
        'hama': {
            'open': hama_open,
            'high': hama_high,
            'low': hama_low,
            'close': hama_close,
            'ma': hama_ma,
            'color': color,
            'cross_up': cross_up,
            'cross_down': cross_down
        },
        'trend': {
            'direction': direction,
            'rising': is_rising,
            'falling': not is_rising
        },
        'bollinger_bands': {
            'upper': bb_upper,
            'basis': bb_basis,
            'lower': bb_lower,
            'width': bb_width,
            'squeeze': bb_width < 0.04,
            'expansion': bb_width > 0.06
        }
    }


@hama_market_bp.route('/watchlist', methods=['GET'])
def get_hama_watchlist():
    """
    获取 HAMA 监控列表

    参数:
        symbols: 币种列表，逗号分隔 (可选)
        market: 市场 (spot/futures, 默认 spot)

    返回:
    {
        "success": true,
        "data": {
            "watchlist": [
                {
                    "symbol": "BTCUSDT",
                    "price": 3000.0,
                    "change_percentage": 2.5,
                    "hama": {
                        "open": 2995.0,
                        "high": 3005.0,
                        "low": 2990.0,
                        "close": 3000.0,
                        "ma": 2998.0,
                        "color": "green",
                        "cross_up": false,
                        "cross_down": false
                    },
                    "trend": {
                        "direction": "up",
                        "rising": true,
                        "falling": false
                    },
                    "bollinger_bands": {
                        "upper": 3100.0,
                        "basis": 3000.0,
                        "lower": 2900.0,
                        "width": 0.067,
                        "squeeze": false,
                        "expansion": false
                    }
                }
            ]
        }
    }
    """
    try:
        # 获取参数
        symbols_param = request.args.get('symbols')
        market = request.args.get('market', 'spot')

        # 确定要查询的币种列表
        if symbols_param:
            symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
        else:
            symbols = DEFAULT_SYMBOLS

        logger.info(f"获取 HAMA 监控列表, 币种数量: {len(symbols)}, 市场: {market}")

        watchlist = []

        for symbol in symbols:
            try:
                # DEMO模式或无数据时使用模拟数据
                if DEMO_MODE:
                    watchlist.append(generate_demo_hama_data(symbol))
                    continue

                # 获取 OHLCV 数据 (500条 15分钟K线)
                kline_data = kline_service.get_kline(
                    market='Crypto',
                    symbol=symbol,
                    timeframe='15m',
                    limit=500
                )

                if not kline_data or len(kline_data) < 100:
                    logger.warning(f"{symbol} 数据不足, 跳过")
                    continue

                # 转换为 OHLCV 格式
                ohlcv_data = []
                for k in kline_data:
                    ohlcv_data.append([
                        k.get('timestamp', 0),
                        k.get('open', 0),
                        k.get('high', 0),
                        k.get('low', 0),
                        k.get('close', 0),
                        k.get('volume', 0)
                    ])

                if not ohlcv_data or len(ohlcv_data) < 100:
                    logger.warning(f"{symbol} 数据不足, 跳过")
                    continue

                # 计算 HAMA 指标
                hama_result = calculate_hama_from_ohlcv(ohlcv_data)

                if not hama_result:
                    logger.warning(f"{symbol} HAMA 计算失败, 跳过")
                    continue

                # 构造返回数据
                item = {
                    'symbol': symbol,
                    'price': hama_result.get('close'),
                    'change_percentage': 0.0,  # 暂时不计算涨跌幅
                    'hama': hama_result.get('hama'),
                    'trend': hama_result.get('trend'),
                    'bollinger_bands': hama_result.get('bollinger_bands')
                }

                watchlist.append(item)

            except Exception as e:
                logger.error(f"处理 {symbol} 时发生错误: {e}")
                continue

        logger.info(f"HAMA 监控列表获取成功, 有效币种: {len(watchlist)}/{len(symbols)}")

        # 如果没有真实数据，返回模拟数据用于演示
        if len(watchlist) == 0:
            logger.info("无真实数据，使用模拟数据展示")
            for symbol in symbols:
                watchlist.append(generate_demo_hama_data(symbol))

        return jsonify({
            'success': True,
            'data': {
                'watchlist': watchlist
            }
        })

    except Exception as e:
        logger.error(f"获取 HAMA 监控列表失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbol', methods=['GET'])
def get_hama_symbol():
    """
    获取单个币种的 HAMA 指标

    参数:
        symbol: 币种 (必需)
        interval: K线周期 (默认 15m)
        limit: K线数量 (默认 500)

    返回:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "price": 3000.0,
            "hama": {...},
            "trend": {...},
            "bollinger_bands": {...}
        }
    }
    """
    try:
        symbol = request.args.get('symbol')
        interval = request.args.get('interval', '15m')
        limit = int(request.args.get('limit', 500))

        if not symbol:
            return jsonify({
                'success': False,
                'error': '请提供币种参数'
            }), 400

        symbol = symbol.upper()
        logger.info(f"获取 {symbol} 的 HAMA 指标, 周期: {interval}, 数量: {limit}")

        # 获取 OHLCV 数据
        kline_data = kline_service.get_kline(
            market='Crypto',
            symbol=symbol,
            timeframe=interval,
            limit=limit
        )

        if not kline_data or len(kline_data) < 100:
            return jsonify({
                'success': False,
                'error': f'数据不足，至少需要 100 条 OHLCV 数据，当前: {len(kline_data) if kline_data else 0}'
            }), 400

        # 转换为 OHLCV 格式
        ohlcv_data = []
        for k in kline_data:
            ohlcv_data.append([
                k.get('timestamp', 0),
                k.get('open', 0),
                k.get('high', 0),
                k.get('low', 0),
                k.get('close', 0),
                k.get('volume', 0)
            ])

        if not ohlcv_data or len(ohlcv_data) < 100:
            return jsonify({
                'success': False,
                'error': f'数据不足，至少需要 100 条 OHLCV 数据，当前: {len(ohlcv_data) if ohlcv_data else 0}'
            }), 400

        # 计算 HAMA 指标
        hama_result = calculate_hama_from_ohlcv(ohlcv_data)

        if not hama_result:
            return jsonify({
                'success': False,
                'error': 'HAMA 指标计算失败'
            }), 500

        # 添加币种信息
        hama_result['symbol'] = symbol

        logger.info(f"{symbol} HAMA 指标获取成功")

        return jsonify({
            'success': True,
            'data': hama_result
        })

    except Exception as e:
        logger.error(f"获取 {symbol} HAMA 指标失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/signals', methods=['GET'])
def get_hama_signals():
    """
    获取 HAMA 信号列表

    返回当前有信号的币种（金叉或死叉）

    参数:
        symbols: 币种列表，逗号分隔 (可选，默认使用 DEFAULT_SYMBOLS)

    返回:
    {
        "success": true,
        "data": {
            "signals": [
                {
                    "symbol": "BTCUSDT",
                    "signal_type": "UP",  // UP=金叉, DOWN=死叉
                    "price": 3000.0,
                    "hama_close": 3000.0,
                    "ma": 2998.0,
                    "timestamp": 1234567890000
                }
            ]
        }
    }
    """
    try:
        symbols_param = request.args.get('symbols')

        if symbols_param:
            symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
        else:
            symbols = DEFAULT_SYMBOLS

        logger.info(f"扫描 HAMA 信号, 币种数量: {len(symbols)}")

        signals = []

        for symbol in symbols:
            try:
                # 获取 OHLCV 数据
                kline_data = kline_service.get_kline(
                    market='Crypto',
                    symbol=symbol,
                    timeframe='15m',
                    limit=500
                )

                if not kline_data or len(kline_data) < 100:
                    continue

                # 转换为 OHLCV 格式
                ohlcv_data = []
                for k in kline_data:
                    ohlcv_data.append([
                        k.get('timestamp', 0),
                        k.get('open', 0),
                        k.get('high', 0),
                        k.get('low', 0),
                        k.get('close', 0),
                        k.get('volume', 0)
                    ])

                if not ohlcv_data or len(ohlcv_data) < 100:
                    continue

                # 计算 HAMA 指标
                hama_result = calculate_hama_from_ohlcv(ohlcv_data)

                if not hama_result:
                    continue

                hama = hama_result.get('hama', {})

                # 检查是否有信号
                if hama.get('cross_up'):
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'UP',
                        'price': hama_result.get('close'),
                        'hama_close': hama.get('close'),
                        'ma': hama.get('ma'),
                        'timestamp': hama_result.get('timestamp')
                    })
                elif hama.get('cross_down'):
                    signals.append({
                        'symbol': symbol,
                        'signal_type': 'DOWN',
                        'price': hama_result.get('close'),
                        'hama_close': hama.get('close'),
                        'ma': hama.get('ma'),
                        'timestamp': hama_result.get('timestamp')
                    })

            except Exception as e:
                logger.error(f"处理 {symbol} 时发生错误: {e}")
                continue

        logger.info(f"HAMA 信号扫描完成, 发现 {len(signals)} 个信号")

        return jsonify({
            'success': True,
            'data': {
                'signals': signals
            }
        })

    except Exception as e:
        logger.error(f"获取 HAMA 信号失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/hot-symbols', methods=['GET'])
def get_hot_symbols():
    """
    获取热门币种列表

    返回:
    {
        "success": true,
        "data": {
            "symbols": ["BTCUSDT", "ETHUSDT", ...]
        }
    }
    """
    try:
        # 从种子数据获取热门币种
        from app.data.market_symbols_seed import get_hot_symbols as seed_get_hot_symbols
        hot_symbols_data = seed_get_hot_symbols(limit=50, market='Crypto')

        # 提取 symbol
        symbols = [s.get('symbol') for s in hot_symbols_data if s.get('symbol')]

        logger.info(f"获取热门币种列表, 数量: {len(symbols)}")

        return jsonify({
            'success': True,
            'data': {
                'symbols': symbols
            }
        })

    except Exception as e:
        logger.error(f"获取热门币种失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'success': True,
        'service': 'HAMA Market API',
        'status': 'running'
    })
