#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速截图工具 - 使用 Selenium
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import json

def quick_screenshot(url, output_path, wait_time=10, width=1920, height=1080, headless=True):
    """
    快速截图

    Args:
        url: 目标 URL
        output_path: 输出路径
        wait_time: 等待时间(秒)
        width: 窗口宽度
        height: 窗口高度
        headless: 是否无头模式
    """
    # 配置 Chrome
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'--window-size={width},{height}')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # 如果有代理配置
    proxy_port = os.environ.get('PROXY_PORT')
    if proxy_port:
        chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{proxy_port}')
        print(f'使用代理: 127.0.0.1:{proxy_port}')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f'访问: {url}')
        driver.get(url)

        print(f'等待 {wait_time} 秒...')
        time.sleep(wait_time)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        # 截图
        driver.save_screenshot(output_path)
        file_size = os.path.getsize(output_path)

        print(f'✅ 截图成功!')
        print(f'   保存路径: {output_path}')
        print(f'   文件大小: {file_size / 1024:.1f} KB')

        return True

    except Exception as e:
        print(f'❌ 截图失败: {e}')
        return False

    finally:
        driver.quit()


def screenshot_with_cookies(url, output_path, cookie_file, wait_time=10):
    """
    使用 Cookie 截图

    Args:
        url: 目标 URL
        output_path: 输出路径
        cookie_file: Cookie JSON 文件路径
        wait_time: 等待时间
    """
    # 读取 Cookie
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie_data = json.load(f)

    cookie_string = cookie_data['cookies']

    # 配置 Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=2560,1440')

    # 代理配置
    proxy_port = os.environ.get('PROXY_PORT')
    if proxy_port:
        chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{proxy_port}')
        print(f'使用代理: 127.0.0.1:{proxy_port}')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 先访问主页以设置域
        print('访问 TradingView 主页...')
        driver.get('https://cn.tradingview.com/')
        time.sleep(2)

        # 解析并添加 Cookie
        print('添加 Cookie...')
        for item in cookie_string.split('; '):
            if '=' in item:
                name, value = item.split('=', 1)
                try:
                    driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.tradingview.com',
                        'path': '/'
                    })
                except:
                    pass

        # 访问目标页面
        print(f'访问目标页面: {url}')
        driver.get(url)

        print(f'等待 {wait_time} 秒...')
        time.sleep(wait_time)

        # 截图
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        driver.save_screenshot(output_path)
        file_size = os.path.getsize(output_path)

        print(f'✅ 截图成功!')
        print(f'   保存路径: {output_path}')
        print(f'   文件大小: {file_size / 1024:.1f} KB')

        return True

    except Exception as e:
        print(f'❌ 截图失败: {e}')
        return False

    finally:
        driver.quit()


if __name__ == '__main__':
    print('=' * 70)
    print(' ' * 20 + '快速截图工具')
    print('=' * 70)

    # 示例 1: 基本截图
    print('\n【示例 1】基本截图')
    print('-' * 70)

    quick_screenshot(
        url='https://www.binance.com',
        output_path='../screenshot/binance_home.png',
        wait_time=5
    )

    # 示例 2: TradingView Widget
    print('\n【示例 2】TradingView Widget')
    print('-' * 70)

    widget_url = 'https://s.tradingview.com/widgetembed/'
    params = '?symbol=BINANCE%3ABTCUSDT&interval=15&hidesidetoolbar=1'

    quick_screenshot(
        url=widget_url + params,
        output_path='../screenshot/btcusdt_widget.png',
        wait_time=10
    )

    # 示例 3: 使用 Cookie 访问私有图表
    print('\n【示例 3】使用 Cookie 访问私有图表')
    print('-' * 70)

    try:
        screenshot_with_cookies(
            url='https://cn.tradingview.com/chart/U1FY2qxO/',
            output_path='../screenshot/private_chart_with_cookie.png',
            cookie_file='./tradingview_cookies.json',
            wait_time=15
        )
    except Exception as e:
        print(f'Cookie 截图失败: {e}')
        print('提示: 需要配置代理或更新 Cookie')

    print('\n' + '=' * 70)
    print('✅ 完成!')
    print('=' * 70)
