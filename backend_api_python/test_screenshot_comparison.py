#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图方案对比测试
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
import os

print('=' * 70)
print(' ' * 20 + '截图方案对比测试')
print('=' * 70)

# 测试 URL
test_url = 'https://s.tradingview.com/widgetembed/'
test_params = '?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1'
full_url = test_url + test_params

print(f'\n测试 URL: {full_url}\n')

# 创建输出目录
output_dir = '../screenshot/comparison'
os.makedirs(output_dir, exist_ok=True)

results = []

# 方案 1: Selenium (已安装)
print('=' * 70)
print('方案 1: Selenium')
print('=' * 70)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    start = time.time()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get(full_url)
    time.sleep(10)

    output_path = os.path.join(output_dir, 'selenium_chart.png')
    driver.save_screenshot(output_path)
    driver.quit()

    elapsed = time.time() - start
    file_size = os.path.getsize(output_path)

    results.append({
        'name': 'Selenium',
        'success': True,
        'time': elapsed,
        'size': file_size,
        'path': output_path
    })

    print(f'✅ 成功')
    print(f'   耗时: {elapsed:.2f} 秒')
    print(f'   大小: {file_size / 1024:.1f} KB')
    print(f'   路径: {output_path}\n')

except Exception as e:
    results.append({'name': 'Selenium', 'success': False, 'error': str(e)})
    print(f'❌ 失败: {e}\n')

# 方案 2: Playwright
print('=' * 70)
print('方案 2: Playwright')
print('=' * 70)

try:
    from playwright.sync_api import sync_playwright

    start = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.goto(full_url, wait_until='networkidle')
        time.sleep(10)

        output_path = os.path.join(output_dir, 'playwright_chart.png')
        page.screenshot(path=output_path)
        browser.close()

    elapsed = time.time() - start
    file_size = os.path.getsize(output_path)

    results.append({
        'name': 'Playwright',
        'success': True,
        'time': elapsed,
        'size': file_size,
        'path': output_path
    })

    print(f'✅ 成功')
    print(f'   耗时: {elapsed:.2f} 秒')
    print(f'   大小: {file_size / 1024:.1f} KB')
    print(f'   路径: {output_path}\n')

except ImportError:
    results.append({'name': 'Playwright', 'success': False, 'error': '未安装'})
    print('❌ 未安装')
    print('   安装: pip install playwright && playwright install chromium\n')

except Exception as e:
    results.append({'name': 'Playwright', 'success': False, 'error': str(e)})
    print(f'❌ 失败: {e}\n')

# 方案 3: Pyppeteer
print('=' * 70)
print('方案 3: Pyppeteer')
print('=' * 70)

try:
    import pyppeteer
    import asyncio

    async def pyppeteer_test():
        browser = await pyppeteer.launch(headless=True)
        page = await browser.newPage()
        await page.setViewport({'width': 1920, 'height': 1080})
        await page.goto(full_url)
        await asyncio.sleep(10)

        output_path = os.path.join(output_dir, 'pyppeteer_chart.png')
        await page.screenshot({'path': output_path})
        await browser.close()

        return output_path, time.time() - start

    start = time.time()
    output_path, elapsed = asyncio.get_event_loop().run_until_complete(pyppeteer_test())
    file_size = os.path.getsize(output_path)

    results.append({
        'name': 'Pyppeteer',
        'success': True,
        'time': elapsed,
        'size': file_size,
        'path': output_path
    })

    print(f'✅ 成功')
    print(f'   耗时: {elapsed:.2f} 秒')
    print(f'   大小: {file_size / 1024:.1f} KB')
    print(f'   路径: {output_path}\n')

except ImportError:
    results.append({'name': 'Pyppeteer', 'success': False, 'error': '未安装'})
    print('❌ 未安装')
    print('   安装: pip install pyppeteer\n')

except Exception as e:
    results.append({'name': 'Pyppeteer', 'success': False, 'error': str(e)})
    print(f'❌ 失败: {e}\n')

# 总结
print('=' * 70)
print('对比结果')
print('=' * 70)

print(f'\n{'方案':<15} {'状态':<8} {'耗时(秒)':<12} {'文件大小(KB)':<15}')
print('-' * 70)

for r in results:
    status = '✅ 成功' if r['success'] else '❌ 失败'
    time_str = f'{r.get("time", 0):.2f}' if r['success'] else 'N/A'
    size_str = f'{r.get("size", 0) / 1024:.1f}' if r['success'] else 'N/A'

    print(f'{r["name"]:<15} {status:<8} {time_str:<12} {size_str:<15}')

    if not r['success'] and 'error' in r:
        print(f'  错误: {r["error"]}')

print('\n' + '=' * 70)
print('推荐方案:')
print('=' * 70)

if any(r['success'] for r in results):
    successful = [r for r in results if r['success']]
    fastest = min(successful, key=lambda x: x['time'])

    print(f'\n✅ 最快: {fastest["name"]} ({fastest["time"]:.2f} 秒)')
    print(f'   适合对速度要求高的场景\n')

    print('其他建议:')
    print('1. Playwright: 最现代,API 简洁,推荐新项目使用')
    print('2. Selenium: 最成熟,社区支持好,适合复杂场景')
    print('3. Pyppeteer: 轻量级,适合简单需求')
else:
    print('\n⚠️  所有方案都失败了,请检查依赖安装')

print('\n' + '=' * 70)
