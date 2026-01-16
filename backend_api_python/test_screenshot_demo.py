#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Selenium 截图功能
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.services.screenshot_helper import capture_screenshot, ScreenshotHelper
import logging

logging.basicConfig(level=logging.INFO)

print('=' * 70)
print(' ' * 20 + 'Selenium 截图功能测试')
print('=' * 70)

# 测试 1: 基本截图 - TradingView Widget
print('\n【测试 1】TradingView Widget 截图')
print('-' * 70)

widget_url = 'https://s.tradingview.com/widgetembed/'
params = '?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1&symboledit=1&saveimage=0&toolbarbg=f1f3f6&studies=%5B%5D&theme=Light&style=1&timezone=Etc%2FUTC'

result1 = capture_screenshot(
    url=widget_url + params,
    output_path='../screenshot/test_btcusdt_widget.png',
    wait_time=10,
    proxy_port=7890
)

if result1['success']:
    print(f'✅ 成功!')
    print(f'   文件: {result1["output_path"]}')
    print(f'   大小: {result1["file_size"] / 1024:.1f} KB')
    print(f'   耗时: {result1["elapsed"]:.1f} 秒')
else:
    print(f'❌ 失败: {result1.get("error", "未知错误")}')

# 测试 2: 使用 Cookie 访问私有图表
print('\n【测试 2】使用 Cookie 访问私有图表')
print('-' * 70)

try:
    import json
    import os

    if os.path.exists('./tradingview_cookies.json'):
        with open('./tradingview_cookies.json', 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)

        helper = ScreenshotHelper(proxy_port=7890)
        result2 = helper.capture_with_cookie(
            url='https://cn.tradingview.com/chart/U1FY2qxO/',
            output_path='../screenshot/test_private_chart.png',
            cookie_string=cookie_data['cookies'],
            wait_time=15
        )

        if result2['success']:
            print(f'✅ 成功!')
            print(f'   文件: {result2["output_path"]}')
            print(f'   大小: {result2["file_size"] / 1024:.1f} KB')
            print(f'   耗时: {result2["elapsed"]:.1f} 秒')
        else:
            print(f'❌ 失败: {result2.get("error", "未知错误")}')
    else:
        print('⚠️  Cookie 文件不存在')

except Exception as e:
    print(f'❌ 错误: {e}')

# 测试 3: 批量截图多个币种
print('\n【测试 3】批量截图多个币种')
print('-' * 70)

symbols = ['ETHUSDT', 'SOLUSDT', 'BNBUSDT']
success_count = 0

for symbol in symbols:
    params = f'?symbol=BINANCE%3A{symbol}&interval=15&hidesidetoolbar=1'
    result = capture_screenshot(
        url=widget_url + params,
        output_path=f'../screenshot/test_{symbol.lower()}_15m.png',
        wait_time=8,
        proxy_port=7890
    )

    if result['success']:
        success_count += 1
        print(f'  ✅ {symbol}: {result["file_size"] / 1024:.1f} KB')
    else:
        print(f'  ❌ {symbol}: 失败')

print(f'\n批量截图完成: {success_count}/{len(symbols)} 成功')

# 总结
print('\n' + '=' * 70)
print('测试总结')
print('=' * 70)

tests = [
    ('TradingView Widget', result1['success']),
    ('私有图表 (Cookie)', result2.get('success', False) if 'result2' in locals() else False),
    ('批量截图', success_count == len(symbols))
]

for name, success in tests:
    status = '✅ 通过' if success else '❌ 失败'
    print(f'{name}: {status}')

passed = sum(1 for _, s in tests if s)
total = len(tests)

print(f'\n通过率: {passed}/{total} ({passed/total*100:.0f}%)')

if passed == total:
    print('\n🎉 所有测试通过! Selenium 截图功能正常!')
else:
    print('\n⚠️  部分测试失败,请检查网络和代理配置')

print('=' * 70)
