#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 TradingView Widget 截图并 OCR 识别
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from paddleocr import PaddleOCR
import os
import time
import re

print('=' * 70)
print(' ' * 15 + 'TradingView Widget 截图 + OCR 识别')
print('=' * 70)

# TradingView Widget Embed URL (不需要登录)
widget_url = 'https://s.tradingview.com/widgetembed/'

# 参数
symbol = 'BTCUSDT'
interval = '15'
params = f'?frameElementId=tradingview_76d87&symbol=BINANCE%3A{symbol}&interval={interval}&hidesidetoolbar=1&symboledit=1&saveimage=0&toolbarbg=f1f3f6&studies=%5B%5D&theme=Light&style=1&timezone=Etc%2FUTC'

full_url = widget_url + params

print(f'\nWidget URL: {full_url}')
print(f'币种: {symbol}')
print(f'周期: {interval} 分钟\n')

# 启动浏览器
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')

print('启动浏览器...')
driver = webdriver.Chrome(options=chrome_options)

try:
    print(f'访问 Widget URL...')
    driver.get(full_url)

    # 等待图表加载
    print('等待图表加载 (10秒)...')
    time.sleep(10)

    # 截图
    screenshot_path = '../screenshot/TV_Widget_BTCUSDT_15m.png'
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

    driver.save_screenshot(screenshot_path)
    file_size = os.path.getsize(screenshot_path) / 1024

    print(f'\n✅ 截图成功!')
    print(f'   保存路径: {screenshot_path}')
    print(f'   文件大小: {file_size:.1f} KB')

    driver.quit()

    # OCR 识别
    print('\n' + '=' * 70)
    print('开始 OCR 识别')
    print('=' * 70 + '\n')

    print('初始化 PaddleOCR (英文模型)...')
    ocr = PaddleOCR(lang='en')
    print('✅ 就绪\n')

    print('识别图表...\n')
    result = ocr.ocr(screenshot_path)

    if result and len(result) > 0:
        ocr_result = result[0]

        # 获取文本
        texts = []
        if hasattr(ocr_result, 'rec_texts'):
            texts = ocr_result.rec_texts
        elif isinstance(ocr_result, dict):
            for key, value in ocr_result.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
                    texts = value
                    break

        if texts:
            print(f'✅ 识别到 {len(texts)} 个文本块\n')
            print('=' * 70)
            print('识别结果 (前100个):')
            print('=' * 70 + '\n')

            for i, text in enumerate(texts[:100], 1):
                print(f'{i:2d}. {text}')

            if len(texts) > 100:
                print(f'\n... 还有 {len(texts) - 100} 个文本块')

            # 完整文本
            full_text = ' '.join(texts)
            print(f'\n\n完整文本 (前1000字符):')
            print('-' * 70)
            print(full_text[:1000])

            # 提取价格信息
            prices = re.findall(r'\d{1,6}[,.]?\d{0,2}', full_text)
            print(f'\n\n发现的价格数据: {prices[:40]}')

            # 查找关键信息
            keywords = ['BTCUSDT', 'BINANCE', 'Open', 'High', 'Low', 'Close', 'Volume', 'MA', 'EMA', 'BB', 'HAMA']
            found = [text for text in texts if any(keyword.upper() in text.upper() for keyword in keywords)]
            if found:
                print(f'\n关键信息:')
                for item in found:
                    print(f'  - {item}')

        else:
            print('❌ 无法提取文本')
    else:
        print('❌ OCR 识别失败')

except Exception as e:
    print(f'\n❌ 错误: {e}')
    import traceback
    traceback.print_exc()
    driver.quit()

print('\n' + '=' * 70)
print('✅ 完成')
print('=' * 70)
