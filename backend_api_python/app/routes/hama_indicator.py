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


@hama_bp.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'success': True,
        'service': 'HAMA Indicator API',
        'status': 'running'
    })
