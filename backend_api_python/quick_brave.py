#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速连接到已打开的 Brave 浏览器
"""

import sys
import os
import time

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def connect_to_brave_and_monitor():
    """连接到 Brave 并监控"""
    try:
        from playwright.sync_api import sync_playwright
        from rapidocr_onnxruntime import RapidOCR

        print("=" * 80)
        print("🔌 连接到 Brave 浏览器")
        print("=" * 80)

        print("\n📝 前提条件:")
        print("   1. 关闭所有 Brave 浏览器窗口")
        print("   2. 以调试模式启动 Brave:")
        print()
        print("   启动命令:")
        print('   "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"')
        print("   --remote-debugging-port=9222")
        print()
        print("   或者创建快捷方式，添加参数: --remote-debugging-port=9222")
        print("=" * 80)

        input("\n⏸️  Brave 以调试模式启动后，按 Enter 键连接...")

        # 初始化 OCR
        print("\n🔍 初始化 RapidOCR...")
        ocr = RapidOCR()

        with sync_playwright() as p:
            print("🔌 连接到 Brave (localhost:9222)...")
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
            except Exception as e:
                print(f"\n❌ 连接失败: {e}")
                print("\n💡 请确保:")
                print("   1. Brave 以 --remote-debugging-port=9222 启动")
                print("   2. 没有其他程序占用 9222 端口")
                print("\n🔧 快速启动脚本（保存为 .bat 文件）:")
                print('   start "" "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" --remote-debugging-port=9222')
                input("\n⏸️  按 Enter 键退出...")
                return

            # 获取页面
            contexts = browser.contexts
            if not contexts:
                print("❌ 未找到浏览器上下文")
                return

            context = contexts[0]
            pages = context.pages

            if not pages:
                print("❌ 未找到页面")
                print("\n💡 请在 Brave 中打开 TradingView 图表页面")
                input("\n⏸️  打开后按 Enter 键重试...")
                pages = context.pages

            if not pages:
                print("❌ 仍然未找到页面")
                return

            # 查找 TradingView 页面
            tv_page = None
            for page in pages:
                if 'tradingview.com' in page.url:
                    tv_page = page
                    break

            if not tv_page:
                print("✅ 已连接到 Brave")
                print(f"\n💡 当前打开的页面:")
                for i, page in enumerate(pages):
                    print(f"   {i+1}. {page.url}")

                print("\n💡 提示:")
                print("   - 在 Brave 中访问: https://cn.tradingview.com/chart/U1FY2qxO/")
                print("   - 登录您的账号")
                print("   - 然后运行此脚本重新连接")
                return

            print(f"✅ 已连接到: {tv_page.url}")

            # 开始监控
            symbols = ["AXSUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT"]

            print(f"\n📋 开始监控 {len(symbols)} 个币种...")
            input("\n⏸️  确保已登录 TradingView，然后按 Enter 键开始...")

            results = []
            total_start = time.time()

            for i, symbol in enumerate(symbols):
                print(f"\n{'─' * 80}")
                print(f"处理 {i+1}/{len(symbols)}: {symbol}")
                print(f"{'─' * 80}")

                start_time = time.time()

                try:
                    new_url = f"https://cn.tradingview.com/chart/U1FY2qxO/?symbol=BINANCE%3A{symbol}&interval=15"

                    print(f"   📡 切换到: {symbol}")
                    tv_page.goto(new_url, timeout=30000)

                    print(f"   ⏳ 等待加载 (10 秒)...")
                    time.sleep(10)

                    # 截图
                    screenshot = f"brave_hama_{symbol}_{int(time.time())}.png"
                    tv_page.screenshot(
                        path=screenshot,
                        clip={'x': 1250, 'y': 400, 'width': 250, 'height': 300}
                    )
                    print(f"   ✅ 截图: {screenshot}")

                    # OCR
                    print(f"   🔍 OCR 识别...")
                    ocr_result = ocr(screenshot)

                    if ocr_result and len(ocr_result) >= 2 and ocr_result[0]:
                        text_lines = []
                        for item in ocr_result[0]:
                            if len(item) >= 3:
                                if item[2] > 0.3:
                                    text_lines.append(item[1])

                        has_up = any('上涨' in line or '涨' in line for line in text_lines)
                        has_down = any('下跌' in line or '跌' in line for line in text_lines)

                        hama_trend = 'unknown'
                        hama_color = 'unknown'

                        if has_up:
                            hama_trend = 'up'
                            hama_color = 'green'
                        elif has_down:
                            hama_trend = 'down'
                            hama_color = 'red'

                        elapsed = time.time() - start_time

                        if hama_trend != 'unknown':
                            print(f"   ✅ {hama_trend.upper()} ({hama_color.upper()}) - {elapsed:.1f}s")
                            results.append({
                                'symbol': symbol,
                                'trend': hama_trend,
                                'color': hama_color,
                                'success': True
                            })
                        else:
                            print(f"   ⚠️  无法识别")
                            results.append({'symbol': symbol, 'success': False})
                    else:
                        print(f"   ❌ OCR 失败")
                        results.append({'symbol': symbol, 'success': False})

                except Exception as e:
                    print(f"   ❌ 错误: {e}")
                    results.append({'symbol': symbol, 'success': False})

                if i < len(symbols) - 1:
                    time.sleep(3)

            total_elapsed = time.time() - total_start

            # 显示结果
            print(f"\n{'=' * 80}")
            print("📊 监控结果")
            print('=' * 80)

            successful = [r for r in results if r.get('success')]
            for r in successful:
                emoji = "🟢" if r['color'] == 'green' else "🔴"
                print(f"{emoji} {r['symbol']}: {r['trend'].upper()}")

            print(f"\n✅ 成功: {len(successful)}/{len(symbols)}")
            print(f"⏱️  总耗时: {total_elapsed:.1f} 秒")

            print(f"\n💡 Brave 保持打开状态")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    connect_to_brave_and_monitor()
