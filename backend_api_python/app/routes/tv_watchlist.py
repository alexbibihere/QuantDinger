#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView 关注列表 API 路由

用 TV 账号密码登录 → 获取关注列表 → 获取 HAMA 数据 + 生成 SVG 截图

API 端点:
  POST /api/tv-watchlist/login        — 登录 TV 获取关注列表
  POST /api/tv-watchlist/hama         — 获取关注列表各品种的 HAMA 数据
  POST /api/tv-watchlist/charts       — 获取关注列表各品种的 HAMA 图表截图
"""

from flask import Blueprint, request, jsonify
import logging
from app.services.tv_watchlist_service import get_watchlist_service
from app.services.hama_tv_service import hama_tv_service

logger = logging.getLogger(__name__)

tv_watchlist_bp = Blueprint("tv_watchlist", __name__, url_prefix="/api/tv-watchlist")


@tv_watchlist_bp.route("/login", methods=["POST"])
def login_and_get_list():
    """
    登录 TradingView 并获取关注列表

    POST /api/tv-watchlist/login
    Body: {
        "username": "your_tv_email@example.com",
        "password": "your_tv_password"
    }

    Returns:
        {
            "success": true,
            "data": {
                "symbols": ["BTCUSDT", "ETHUSDT", ...],
                "count": 10
            }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请提供 JSON 请求体"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "请提供 TradingView 邮箱和密码"}), 400

    logger.info(f"📡 TV 关注列表登录请求: {username}")

    # 登录
    service = get_watchlist_service()
    success = service.login(username, password)

    if not success:
        return jsonify({
            "success": False,
            "message": "TradingView 登录失败，请检查账号密码",
            "hint": "如果开启了二步验证，请使用应用专用密码"
        }), 401

    # 获取关注列表品种
    symbols = service.get_watchlist_symbols()

    if not symbols:
        return jsonify({
            "success": True,
            "message": "登录成功，但未找到关注列表或关注列表为空",
            "data": {"symbols": [], "count": 0}
        })

    # 提取品种名
    clean_symbols = []
    for s in symbols:
        if ":" in s:
            s = s.split(":")[1]
        clean_symbols.append(s.upper())

    # 去重
    clean_symbols = list(dict.fromkeys(clean_symbols))

    return jsonify({
        "success": True,
        "message": f"登录成功，获取到 {len(clean_symbols)} 个关注品种",
        "data": {
            "symbols": clean_symbols,
            "count": len(clean_symbols),
        }
    })


@tv_watchlist_bp.route("/hama", methods=["POST"])
def get_watchlist_hama():
    """
    获取关注列表各品种的 HAMA 指标数据

    POST /api/tv-watchlist/hama
    Body: {
        "username": "your_tv_email@example.com",
        "password": "your_tv_password",
        "timeframe": "D"
    }

    Returns:
        {
            "success": true,
            "data": {
                "count": 10,
                "items": [
                    {
                        "symbol": "BTCUSDT",
                        "price": 64700,
                        "hama_color": "red",
                        "chart_svg": "data:image/svg+xml;base64,..."
                    },
                    ...
                ]
            }
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请提供 JSON 请求体"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    timeframe = data.get("timeframe", "D")

    if not username or not password:
        return jsonify({"success": False, "message": "请提供 TradingView 邮箱和密码"}), 400

    # 登录
    service = get_watchlist_service()
    if not service.login(username, password):
        return jsonify({"success": False, "message": "TradingView 登录失败"}), 401

    symbols = service.get_watchlist_symbols()
    if not symbols:
        return jsonify({"success": True, "message": "关注列表为空", "data": {"count": 0, "items": []}})

    # 提取品种名
    clean_symbols = []
    for s in symbols:
        if ":" in s:
            s = s.split(":")[1]
        clean_symbols.append(s.upper())
    clean_symbols = list(dict.fromkeys(clean_symbols))

    # 获取 HAMA 数据
    from app.services.hama_chart_svg import generate_hama_chart_svg

    results = hama_tv_service.batch_get_hama(
        symbols=clean_symbols,
        timeframe=timeframe,
    )

    items = []
    for sym, hama in results.get("results", {}).items():
        if not hama.get("success"):
            continue
        # 生成 SVG 截图
        svg_base64 = generate_hama_chart_svg(hama)
        items.append({
            "symbol": sym,
            "price": hama.get("price"),
            "hama_color": hama.get("hama_color"),
            "hama_trend": "多头" if hama.get("hama_color") == "green" else "空头" if hama.get("hama_color") == "red" else "横盘",
            "change_pct": hama.get("change_pct"),
            "hama_close": hama.get("hama_close"),
            "hama_ma": hama.get("hama_ma"),
            "cross_up": hama.get("cross_up"),
            "cross_down": hama.get("cross_down"),
            "chart_svg": f"data:image/svg+xml;base64,{svg_base64}" if svg_base64 else None,
        })

    return jsonify({
        "success": True,
        "message": f"获取到 {len(items)} 个品种的 HAMA 数据",
        "data": {
            "count": len(items),
            "items": items,
        }
    })


@tv_watchlist_bp.route("/charts", methods=["POST"])
def get_watchlist_charts():
    """
    获取关注列表各品种的 HAMA 图表截图（纯代码生成 SVG）

    POST /api/tv-watchlist/charts
    Body: {
        "username": "your_tv_email@example.com",
        "password": "your_tv_password",
        "timeframe": "D"
    }

    Returns:
        {
            "success": true,
            "data": {
                "count": 10,
                "items": [
                    {
                        "symbol": "BTCUSDT",
                        "price": 64700,
                        "hama_color": "red",
                        "chart_svg": "data:image/svg+xml;base64,..."
                    },
                    ...
                ]
            }
        }
    """
    return get_watchlist_hama()  # 复用同一个逻辑
