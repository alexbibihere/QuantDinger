#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Cookie 截图 TradingView 私有图表
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from paddleocr import PaddleOCR
import time
import re

print('=' * 70)
print(' ' * 15 + '使用 Cookie 截图 TradingView')
print('=' * 70)

# TradingView 链接
tv_url = 'https://cn.tradingview.com/chart/U1FY2qxO/'

# Cookie 字符串
cookie_string = 'cookiePrivacyPreferenceBannerProduction=notApplicable; _ga=GA1.1.1866852168.1760819691; cookiesSettings={"analytics":true,"advertising":true}; device_t=OThMTjowLDRibHJCUTow.albLE7WBs_dZ5drzD6kWjXsL7iQmttVDo3lvzVFUq90; sessionid=ki9qy7vvfk3h19qp0qd64exhonzapfrd; sessionid_sign=v3:cBmutdL9L5e4Y27C8skCR/dCbqBKOzvhheZiwjOQqOc=; tv_ecuid=2f707cb5-e0fd-457d-a12e-af14f34bee79; _sp_ses.cf1a=*; __gads=ID=14f07cdc5b671962:T=1767987209:RT=1768558213:S=ALNI_MYMXuccOjaGeS7V3qeAdjzkcw9H7w; __gpi=UID=000011e07ded39b9:T=1767987209:RT=1768558213:S=ALNI_MZvLD6OWj01o8fzaR8AwA3B6hMakg; __eoi=ID=94061d16f7692d1d:T=1767987209:RT=1768558213:S=AA-AfjbJz4kBsqzI2qydEXWmmZ2m; _ga_YVVRYGL0E0=GS2.1.s1768557666$o30$g1$t1768558247$j52$l0$h0; _sp_id.cf1a=4ae0f691-127b-49ab-b10b-1895c52c78ba.1760819689.23.1768558247.1768492785.57704e70-4daf-45c8-ba9f-c89c759dc1a6.75d8a48e-70b5-44e3-9db7-5a0015436df6.83ba927b-9d86-4c20-8fcb-9410ff3d135f.1768557665292.4'

print(f'\n目标页面: {tv_url}')
print('已提供 Cookie,将尝试访问私有图表\n')

# 解析 Cookie
def parse_cookies(cookie_string, domain='cn.tradingview.com'):
    """解析 Cookie 字符串"""
    cookies = []
    for item in cookie_string.split('; '):
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': domain,
                'path': '/'
            })
    return cookies

cookies = parse_cookies(cookie_string)
print(f'解析到 {len(cookies)} 个 Cookie\n')

# 配置 Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=2560,1440')  # 2K 分辨率

print('启动浏览器...')
driver = webdriver.Chrome(options=chrome_options)

try:
    # 先访问主页以设置域
    print('访问 TradingView 主页...')
    driver.get('https://cn.tradingview.com/')
    time.sleep(2)

    # 添加 Cookie
    print('添加 Cookie...')
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f'  警告: 无法添加 Cookie {cookie["name"]}: {e}')

    print('✅ Cookie 已添加\n')

    # 访问目标页面
    print(f'访问目标图表: {tv_url}')
    driver.get(tv_url)

    # 等待页面加载
    print('等待页面加载 (20秒)...')
    time.sleep(20)

    # 截图
    screenshot_path = '../screenshot/TV_With_Cookie.png'
    driver.save_screenshot(screenshot_path)
    file_size = driver.get_screenshot_as_png().__sizeof__() / 1024

    print(f'\n✅ 截图成功!')
    print(f'   保存路径: {screenshot_path}')
    print(f'   文件大小: {file_size:.1f} KB\n')

    driver.quit()

    # 开始 OCR 识别
    print('=' * 70)
    print('开始 OCR 识别')
    print('=' * 70 + '\n')

    print('初始化 PaddleOCR (中英文混合)...')
    ocr = PaddleOCR(lang='ch')
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

            # 提取关键信息
            print(f'\n\n关键信息提取:')
            print('-' * 70)

            # 价格数据
            prices = re.findall(r'\d{1,6}[,.]?\d{0,2}', full_text)
            print(f'价格数据: {prices[:30]}')

            # 币种
            crypto_symbols = re.findall(r'[A-Z]{3,6}USDT', full_text)
            if crypto_symbols:
                print(f'币种: {set(crypto_symbols)}')

            # 指标
            indicators = ['HAMA', 'MA', 'EMA', 'BB', 'MACD', 'RSI', 'Volume', 'SMA']
            found = [text for text in texts if any(indicator in text.upper() for indicator in indicators)]
            if found:
                print(f'\n指标相关信息:')
                for item in found[:20]:
                    print(f'  - {item}')

            # 查找数字和百分比
            percentages = re.findall(r'\d+\.?\d*%', full_text)
            if percentages:
                print(f'\n百分比数据: {percentages[:10]}')

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

print('\n' + '=' * 70)
print('✅ 完成')
print('=' * 70)
