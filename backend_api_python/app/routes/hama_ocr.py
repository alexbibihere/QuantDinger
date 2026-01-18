#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA OCR 识别 API 路由

使用本地 OCR（RapidOCR/PaddleOCR/Tesseract/EasyOCR）识别 TradingView 图表中的 HAMA 指标
完全免费，无需 API 密钥！

默认使用 RapidOCR（速度快，准确率高，兼容性好）
"""
from flask import Blueprint, jsonify, request
from app.services.hama_ocr_extractor import extract_hama_with_ocr
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
hama_ocr_bp = Blueprint('hama_ocr', __name__, url_prefix='/api/hama-ocr')


@hama_ocr_bp.route('/extract', methods=['POST'])
def extract_hama():
    """
    使用本地 OCR 提取 HAMA 指标（完全免费）

    请求体 (JSON):
    {
        "chart_url": "https://cn.tradingview.com/chart/U1FY2qxO/",  // 可选
        "symbol": "BTCUSDT",  // 可选
        "interval": "15",  // 可选
        "ocr_engine": "rapidocr"  // 可选: rapidocr/paddleocr/tesseract/easyocr
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
            "ocr_engine": "paddleocr",
            "confidence": "medium",
            "source": "ocr",
            "screenshot_path": "/tmp/ETHUSD_15_chart.png"
        }
    }
    """
    try:
        data = request.get_json() or {}

        chart_url = data.get('chart_url')
        symbol = data.get('symbol', 'BTCUSDT')
        interval = data.get('interval', '15')
        ocr_engine = data.get('ocr_engine', 'rapidocr')

        logger.info(f"开始 OCR 识别: symbol={symbol}, interval={interval}, "
                   f"chart_url={chart_url}, ocr_engine={ocr_engine}")

        # 调用 OCR 识别
        result = extract_hama_with_ocr(
            chart_url=chart_url,
            symbol=symbol,
            interval=interval,
            ocr_engine=ocr_engine
        )

        if result:
            logger.info(f"✅ OCR 识别成功: hama_value={result.get('hama_value')}, "
                       f"color={result.get('hama_color')}, engine={result.get('ocr_engine')}")
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'OCR 识别失败，请检查 OCR 引擎是否已安装'
            }), 500

    except Exception as e:
        logger.error(f"OCR 识别时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hama_ocr_bp.route('/health', methods=['GET'])
def health():
    """健康检查"""
    import os

    # 检查已安装的 OCR 引擎
    available_engines = []

    try:
        import rapidocr_onnxruntime
        available_engines.append('rapidocr')
    except ImportError:
        pass

    try:
        import paddleocr
        available_engines.append('paddleocr')
    except ImportError:
        pass

    try:
        import pytesseract
        available_engines.append('tesseract')
    except ImportError:
        pass

    try:
        import easyocr
        available_engines.append('easyocr')
    except ImportError:
        pass

    return jsonify({
        'success': True,
        'service': 'HAMA OCR API',
        'status': 'running',
        'available_engines': available_engines,
        'default_engine': 'rapidocr' if 'rapidocr' in available_engines else available_engines[0] if available_engines else None
    })
