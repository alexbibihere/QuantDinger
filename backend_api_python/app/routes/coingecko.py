"""
CoinGecko 涨幅榜路由 - 现货 24h 涨跌幅
"""
import logging
from flask import Blueprint, jsonify, request
from app.services.coingecko_gainers import fetch_gainers, fetch_all

logger = logging.getLogger(__name__)
coingecko_bp = Blueprint("coingecko", __name__)


@coingecko_bp.route("/api/coingecko/top", methods=["GET"])
def get_top_gainers():
    limit = request.args.get("limit", 10, type=int)
    limit = min(max(limit, 1), 100)
    try:
        data = fetch_gainers(limit=limit)
        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        logger.error(f"CoinGecko 涨幅榜失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@coingecko_bp.route("/api/coingecko/all", methods=["GET"])
def get_all():
    try:
        data = fetch_all()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"CoinGecko 全部数据失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
