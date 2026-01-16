#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 视觉识别 API 路由

使用大模型视觉能力从 TradingView 图表中识别 HAMA 指标
"""
from flask import Blueprint, jsonify, request
from app.services.hama_vision_extractor import extract_hama_with_vision
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
hama_vision_bp = Blueprint('hama_vision', __name__, url_prefix='/api/hama-vision')


@hama_vision_bp.route('/extract', methods=['POST'])
def extract_hama():
    """
    使用视觉识别提取 HAMA 指标

    请求体 (JSON):
    {
        "chart_url": "https://cn.tradingview.com/chart/U1FY2qxO/",  // 可选
        "symbol": "BTCUSDT",  // 可选
        "interval": "15"  // 可选
    }

    返回 (JSON):
    {
        "success": true,
        "data": {
            "hama_value": 3418.03,
            "hama_color": "green",
            "trend": "up",
            "current_price": 3369.1,
            "bollinger_bands": {
                "upper": 3500.0,
                "middle": 3400.0,
                "lower": 3300.0
            },
            "confidence": "high",
            "source": "vision",
            "screenshot_path": "/tmp/BTCUSDT_15_chart.png"
        }
    }
    """
    try:
        data = request.get_json() or {}

        chart_url = data.get('chart_url')
        symbol = data.get('symbol', 'BTCUSDT')
        interval = data.get('interval', '15')

        logger.info(f"开始视觉识别: symbol={symbol}, interval={interval}, chart_url={chart_url}")

        # 调用视觉识别
        result = extract_hama_with_vision(
            chart_url=chart_url,
            symbol=symbol,
            interval=interval
        )

        if result:
            logger.info(f"✅ 视觉识别成功: hama_value={result.get('hama_value')}, "
                       f"color={result.get('hama_color')}, confidence={result.get('confidence')}")
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': '视觉识别失败，请检查 OPENROUTER_API_KEY 配置和图表 URL'
            }), 500

    except Exception as e:
        logger.error(f"视觉识别时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_vision_bp.route('/health', methods=['GET'])
def health():
    """健康检查"""
    import os
    api_key_configured = bool(os.getenv('OPENROUTER_API_KEY'))

    return jsonify({
        'success': True,
        'service': 'HAMA Vision API',
        'status': 'running',
        'api_key_configured': api_key_configured,
        'model': os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o')
    })
