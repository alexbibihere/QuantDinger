#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 行情 API 路由

提供类似 TradingView 的 HAMA 行情数据接口
集成 Brave 浏览器监控数据
集成 OCR 识别功能
"""
from flask import Blueprint, request, jsonify
import traceback
import random
import os
import sqlite3
from app.services.kline import KlineService
from app.services.hama_calculator import calculate_hama_from_ohlcv
try:
    from app.services.hama_brave_monitor import get_brave_monitor
except ImportError:
    # 如果模块不存在，创建一个空实现
    def get_brave_monitor():
        return None
try:
    from app.services.hama_ocr_service import get_ocr_service
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    def get_ocr_service():
        return None
from app.utils.logger import get_logger
from app.data.market_symbols_seed import get_hot_symbols
import os
import asyncio

logger = get_logger(__name__)

hama_market_bp = Blueprint('hama_market', __name__)
kline_service = KlineService()

# 模拟数据模式（用于演示）
DEMO_MODE = os.getenv('HAMA_DEMO_MODE', 'false').lower() == 'true'

# 是否启用 Brave 浏览器监控
BRAVE_MONITOR_ENABLED = os.getenv('BRAVE_MONITOR_ENABLED', 'true').lower() == 'true'

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
    获取 HAMA 监控列表（优先从 SQLite 数据库读取 Brave 监控数据）

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
                    "price": 95159.0,
                    "hama_brave": {
                        "hama_trend": "up",
                        "hama_color": "green",
                        "hama_value": 95117.59,
                        "cached_at": "2025-01-17T10:30:00",
                        "cache_source": "sqlite_brave_monitor"
                    }
                }
            ]
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

        logger.info(f"获取 HAMA 监控列表 (SQLite优先), 币种数量: {len(symbols)}, 市场: {market}")

        # 获取 Brave 监控器 (从 app init)
        from app import get_hama_brave_monitor
        brave_monitor = get_hama_brave_monitor()

        if not brave_monitor:
            logger.warning("Brave 监控器未初始化,尝试直接初始化...")
            try:
                from app.services.hama_brave_monitor import get_brave_monitor as get_monitor
                brave_monitor = get_monitor(use_sqlite=True)
                logger.info("✅ 直接初始化 Brave 监控器成功")
            except Exception as e:
                logger.error(f"直接初始化 Brave 监控器失败: {e}")
                brave_monitor = None

        watchlist = []

        for symbol in symbols:
            try:
                # 从 Brave 监控器获取 HAMA 状态 (优先从 SQLite 数据库)
                brave_hama = None
                if brave_monitor:
                    brave_hama = brave_monitor.get_cached_hama(symbol)

                if brave_hama:
                    # 获取当前价格（从缓存数据或实时获取）
                    price = brave_hama.get('price') or brave_hama.get('hama_value', 0)

                    # 处理截图路径
                    screenshot_path = brave_hama.get('screenshot_path')
                    screenshot_url = None
                    if screenshot_path:
                        # 将本地文件路径转换为 URL
                        # 例如: "hama_brave_BTCUSDT_1234567890.png" -> "/screenshot/hama_brave_BTCUSDT_1234567890.png"
                        filename = os.path.basename(screenshot_path)
                        screenshot_url = f"/screenshot/{filename}"

                    # 构造返回数据（包含多时间周期）
                    hama_brave_data = {
                        'hama_trend': brave_hama.get('hama_trend'),
                        'hama_color': brave_hama.get('hama_color'),
                        'hama_value': brave_hama.get('hama_value'),
                        'candle_ma_status': brave_hama.get('candle_ma_status'),
                        'bollinger_status': brave_hama.get('bollinger_status'),
                        'last_cross_info': brave_hama.get('last_cross_info'),
                        'screenshot_path': screenshot_path,
                        'screenshot_url': screenshot_url,
                        'screenshot_base64': brave_hama.get('screenshot_base64'),
                        'cached_at': brave_hama.get('cached_at'),
                        'cache_source': brave_hama.get('cache_source', 'brave_browser')
                    }

                    # 添加多时间周期数据
                    if 'timeframe_15m' in brave_hama:
                        hama_brave_data['timeframe_15m'] = brave_hama['timeframe_15m']
                    if 'timeframe_1h' in brave_hama:
                        hama_brave_data['timeframe_1h'] = brave_hama['timeframe_1h']
                    if 'timeframe_4h' in brave_hama:
                        hama_brave_data['timeframe_4h'] = brave_hama['timeframe_4h']

                    item = {
                        'symbol': symbol,
                        'price': price,
                        'hama_brave': hama_brave_data
                    }
                    watchlist.append(item)
                    logger.debug(f"{symbol} 从 Brave 监控获取到数据: {brave_hama.get('hama_color')}, 截图: {screenshot_path}")
                else:
                    # 没有Brave缓存数据,不显示本地计算数据
                    # 只展示通过Brave监控OCR识别的数据
                    item = {
                        'symbol': symbol,
                        'price': 0,
                        'hama_brave': None
                    }
                    watchlist.append(item)
                    logger.debug(f"{symbol} 暂无 Brave 监控数据")

            except Exception as e:
                logger.error(f"处理 {symbol} 时发生错误: {e}")
                continue

        logger.info(f"HAMA 监控列表获取成功, 有效币种: {len([w for w in watchlist if w['hama_brave']])}/{len(symbols)}")

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


@hama_market_bp.route('/brave/status', methods=['GET'])
def get_brave_status():
    """
    获取 Brave 监控器状态

    返回:
    {
        "success": true,
        "data": {
            "available": true,
            "cached_symbols": 10,
            "cache_ttl_seconds": 300,
            "is_monitoring": true,
            "monitor_interval": 300
        }
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': True,
                'data': {
                    'enabled': False,
                    'message': 'Brave 监控未启用 (BRAVE_MONITOR_ENABLED=false)'
                }
            })

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        stats = brave_monitor.get_stats()
        cached_symbols = brave_monitor.get_cached_symbols()

        return jsonify({
            'success': True,
            'data': {
                **stats,
                'cached_symbols_list': cached_symbols
            }
        })

    except Exception as e:
        logger.error(f"获取 Brave 状态失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/monitor', methods=['POST'])
def trigger_brave_monitor():
    """
    手动触发 Brave 监控

    参数:
        symbols: 币种列表，逗号分隔 (可选，默认使用 DEFAULT_SYMBOLS)
        browser_type: 浏览器类型 (brave/chrome/edge/firefox, 默认 brave)

    返回:
    {
        "success": true,
        "data": {
            "total": 10,
            "success": 8,
            "failed": 2,
            "symbols": {
                "BTCUSDT": {
                    "success": true,
                    "data": {...}
                }
            }
        }
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用 (BRAVE_MONITOR_ENABLED=false)'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        symbols_param = request_data.get('symbols') or request.args.get('symbols')
        browser_type = request_data.get('browser_type') or request.args.get('browser_type', 'brave')

        # 确定要监控的币种列表
        if symbols_param:
            if isinstance(symbols_param, str):
                symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
            else:
                symbols = symbols_param
        else:
            symbols = DEFAULT_SYMBOLS

        logger.info(f"手动触发 Brave 监控, 币种数: {len(symbols)}, 浏览器: {browser_type}")

        # 执行批量监控
        results = brave_monitor.monitor_batch(symbols, browser_type)

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"手动触发 Brave 监控失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/start', methods=['POST'])
def start_brave_monitoring():
    """
    启动持续监控

    参数:
        symbols: 币种列表 (可选)
        interval: 刷新间隔秒数 (可选，默认300)
        browser_type: 浏览器类型 (可选，默认brave)

    返回:
    {
        "success": true,
        "message": "持续监控已启动"
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用 (BRAVE_MONITOR_ENABLED=false)'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        symbols = request_data.get('symbols') or DEFAULT_SYMBOLS
        interval = int(request_data.get('interval', 300))
        browser_type = request_data.get('browser_type', 'brave')

        logger.info(f"启动持续监控, 币种数: {len(symbols)}, 间隔: {interval}秒, 浏览器: {browser_type}")

        brave_monitor.start_monitoring(symbols, interval, browser_type)

        return jsonify({
            'success': True,
            'message': f'持续监控已启动, 间隔: {interval}秒'
        })

    except Exception as e:
        logger.error(f"启动持续监控失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/stop', methods=['POST'])
def stop_brave_monitoring():
    """
    停止持续监控

    返回:
    {
        "success": true,
        "message": "持续监控已停止"
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        logger.info("停止持续监控")
        brave_monitor.stop_monitoring()

        return jsonify({
            'success': True,
            'message': '持续监控已停止'
        })

    except Exception as e:
        logger.error(f"停止持续监控失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/ocr/capture', methods=['POST'])
def ocr_capture_hama():
    """
    使用 OCR 从 TradingView 截取并识别 HAMA 指标

    参数:
        symbol: 币种符号 (可选，如 BTCUSDT)
        tv_url: TradingView 图表 URL (可选，覆盖 symbol)

    返回:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "trend": "UP",
            "hama_color": "green",
            "candle_ma": "above",
            "contraction": "yes",
            "last_cross": null,
            "price": 3311.73,
            "screenshot": "screenshot/hama_panel_20260118_081620.png",
            "timestamp": "20260118_081620"
        }
    }
    """
    try:
        if not OCR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'OCR 服务不可用（需要安装 playwright 和 rapidocr-onnxruntime）'
            }), 400

        # 获取参数
        request_data = request.get_json() or {}
        symbol = request_data.get('symbol') or request.args.get('symbol')
        tv_url = request_data.get('tv_url') or request.args.get('tv_url')

        if not symbol and not tv_url:
            return jsonify({
                'success': False,
                'error': '请提供 symbol 或 tv_url 参数'
            }), 400

        logger.info(f"OCR 识别 HAMA 指标: symbol={symbol}, tv_url={tv_url}")

        # 获取 OCR 服务
        ocr_service = get_ocr_service()

        # 异步执行 OCR 识别
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ocr_service.capture_hama_panel(symbol, tv_url))
        finally:
            loop.close()

        if result.get('success'):
            logger.info(f"OCR 识别成功: {result['data'].get('symbol')}")
            return jsonify({
                'success': True,
                'data': result['data']
            })
        else:
            error_msg = result.get('error', '未知错误')
            logger.error(f"OCR 识别失败: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

    except Exception as e:
        logger.error(f"OCR 识别 HAMA 失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/ocr/batch', methods=['POST'])
def ocr_batch_capture():
    """
    批量 OCR 识别多个币种的 HAMA 指标

    参数:
        symbols: 币种列表，如 ["BTCUSDT", "ETHUSDT"]

    返回:
    {
        "success": true,
        "data": {
            "total": 2,
            "success": 2,
            "failed": 0,
            "results": [
                {
                    "symbol": "BTCUSDT",
                    "success": true,
                    "data": {...}
                }
            ]
        }
    }
    """
    try:
        if not OCR_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'OCR 服务不可用'
            }), 400

        # 获取参数
        request_data = request.get_json() or {}
        symbols = request_data.get('symbols', [])

        if not symbols:
            return jsonify({
                'success': False,
                'error': '请提供 symbols 参数（币种列表）'
            }), 400

        logger.info(f"批量 OCR 识别 HAMA 指标: {len(symbols)} 个币种")

        ocr_service = get_ocr_service()

        results = []
        success_count = 0
        failed_count = 0

        for symbol in symbols:
            try:
                # 异步执行 OCR 识别
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(ocr_service.capture_hama_panel(symbol))
                finally:
                    loop.close()

                if result.get('success'):
                    results.append({
                        'symbol': symbol,
                        'success': True,
                        'data': result['data']
                    })
                    success_count += 1
                else:
                    results.append({
                        'symbol': symbol,
                        'success': False,
                        'error': result.get('error', '未知错误')
                    })
                    failed_count += 1

            except Exception as e:
                logger.error(f"处理 {symbol} 时发生错误: {e}")
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1

        logger.info(f"批量 OCR 完成: 成功 {success_count}, 失败 {failed_count}")

        return jsonify({
            'success': True,
            'data': {
                'total': len(symbols),
                'success': success_count,
                'failed': failed_count,
                'results': results
            }
        })

    except Exception as e:
        logger.error(f"批量 OCR 识别失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/worker/status', methods=['GET'])
def get_worker_status():
    """
    获取 HAMA 监控 Worker 状态

    返回:
    {
        "success": true,
        "data": {
            "is_running": true,
            "cached_symbols": 5,
            "symbols": ["BTCUSDT", ...],
            "interval": 600
        }
    }
    """
    try:
        from app.services.hama_monitor_worker import get_hama_monitor_worker
        
        worker = get_hama_monitor_worker()
        status = worker.get_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"获取 Worker 状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/worker/start', methods=['POST'])
def start_worker():
    """
    启动 HAMA 监控 Worker

    返回:
    {
        "success": true,
        "message": "Worker 已启动"
    }
    """
    try:
        from app.services.hama_monitor_worker import get_hama_monitor_worker
        
        worker = get_hama_monitor_worker()
        worker.start()
        
        return jsonify({
            'success': True,
            'message': 'HAMA 监控 Worker 已启动'
        })
    except Exception as e:
        logger.error(f"启动 Worker 失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/worker/stop', methods=['POST'])
def stop_worker():
    """
    停止 HAMA 监控 Worker

    返回:
    {
        "success": true,
        "message": "Worker 已停止"
    }
    """
    try:
        from app.services.hama_monitor_worker import get_hama_monitor_worker
        
        worker = get_hama_monitor_worker()
        worker.stop()
        
        return jsonify({
            'success': True,
            'message': 'HAMA 监控 Worker 已停止'
        })
    except Exception as e:
        logger.error(f"停止 Worker 失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/worker/monitor', methods=['POST'])
def worker_monitor_now():
    """
    立即触发监控 (异步)

    参数:
        symbols: 币种列表 (可选，默认使用 Worker 的币种列表)

    返回:
    {
        "success": true,
        "message": "监控任务已提交"
    }
    """
    try:
        from flask import request
        from app.services.hama_monitor_worker import get_hama_monitor_worker
        import threading

        data = request.get_json() or {}
        symbols = data.get('symbols')

        worker = get_hama_monitor_worker()

        # 在后台线程执行监控
        def monitor_task():
            try:
                results = worker.monitor_now(symbols)
                logger.info(f"后台监控完成: {results}")
            except Exception as e:
                logger.error(f"后台监控失败: {e}")

        thread = threading.Thread(target=monitor_task, daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'message': '监控任务已在后台启动'
        })
    except Exception as e:
        logger.error(f"触发监控失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== HAMA 币种管理 API ====================

def get_db_connection():
    """获取数据库连接"""
    from app import create_app
    app = create_app()
    db_path = app.config.get('SQLITE_DATABASE_FILE', 'data/quantdinger.db')
    import sqlite3
    return sqlite3.connect(db_path)


@hama_market_bp.route('/symbols/list', methods=['GET'])
def get_symbols_list():
    """
    获取 HAMA 监控币种列表

    参数:
        enabled: 是否只返回启用的币种 (true/false, 可选)
        market: 市场类型 (spot/futures, 可选)

    返回:
    {
        "success": true,
        "data": {
            "symbols": [
                {
                    "id": 1,
                    "symbol": "BTCUSDT",
                    "symbol_name": "Bitcoin",
                    "market": "spot",
                    "enabled": true,
                    "priority": 100,
                    "notify_enabled": true,
                    "notify_threshold": 2.0,
                    "notes": "BTC 永续监控",
                    "created_at": "2025-01-18T10:00:00",
                    "updated_at": "2025-01-18T10:00:00",
                    "last_monitored_at": null
                }
            ]
        }
    }
    """
    try:
        enabled_only = request.args.get('enabled', '').lower() == 'true'
        market = request.args.get('market')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建查询
        query = "SELECT * FROM hama_symbols WHERE 1=1"
        params = []

        if enabled_only:
            query += " AND enabled = 1"
        if market:
            query += " AND market = ?"
            params.append(market)

        query += " ORDER BY priority DESC, symbol ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取列名
        cursor.execute("PRAGMA table_info(hama_symbols)")
        columns = [col[1] for col in cursor.fetchall()]

        symbols = []
        for row in rows:
            symbol_dict = dict(zip(columns, row))
            # 转换布尔值
            symbol_dict['enabled'] = bool(symbol_dict.get('enabled'))
            symbol_dict['notify_enabled'] = bool(symbol_dict.get('notify_enabled'))
            symbols.append(symbol_dict)

        cursor.close()
        conn.close()

        logger.info(f"获取币种列表成功: {len(symbols)} 个币种")

        return jsonify({
            'success': True,
            'data': {
                'symbols': symbols
            }
        })

    except Exception as e:
        logger.error(f"获取币种列表失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbols/add', methods=['POST'])
def add_symbol():
    """
    添加新的监控币种

    参数:
        symbol: 币种符号 (必需, 如 BTCUSDT)
        symbol_name: 币种名称 (可选)
        market: 市场 (spot/futures, 默认 spot)
        enabled: 是否启用 (默认 true)
        priority: 优先级 (默认 0)
        notify_enabled: 是否启用通知 (默认 false)
        notify_threshold: 通知阈值百分比 (默认 2.0)
        notes: 备注 (可选)

    返回:
    {
        "success": true,
        "data": {
            "id": 11,
            "symbol": "MATICUSDT"
        }
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get('symbol'):
            return jsonify({
                'success': False,
                'error': '请提供币种符号 (symbol)'
            }), 400

        symbol = data['symbol'].upper().strip()
        symbol_name = data.get('symbol_name', '')
        market = data.get('market', 'spot')
        enabled = 1 if data.get('enabled', True) else 0
        priority = int(data.get('priority', 0))
        notify_enabled = 1 if data.get('notify_enabled', False) else 0
        notify_threshold = float(data.get('notify_threshold', 2.0))
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO hama_symbols
                (symbol, symbol_name, market, enabled, priority, notify_enabled, notify_threshold, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, symbol_name, market, enabled, priority, notify_enabled, notify_threshold, notes))

            conn.commit()
            symbol_id = cursor.lastrowid

            logger.info(f"添加币种成功: {symbol} (ID: {symbol_id})")

            cursor.close()
            conn.close()

            return jsonify({
                'success': True,
                'data': {
                    'id': symbol_id,
                    'symbol': symbol
                }
            })

        except sqlite3.IntegrityError:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'币种 {symbol} 已存在'
            }), 400

    except Exception as e:
        logger.error(f"添加币种失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbols/update', methods=['PUT', 'POST'])
def update_symbol():
    """
    更新币种信息

    参数:
        symbol: 币种符号 (必需)
        symbol_name: 币种名称 (可选)
        market: 市场 (可选)
        enabled: 是否启用 (可选)
        priority: 优先级 (可选)
        notify_enabled: 是否启用通知 (可选)
        notify_threshold: 通知阈值 (可选)
        notes: 备注 (可选)

    返回:
    {
        "success": true,
        "data": {
            "updated": true
        }
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get('symbol'):
            return jsonify({
                'success': False,
                'error': '请提供币种符号 (symbol)'
            }), 400

        symbol = data['symbol'].upper().strip()

        # 构建更新字段
        update_fields = []
        update_values = []

        if 'symbol_name' in data:
            update_fields.append('symbol_name = ?')
            update_values.append(data['symbol_name'])
        if 'market' in data:
            update_fields.append('market = ?')
            update_values.append(data['market'])
        if 'enabled' in data:
            update_fields.append('enabled = ?')
            update_values.append(1 if data['enabled'] else 0)
        if 'priority' in data:
            update_fields.append('priority = ?')
            update_values.append(int(data['priority']))
        if 'notify_enabled' in data:
            update_fields.append('notify_enabled = ?')
            update_values.append(1 if data['notify_enabled'] else 0)
        if 'notify_threshold' in data:
            update_fields.append('notify_threshold = ?')
            update_values.append(float(data['notify_threshold']))
        if 'notes' in data:
            update_fields.append('notes = ?')
            update_values.append(data['notes'])

        if not update_fields:
            return jsonify({
                'success': False,
                'error': '没有提供要更新的字段'
            }), 400

        # 添加 updated_at
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        update_values.append(symbol)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"UPDATE hama_symbols SET {', '.join(update_fields)} WHERE symbol = ?"
        cursor.execute(query, update_values)

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'币种 {symbol} 不存在'
            }), 404

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"更新币种成功: {symbol}")

        return jsonify({
            'success': True,
            'data': {
                'updated': True
            }
        })

    except Exception as e:
        logger.error(f"更新币种失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbols/delete', methods=['DELETE', 'POST'])
def delete_symbol():
    """
    删除币种

    参数:
        symbol: 币种符号 (必需)

    返回:
    {
        "success": true,
        "data": {
            "deleted": true
        }
    }
    """
    try:
        data = request.get_json() or {}
        symbol = (data.get('symbol') or request.args.get('symbol'))

        if not symbol:
            return jsonify({
                'success': False,
                'error': '请提供币种符号 (symbol)'
            }), 400

        symbol = symbol.upper().strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM hama_symbols WHERE symbol = ?", (symbol,))

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'币种 {symbol} 不存在'
            }), 404

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"删除币种成功: {symbol}")

        return jsonify({
            'success': True,
            'data': {
                'deleted': True
            }
        })

    except Exception as e:
        logger.error(f"删除币种失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbols/enable', methods=['PUT', 'POST'])
def toggle_symbol():
    """
    启用/禁用币种

    参数:
        symbol: 币种符号 (必需)
        enabled: 是否启用 (true/false, 必需)

    返回:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "enabled": true
        }
    }
    """
    try:
        data = request.get_json() or {}
        symbol = (data.get('symbol') or request.args.get('symbol'))
        enabled = data.get('enabled', request.args.get('enabled'))

        if not symbol:
            return jsonify({
                'success': False,
                'error': '请提供币种符号 (symbol)'
            }), 400

        if enabled is None:
            return jsonify({
                'success': False,
                'error': '请提供 enabled 参数 (true/false)'
            }), 400

        symbol = symbol.upper().strip()
        enabled_value = 1 if str(enabled).lower() == 'true' else 0

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE hama_symbols
            SET enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        ''', (enabled_value, symbol))

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'币种 {symbol} 不存在'
            }), 404

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"{'启用' if enabled_value else '禁用'}币种成功: {symbol}")

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'enabled': bool(enabled_value)
            }
        })

    except Exception as e:
        logger.error(f"切换币种状态失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/symbols/batch-enable', methods=['POST'])
def batch_enable_symbols():
    """
    批量启用/禁用币种

    参数:
        symbols: 币种列表 ["BTCUSDT", "ETHUSDT"]
        enabled: 是否启用 (true/false)

    返回:
    {
        "success": true,
        "data": {
            "total": 2,
            "updated": 2
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '请提供请求体'
            }), 400

        symbols = data.get('symbols', [])
        enabled = data.get('enabled', True)

        if not symbols:
            return jsonify({
                'success': False,
                'error': '请提供币种列表 (symbols)'
            }), 400

        enabled_value = 1 if enabled else 0

        conn = get_db_connection()
        cursor = conn.cursor()

        updated_count = 0
        for symbol in symbols:
            symbol = symbol.upper().strip()
            cursor.execute('''
                UPDATE hama_symbols
                SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            ''', (enabled_value, symbol))
            if cursor.rowcount > 0:
                updated_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"批量{'启用' if enabled_value else '禁用'}币种: {updated_count}/{len(symbols)}")

        return jsonify({
            'success': True,
            'data': {
                'total': len(symbols),
                'updated': updated_count
            }
        })

    except Exception as e:
        logger.error(f"批量切换币种状态失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Brave 监控优化 API ====================

@hama_market_bp.route('/brave/monitor-parallel', methods=['POST'])
def trigger_brave_monitor_parallel():
    """
    手动触发并行 Brave 监控（性能优化版本）

    参数:
        symbols: 币种列表，逗号分隔 (可选，默认使用 DEFAULT_SYMBOLS)
        browser_type: 浏览器类型 (brave/chrome/edge/firefox, 默认 brave)
        max_workers: 最大并发数 (可选，默认3)

    返回:
    {
        "success": true,
        "data": {
            "total": 10,
            "success": 9,
            "failed": 1,
            "symbols": {...}
        }
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用 (BRAVE_MONITOR_ENABLED=false)'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        symbols_param = request_data.get('symbols') or request.args.get('symbols')
        browser_type = request_data.get('browser_type') or request.args.get('browser_type', 'brave')
        max_workers = int(request_data.get('max_workers', 3))

        # 确定要监控的币种列表
        if symbols_param:
            if isinstance(symbols_param, str):
                symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
            else:
                symbols = symbols_param
        else:
            symbols = DEFAULT_SYMBOLS

        logger.info(f"手动触发并行 Brave 监控, 币种数: {len(symbols)}, 并发数: {max_workers}, 浏览器: {browser_type}")

        # 执行并行批量监控
        results = brave_monitor.monitor_batch_parallel(symbols, browser_type, max_workers)

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"手动触发并行 Brave 监控失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/warmup', methods=['POST'])
def warmup_brave_cache():
    """
    缓存预热：监控热门币种

    参数:
        symbols: 热门币种列表 (可选，默认 BTC, ETH, BNB, SOL)
        browser_type: 浏览器类型 (可选，默认 brave)

    返回:
    {
        "success": true,
        "data": {
            "total": 4,
            "success": 4,
            "failed": 0
        }
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        hot_symbols = request_data.get('symbols')
        browser_type = request_data.get('browser_type', 'brave')

        logger.info(f"开始缓存预热，币种: {hot_symbols or '默认热门'}")

        # 执行预热
        results = brave_monitor.warmup_cache(hot_symbols, browser_type)

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/start-smart', methods=['POST'])
def start_smart_brave_monitoring():
    """
    启动智能持续监控（动态调整间隔）

    参数:
        symbols: 币种列表 (可选)
        base_interval: 基础监控间隔秒数 (可选，默认600)
        browser_type: 浏览器类型 (可选，默认brave)

    返回:
    {
        "success": true,
        "message": "智能持续监控已启动",
        "dynamic_interval": 300
    }
    """
    try:
        if not BRAVE_MONITOR_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Brave 监控未启用'
            }), 400

        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        symbols = request_data.get('symbols') or DEFAULT_SYMBOLS
        base_interval = int(request_data.get('base_interval', 600))
        browser_type = request_data.get('browser_type', 'brave')

        logger.info(f"启动智能持续监控, 币种数: {len(symbols)}, 基础间隔: {base_interval}秒")

        # 获取当前动态间隔
        dynamic_interval = brave_monitor.get_dynamic_interval()

        # 启动智能监控
        brave_monitor.start_monitoring_smart(symbols, base_interval, browser_type)

        return jsonify({
            'success': True,
            'message': f'智能持续监控已启动 (当前动态间隔: {dynamic_interval}秒)',
            'dynamic_interval': dynamic_interval,
            'base_interval': base_interval
        })

    except Exception as e:
        logger.error(f"启动智能持续监控失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/health', methods=['GET'])
def brave_health_check():
    """
    Brave 监控系统健康检查

    返回:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "checks": {
                "ocr_available": true,
                "sqlite_available": true,
                "redis_available": false,
                "monitoring_active": true,
                "last_monitor_time": "2026-01-20T15:30:00",
                "cached_symbols_count": 10,
                "monitor_interval": 300
            }
        }
    }
    """
    try:
        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 执行健康检查
        health_status = brave_monitor.health_check()

        return jsonify({
            'success': True,
            'data': health_status
        })

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/brave/cleanup', methods=['POST'])
def cleanup_brave_resources():
    """
    清理旧资源（数据库记录和截图文件）

    参数:
        days: 保留天数 (可选，默认7)
        cleanup_screenshots: 是否清理截图 (可选，默认true)
        cleanup_records: 是否清理数据库记录 (可选，默认true)

    返回:
    {
        "success": true,
        "data": {
            "deleted_records": 120,
            "deleted_screenshots": 45
        }
    }
    """
    try:
        brave_monitor = get_brave_monitor()

        if not brave_monitor:
            return jsonify({
                'success': False,
                'error': 'Brave 监控器未初始化'
            }), 500

        # 获取参数
        request_data = request.get_json() or {}
        days = int(request_data.get('days', 7))
        cleanup_screenshots = request_data.get('cleanup_screenshots', True)
        cleanup_records = request_data.get('cleanup_records', True)

        logger.info(f"开始清理资源，保留天数: {days}天")

        deleted_records = 0
        deleted_screenshots = 0

        # 清理数据库记录
        if cleanup_records:
            deleted_records = brave_monitor.cleanup_old_records(days)

        # 清理截图文件
        if cleanup_screenshots:
            deleted_screenshots = brave_monitor.cleanup_old_screenshots(days)

        return jsonify({
            'success': True,
            'data': {
                'deleted_records': deleted_records,
                'deleted_screenshots': deleted_screenshots,
                'days': days
            },
            'message': f'已清理 {deleted_records} 条记录和 {deleted_screenshots} 个截图（{days}天内）'
        })

    except Exception as e:
        logger.error(f"清理资源失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/stats', methods=['GET'])
def get_hama_stats():
    """
    获取 HAMA 行情统计信息

    返回:
    {
        "success": true,
        "data": {
            "total": 10,
            "up": 3,
            "down": 5,
            "neutral": 2,
            "bollinger_expansion": 6,
            "bollinger_contraction": 2,
            "bollinger_normal": 2,
            "last_updated": "2026-01-21 11:14:35"
        }
    }
    """
    try:
        from app import get_hama_brave_monitor
        brave_monitor = get_hama_brave_monitor()

        if not brave_monitor:
            try:
                from app.services.hama_brave_monitor import get_brave_monitor as get_monitor
                brave_monitor = get_monitor(use_sqlite=True)
            except Exception as e:
                logger.error(f"初始化 Brave 监控器失败: {e}")
                brave_monitor = None

        stats = {
            'total': 0,
            'up': 0,
            'down': 0,
            'neutral': 0,
            'bollinger_expansion': 0,
            'bollinger_contraction': 0,
            'bollinger_normal': 0,
            'last_updated': None
        }

        if brave_monitor:
            # 获取所有缓存币种
            cached_symbols = brave_monitor.get_cached_symbols()

            stats['total'] = len(cached_symbols)

            # 统计趋势
            for symbol in cached_symbols:
                hama_data = brave_monitor.get_cached_hama(symbol)
                if hama_data:
                    # 统计趋势
                    hama_color = hama_data.get('hama_color', '').lower()
                    if hama_color == 'green':
                        stats['up'] += 1
                    elif hama_color == 'red':
                        stats['down'] += 1
                    else:
                        stats['neutral'] += 1

                    # 统计布林带状态
                    bollinger_status = hama_data.get('bollinger_status', '').lower()
                    if bollinger_status == 'expansion':
                        stats['bollinger_expansion'] += 1
                    elif bollinger_status == 'squeeze':
                        stats['bollinger_contraction'] += 1
                    else:
                        stats['bollinger_normal'] += 1

                    # 获取最后更新时间
                    cached_at = hama_data.get('cached_at')
                    if cached_at and (not stats['last_updated'] or cached_at > stats['last_updated']):
                        stats['last_updated'] = cached_at

        logger.info(f"获取 HAMA 统计信息: 总计{stats['total']}, 上涨{stats['up']}, 下跌{stats['down']}, 盘整{stats['neutral']}")

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取 HAMA 统计信息失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/cached-symbols', methods=['GET'])
def get_cached_symbols():
    """
    获取已缓存的币种列表

    返回:
    {
        "success": true,
        "data": {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "hama_color": "red",
                    "hama_trend": "down",
                    "cached_at": "2026-01-21 11:14:15",
                    "screenshot_url": "/screenshot/hama_brave_BTCUSDT_1768965210.png"
                }
            ],
            "count": 10
        }
    }
    """
    try:
        from app import get_hama_brave_monitor
        brave_monitor = get_hama_brave_monitor()

        if not brave_monitor:
            try:
                from app.services.hama_brave_monitor import get_brave_monitor as get_monitor
                brave_monitor = get_monitor(use_sqlite=True)
            except Exception as e:
                logger.error(f"初始化 Brave 监控器失败: {e}")
                brave_monitor = None

        symbols = []

        if brave_monitor:
            # 获取所有缓存币种
            cached_symbols = brave_monitor.get_cached_symbols()

            for symbol in cached_symbols:
                hama_data = brave_monitor.get_cached_hama(symbol)
                if hama_data:
                    screenshot_path = hama_data.get('screenshot_path')
                    screenshot_url = None
                    if screenshot_path:
                        filename = os.path.basename(screenshot_path)
                        screenshot_url = f"/screenshot/{filename}"

                    symbols.append({
                        'symbol': symbol,
                        'hama_color': hama_data.get('hama_color'),
                        'hama_trend': hama_data.get('hama_trend'),
                        'hama_value': hama_data.get('hama_value'),
                        'cached_at': hama_data.get('cached_at'),
                        'screenshot_url': screenshot_url
                    })

        logger.info(f"获取缓存币种列表: {len(symbols)} 个")

        return jsonify({
            'success': True,
            'data': {
                'symbols': symbols,
                'count': len(symbols)
            }
        })

    except Exception as e:
        logger.error(f"获取缓存币种列表失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_market_bp.route('/history/<symbol>', methods=['GET'])
def get_hama_history(symbol):
    """
    获取指定币种的HAMA监控历史记录

    参数:
        symbol: 币种符号
        limit: 返回记录数（可选，默认50）
        offset: 偏移量（可选，默认0）

    返回:
    {
        "success": true,
        "data": {
            "symbol": "BTCUSDT",
            "total": 120,
            "history": [
                {
                    "hama_trend": "up",
                    "hama_color": "green",
                    "hama_value": 90150.25,
                    "price": 90150.25,
                    "monitored_at": "2026-01-22 10:30:00"
                }
            ]
        }
    }
    """
    try:
        from app import get_hama_brave_monitor
        brave_monitor = get_hama_brave_monitor()

        if not brave_monitor:
            try:
                from app.services.hama_brave_monitor import get_brave_monitor as get_monitor
                brave_monitor = get_monitor(use_sqlite=True)
            except Exception as e:
                logger.error(f"初始化 Brave 监控器失败: {e}")
                brave_monitor = None

        # 获取参数
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        history = []
        total = 0

        if brave_monitor and brave_monitor.use_sqlite:
            import sqlite3
            import os

            db_path = os.path.join(os.path.dirname(brave_monitor.__class__.__module__.replace('.', '/')), '..', '..', 'data', 'quantdinger.db')
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db'))

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询总记录数
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM hama_monitor_history
                WHERE symbol = ?
            ''', (symbol.upper(),))
            total = cursor.fetchone()['total']

            # 查询历史记录
            cursor.execute('''
                SELECT hama_trend, hama_color, hama_value, price,
                       candle_ma_status, bollinger_status, last_cross_info,
                       monitored_at
                FROM hama_monitor_history
                WHERE symbol = ?
                ORDER BY monitored_at DESC
                LIMIT ? OFFSET ?
            ''', (symbol.upper(), limit, offset))

            rows = cursor.fetchall()

            for row in rows:
                history.append({
                    'hama_trend': row['hama_trend'],
                    'hama_color': row['hama_color'],
                    'hama_value': float(row['hama_value']) if row['hama_value'] else None,
                    'price': float(row['price']) if row['price'] else None,
                    'candle_ma_status': row['candle_ma_status'],
                    'bollinger_status': row['bollinger_status'],
                    'last_cross_info': row['last_cross_info'],
                    'monitored_at': row['monitored_at']
                })

            conn.close()

        logger.info(f"获取 {symbol} 历史记录: {len(history)} 条 (总共 {total} 条)")

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol.upper(),
                'total': total,
                'history': history,
                'limit': limit,
                'offset': offset
            }
        })

    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
