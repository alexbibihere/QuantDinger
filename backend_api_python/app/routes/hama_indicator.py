#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 指标 API 路由

提供本地计算 HAMA 指标的 API 接口
"""
from flask import Blueprint, jsonify, request
from app.services.hama_calculator import calculate_hama_from_ohlcv
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
hama_bp = Blueprint('hama', __name__, url_prefix='/api/hama')


@hama_bp.route('/calculate', methods=['POST'])
def calculate_hama():
    """
    计算 HAMA 指标

    请求体 (JSON):
    {
        "symbol": "BTCUSDT",
        "ohlcv": [[timestamp, open, high, low, close, volume], ...],
        "limit": 500  // 可选，默认使用全部数据
    }

    返回 (JSON):
    {
        "success": true,
        "data": {
            "timestamp": 1234567890000,
            "close": 3000.0,
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
            "bollinger_bands": {
                "upper": 3100.0,
                "basis": 3000.0,
                "lower": 2900.0,
                "width": 0.067,
                "squeeze": false,
                "expansion": false
            },
            "trend": {
                "direction": "up",
                "rising": true,
                "falling": false
            }
        }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        symbol = data.get('symbol', 'UNKNOWN')
        ohlcv = data.get('ohlcv', [])

        if not ohlcv or len(ohlcv) < 100:
            return jsonify({
                'success': False,
                'error': f'数据不足，至少需要 100 条 OHLCV 数据，当前: {len(ohlcv)}'
            }), 400

        logger.info(f"开始计算 {symbol} 的 HAMA 指标，数据量: {len(ohlcv)}")

        # 计算 HAMA 指标
        result = calculate_hama_from_ohlcv(ohlcv)

        if not result:
            return jsonify({
                'success': False,
                'error': 'HAMA 指标计算失败'
            }), 500

        # 添加币种信息
        result['symbol'] = symbol

        logger.info(f"{symbol} HAMA 指标计算成功: close={result['close']:.2f}, "
                   f"hama_close={result['hama']['close']:.2f}, color={result['hama']['color']}")

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"计算 HAMA 指标时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_bp.route('/latest', methods=['GET'])
def get_latest_hama():
    """
    获取指定币种和时间周期的最新 HAMA 指标

    查询参数:
        symbol: 币种符号 (例如: BTCUSDT)
        interval: 时间周期 (例如: 15m, 1h, 1d)
        limit: 数据条数 (可选，默认 500)

    返回 (JSON):
        {
            "success": true,
            "data": {
                "symbol": "BTCUSDT",
                "interval": "15m",
                "timestamp": 1234567890000,
                "close": 3000.0,
                "hama": {
                    ...
                },
                "bollinger_bands": {
                    ...
                },
                "trend": {
                    ...
                }
            }
        }
    """
    try:
        from app.services.kline import KlineService

        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '15m')
        limit = int(request.args.get('limit', 500))

        logger.info(f"获取 {symbol} ({interval}) 最新 HAMA 指标")

        # 使用 KlineService 获取 K线数据
        kline_service = KlineService()
        klines = kline_service.get_kline('Crypto', symbol, interval, limit)

        if not klines or len(klines) < 100:
            return jsonify({
                'success': False,
                'error': f'数据不足，至少需要 100 条 K线数据，当前: {len(klines) if klines else 0}'
            }), 400

        # 转换数据格式为 OHLCV 列表
        ohlcv_data = []
        for kline in klines:
            ohlcv_data.append([
                kline.get('time', 0),
                kline.get('open', 0),
                kline.get('high', 0),
                kline.get('low', 0),
                kline.get('close', 0),
                kline.get('volume', 0)
            ])

        if not ohlcv_data or len(ohlcv_data) < 100:
            return jsonify({
                'success': False,
                'error': f'数据不足，至少需要 100 条 K线数据'
            }), 400

        # 计算 HAMA 指标
        result = calculate_hama_from_ohlcv(ohlcv_data)

        if not result:
            return jsonify({
                'success': False,
                'error': 'HAMA 指标计算失败'
            }), 500

        # 添加币种和时间周期信息
        result['symbol'] = symbol
        result['interval'] = interval

        logger.info(f"{symbol} ({interval}) 最新 HAMA: close={result['close']:.2f}, "
                   f"color={result['hama']['color']}, "
                   f"cross_up={result['hama']['cross_up']}, "
                   f"cross_down={result['hama']['cross_down']}")

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"获取最新 HAMA 指标时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_bp.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'success': True,
        'service': 'HAMA Indicator API',
        'status': 'running'
    })
