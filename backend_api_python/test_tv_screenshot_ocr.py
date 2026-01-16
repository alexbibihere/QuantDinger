#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
截图 TradingView 页面并进行 OCR 识别
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import requests
import os
import time

print('=' * 70)
print(' ' * 15 + 'TradingView 页面截图 + OCR 识别')
print('=' * 70)

# TradingView 图表 URL
tv_url = 'https://cn.tradingview.com/chart/U1FY2qxO/'

print(f'\n目标页面: {tv_url}')
print('正在准备截图...\n')

# 方法 1: 使用 TradingView Widget URL (推荐)
widget_url = 'https://s.tradingview.com/widgetembed/'
symbol = 'BTCUSDT'
interval = '15'

params = {
    'symbol': f'BINANCE:{symbol}',
    'interval': interval,
    'hidesidetoolbar': '1',
    'symboledit': '1',
    'saveimage': '0',
    'toolbarbg': 'f1f3f6',
    'studies': '[]',
    'theme': 'Light',
    'style': '1',
    'timezone': 'Etc/UTC',
}

print(f'使用 Widget URL: {widget_url}')
print(f'币种: {symbol}')
print(f'周期: {interval}分钟\n')

# 检查 Playwright 是否可用
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    print('✅ Playwright 可用')
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print('❌ Playwright 未安装')

if PLAYWRIGHT_AVAILABLE:
    print('\n开始截图...\n')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # 访问页面
        print(f'访问: {tv_url}')
        page.goto(tv_url, wait_until='networkidle', timeout=60000)

        # 等待页面加载
        print('等待页面加载...')
        time.sleep(5)

        # 截图
        screenshot_path = '../screenshot/TV_BTCUSDT_15m.png'
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

        page.screenshot(path=screenshot_path, full_page=False)
        print(f'✅ 截图已保存: {screenshot_path}')
        print(f'   文件大小: {os.path.getsize(screenshot_path) / 1024:.1f} KB\n')

        browser.close()

    # 开始 OCR 识别
    print('=' * 70)
    print('开始 OCR 识别')
    print('=' * 70 + '\n')

    print('初始化 PaddleOCR (英文模型)...')
    ocr = PaddleOCR(lang='en')
    print('✅ OCR 就绪\n')

    print('识别图表...\n')
    result = ocr.ocr(screenshot_path)

    if result and len(result) > 0:
        ocr_result = result[0]

        # 尝试多种方式获取文本
        texts = []

        # 方法1: 检查是否有 rec_texts 属性
        if hasattr(ocr_result, 'rec_texts'):
            texts = ocr_result.rec_texts
        # 方法2: 尝试作为字典访问
        elif isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
            texts = ocr_result['rec_texts']
        # 方法3: 遍历所有值
        else:
            for key, value in ocr_result.items() if isinstance(ocr_result, dict) else []:
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    texts = value
                    break

        if texts:
            print(f'✅ 识别到 {len(texts)} 个文本块\n')
            print('=' * 70)
            print('识别结果:')
            print('=' * 70 + '\n')

            # 显示前50个文本
            for i, text in enumerate(texts[:50], 1):
                print(f'{i:2d}. {text}')

            if len(texts) > 50:
                print(f'\n... 还有 {len(texts) - 50} 个文本块')

            # 完整文本
            full_text = ' '.join(texts)
            print(f'\n完整文本 (前500字符):')
            print(full_text[:500] + '...' if len(full_text) > 500 else full_text)

            # 提取价格信息
            import re
            prices = re.findall(r'\d{1,6}[,.]?\d{0,2}', full_text)
            if prices:
                print(f'\n发现的价格数据: {prices[:15]}')

            # 查找 HAMA 相关信息
            hama_keywords = ['HAMA', 'hama', 'Heiken', 'Ashi', 'Moving Average']
            hama_found = [text for text in texts if any(keyword.lower() in text.lower() for keyword in hama_keywords)]
            if hama_found:
                print(f'\nHAMA 指标相关信息:')
                for item in hama_found:
                    print(f'  - {item}')

        else:
            print('❌ 未找到文本数据')
            print('\nOCRResult 对象结构:')
            if isinstance(ocr_result, dict):
                print(f'键: {list(ocr_result.keys())[:10]}')
            else:
                print(f'类型: {type(ocr_result)}')
                print(f'属性: {[attr for attr in dir(ocr_result) if not attr.startswith("_")][:10]}')

    else:
        print('❌ OCR 识别失败')

else:
    print('\n❌ 无法截图, Playwright 未安装')
    print('请运行: pip install playwright && playwright install chromium')
    print('\n或使用现有的截图进行测试')

print('\n' + '=' * 70)
print('✅ 完成')
print('=' * 70)
