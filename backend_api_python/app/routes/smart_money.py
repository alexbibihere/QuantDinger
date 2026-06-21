"""
聪明钱 (Smart Money) API 路由
提供 Binance 合约聪明钱指标数据
"""
from flask import Blueprint, jsonify, request
from app.services.smart_money import get_smart_money_overview, get_batch_smart_money
from app.utils.logger import get_logger

logger = get_logger(__name__)
smart_money_bp = Blueprint('smart_money', __name__, url_prefix='/api/smart-money')


@smart_money_bp.route('/overview/<symbol>', methods=['GET'])
def overview(symbol: str):
    """获取单个币种的聪明钱数据"""
    try:
        data = get_smart_money_overview(symbol.upper())
        if data:
            return jsonify({'success': True, 'data': data})
        return jsonify({'success': False, 'message': '获取数据失败'}), 500
    except Exception as e:
        logger.error(f"Smart Money overview error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@smart_money_bp.route('/batch', methods=['POST'])
def batch():
    """批量获取聪明钱数据"""
    try:
        symbols = request.get_json().get('symbols', [])
        if not symbols:
            return jsonify({'success': False, 'message': '请提供symbols列表'}), 400

        data = get_batch_smart_money(symbols, max_workers=3)
        return jsonify({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        logger.error(f"Smart Money batch error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
