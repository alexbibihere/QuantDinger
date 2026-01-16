#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView 图表数据提取 API 路由
使用 pyppeteer 从 TradingView 提取图表指标数据
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Optional

from app.services.tradingview_pyppeteer import (
    get_tradingview_data,
    get_hama_from_tradingview,
    PYPPETEER_AVAILABLE
)

logger = logging.getLogger(__name__)

tradingview_pyppeteer_bp = Blueprint('tradingview_pyppeteer', __name__)


@tradingview_pyppeteer_bp.route('/health', methods=['GET'])
def health_check():
    """检查服务是否可用"""
    return jsonify({
        'success': True,
        'data': {
            'available': PYPPETEER_AVAILABLE,
            'service': 'tradingview_pyppeteer'
        }
    })


@tradingview_pyppeteer_bp.route('/get-chart-data', methods=['POST'])
def get_chart_data():
    """
    获取 TradingView 图表数据

    POST /api/tradingview-pyppeteer/get-chart-data
    Body: {
        "symbol": "BTCUSDT",
        "interval": "15",  // 可选,默认15
        "exchange": "BINANCE",  // 可选,默认BINANCE
        "headless": true  // 可选,默认true
    }
    """
    try:
        if not PYPPETEER_AVAILABLE:
            return jsonify({
                'success': False,
                'message': 'pyppeteer 未安装，请运行: pip install pyppeteer'
            }), 500

        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        interval = data.get('interval', '15')
        exchange = data.get('exchange', 'BINANCE')
        headless = data.get('headless', True)

        logger.info(f"开始获取 {symbol} 的图表数据 (interval={interval}, exchange={exchange})")

        # 获取数据
        result = get_tradingview_data(symbol, interval, exchange, headless)

        if result:
            logger.info(f"✅ 成功获取 {symbol} 的图表数据")
            return jsonify({
                'success': True,
                'message': '成功获取图表数据',
                'data': result
            })
        else:
            logger.error(f"❌ 获取 {symbol} 的图表数据失败")
            return jsonify({
                'success': False,
                'message': '获取图表数据失败'
            }), 500

    except Exception as e:
        logger.error(f"获取图表数据异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tradingview_pyppeteer_bp.route('/get-hama', methods=['POST'])
def get_hama():
    """
    获取 HAMA 指标数据

    POST /api/tradingview-pyppeteer/get-hama
    Body: {
        "symbol": "BTCUSDT",
        "interval": "15",  // 可选,默认15
        "headless": true  // 可选,默认true
    }
    """
    try:
        if not PYPPETEER_AVAILABLE:
            return jsonify({
                'success': False,
                'message': 'pyppeteer 未安装，请运行: pip install pyppeteer'
            }), 500

        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        interval = data.get('interval', '15')
        headless = data.get('headless', True)

        logger.info(f"开始获取 {symbol} 的HAMA指标 (interval={interval})")

        # 获取HAMA数据
        result = get_hama_from_tradingview(symbol, interval, headless)

        if result:
            logger.info(f"✅ 成功获取 {symbol} 的HAMA指标")
            return jsonify({
                'success': True,
                'message': '成功获取HAMA指标',
                'data': result
            })
        else:
            logger.error(f"❌ 获取 {symbol} 的HAMA指标失败")
            return jsonify({
                'success': False,
                'message': '获取HAMA指标失败'
            }), 500

    except Exception as e:
        logger.error(f"获取HAMA指标异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tradingview_pyppeteer_bp.route('/batch-get-hama', methods=['POST'])
def batch_get_hama():
    """
    批量获取多个币种的 HAMA 指标

    POST /api/tradingview-pyppeteer/batch-get-hama
    Body: {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "15",  // 可选
        "headless": true  // 可选
    }
    """
    try:
        if not PYPPETEER_AVAILABLE:
            return jsonify({
                'success': False,
                'message': 'pyppeteer 未安装'
            }), 500

        data = request.get_json()
        symbols = data.get('symbols', [])

        if not symbols:
            return jsonify({
                'success': False,
                'message': '请提供币种列表'
            }), 400

        interval = data.get('interval', '15')
        headless = data.get('headless', True)

        results = []
        errors = []

        logger.info(f"开始批量获取 {len(symbols)} 个币种的HAMA指标")

        for symbol in symbols:
            try:
                symbol = symbol.upper()
                logger.info(f"正在处理 {symbol}...")

                result = get_hama_from_tradingview(symbol, interval, headless)

                if result:
                    results.append(result)
                    logger.info(f"✅ {symbol} 获取成功")
                else:
                    errors.append({'symbol': symbol, 'error': '获取失败'})
                    logger.warning(f"⚠️ {symbol} 获取失败")

            except Exception as e:
                errors.append({'symbol': symbol, 'error': str(e)})
                logger.error(f"❌ {symbol} 处理异常: {e}")

        logger.info(f"批量获取完成: 成功 {len(results)}, 失败 {len(errors)}")

        return jsonify({
            'success': True,
            'message': f'批量获取完成: 成功 {len(results)}, 失败 {len(errors)}',
            'data': {
                'results': results,
                'errors': errors,
                'total': len(symbols),
                'success_count': len(results),
                'error_count': len(errors)
            }
        })

    except Exception as e:
        logger.error(f"批量获取HAMA指标异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'批量获取失败: {str(e)}'
        }), 500
