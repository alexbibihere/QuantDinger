"""
AiCoin 涨幅榜路由
"""
from flask import Blueprint, jsonify, request
from app.services.aicoin_gainers import get_aicoin_gainers_api
from app.utils.logger import get_logger

logger = get_logger(__name__)
aicoin_gainers_bp = Blueprint("aicoin_gainers", __name__, url_prefix="/api/aicoin-gainers")


@aicoin_gainers_bp.route("/top", methods=["GET"])
def top_gainers():
    """获取 AiCoin 币安合约涨幅榜"""
    limit = min(int(request.args.get("limit", 20)), 50)
    data = get_aicoin_gainers_api(limit=limit)
    if data:
        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),
            "source": "aicoin",
        })
    return jsonify({"success": False, "message": "获取数据失败"}), 500
