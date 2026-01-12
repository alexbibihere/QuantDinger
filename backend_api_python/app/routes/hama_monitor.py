#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA信号监控API路由
提供监控管理、信号查询等功能
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from datetime import datetime

from app.services.hama_monitor import get_monitor
from app.services.binance_gainer import BinanceGainerService

logger = logging.getLogger(__name__)

hama_monitor_bp = Blueprint('hama_monitor', __name__)


def login_required(f):
    """登录验证装饰器 (支持JWT token和session)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session

        # 方法1: 检查session
        if session.get('logged_in'):
            return f(*args, **kwargs)

        # 方法2: 检查JWT token
        from app.utils.auth import verify_token
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload:
                return f(*args, **kwargs)

        return jsonify({
            'success': False,
            'message': '请先登录'
        }), 401
    return decorated_function


@hama_monitor_bp.route('/status', methods=['GET'])
def get_monitor_status():
    """
    获取监控状态

    GET /api/hama-monitor/status
    """
    try:
        monitor = get_monitor()

        return jsonify({
            'success': True,
            'data': {
                'running': monitor.running,
                'monitored_symbols': list(monitor.monitored_symbols.keys()),
                'symbol_count': len(monitor.monitored_symbols),
                'check_interval': monitor.check_interval,
                'signal_cooldown': monitor.signal_cooldown,
                'total_signals': len(monitor.signals)
            }
        })

    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取监控状态失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/start', methods=['POST'])
def start_monitor():
    """
    启动监控服务

    POST /api/hama-monitor/start
    """
    try:
        monitor = get_monitor()

        if monitor.running:
            return jsonify({
                'success': True,
                'message': '监控服务已在运行中',
                'data': {'running': True}
            })

        monitor.start()

        logger.info("HAMA监控服务已通过API启动")
        return jsonify({
            'success': True,
            'message': '监控服务已启动',
            'data': {'running': True}
        })

    except Exception as e:
        logger.error(f"启动监控服务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'启动监控服务失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/stop', methods=['POST'])
def stop_monitor():
    """
    停止监控服务

    POST /api/hama-monitor/stop
    """
    try:
        monitor = get_monitor()

        if not monitor.running:
            return jsonify({
                'success': True,
                'message': '监控服务未运行',
                'data': {'running': False}
            })

        monitor.stop()

        logger.info("HAMA监控服务已通过API停止")
        return jsonify({
            'success': True,
            'message': '监控服务已停止',
            'data': {'running': False}
        })

    except Exception as e:
        logger.error(f"停止监控服务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'停止监控服务失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/symbols', methods=['GET'])
def get_monitored_symbols():
    """
    获取监控币种列表

    GET /api/hama-monitor/symbols
    """
    try:
        monitor = get_monitor()

        symbols_data = []
        for symbol, info in monitor.monitored_symbols.items():
            symbols_data.append({
                'symbol': symbol,
                'market_type': info['market_type'],
                'added_at': info['added_at'].isoformat() if info.get('added_at') else None,
                'last_check': info['last_check'].isoformat() if info.get('last_check') else None,
                'last_signal': info.get('last_signal'),
                'last_signal_time': info['last_signal_time'].isoformat() if info.get('last_signal_time') else None
            })

        return jsonify({
            'success': True,
            'data': {
                'symbols': symbols_data,
                'count': len(symbols_data)
            }
        })

    except Exception as e:
        logger.error(f"获取监控币种列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取监控币种列表失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/symbols/add', methods=['POST'])
def add_symbol():
    """
    添加监控币种

    POST /api/hama-monitor/symbols/add
    Body: {
        "symbol": "BTCUSDT",
        "market_type": "spot"  // 可选,默认 spot
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        market_type = data.get('market_type', 'spot')

        monitor = get_monitor()
        monitor.add_symbol(symbol, market_type)

        logger.info(f"已添加监控币种: {symbol} ({market_type})")
        return jsonify({
            'success': True,
            'message': f'已添加监控币种: {symbol}',
            'data': {'symbol': symbol, 'market_type': market_type}
        })

    except Exception as e:
        logger.error(f"添加监控币种失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加监控币种失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/symbols/remove', methods=['POST'])
def remove_symbol():
    """
    移除监控币种

    POST /api/hama-monitor/symbols/remove
    Body: {
        "symbol": "BTCUSDT"
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        monitor = get_monitor()
        monitor.remove_symbol(symbol)

        logger.info(f"已移除监控币种: {symbol}")
        return jsonify({
            'success': True,
            'message': f'已移除监控币种: {symbol}',
            'data': {'symbol': symbol}
        })

    except Exception as e:
        logger.error(f"移除监控币种失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'移除监控币种失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/symbols/add-top-gainers', methods=['POST'])
def add_top_gainers():
    """
    添加涨幅榜前N名为监控币种

    POST /api/hama-monitor/symbols/add-top-gainers
    Body: {
        "limit": 20,  // 可选,默认20
        "market": "spot"  // 可选,默认 spot
    }
    """
    try:
        data = request.get_json()
        limit = data.get('limit', 20)
        market = data.get('market', 'spot')

        # 获取涨幅榜
        binance = BinanceGainerService()
        if market == 'futures':
            gainers = binance.get_top_gainers_futures(limit)
        else:
            gainers = binance.get_top_gainers(limit, market)

        if not gainers:
            return jsonify({
                'success': False,
                'message': '获取涨幅榜失败'
            }), 500

        # 添加到监控
        monitor = get_monitor()
        added_count = 0
        for gainer in gainers:
            symbol = gainer['symbol']
            if symbol not in monitor.monitored_symbols:
                monitor.add_symbol(symbol, market)
                added_count += 1

        logger.info(f"已添加 {added_count} 个涨幅榜币种到监控")
        return jsonify({
            'success': True,
            'message': f'已添加 {added_count} 个涨幅榜币种到监控',
            'data': {
                'total': len(gainers),
                'added': added_count,
                'already_monitored': len(gainers) - added_count
            }
        })

    except Exception as e:
        logger.error(f"添加涨幅榜失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加涨幅榜失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/signal/<symbol>', methods=['GET'])
def get_signal(symbol):
    """
    获取指定币种的最新HAMA信号

    GET /api/hama-monitor/signal/BTCUSDT
    """
    try:
        monitor = get_monitor()

        # 检查币种是否在监控列表
        if symbol not in monitor.monitored_symbols:
            return jsonify({
                'success': False,
                'message': f'{symbol} 不在监控列表中'
            }), 404

        # 获取币种信息
        symbol_info = monitor.monitored_symbols[symbol]

        # 尝试获取实时信号
        try:
            signal = monitor.get_hama_signal(symbol)
            price = symbol_info.get('last_price', 0)

            return jsonify({
                'success': True,
                'data': {
                    'symbol': symbol,
                    'signal': signal,
                    'price': price,
                    'market_type': symbol_info.get('market_type'),
                    'last_check': symbol_info.get('last_check').isoformat() if symbol_info.get('last_check') else None,
                    'last_signal': symbol_info.get('last_signal'),
                    'last_signal_time': symbol_info.get('last_signal_time').isoformat() if symbol_info.get('last_signal_time') else None
                }
            })
        except Exception as e:
            logger.error(f"获取{symbol}信号失败: {e}")
            return jsonify({
                'success': False,
                'message': f'获取信号失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"获取{symbol}信号失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取信号失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/signals', methods=['GET'])
def get_signals():
    """
    获取信号历史

    GET /api/hama-monitor/signals?limit=50
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # 最多返回200条

        monitor = get_monitor()
        signals = monitor.get_recent_signals(limit)

        # 转换为可序列化格式
        signals_data = []
        for signal in signals:
            signals_data.append({
                'symbol': signal['symbol'],
                'signal_type': signal['signal_type'],
                'price': signal['price'],
                'candle_close': signal['candle_close'],
                'ma': signal['ma'],
                'timestamp': signal['timestamp'].isoformat(),
                'description': signal['description']
            })

        return jsonify({
            'success': True,
            'data': {
                'signals': signals_data,
                'count': len(signals_data)
            }
        })

    except Exception as e:
        logger.error(f"获取信号历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取信号历史失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/clear-signals', methods=['POST'])
def clear_signals():
    """
    清空信号历史

    POST /api/hama-monitor/clear-signals
    """
    try:
        monitor = get_monitor()
        signal_count = len(monitor.signals)
        monitor.signals.clear()

        logger.info(f"已清空 {signal_count} 条信号历史")
        return jsonify({
            'success': True,
            'message': f'已清空 {signal_count} 条信号历史',
            'data': {'cleared_count': signal_count}
        })

    except Exception as e:
        logger.error(f"清空信号历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清空信号历史失败: {str(e)}'
        }), 500


@hama_monitor_bp.route('/config', methods=['GET', 'POST'])
def monitor_config():
    """
    获取或更新监控配置

    GET /api/hama-monitor/config - 获取配置
    POST /api/hama-monitor/config - 更新配置
    Body: {
        "check_interval": 60,  // 检查间隔(秒)
        "signal_cooldown": 300,  // 信号冷却时间(秒)
        "auto_fetch_gainers": false,  // 是否自动获取涨幅榜
        "auto_fetch_interval": 180,  // 自动获取间隔(秒)
        "auto_fetch_limit": 20  // 自动获取数量
    }
    """
    try:
        monitor = get_monitor()

        if request.method == 'GET':
            return jsonify({
                'success': True,
                'data': {
                    'check_interval': monitor.check_interval,
                    'signal_cooldown': monitor.signal_cooldown,
                    'auto_fetch_gainers': monitor.auto_fetch_gainers,
                    'auto_fetch_interval': monitor.auto_fetch_interval,
                    'auto_fetch_limit': monitor.auto_fetch_limit
                }
            })

        else:  # POST
            data = request.get_json()

            if 'check_interval' in data:
                interval = data['check_interval']
                if interval < 10:
                    return jsonify({
                        'success': False,
                        'message': '检查间隔不能小于10秒'
                    }), 400
                monitor.check_interval = interval

            if 'signal_cooldown' in data:
                cooldown = data['signal_cooldown']
                if cooldown < 0:
                    return jsonify({
                        'success': False,
                        'message': '冷却时间不能为负数'
                    }), 400
                monitor.signal_cooldown = cooldown

            if 'auto_fetch_gainers' in data:
                monitor.auto_fetch_gainers = data['auto_fetch_gainers']

            if 'auto_fetch_interval' in data:
                interval = data['auto_fetch_interval']
                if interval < 60:
                    return jsonify({
                        'success': False,
                        'message': '自动获取间隔不能小于60秒'
                    }), 400
                monitor.auto_fetch_interval = interval

            if 'auto_fetch_limit' in data:
                limit = data['auto_fetch_limit']
                if limit < 1 or limit > 100:
                    return jsonify({
                        'success': False,
                        'message': '自动获取数量必须在1-100之间'
                    }), 400
                monitor.auto_fetch_limit = limit

            logger.info(
                f"监控配置已更新: check_interval={monitor.check_interval}, "
                f"signal_cooldown={monitor.signal_cooldown}, "
                f"auto_fetch_gainers={monitor.auto_fetch_gainers}, "
                f"auto_fetch_interval={monitor.auto_fetch_interval}, "
                f"auto_fetch_limit={monitor.auto_fetch_limit}"
            )
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'data': {
                    'check_interval': monitor.check_interval,
                    'signal_cooldown': monitor.signal_cooldown,
                    'auto_fetch_gainers': monitor.auto_fetch_gainers,
                    'auto_fetch_interval': monitor.auto_fetch_interval,
                    'auto_fetch_limit': monitor.auto_fetch_limit
                }
            })

    except Exception as e:
        logger.error(f"配置操作失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'配置操作失败: {str(e)}'
        }), 500
