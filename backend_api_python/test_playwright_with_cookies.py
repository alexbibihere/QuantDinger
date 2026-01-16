#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Cookies 测试 TradingView 自定义图表访问
"""
import json
import os
from app.services.tradingview_playwright import extract_hama

def load_cookies():
    """从配置文件加载 cookies"""
    cookie_file = '/app/tradingview_cookies.json'

    if not os.path.exists(cookie_file):
        print(f"❌ Cookie 文件不存在: {cookie_file}")
        return None, None

    with open(cookie_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    cookies = config.get('cookies', [])
    chart_url = config.get('chart_url', 'https://www.tradingview.com/chart/jvR08dsB/')

    print(f"✅ 加载了 {len(cookies)} 个 cookies")
    print(f"📊 图表 URL: {chart_url}")

    return cookies, chart_url

def test_with_cookies():
    """使用 cookies 测试图表访问"""
    print('='*60)
    print('测试使用 Cookies 访问 TradingView 自定义图表')
    print('='*60)

    cookies, chart_url = load_cookies()

    if not cookies:
        print("❌ 无法加载 cookies")
        return

    print("\n开始提取 HAMA 数据...")
    result = extract_hama(
        symbol=None,
        interval='15',
        headless=True,
        chart_url=chart_url,
        cookies=cookies
    )

    if result:
        print('\n' + '='*60)
        print('✅ 提取成功！')
        print('='*60)
        print(f"币种: {result.get('symbol')}")
        print(f"HAMA 值: {result.get('hama_value')}")
        print(f"HAMA 颜色: {result.get('hama_color')}")
        print(f"HAMA 趋势: {result.get('hama_trend')}")
        print(f"价格: {result.get('price')}")
        print(f"数据源: {result.get('source')}")
        if result.get('note'):
            print(f"注意: {result.get('note')}")
    else:
        print('\n❌ 提取失败')

if __name__ == '__main__':
    test_with_cookies()
