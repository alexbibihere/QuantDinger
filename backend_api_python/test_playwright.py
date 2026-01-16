#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Playwright HAMA 提取功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tradingview_playwright import extract_hama

def test_default_chart():
    """测试默认图表"""
    print("\n" + "="*60)
    print("测试 1: 默认图表（不包含 HAMA 指标）")
    print("="*60)

    result = extract_hama(
        symbol="BTCUSDT",
        interval="15",
        headless=True
    )

    print(f"\n结果: {result}")

    if result:
        print(f"✅ 成功提取数据")
        print(f"  - 币种: {result.get('symbol')}")
        print(f"  - 价格: {result.get('price')}")
        print(f"  - HAMA 值: {result.get('hama_value')}")
        print(f"  - HAMA 颜色: {result.get('hama_color')}")
        print(f"  - 备注: {result.get('note', '无')}")
    else:
        print("❌ 提取失败")

def test_custom_chart():
    """测试自定义图表"""
    print("\n" + "="*60)
    print("测试 2: 自定义图表（包含 HAMA 指标）")
    print("="*60)

    chart_url = "https://www.tradingview.com/chart/jvR08dsB/"
    print(f"图表 URL: {chart_url}")

    result = extract_hama(
        symbol=None,
        interval="15",
        headless=True,  # Docker 容器内必须使用 headless=True
        chart_url=chart_url
    )

    print(f"\n结果: {result}")

    if result:
        print(f"✅ 成功提取数据")
        print(f"  - 币种: {result.get('symbol')}")
        print(f"  - 价格: {result.get('price')}")
        print(f"  - HAMA 值: {result.get('hama_value')}")
        print(f"  - HAMA 颜色: {result.get('hama_color')}")
        print(f"  - HAMA 趋势: {result.get('hama_trend')}")
        print(f"  - 备注: {result.get('note', '无')}")
    else:
        print("❌ 提取失败")

if __name__ == "__main__":
    print("\n开始测试 Playwright HAMA 提取功能...")

    # 测试 1: 默认图表
    test_default_chart()

    # 测试 2: 自定义图表
    test_custom_chart()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
