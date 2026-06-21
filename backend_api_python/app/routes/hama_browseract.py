#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA BrowserAct API 路由
提供 BrowserAct 监控器的 REST API 接口
"""

from flask import Blueprint, jsonify, request
from app.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint('hama_browseract', __name__)


@bp.route('/api/browseract/status', methods=['GET'])
def get_browseract_status():
    """
    获取 BrowserAct 监控器状态

    Returns:
        JSON: 监控器状态信息
    """
    try:
        from app import get_hama_browseract_monitor, get_hama_brave_monitor
        from app.config.browseract_config import BrowserActConfig

        browseract_monitor = get_hama_browseract_monitor()
        brave_monitor = get_hama_brave_monitor()

        # 获取配置信息
        config = BrowserActConfig.get_monitor_config()

        status = {
            'success': True,
            'browseract': {
                'available': browseract_monitor is not None,
                'status': browseract_monitor.get_status() if browseract_monitor else None
            },
            'brave': {
                'available': brave_monitor is not None,
                'status': brave_monitor.get_status() if brave_monitor else None
            },
            'config': config,
            'current_monitor': 'browseract' if browseract_monitor else 'brave'
        }

        return jsonify(status)

    except Exception as e:
        logger.error(f"获取BrowserAct状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/monitor', methods=['POST'])
def monitor_symbols():
    """
    监控指定的交易对

    Request Body:
        {
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "timeframe": "15m"
        }

    Returns:
        JSON: 监控结果
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        timeframe = data.get('timeframe', '15m')

        if not symbols:
            return jsonify({
                'success': False,
                'error': '请提供要监控的交易对列表'
            }), 400

        # 直接使用BrowserAct监控器
        from app import get_hama_browseract_monitor

        monitor = get_hama_browseract_monitor()
        if not monitor:
            return jsonify({
                'success': False,
                'error': 'BrowserAct监控器不可用'
            }), 500

        # 执行监控
        result = monitor.monitor_batch_parallel(symbols, timeframe)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"监控交易对失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/symbol/<symbol>', methods=['GET'])
def monitor_single_symbol(symbol):
    """
    监控单个交易对

    Args:
        symbol: 交易对符号 (如 BTCUSDT)

    Query Params:
        timeframe: 时间周期，默认 15m

    Returns:
        JSON: 监控结果
    """
    try:
        timeframe = request.args.get('timeframe', '15m')

        # 直接使用BrowserAct监控器
        from app import get_hama_browseract_monitor

        monitor = get_hama_browseract_monitor()
        if not monitor:
            return jsonify({
                'success': False,
                'error': 'BrowserAct监控器不可用'
            }), 500

        # 执行监控
        result = monitor.monitor_single_symbol(symbol, timeframe)

        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'监控 {symbol} 失败'
            }), 500

    except Exception as e:
        logger.error(f"监控 {symbol} 失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/config', methods=['GET'])
def get_config():
    """
    获取 BrowserAct 配置信息

    Returns:
        JSON: 配置信息
    """
    try:
        from app.config.browseract_config import BrowserActConfig

        config = BrowserActConfig.get_monitor_config()
        recommended_symbols = BrowserActConfig.get_recommended_symbols()
        optimal_interval = BrowserActConfig.get_optimal_interval()

        return jsonify({
            'success': True,
            'config': config,
            'recommended_symbols': recommended_symbols,
            'optimal_interval': optimal_interval
        })

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/config', methods=['POST'])
def update_config():
    """
    更新 BrowserAct 配置

    Request Body:
        {
            "method": "hybrid",  // browseract, playwright_ocr, hybrid
            "interval": 300
        }

    Returns:
        JSON: 更新结果
    """
    try:
        data = request.get_json()
        method = data.get('method')
        interval = data.get('interval')

        if method and method not in ['browseract', 'playwright_ocr', 'hybrid']:
            return jsonify({
                'success': False,
                'error': '无效的监控方法'
            }), 400

        # 这里可以添加配置更新的逻辑
        # 注意：实际配置修改通常需要重启服务才能生效

        return jsonify({
            'success': True,
            'message': '配置已更新，请重启服务以应用更改',
            'data': {
                'method': method,
                'interval': interval
            }
        })

    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/compare', methods=['GET'])
def compare_methods():
    """
    对比 BrowserAct 和 Playwright 两种监控方法

    Returns:
        JSON: 对比结果
    """
    try:
        from app import get_hama_browseract_monitor, get_hama_brave_monitor

        browseract_monitor = get_hama_browseract_monitor()
        brave_monitor = get_hama_brave_monitor()

        comparison = {
            'success': True,
            'methods': []
        }

        # BrowserAct 信息
        if browseract_monitor:
            comparison['methods'].append({
                'name': 'BrowserAct',
                'type': 'browseract',
                'available': True,
                'advantages': [
                    '直接提取结构化数据',
                    '无需OCR识别',
                    '速度更快',
                    '准确性更高',
                    '支持自动登录',
                    'Cloudflare绕过'
                ],
                'disadvantages': [
                    '需要Python 3.12+',
                    '需要安装BrowserAct CLI'
                ]
            })
        else:
            comparison['methods'].append({
                'name': 'BrowserAct',
                'type': 'browseract',
                'available': False,
                'install_command': 'uv tool install browser-act-cli --python 3.12'
            })

        # Playwright+OCR 信息
        if brave_monitor:
            comparison['methods'].append({
                'name': 'Playwright+OCR',
                'type': 'playwright_ocr',
                'available': True,
                'advantages': [
                    'Python 3.11兼容',
                    '成熟稳定',
                    '不依赖外部CLI'
                ],
                'disadvantages': [
                    '需要截图+OCR',
                    '识别可能出错',
                    '速度较慢',
                    '资源消耗较大'
                ]
            })
        else:
            comparison['methods'].append({
                'name': 'Playwright+OCR',
                'type': 'playwright_ocr',
                'available': False,
                'install_command': 'pip install playwright rapidocr_onnxruntime'
            })

        return jsonify(comparison)

    except Exception as e:
        logger.error(f"对比方法失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/browseract/test', methods=['POST'])
def test_browseract():
    """
    测试 BrowserAct 监控功能

    Request Body:
        {
            "symbol": "BTCUSDT",
            "method": "browseract"  // browseract, auto
        }

    Returns:
        JSON: 测试结果
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        method = data.get('method', 'auto')

        from app import get_hama_browseract_monitor, get_hama_brave_monitor

        test_results = []

        # 测试 BrowserAct
        if method in ['browseract', 'auto']:
            browseract_monitor = get_hama_browseract_monitor()
            if browseract_monitor:
                import time
                start_time = time.time()
                result = browseract_monitor.monitor_single_symbol(symbol)
                elapsed_time = time.time() - start_time

                test_results.append({
                    'method': 'BrowserAct',
                    'success': result is not None,
                    'time': round(elapsed_time, 2),
                    'data': result
                })

        # 测试 Playwright
        if method in ['playwright', 'auto']:
            brave_monitor = get_hama_brave_monitor()
            if brave_monitor:
                import time
                start_time = time.time()
                result = brave_monitor.monitor_single_symbol(symbol, '15m')
                elapsed_time = time.time() - start_time

                test_results.append({
                    'method': 'Playwright+OCR',
                    'success': result is not None,
                    'time': round(elapsed_time, 2),
                    'data': result
                })

        return jsonify({
            'success': True,
            'symbol': symbol,
            'test_results': test_results
        })

    except Exception as e:
        logger.error(f"测试BrowserAct失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_browseract_routes(app):
    """注册 BrowserAct 路由"""
    app.register_blueprint(bp)
    logger.info("✅ BrowserAct API 路由已注册")