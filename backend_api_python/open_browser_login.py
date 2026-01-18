#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打开浏览器并自动登录 TradingView

功能：
1. 启动 Chrome 浏览器（带远程调试端口）
2. 导入 CLAUDE.md 中的 Cookie
3. 自动访问 TradingView 页面
"""

import sys
import os
import json
import time

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


def get_tradingview_cookies():
    """从 CLAUDE.md 读取 Cookie"""
    try:
        claude_md_path = os.path.join(os.path.dirname(__file__), '..', 'CLAUDE.md')

        if not os.path.exists(claude_md_path):
            print(f"❌ 找不到 CLAUDE.md: {claude_md_path}")
            return None

        with open(claude_md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Cookie 在第 11 行（索引 10）
        if len(lines) <= 10:
            print("❌ CLAUDE.md 格式错误（行数不足）")
            return None

        cookie_string = lines[10].strip()

        if not cookie_string.startswith('cookie'):
            print("❌ CLAUDE.md 第 11 行不是 Cookie")
            print(f"   内容: {cookie_string[:50]}...")
            return None

        # 提取 Cookie 值（去除 "cookiePrivacyPreferenceBannerProduction=" 前缀）
        cookie_value = cookie_string.split('=', 1)[1] if '=' in cookie_string else cookie_string

        # 解析 Cookie
        cookies = []
        for cookie_pair in cookie_value.split(';'):
            cookie_pair = cookie_pair.strip()
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.tradingview.com',
                    'path': '/',
                    'expires': -1,
                    'httpOnly': True,
                    'secure': True
                })

        print(f"✅ 成功解析 {len(cookies)} 个 Cookie")
        return cookies

    except Exception as e:
        print(f"❌ 读取 Cookie 失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def open_browser_with_cookies():
    """打开浏览器并导入 Cookie"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright 未安装")
        print("   安装: pip install playwright")
        return

    print_separator("🌐 打开浏览器并登录 TradingView")

    # 获取 Cookie
    cookies = get_tradingview_cookies()

    if not cookies:
        print("\n⚠️  无法获取 Cookie，将打开普通浏览器")

    print("\n🚀 启动浏览器...")

    with sync_playwright() as p:
        # 启动浏览器（非无头模式）
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--remote-debugging-port=9222',  # 启用远程调试
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 导入 Cookie
        if cookies:
            context.add_cookies(cookies)
            print("✅ Cookie 已导入")

        page = context.new_page()

        # 访问 TradingView
        chart_url = "https://cn.tradingview.com/chart/U1FY2qxO/"

        print(f"\n📗 访问: {chart_url}")
        print("⏳ 正在加载页面...")

        page.goto(chart_url, wait_until='networkidle', timeout=60000)

        print("✅ 页面加载完成!")

        print("\n" + "=" * 80)
        print("💡 浏览器已打开:")
        print("   - 远程调试端口: 9222")
        print("   - 可以使用其他脚本连接到此浏览器")
        print("   - 按 Ctrl+C 可关闭浏览器")
        print("=" * 80)

        # 保持浏览器打开
        try:
            input("\n按 Enter 键关闭浏览器...")
        except KeyboardInterrupt:
            print("\n\n⏹️  收到中断信号，正在关闭浏览器...")

        browser.close()
        print("✅ 浏览器已关闭")


def main():
    """主函数"""
    print_separator("🔑 TradingView 自动登录")

    print("功能:")
    print("   1. 读取 CLAUDE.md 中的 Cookie")
    print("   2. 启动 Chrome 浏览器")
    print("   3. 自动导入 Cookie")
    print("   4. 访问你的 TradingView 私有图表")
    print("   5. 启用远程调试端口（供其他脚本连接）")

    print("\n" + "=" * 80)

    open_browser_with_cookies()

    print("\n" + "=" * 80)
    print("✅ 完成!")
    print("=" * 80)


if __name__ == '__main__':
    main()
