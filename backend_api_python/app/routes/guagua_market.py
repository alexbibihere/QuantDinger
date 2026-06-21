"""
呱呱选币 API 路由
提供呱呱选币信号数据的 REST API
"""
from flask import Blueprint, request, jsonify
from app.services.guagua_service import get_signals_by_zone, fetch_posts
from datetime import datetime

guagua_bp = Blueprint("guagua", __name__)


def _estimate_hama_status_simple(signal: dict) -> dict:
    """基于涨幅和成交量估算 HAMA 状态（参考涨幅榜 tradingview_scanner 逻辑）"""
    gain = signal.get("gain", 0)
    vol = signal.get("vol_24h", 0)

    if gain > 3 and vol > 1000000:
        status = "strong_uptrend"
        trend = "up"
        color = "green"
    elif gain > 1:
        status = "uptrend"
        trend = "up"
        color = "green"
    elif gain < -3:
        status = "strong_downtrend"
        trend = "down"
        color = "red"
    elif gain < -1:
        status = "downtrend"
        trend = "down"
        color = "red"
    else:
        status = "sideways"
        trend = "neutral"
        color = "gray"

    return {
        "status": status,
        "trend": trend,
        "color": color,
        "method": "estimated_by_gain",
        "timestamp": datetime.now().isoformat()
    }


@guagua_bp.route("/api/guagua/signals", methods=["GET"])
def get_signals():
    zone_param = request.args.get("zone")
    limit = request.args.get("limit", type=int)

    # 强制默认值
    if zone_param is None or zone_param not in ("high", "mid", "low", "all"):
        zone_param = "high"
    if limit is None or limit <= 0:
        limit = 10

    print(f"[guagua] zone_param={zone_param!r}, limit={limit!r}", flush=True)

    zone_map = {"high": 3, "mid": 2, "low": 1, "all": None}
    zone_level = zone_map.get(zone_param, None)

    try:
        data = get_signals_by_zone(zone_level)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[guagua] get_signals_by_zone error: {e}", flush=True)
        return jsonify({"success": False, "error": str(e)}), 500

    signals = data.get("filtered", data["signals"])
    if limit and len(signals) > limit:
        signals = signals[:limit]

    # 给每个信号加上 hama_status（参考涨幅榜逻辑）
    for s in signals:
        s["hama_status"] = _estimate_hama_status_simple(s)

    return jsonify({
        "success": True,
        "data": signals,
        "stats": data["stats"],
        "filter": {
            "zone": zone_param,
            "limit": limit,
        },
    })


@guagua_bp.route("/api/guagua/summary", methods=["GET"])
def get_summary():
    """获取呱呱选币汇总统计"""
    data = get_signals_by_zone()
    stats = data["stats"]
    # Top 5 高流动性
    top5_high = data["high"][:5]
    # Top 5 涨幅
    all_sorted = sorted(data["signals"], key=lambda x: x.get("gain", 0), reverse=True)
    top5_gainers = all_sorted[:5]

    return jsonify({
        "success": True,
        "data": {
            "stats": stats,
            "top_high_liquidity": top5_high,
            "top_gainers": top5_gainers,
        },
    })


@guagua_bp.route("/api/guagua/posts", methods=["GET"])
def get_posts():
    """获取呱呱选币观点分享"""
    limit = request.args.get("limit", type=int, default=10)
    posts = fetch_posts(limit)

    return jsonify({
        "success": True,
        "data": posts,
        "total": len(posts),
    })


@guagua_bp.route("/api/guagua/health", methods=["GET"])
def health():
    """检测呱呱选币服务连接状态"""
    from app.services.guagua_service import _get_token, fetch_signals

    token = _get_token()
    if not token:
        return jsonify({
            "success": False,
            "connected": False,
            "message": "无法登录呱呱选币",
        })

    signals = fetch_signals()
    connected = len(signals) > 0

    return jsonify({
        "success": connected,
        "connected": connected,
        "signal_count": len(signals),
        "message": "呱呱选币连接正常" if connected else "呱呱选币数据为空",
    })
