#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TradingView Playwright API 路由
使用 Playwright 从 TradingView 提取 HAMA 指标数据
"""
from flask import Blueprint, request, jsonify
from app.utils.logger import get_logger
from app.services.tradingview_playwright import (
    PLAYWRIGHT_AVAILABLE,
    get_hama_from_tradingview,
    get_tradingview_data
)

logger = get_logger(__name__)

# 创建蓝图
tradingview_playwright_bp = Blueprint('tradingview_playwright', __name__)


@tradingview_playwright_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'success': True,
        'data': {
            'available': PLAYWRIGHT_AVAILABLE,
            'service': 'tradingview_playwright'
        }
    })


@tradingview_playwright_bp.route('/get-chart-data', methods=['POST'])
def get_chart_data():
    """
    获取图表数据

    请求体:
    {
        "symbol": "BTCUSDT",
        "interval": "15",
        "exchange": "BINANCE",
        "headless": true
    }
    """
    if not PLAYWRIGHT_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Playwright 服务不可用'
        }), 500

    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        interval = data.get('interval', '15')
        exchange = data.get('exchange', 'BINANCE')
        headless = data.get('headless', True)

        if not symbol:
            return jsonify({
                'success': False,
                'message': '缺少 symbol 参数'
            }), 400

        logger.info(f"开始获取 {symbol} 的图表数据 (interval={interval})")

        result = get_tradingview_data(symbol, interval, exchange, headless)

        if result:
            return jsonify({
                'success': True,
                'message': f'成功获取 {symbol} 的图表数据',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取图表数据失败'
            }), 500

    except Exception as e:
        logger.error(f"获取图表数据异常: {e}")
        return jsonify({
            'success': False,
            'message': f'获取图表数据异常: {str(e)}'
        }), 500


@tradingview_playwright_bp.route('/get-hama', methods=['POST'])
def get_hama():
    """
    获取 HAMA 指标

    请求体:
    {
        "symbol": "BTCUSDT",
        "interval": "15",
        "headless": true,
        "chart_url": "https://www.tradingview.com/chart/XXXXXXXX/"  # 可选：自定义图表 URL
    }

    响应:
    {
        "success": true,
        "message": "成功获取HAMA指标",
        "data": {
            "symbol": "BTCUSDT",
            "hama_value": 95678.42,
            "hama_color": "green",
            "hama_trend": "up",
            "price": 95680.50,
            "source": "tradingview_playwright"
        }
    }

    注意：
    - 如果不提供 chart_url，将使用默认的 TradingView 图表（可能不包含 HAMA 指标）
    - 建议使用 chart_url 来访问包含 HAMA 指标的自定义图表
    """
    if not PLAYWRIGHT_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Playwright 服务不可用'
        }), 500

    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        interval = data.get('interval', '15')
        headless = data.get('headless', True)
        chart_url = data.get('chart_url', None)

        if not symbol and not chart_url:
            return jsonify({
                'success': False,
                'message': '缺少 symbol 参数或 chart_url 参数'
            }), 400

        logger.info(f"开始获取 {symbol or chart_url} 的HAMA指标 (interval={interval})")

        result = get_hama_from_tradingview(symbol, interval, headless, chart_url)

        if result:
            message = '成功获取HAMA指标'
            if result.get('note'):
                message = f'获取成功，但{result["note"]}'
            return jsonify({
                'success': True,
                'message': message,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '获取HAMA指标失败'
            }), 500

    except Exception as e:
        logger.error(f"获取HAMA指标异常: {e}")
        return jsonify({
            'success': False,
            'message': f'获取HAMA指标异常: {str(e)}'
        }), 500


@tradingview_playwright_bp.route('/batch-get-hama', methods=['POST'])
def batch_get_hama():
    """
    批量获取多个币种的 HAMA 指标

    请求体:
    {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "15",
        "headless": true
    }
    """
    if not PLAYWRIGHT_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Playwright 服务不可用'
        }), 500

    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        interval = data.get('interval', '15')
        headless = data.get('headless', True)

        if not symbols:
            return jsonify({
                'success': False,
                'message': '缺少 symbols 参数'
            }), 400

        logger.info(f"开始批量获取 {len(symbols)} 个币种的HAMA指标")

        results = []
        success_count = 0
        fail_count = 0

        for symbol in symbols:
            symbol = symbol.upper()
            try:
                result = get_hama_from_tradingview(symbol, interval, headless)
                if result:
                    results.append(result)
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"获取 {symbol} HAMA失败: {e}")
                fail_count += 1

        return jsonify({
            'success': True,
            'message': f'批量获取完成: 成功 {success_count} 个, 失败 {fail_count} 个',
            'data': {
                'results': results,
                'summary': {
                    'total': len(symbols),
                    'success': success_count,
                    'failed': fail_count
                }
            }
        })

    except Exception as e:
        logger.error(f"批量获取HAMA指标异常: {e}")
        return jsonify({
            'success': False,
            'message': f'批量获取HAMA指标异常: {str(e)}'
        }), 500
