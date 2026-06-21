"""
爱交易涨幅榜路由
"""
from flask import Blueprint, jsonify, request
from app.services.aijiaoyi_gainers import get_aijiaoyi_gainers
# from app.services.aijiaoyi_gainers_v2 import get_aijiaoyi_gainers_simple
from app.utils.logger import get_logger

logger = get_logger(__name__)
aijiaoyi_gainers_bp = Blueprint("aijiaoyi_data", __name__, url_prefix="/api/aijiaoyi")


@aijiaoyi_gainers_bp.route("/gainers", methods=["GET"])
def gainers():
    limit = min(int(request.args.get("limit", 20)), 50)

    # 优先使用简单模式 (browser-act markdown)
    data = get_aijiaoyi_gainers(limit=limit)

    # 如果简单模式失败，尝试原方法
    if not data:
        logger.info("简单模式无数据，尝试原方法...")
        data = get_aijiaoyi_gainers(limit=limit)

    if data:
        return jsonify({"success": True, "data": data, "count": len(data), "source": "aijiaoyi"})
    return jsonify({"success": False, "message": "获取数据失败"}), 500
