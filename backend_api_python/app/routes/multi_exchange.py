"""
多交易所涨幅榜对比API路由
"""
from flask import Blueprint, request, jsonify
from app.utils.logger import get_logger

logger = get_logger(__name__)

multi_exchange_bp = Blueprint('multi_exchange', __name__)


@multi_exchange_bp.route('/compare', methods=['GET'])
def compare_exchanges():
    """
    对比多个交易所的涨幅榜数据

    参数:
        market: 市场类型 (spot/futures)，默认 futures
        limit: 返回数量，默认 10

    返回:
        Binance和OKX的涨幅榜数据及对比分析
    """
    try:
        market = request.args.get('market', 'futures')
        limit = int(request.args.get('limit', 10))

        if market not in ['spot', 'futures']:
            return jsonify({
                'code': 0,
                'msg': 'market must be spot or futures',
                'data': None
            }), 400

        if limit < 1 or limit > 50:
            return jsonify({
                'code': 0,
                'msg': 'limit must be between 1 and 50',
                'data': None
            }), 400

        from app.services.multi_exchange_gainer import MultiExchangeGainerService

        service = MultiExchangeGainerService()
        comparison = service.compare_exchanges(market=market, limit=limit)

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': comparison
        })

    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return jsonify({
            'code': 0,
            'msg': f'Invalid parameter: {str(e)}',
            'data': None
        }), 400
    except Exception as e:
        logger.error(f"Error in compare_exchanges: {e}", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@multi_exchange_bp.route('/binance', methods=['GET'])
def get_binance_gainers():
    """获取Binance涨幅榜"""
    try:
        market = request.args.get('market', 'futures')
        limit = int(request.args.get('limit', 10))

        from app.services.multi_exchange_gainer import MultiExchangeGainerService

        service = MultiExchangeGainerService()

        if market == 'futures':
            data = service.get_binance_futures_gainers(limit)
        else:
            data = service.get_binance_spot_gainers(limit)

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'exchange': 'Binance',
                'market': market,
                'count': len(data),
                'gainers': data
            }
        })

    except Exception as e:
        logger.error(f"Error getting Binance gainers: {e}")
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500


@multi_exchange_bp.route('/okx', methods=['GET'])
def get_okx_gainers():
    """获取OKX涨幅榜"""
    try:
        market = request.args.get('market', 'futures')
        limit = int(request.args.get('limit', 10))

        from app.services.multi_exchange_gainer import MultiExchangeGainerService

        service = MultiExchangeGainerService()

        if market == 'futures':
            data = service.get_okx_futures_gainers(limit)
        else:
            data = service.get_okx_spot_gainers(limit)

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'exchange': 'OKX',
                'market': market,
                'count': len(data),
                'gainers': data
            }
        })

    except Exception as e:
        logger.error(f"Error getting OKX gainers: {e}")
        return jsonify({
            'code': 0,
            'msg': str(e),
            'data': None
        }), 500
