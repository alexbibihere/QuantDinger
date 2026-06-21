"""
链上聪明钱 (On-chain Smart Money) API 路由
提供 Binance Web3 链上聪明钱信号数据
"""
from flask import Blueprint, jsonify, request
from app.services.chain_smart_money import (
    get_smart_money_signals,
    get_recent_signals,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
chain_smart_money_bp = Blueprint(
    "chain_smart_money", __name__, url_prefix="/api/chain-smart-money"
)


@chain_smart_money_bp.route("/signals", methods=["GET"])
def signals():
    """获取链上聪明钱信号"""
    chain_id = request.args.get("chain_id", "CT_501")
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 10)), 100)
    signal_type = request.args.get("signal_type", "")

    data = get_smart_money_signals(
        chain_id=chain_id,
        page=page,
        page_size=page_size,
        signal_type=signal_type,
    )
    if data is not None:
        return jsonify(
            {
                "success": True,
                "data": data,
                "count": len(data),
                "chain": "Solana" if chain_id == "CT_501" else "BSC",
            }
        )
    return jsonify({"success": False, "message": "获取链上聪明钱数据失败"}), 500


@chain_smart_money_bp.route("/recent", methods=["GET"])
def recent():
    """一次性获取 Solana 和 BSC 的最新信号"""
    page_size = min(int(request.args.get("page_size", 5)), 100)
    data = get_recent_signals(page_size=page_size)
    if data and data.get("_count", {}).get("solana", 0) + data.get("_count", {}).get(
        "bsc", 0
    ) > 0:
        return jsonify(
            {
                "success": True,
                "data": data,
                "count": data.pop("_count", {}),
            }
        )
    return jsonify({"success": False, "message": "获取链上聪明钱数据失败"}), 500
