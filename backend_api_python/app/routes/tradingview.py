"""
TradingView 数据API路由
提供HAMA指标和其他技术指标数据
"""
from flask import Blueprint, request, jsonify
from app.services.tradingview_service import TradingViewDataService
from app.utils.logger import get_logger

logger = get_logger(__name__)

tradingview_bp = Blueprint('tradingview', __name__)
tv_service = TradingViewDataService()


@tradingview_bp.route('/hama/<symbol>', methods=['GET'])
def get_hama_signals(symbol):
    """
    获取指定币种的HAMA指标信号

    参数:
        symbol: 币种符号 (如 BTCUSDT)

    返回:
        HAMA指标分析结果
    """
    try:
        logger.info(f"Fetching HAMA signals for {symbol}")

        result = tv_service.get_hama_cryptocurrency_signals(symbol)

        # 检查条件
        conditions = tv_service.check_hama_conditions(result)

        return jsonify({
            'success': True,
            'data': {
                'symbol': result['symbol'],
                'trend': result['trend'],
                'candle_pattern': result['candle_pattern'],
                'recommendation': result['recommendation'],
                'confidence': result['confidence'],
                'hama_signals': result['signals'],
                'technical_indicators': result['technical_indicators'],
                'conditions': conditions,
                'timestamp': result['timestamp']
            }
        })

    except Exception as e:
        logger.error(f"Error fetching HAMA signals for {symbol}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_bp.route('/hama/batch', methods=['POST'])
def get_batch_hama_signals():
    """
    批量获取多个币种的HAMA指标信号

    请求体:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        }

    返回:
        批量HAMA指标分析结果
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])

        if not symbols:
            return jsonify({
                'success': False,
                'error': 'symbols parameter is required'
            }), 400

        logger.info(f"Fetching HAMA signals for {len(symbols)} symbols")

        results = tv_service.analyze_multiple_symbols(symbols)

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        logger.error(f"Error in batch HAMA analysis: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_bp.route('/gainers/hama', methods=['GET'])
def get_gainers_with_hama():
    """
    获取涨幅榜并进行HAMA指标分析

    参数:
        limit: 返回数量 (默认10)
        market: 市场类型 (spot/futures, 默认futures)

    返回:
        涨幅榜 + HAMA分析结果
    """
    try:
        from app.services.tradingview_service import get_binance_top_gainers_with_hama_analysis

        limit = int(request.args.get('limit', 10))
        market = request.args.get('market', 'futures')

        logger.info(f"Fetching top {limit} gainers with HAMA analysis for {market} market")

        result = get_binance_top_gainers_with_hama_analysis(limit=limit, market_type=market)

        if result['success']:
            return jsonify({
                'success': True,
                'count': result['count'],
                'timestamp': result['timestamp'],
                'data': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500

    except Exception as e:
        logger.error(f"Error fetching gainers with HAMA: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
