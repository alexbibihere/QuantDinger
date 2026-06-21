"""
AiCoin 开放 API 路由
提供合约聪明钱、多空比、强平、大单等数据
"""
from flask import Blueprint, jsonify, request
from app.services.aicoin_api import (
    get_ticker,
    get_futures_interest,
    get_long_short_ratio,
    get_liquidation,
    get_big_orders,
    get_coin_info,
    get_smart_money_signals,
    get_market_overview,
    get_trading_pairs,
    get_all_binance_tickers,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
aicoin_bp = Blueprint("aicoin", __name__, url_prefix="/api/aicoin")


@aicoin_bp.route("/ticker", methods=["GET"])
def ticker():
    """币种实时行情"""
    coins = request.args.get("coins", "BTC,ETH")
    data = get_ticker(coin_list=coins)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取行情失败"}), 500


@aicoin_bp.route("/futures-interest", methods=["GET"])
def futures_interest():
    """合约持仓数据"""
    symbol = request.args.get("symbol")
    platform = request.args.get("platform")
    data = get_futures_interest(symbol=symbol, platform=platform)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取持仓数据失败"}), 500


@aicoin_bp.route("/long-short-ratio", methods=["GET"])
def long_short_ratio():
    """多空比"""
    symbol = request.args.get("symbol", "BTCUSDT")
    platform = request.args.get("platform", "binance")
    data = get_long_short_ratio(symbol=symbol, platform=platform)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取多空比失败"}), 500


@aicoin_bp.route("/liquidation", methods=["GET"])
def liquidation():
    """强平数据"""
    symbol = request.args.get("symbol")
    platform = request.args.get("platform")
    data = get_liquidation(symbol=symbol, platform=platform)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取强平数据失败"}), 500


@aicoin_bp.route("/big-orders", methods=["GET"])
def big_orders():
    """主力大单"""
    symbol = request.args.get("symbol")
    platform = request.args.get("platform")
    data = get_big_orders(symbol=symbol, platform=platform)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取大单数据失败"}), 500


@aicoin_bp.route("/smart-money", methods=["GET"])
def smart_money():
    """聪明钱信号（策略胜率信号）"""
    data = get_smart_money_signals()
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取聪明钱信号失败"}), 500


@aicoin_bp.route("/market-overview", methods=["GET"])
def market_overview():
    """市场概览（多空比+强平+灰度等）"""
    data = get_market_overview()
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "获取市场概览失败"}), 500


@aicoin_bp.route("/trading-pairs", methods=["GET"])
def trading_pairs():
    """获取平台所有交易对"""
    market = request.args.get("market", "binance")
    currency = request.args.get("currency", "USDT")
    data = get_trading_pairs(market=market, currency=currency)
    if data:
        return jsonify({"success": True, "data": data, "count": len(data)})
    return jsonify({"success": False, "message": "获取交易对失败"}), 500


@aicoin_bp.route("/binance-tickers", methods=["GET"])
def binance_tickers():
    """获取 Binance 所有 USDT 交易对行情"""
    data = get_all_binance_tickers()
    if data:
        return jsonify({"success": True, "data": data, "count": len(data)})
    return jsonify({"success": False, "message": "获取行情失败"}), 500

