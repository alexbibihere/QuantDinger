#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接从 TradingView 页面提取 HAMA 指标数据

方案：
1. 连接到 TradingView 页面
2. 监听网络请求，找到图表数据 API
3. 直接调用 API 获取指标数据
"""

import sys
import os
import json

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def print_separator(title=""):
    """打印分隔线"""
    width = 80
    if title:
        print(f"\n{'=' * width}")
        print(f"  {title}")
        print(f"{'=' * width}\n")
    else:
        print(f"{'=' * width}")


def inspect_tradingview_requests():
    """
    监听 TradingView 页面的网络请求

    目标：找到获取图表数据和指标的 API
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright 未安装")
        print("   安装: pip install playwright")
        return

    print_separator("🔍 TradingView API 请求分析工具")

    print("💡 使用说明:")
    print("   1. 此工具会打开你的 TradingView 页面")
    print("   2. 监听所有网络请求")
    print("   3. 找到获取图表数据的 API")
    print("   4. 尝试直接调用 API 获取数据")

    chart_url = input("\n请输入你的 TradingView 图表 URL: ").strip()

    if not chart_url:
        chart_url = "https://cn.tradingview.com/chart/U1FY2qxO/"
        print(f"使用默认 URL: {chart_url}")

    print(f"\n🌐 正在打开: {chart_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 有头模式，可以看到浏览器

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        # 添加 Cookie（如果需要）
        print("\n🍪 是否添加 TradingView Cookie?")
        add_cookie = input("输入 y 添加，其他键跳过: ").strip().lower() == 'y'

        if add_cookie:
            print("\n请粘贴你的 Cookie 字符串 (从 CLAUDE.md 复制):")
            cookie_string = input("Cookie: ").strip()

            # 解析 Cookie
            cookies = []
            for cookie_pair in cookie_string.split(';'):
                cookie_pair = cookie_pair.strip()
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.tradingview.com',
                        'path': '/',
                    })

            context.add_cookies(cookies)
            print(f"✅ 已添加 {len(cookies)} 个 Cookie")

        page = context.new_page()

        # 监听网络请求
        requests_log = []

        def log_request(request):
            """记录请求"""
            url = request.url
            method = request.method
            resource_type = request.resource_type

            # 只记录 API 请求
            if resource_type in ['xhr', 'fetch']:
                requests_log.append({
                    'url': url,
                    'method': method,
                    'type': resource_type,
                    'headers': request.headers
                })

                print(f"📡 [{method}] {resource_type.upper()}: {url[:100]}")

        page.on('request', log_request)

        # 监听响应
        responses_log = []

        def log_response(response):
            """记录响应"""
            url = response.url
            status = response.status
            resource_type = response.resource_type

            # 只记录 API 响应
            if resource_type in ['xhr', 'fetch']:
                print(f"📥 [{status}] {resource_type.upper()}: {url[:100]}")

                # 尝试获取响应内容
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        json_data = response.json()
                        responses_log.append({
                            'url': url,
                            'status': status,
                            'data': json_data
                        })

                        # 保存重要的响应
                        if 'history' in url or 'symbol' in url or 'chart' in url:
                            filename = f"api_response_{len(responses_log)}.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            print(f"   💾 已保存: {filename}")
                except:
                    pass

        page.on('response', log_response)

        # 访问页面
        print("\n⏳ 正在加载页面...")
        page.goto(chart_url, wait_until='networkidle', timeout=60000)

        print("\n✅ 页面加载完成!")
        print("\n💡 请等待 30 秒，让页面完全加载并发送所有请求...")

        import time
        time.sleep(30)

        print(f"\n📊 捕获到 {len(requests_log)} 个 API 请求")
        print(f"📊 捕获到 {len(responses_log)} 个 API 响应")

        # 分析请求
        print_separator("🔍 关键 API 分析")

        # 查找可能的图表数据 API
        chart_apis = []

        for req in requests_log:
            url = req['url']

            # TradingView 图表数据 API 的特征
            if any(keyword in url for keyword in [
                'history',
                'symbol',
                'quotes',
                'timescale',
                'chart',
                'token',
                'session'
            ]):
                chart_apis.append(req)

        if chart_apis:
            print(f"\n✅ 找到 {len(chart_apis)} 个可能的关键 API:\n")

            for i, api in enumerate(chart_apis[:10], 1):  # 只显示前 10 个
                print(f"[{i}] {api['method']} {api['url']]}")

                # 显示关键 headers
                headers = api['headers']
                if 'Authorization' in headers:
                    print(f"    🔑 Authorization: {headers['Authorization']}")
                if 'Cookie' in headers:
                    print(f"    🍪 Cookie: {headers['Cookie'][:50]}...")

        # 查找包含指标数据的响应
        print_separator("📊 可能包含指标数据的响应")

        for resp in responses_log:
            url = resp['url']
            data = resp['data']

            # 查找包含数值数据的响应
            if isinstance(data, dict):
                # 查找包含价格、指标等关键字的响应
                data_str = json.dumps(data, ensure_ascii=False)

                if any(keyword in data_str.lower() for keyword in [
                    'hama',
                    'ema',
                    'sma',
                    'bb',
                    'bollinger',
                    'price',
                    'close',
                    'volume'
                ]):
                    print(f"\n✅ 可能包含指标数据:")
                    print(f"   URL: {url[:100]}")
                    print(f"   数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")

                    # 保存完整响应
                    filename = f"indicator_data_{len(responses_log)}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"   💾 已保存: {filename}")

        # 保存所有日志
        with open('tradingview_api_log.json', 'w', encoding='utf-8') as f:
            json.dump({
                'requests': requests_log,
                'responses': [{'url': r['url'], 'status': r['status']} for r in responses_log]
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 所有日志已保存: tradingview_api_log.json")

        print("\n" + "=" * 80)
        print("💡 提示:")
        print("   1. 查看生成的 JSON 文件，找到包含指标数据的 API")
        print("   2. 分析 API 的请求参数和响应格式")
        print("   3. 尝试直接调用该 API 获取数据")
        print("=" * 80)

        input("\n按 Enter 键关闭浏览器...")
        browser.close()


def try_direct_api_call():
    """
    尝试直接调用 TradingView API

    基于已知的 TradingView API 端点
    """
    print_separator("🎯 直接调用 TradingView API")

    print("TradingView 已知的 API 端点:\n")

    apis = [
        {
            'name': 'Token 生成',
            'url': 'https://www.tradingview.com/charting_library/client/',
            'description': '生成认证 token'
        },
        {
            'name': '历史数据',
            'url': 'https://data.tradingview.com/chart/',
            'description': '获取历史 K 线数据'
        },
        {
            'name': 'WebSocket',
            'url': 'wss://data.tradingview.com/socket.io/websocket',
            'description': '实时数据推送'
        },
        {
            'name': '符号搜索',
            'url': 'https://symbol-search.tradingview.com/',
            'description': '搜索交易品种'
        }
    ]

    for i, api in enumerate(apis, 1):
        print(f"[{i}] {api['name']}")
        print(f"    URL: {api['url']}")
        print(f"    描述: {api['description']}")
        print()

    print("=" * 80)
    print("⚠️  注意:")
    print("   TradingView 的 API 大多需要:")
    print("   1. 认证 Token (从页面获取)")
    print("   2. Session ID (登录后获得)")
    print("   3. Cookie (身份验证)")
    print("   4. 特定的请求格式")
    print()
    print("   最简单的方法:")
    print("   1. 在浏览器中打开开发者工具 (F12)")
    print("   2. 切换到 Network 标签")
    print("   3. 刷新 TradingView 页面")
    print("   4. 找到返回图表数据的请求")
    print("   5. 右键 -> Copy as cURL")
    print("   6. 转换为 Python 代码")
    print("=" * 80)


def main():
    """主函数"""
    print_separator("🔍 TradingView API 探测工具")

    print("选项:")
    print("   1. 监听页面网络请求（找到 API）")
    print("   2. 查看已知 API 端点")

    choice = input("\n请选择 (1-2): ").strip()

    if choice == '1':
        inspect_tradingview_requests()
    elif choice == '2':
        try_direct_api_call()
    else:
        print("❌ 无效选择")


if __name__ == '__main__':
    main()
