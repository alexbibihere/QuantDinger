"""
涨幅榜统计分析API路由
"""
from flask import Blueprint, jsonify, request
from app.services.gainer_tracker import get_gainer_tracker
from app.utils.logger import get_logger

logger = get_logger(__name__)
gainer_stats_bp = Blueprint('gainer_stats', __name__, url_prefix='/api/gainer-stats')


@gainer_stats_bp.route('/frequent-symbols', methods=['GET'])
def get_frequent_symbols():
    """
    获取最常出现在涨幅榜的币种

    参数:
        limit: 返回数量,默认20
        days: 统计最近多少天,默认7
    """
    try:
        limit = int(request.args.get('limit', 20))
        days = int(request.args.get('days', 7))

        logger.info(f"获取最近{days}天最常出现的币种 (top {limit})")

        tracker = get_gainer_tracker()
        result = tracker.get_top_frequent_symbols(limit=limit, days=days)

        return jsonify({
            'success': True,
            'data': result,
            'count': len(result),
            'days': days
        })

    except Exception as e:
        logger.error(f"获取涨幅榜统计失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"获取统计数据失败: {str(e)}"
        }), 500


@gainer_stats_bp.route('/symbol/<symbol>/appearances', methods=['GET'])
def get_symbol_appearances(symbol: str):
    """
    获取指定币种的出现记录

    参数:
        symbol: 币种符号
        days: 查询最近多少天,默认30
    """
    try:
        days = int(request.args.get('days', 30))

        logger.info(f"获取币种 {symbol} 最近{days}天的出现记录")

        tracker = get_gainer_tracker()
        appearance_days = tracker.get_symbol_appearance_days(symbol, days=days)
        total_appearances = len(appearance_days)

        # 获取总统计中的次数
        all_stats = tracker.get_top_frequent_symbols(limit=1000, days=days)
        symbol_stats = next((s for s in all_stats if s['symbol'] == symbol), None)

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'total_appearances': total_appearances,
                'appearance_days': appearance_days,
                'percentage': symbol_stats['percentage'] if symbol_stats else 0,
                'rank': next((i + 1 for i, s in enumerate(all_stats) if s['symbol'] == symbol), None)
            }
        })

    except Exception as e:
        logger.error(f"获取币种 {symbol} 出现记录失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"获取数据失败: {str(e)}"
        }), 500


@gainer_stats_bp.route('/today', methods=['GET'])
def get_today_appearances():
    """
    获取今天出现在涨幅榜的币种列表
    """
    try:
        logger.info("获取今日涨幅榜币种列表")

        tracker = get_gainer_tracker()
        symbols = tracker.get_today_appearances()

        return jsonify({
            'success': True,
            'data': symbols,
            'count': len(symbols),
            'date': tracker.daily_key.split(':')[-1] if hasattr(tracker, 'daily_key') else None
        })

    except Exception as e:
        logger.error(f"获取今日涨幅榜失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"获取数据失败: {str(e)}"
        }), 500


@gainer_stats_bp.route('/record', methods=['POST'])
def record_appearances():
    """
    手动记录涨幅榜出现(用于测试或手动更新)

    Body:
        {
            "symbols": ["BTCUSDT", "ETHUSDT", ...],
            "date": "2024-01-10"  // 可选,默认为今天
        }
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        date = data.get('date', None)

        if not symbols:
            return jsonify({
                'success': False,
                'message': '请提供币种列表'
            }), 400

        logger.info(f"手动记录涨幅榜出现: {len(symbols)} 个币种, 日期: {date or '今天'}")

        tracker = get_gainer_tracker()
        for symbol in symbols:
            tracker.record_appearance(symbol, date)

        return jsonify({
            'success': True,
            'message': f"已记录 {len(symbols)} 个币种"
        })

    except Exception as e:
        logger.error(f"记录涨幅榜出现失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"记录失败: {str(e)}"
        }), 500
