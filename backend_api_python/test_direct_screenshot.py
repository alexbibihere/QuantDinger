#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接截图 TradingView 链接并进行 OCR 识别
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR
import os
import time

print('=' * 70)
print(' ' * 15 + 'TradingView 直接截图 + OCR 识别')
print('=' * 70)

# 尝试使用 Selenium (如果可用)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    SELENIUM_AVAILABLE = True
    print('✅ Selenium 可用')
except ImportError:
    SELENIUM_AVAILABLE = False
    print('❌ Selenium 未安装')

tv_url = 'https://cn.tradingview.com/chart/U1FY2qxO/'
print(f'\n目标页面: {tv_url}')

if SELENIUM_AVAILABLE:
    # 配置 Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    print('\n启动浏览器...')
    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f'访问: {tv_url}')
        driver.get(tv_url)

        # 等待页面加载
        print('等待页面加载 (15秒)...')
        time.sleep(15)

        # 截图
        screenshot_path = '../screenshot/TV_Direct_Screenshot.png'
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

        driver.save_screenshot(screenshot_path)
        file_size = os.path.getsize(screenshot_path) / 1024

        print(f'\n✅ 截图成功!')
        print(f'   保存路径: {screenshot_path}')
        print(f'   文件大小: {file_size:.1f} KB')

        driver.quit()

        # 开始 OCR 识别
        print('\n' + '=' * 70)
        print('开始 OCR 识别')
        print('=' * 70 + '\n')

        print('初始化 PaddleOCR (英文 + 中文)...')
        ocr = PaddleOCR(lang='ch')  # 中英文混合
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
                print('识别结果 (前80个):')
                print('=' * 70 + '\n')

                for i, text in enumerate(texts[:80], 1):
                    print(f'{i:2d}. {text}')

                if len(texts) > 80:
                    print(f'\n... 还有 {len(texts) - 80} 个文本块')

                # 完整文本
                full_text = ' '.join(texts)
                print(f'\n完整文本 (前800字符):')
                print('-' * 70)
                print(full_text[:800])

                # 提取价格和指标信息
                import re
                prices = re.findall(r'\d{1,6}[,.]?\d{0,2}', full_text)
                print(f'\n\n发现的价格数据: {prices[:30]}')

                # 查找指标信息
                indicators = ['HAMA', 'MA', 'EMA', 'BB', 'MACD', 'RSI', 'Volume', 'Open', 'High', 'Low', 'Close']
                found_indicators = [text for text in texts if any(indicator in text.upper() for indicator in indicators)]
                if found_indicators:
                    print(f'\n指标相关信息:')
                    for item in found_indicators:
                        print(f'  - {item}')

            else:
                print('❌ 无法提取文本')
                if isinstance(ocr_result, dict):
                    print('所有键:', list(ocr_result.keys())[:20])

        else:
            print('❌ OCR 识别失败')

    except Exception as e:
        print(f'\n❌ 错误: {e}')
        import traceback
        traceback.print_exc()
        driver.quit()

else:
    print('\n❌ Selenium 未安装,无法截图')
    print('\n请安装 Selenium:')
    print('  pip install selenium')
    print('  # 并确保安装了 Chrome 浏览器')
    print('\n或者使用现有的截图进行测试')

print('\n' + '=' * 70)
print('✅ 完成')
print('=' * 70)
