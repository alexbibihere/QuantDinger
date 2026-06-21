"""
爱交易涨幅榜 v2 路由 - 币安永续合约当日涨跌幅
"""
import logging
from flask import Blueprint, jsonify, request

from app.services.aijiaoyi_gainers_v2 import fetch_gainers, BINANCE_PERP_SYMBOLS

logger = logging.getLogger(__name__)

aijiaoyi_v2_bp = Blueprint("aijiaoyi_v2", __name__)


@aijiaoyi_v2_bp.route("/api/aijiaoyi-v2/top", methods=["GET"])
def get_top_gainers():
    """获取当日涨幅榜 Top N"""
    limit = request.args.get("limit", 10, type=int)
    limit = min(max(limit, 1), 50)

    try:
        data = fetch_gainers(limit=limit)
        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),
        })
    except Exception as e:
        logger.error(f"爱交易 v2 涨幅榜失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@aijiaoyi_v2_bp.route("/api/aijiaoyi-v2/all", methods=["GET"])
def get_all_gainers():
    """获取全部币种涨跌幅"""
    try:
        data = fetch_gainers(limit=200)
        # 再排序一次
        gainers = sorted([d for d in data if d["change_pct"] >= 0], key=lambda x: x["change_pct"], reverse=True)
        losers = sorted([d for d in data if d["change_pct"] < 0], key=lambda x: x["change_pct"])
        return jsonify({
            "success": True,
            "data": {
                "gainers": gainers[:20],
                "losers": losers[:20],
                "total": len(data),
            },
        })
    except Exception as e:
        logger.error(f"爱交易 v2 全部数据失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@aijiaoyi_v2_bp.route("/api/aijiaoyi-v2/symbols", methods=["GET"])
def get_symbols():
    """获取支持的币种列表"""
    return jsonify({
        "success": True,
        "data": BINANCE_PERP_SYMBOLS,
        "count": len(BINANCE_PERP_SYMBOLS),
    })
