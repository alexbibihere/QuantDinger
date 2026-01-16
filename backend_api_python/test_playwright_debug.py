#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试 TradingView 图表内容提取
"""
import json
import os
import re
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

def load_cookies():
    """从配置文件加载 cookies"""
    cookie_file = '/app/tradingview_cookies.json'

    if not os.path.exists(cookie_file):
        return None, None

    with open(cookie_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config.get('cookies', []), config.get('chart_url')

def debug_chart_content():
    """调试图表内容"""
    print('='*60)
    print('调试 TradingView 图表内容')
    print('='*60)

    cookies, chart_url = load_cookies()
    proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY')

    print(f'图表 URL: {chart_url}')
    print(f'使用代理: {proxy_url}')

    proxy_config = {'server': proxy_url, 'bypass': 'localhost,127.0.0.1'} if proxy_url else None

    with sync_playwright() as p:
        print('\n启动浏览器...')
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy_config,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                f'--proxy-server={proxy_url}' if proxy_url else ''
            ]
        )

        context = browser.new_context()
        page = context.new_page()

        # 应用 stealth 模式
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(page)
        print('✅ Stealth 模式已启用')

        # 添加 cookies
        if cookies:
            context.add_cookies(cookies)
            print(f'✅ 已添加 {len(cookies)} 个 cookies')

        # 访问图表
        print(f'\n访问图表: {chart_url}')
        page.goto(chart_url, timeout=90000, wait_until='load')
        print('✅ 页面加载完成')

        # 等待图表渲染
        print('等待图表渲染...')
        page.wait_for_timeout(15000)

        # 尝试截图（保存到文件）
        screenshot_path = '/tmp/tradingview_chart_debug.png'
        page.screenshot(path=screenshot_path)
        print(f'✅ 截图已保存: {screenshot_path}')

        # 获取页面内容
        content = page.content()
        print(f'\n页面内容长度: {len(content)} 字符')

        # 查找图例相关内容
        print('\n查找图例元素...')
        try:
            # 查找所有包含 "legend" 的元素
            legends = page.query_selector_all('[class*="legend"]')
            print(f'找到 {len(legends)} 个图例元素')

            for i, legend in enumerate(legends[:10]):  # 只显示前 10 个
                text = legend.inner_text()
                if text and text.strip():
                    print(f'\n图例 {i+1}:')
                    print(f'  文本: {text[:200]}')  # 只显示前 200 个字符

                    # 检查是否包含 HAMA
                    if 'HAMA' in text:
                        print('  ⭐ 找到 HAMA 指标！')

                        # 尝试提取 HAMA 值
                        hama_match = re.search(r'HAMA.*?([\d,]+\.?\d*)', text)
                        if hama_match:
                            hama_value = hama_match.group(1).replace(',', '')
                            print(f'  HAMA 值: {hama_value}')

                        # 检查颜色
                        if 'green' in text.lower() or '▲' in text or '↑' in text:
                            print('  趋势: 上涨 (绿色)')
                        elif 'red' in text.lower() or '▼' in text or '↓' in text:
                            print('  趋势: 下跌 (红色)')

        except Exception as e:
            print(f'❌ 查找图例失败: {e}')

        browser.close()
        print('\n✅ 调试完成')

if __name__ == '__main__':
    debug_chart_content()
