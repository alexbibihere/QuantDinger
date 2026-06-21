#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA TV API 路由 — 通过 TradingView-API 桥接层获取 HAMA 指标

使用 tv-bridge (Node.js, localhost:3456) 获取 TradingView WebSocket 数据，
然后在本地 Python 中计算完整 HAMA 指标（EMA/WMA/SMA + 布林带 + 交叉信号）。

替代现有 OCR 截图方案（hama_ocr.py / hama_brave_monitor.py），速度快 5-10 倍。

API 端点：
  GET  /api/hama-tv/hama/:symbol          — 获取单个品种 HAMA
  POST /api/hama-tv/hama/batch             — 批量获取 HAMA
  GET  /api/hama-tv/health                 — 检查 tv-bridge 连接状态
"""

from flask import Blueprint, request, jsonify
import logging

from app.services.hama_tv_service import hama_tv_service

logger = logging.getLogger(__name__)

hama_tv_bp = Blueprint("hama_tv", __name__, url_prefix="/api/hama-tv")


@hama_tv_bp.route("/health", methods=["GET"])
def health_check():
    """检查 tv-bridge 连接状态"""
    import requests

    try:
        resp = requests.get("http://localhost:3456/health", timeout=3)
        bridge_status = resp.json()
        return jsonify(
            {
                "success": True,
                "message": "tv-bridge 服务运行正常",
                "data": {
                    "bridge_connected": True,
                    "tv_connected": bridge_status.get("tvConnected", False),
                    "bridge_uptime": bridge_status.get("uptime", 0),
                    "degraded": hama_tv_service.is_degraded(),
                },
            }
        )
    except requests.exceptions.ConnectionError:
        return jsonify(
            {
                "success": False,
                "message": "tv-bridge 未启动",
                "data": {
                    "bridge_connected": False,
                    "degraded": hama_tv_service.is_degraded(),
                },
            }
        ), 503


@hama_tv_bp.route("/hama", methods=["GET"])
def get_hama():
    """
    获取单个品种的 HAMA 指标

    GET /api/hama-tv/hama?symbol=BTCUSDT&timeframe=D&range=500

    参数:
        symbol: 品种符号 (必填, 如 BTCUSDT)
        timeframe: 时间周期 (可选, 默认 D, 可选: 1/3/5/15/30/60/240/D/W/M)
        range: K 线数量 (可选, 默认 500)
    """
    symbol = request.args.get("symbol", "").strip().upper()
    timeframe = request.args.get("timeframe", "D").strip()
    range_count = request.args.get("range", 500, type=int)

    if not symbol:
        return jsonify(
            {"success": False, "message": "请提供品种符号 (symbol)"}
        ), 400

    logger.info(f"📊 HAMA-TV 请求: {symbol} ({timeframe}, range={range_count})")

    result = hama_tv_service.get_hama(
        symbol=symbol,
        timeframe=timeframe,
        range_count=range_count,
    )

    if result.get("success"):
        return jsonify(
            {
                "success": True,
                "message": f"成功获取 {symbol} HAMA 指标",
                "data": result,
            }
        )
    else:
        status_code = 500
        if result.get("fallback"):
            status_code = 503  # tv-bridge 不可用
        return jsonify(
            {
                "success": False,
                "message": result.get("error", "获取 HAMA 失败"),
                "data": result,
            }
        ), status_code


@hama_tv_bp.route("/hama/batch", methods=["POST"])
def batch_get_hama():
    """
    批量获取多个品种的 HAMA 指标

    POST /api/hama-tv/hama/batch
    Body: {
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        "timeframe": "D",
        "range": 500
    }
    """
    data = request.get_json()
    if not data:
        return jsonify(
            {"success": False, "message": "请提供 JSON 请求体"}
        ), 400

    symbols = data.get("symbols", [])
    timeframe = data.get("timeframe", "D")
    range_count = data.get("range", 500)

    if not symbols:
        return jsonify(
            {"success": False, "message": "请提供品种列表 (symbols)"}
        ), 400

    logger.info(
        f"📊 HAMA-TV 批量请求: {len(symbols)} 个品种 ({timeframe})"
    )

    result = hama_tv_service.batch_get_hama(
        symbols=symbols,
        timeframe=timeframe,
        range_count=range_count,
    )

    return jsonify(
        {
            "success": result["success"],
            "message": f"批量获取完成: 成功 {result['success_count']} / 失败 {result['error_count']}",
            "data": result,
        }
    )


@hama_tv_bp.route("/hama/simple", methods=["GET"])
def get_hama_simple():
    """
    简化版 HAMA 接口 — 与现有 OCR 接口输出格式兼容

    GET /api/hama-tv/hama/simple?symbol=BTCUSDT&interval=D

    返回格式与 /api/hama-tv/hama 一致，但额外包含
    OCR 兼容字段以便前端直接替换
    """
    symbol = request.args.get("symbol", "").strip().upper()
    interval = request.args.get("interval", "D").strip()

    if not symbol:
        return jsonify(
            {"success": False, "message": "请提供品种符号 (symbol)"}
        ), 400

    result = hama_tv_service.get_hama(
        symbol=symbol,
        timeframe=interval,
    )

    if result.get("success"):
        # 添加 OCR 兼容字段
        data = result.copy()
        data["hama_color"] = data.get("hama_color", "gray")
        data["hama_value"] = data.get("hama_close", 0)
        data["trend"] = (
            "多头" if data.get("hama_color") == "green"
            else "空头" if data.get("hama_color") == "red"
            else "横盘"
        )
        data["interval"] = interval

        return jsonify(
            {
                "success": True,
                "message": f"成功获取 {symbol} HAMA 指标",
                "data": data,
            }
        )
    else:
        return jsonify(
            {
                "success": False,
                "message": result.get("error", "获取 HAMA 失败"),
            }
        ), 500


@hama_tv_bp.route("/hama/chart-svg", methods=["GET"])
def get_hama_chart_svg():
    """
    获取 HAMA 指标图表截图（纯代码生成 SVG，无需浏览器）

    GET /api/hama-tv/hama/chart-svg?symbol=BTCUSDT&timeframe=D

    返回 base64 编码的 SVG 图片，前端可显示为 <img src="data:image/svg+xml;base64,..." />
    """
    from app.services.hama_chart_svg import generate_hama_chart_svg

    symbol = request.args.get("symbol", "").strip().upper()
    timeframe = request.args.get("timeframe", "D").strip()

    if not symbol:
        return jsonify({"success": False, "message": "请提供品种符号"}), 400

    result = hama_tv_service.get_hama(symbol=symbol, timeframe=timeframe)
    if not result.get("success"):
        return jsonify({"success": False, "message": result.get("error", "获取HAMA失败")}), 500

    svg_base64 = generate_hama_chart_svg(result)
    if not svg_base64:
        return jsonify({"success": False, "message": "生成图表失败"}), 500

    return jsonify({
        "success": True,
        "message": f"生成 {symbol} HAMA 图表成功",
        "data": {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": result.get("price"),
            "hama_color": result.get("hama_color"),
            "chart_svg_base64": f"data:image/svg+xml;base64,{svg_base64}",
            "source": "tv-bridge-svg",
        }
    })
