#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图使用示例
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.screenshot_helper import capture_screenshot, ScreenshotHelper
import logging

logging.basicConfig(level=logging.INFO)

print('=' * 70)
print('截图使用示例')
print('=' * 70)

# 示例 1: 快速截图
print('\n【示例 1】快速截图 TradingView Widget')
print('-' * 70)

result = capture_screenshot(
    url='https://s.tradingview.com/widgetembed/?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1',
    output_path='../screenshot/example_btcusdt.png',
    wait_time=10
)

if result['success']:
    print(f'✅ 成功!')
    print(f'   文件: {result["output_path"]}')
    print(f'   大小: {result["file_size"] / 1024:.1f} KB')
    print(f'   耗时: {result["elapsed"]:.1f} 秒')
else:
    print(f'❌ 失败: {result["error"]}')

# 示例 2: 使用代理截图
print('\n【示例 2】使用代理截图')
print('-' * 70)

result = capture_screenshot(
    url='https://s.tradingview.com/widgetembed/?symbol=BINANCE%3AETHUSDT&interval=15',
    output_path='../screenshot/example_ethusdt.png',
    wait_time=10,
    proxy_port=7890  # 使用您的代理端口
)

if result['success']:
    print(f'✅ 成功!')
    print(f'   文件: {result["output_path"]}')
    print(f'   大小: {result["file_size"] / 1024:.1f} KB')
else:
    print(f'❌ 失败: {result["error"]}')

# 示例 3: 使用 Cookie 访问私有图表
print('\n【示例 3】使用 Cookie 访问私有图表')
print('-' * 70)

try:
    import json
    import os

    if os.path.exists('./tradingview_cookies.json'):
        with open('./tradingview_cookies.json', 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)

        helper = ScreenshotHelper(proxy_port=7890)
        result = helper.capture_with_cookie(
            url='https://cn.tradingview.com/chart/U1FY2qxO/',
            output_path='../screenshot/example_private_chart.png',
            cookie_string=cookie_data['cookies'],
            wait_time=15
        )

        if result['success']:
            print(f'✅ 成功!')
            print(f'   文件: {result["output_path"]}')
            print(f'   大小: {result["file_size"] / 1024:.1f} KB')
        else:
            print(f'❌ 失败: {result["error"]}')
    else:
        print('⚠️  Cookie 文件不存在: ./tradingview_cookies.json')

except Exception as e:
    print(f'❌ 错误: {e}')

print('\n' + '=' * 70)
print('✅ 所有示例完成!')
print('=' * 70)
