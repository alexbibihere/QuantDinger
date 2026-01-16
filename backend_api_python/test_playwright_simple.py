#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试 Playwright 代理连接
"""
import os
from playwright.sync_api import sync_playwright

def test_proxy_connection():
    """测试代理连接"""
    proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')

    print('='*60)
    print('测试 Playwright 代理连接')
    print('='*60)
    print(f'代理配置: {proxy_url}')

    proxy_config = {'server': proxy_url} if proxy_url else None

    with sync_playwright() as p:
        print('启动浏览器...')
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        print('创建页面...')
        page = browser.new_page()

        # 访问 Google 测试代理
        print('访问 Google...')
        try:
            page.goto('https://www.google.com', timeout=30000)
            title = page.title()
            print(f'✅ 成功访问 Google，标题: {title}')
        except Exception as e:
            print(f'❌ 访问 Google 失败: {e}')

        # 访问 TradingView
        print('\n访问 TradingView...')
        try:
            page.goto('https://www.tradingview.com', timeout=30000)
            title = page.title()
            print(f'✅ 成功访问 TradingView，标题: {title}')
            print(f'页面内容长度: {len(page.content())} 字符')
        except Exception as e:
            print(f'❌ 访问 TradingView 失败: {e}')

        browser.close()
        print('\n✅ 测试完成')

if __name__ == '__main__':
    test_proxy_connection()
