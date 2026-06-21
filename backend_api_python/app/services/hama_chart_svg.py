#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 图表截图生成器 — 纯代码生成 SVG，无需浏览器

直接使用 hama_tv_service 获取的数据生成 SVG 图表图片，
返回 base64 编码，前端可直接显示。

替代 OCR 截图方案，不需要 Playwright/Brave/RapidOCR。
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


def generate_hama_chart_svg(hama_data: Dict[str, Any]) -> Optional[str]:
    """
    根据 HAMA 数据生成 SVG 图表，返回 base64 编码

    Args:
        hama_data: hama_tv_service.get_hama() 返回的数据

    Returns:
        base64 编码的 SVG 图片数据
    """
    if not hama_data or not hama_data.get("success"):
        return None

    symbol = hama_data.get("symbol", "N/A")
    price = hama_data.get("price", 0)
    hama_close = hama_data.get("hama_close", 0)
    hama_open = hama_data.get("hama_open", 0)
    hama_ma = hama_data.get("hama_ma", 0)
    hama_color = hama_data.get("hama_color", "gray")
    bb_upper = hama_data.get("bb_upper", 0)
    bb_basis = hama_data.get("bb_basis", 0)
    bb_lower = hama_data.get("bb_lower", 0)
    cross_up = hama_data.get("cross_up", False)
    cross_down = hama_data.get("cross_down", False)
    change_pct = hama_data.get("change_pct", 0)
    timeframe = hama_data.get("timeframe", "D")

    # 颜色
    up_color = "#26a69a"
    down_color = "#ef5350"
    ma_color = "#faad14"
    hama_line_color = up_color if hama_color == "green" else down_color
    trend_text = "多头" if hama_color == "green" else "空头" if hama_color == "red" else "横盘"

    W, H = 600, 350
    pad_l, pad_r, pad_t, pad_b = 50, 15, 35, 25

    chart_left = pad_l
    chart_right = W - pad_r
    chart_top = pad_t
    chart_bottom = H - pad_b
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top

    # 布林带区间
    bb_high = bb_upper if bb_upper > 0 else price * 1.1
    bb_low = bb_lower if bb_lower > 0 else price * 0.9
    bb_range = bb_high - bb_low if bb_high > bb_low else price * 0.2
    bb_mid = (bb_high + bb_low) / 2

    def y_pos(v):
        return chart_top + (1 - (v - bb_low) / bb_range) * chart_h

    def x_pos(i, total=5):
        return chart_left + (i / max(total - 1, 1)) * chart_w

    # 颜色标记
    color_tag = f'<rect x="{chart_right - 55}" y="{chart_top + 5}" width="50" height="18" rx="3" fill="{hama_line_color}"/>' \
                f'<text x="{chart_right - 30}" y="{chart_top + 18}" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">{trend_text}</text>'

    # 涨跌标记
    change_color = up_color if change_pct >= 0 else down_color
    change_sign = "+" if change_pct >= 0 else ""

    # 信号
    signal_parts = []
    if cross_up:
        signal_parts.append(f'<text x="{chart_left}" y="{chart_top + 50}" fill="{up_color}" font-size="12">▲ 金叉信号</text>')
    if cross_down:
        signal_parts.append(f'<text x="{chart_left + 100}" y="{chart_top + 50}" fill="{down_color}" font-size="12">▼ 死叉信号</text>')

    # 布林带背景
    bb_area = ""
    if bb_upper > 0 and bb_lower > 0:
        bb_area = f'<rect x="{chart_left}" y="{y_pos(bb_upper)}" width="{chart_w}" height="{y_pos(bb_lower) - y_pos(bb_upper)}" fill="{up_color}08" rx="2"/>'

    # MA 线
    ma_y = y_pos(hama_ma)
    ma_line = f'<line x1="{chart_left}" y1="{ma_y}" x2="{chart_right}" y2="{ma_y}" stroke="{ma_color}" stroke-width="1.5" stroke-dasharray="6,3"/>' \
              f'<text x="{chart_right - 5}" y="{ma_y - 3}" text-anchor="end" fill="{ma_color}" font-size="10">MA {hama_ma:.2f}</text>'

    # 布林线
    bb_lines = ""
    if bb_upper > 0:
        uy = y_pos(bb_upper)
        bb_lines += f'<line x1="{chart_left}" y1="{uy}" x2="{chart_right}" y2="{uy}" stroke="{up_color}" stroke-width="0.8" opacity="0.5"/>' \
                    f'<text x="{chart_right - 5}" y="{uy - 3}" text-anchor="end" fill="{up_color}" font-size="9">上 {bb_upper:.2f}</text>'
    ly = y_pos(bb_lower)
    bb_lines += f'<line x1="{chart_left}" y1="{ly}" x2="{chart_right}" y2="{ly}" stroke="{down_color}" stroke-width="0.8" opacity="0.5"/>' \
                f'<text x="{chart_right - 5}" y="{ly - 3}" text-anchor="end" fill="{down_color}" font-size="9">下 {bb_lower:.2f}</text>'
    by = y_pos(bb_basis)
    bb_lines += f'<line x1="{chart_left}" y1="{by}" x2="{chart_right}" y2="{by}" stroke="#888" stroke-width="0.5" opacity="0.4"/>' \
                f'<text x="{chart_right - 5}" y="{by - 3}" text-anchor="end" fill="#888" font-size="9">中 {bb_basis:.2f}</text>'

    # 当前价格线
    price_y = y_pos(price)
    price_line = f'<line x1="{chart_left}" y1="{price_y}" x2="{chart_right}" y2="{price_y}" stroke="#fff" stroke-width="1" opacity="0.6"/>' \
                 f'<text x="{chart_right - 5}" y="{price_y - 3}" text-anchor="end" fill="#fff" font-size="10" font-weight="bold">当前 {price:.2f}</text>'

    # HAMA Close 线
    hama_close_y = y_pos(hama_close)
    hama_line_svg = f'<line x1="{chart_left}" y1="{hama_close_y}" x2="{chart_right}" y2="{hama_close_y}" stroke="{hama_line_color}" stroke-width="2" stroke-dasharray="4,2"/>' \
                    f'<text x="{chart_left + 5}" y="{hama_close_y - 3}" fill="{hama_line_color}" font-size="10">HAMA {hama_close:.2f}</text>'

    # 底部信息
    info = f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 周期: {timeframe} | 数据源: TradingView WebSocket'

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg)" rx="6"/>
  <text x="{chart_left}" y="22" fill="#fff" font-size="15" font-weight="bold">{symbol}</text>
  <text x="{chart_left + 180}" y="22" fill="{change_color}" font-size="13">{change_sign}{change_pct:.2f}%</text>
  <text x="{chart_left}" y="22" dy="18" fill="#aaa" font-size="11">{price:.2f} USDT</text>
  {color_tag}
  {bb_area}
  {ma_line}
  {bb_lines}
  {price_line}
  {hama_line_svg}
  {''.join(signal_parts)}
  <text x="{W/2}" y="{H - 5}" text-anchor="middle" fill="#555" font-size="9">{info}</text>
</svg>'''

    return base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
