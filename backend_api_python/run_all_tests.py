#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试所有 HAMA 提取方法

使用已打开的浏览器，测试所有可用的提取方法
"""

import sys
import os
import json
import time
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_separator(title=""):
    """打印分隔线"""
    width = 80
    if title:
        print(f"\n{'=' * width}")
        print(f"  {title}")
        print(f"{'=' * width}\n")
    else:
        print(f"{'=' * width}")


def get_cookies_from_claude_md():
    """从 CLAUDE.md 读取 Cookie"""
    try:
        claude_md_path = os.path.join(os.path.dirname(__file__), '..', 'CLAUDE.md')

        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找 Cookie 代码块
        start_marker = '## TradingView Cookie'
        end_marker = '## tv account'

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            return None

        cookie_section = content[start_idx:end_idx]

        # 提取 ``` 中的内容
        code_start = cookie_section.find('```')
        if code_start == -1:
            return None

        code_start += 3
        code_end = cookie_section.find('```', code_start)

        if code_end == -1:
            return None

        cookie_string = cookie_section[code_start:code_end].strip()

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

        print(f"✅ 成功解析 {len(cookies)} 个 Cookie")
        return cookies

    except Exception as e:
        print(f"⚠️  读取 Cookie 失败: {e}")
        return None


def test_method_1_local_calculation():
    """测试方法 1: 本地计算"""
    print_separator("方法 1: 本地计算 HAMA")

    try:
        from app.services.hama_calculator import calculate_hama_from_ohlcv

        print("✅ HAMA 计算器已导入")
        print("\n📊 使用模拟数据测试...")

        # 生成模拟 OHLCV 数据
        import random
        ohlcv = []
        base_price = 100000

        for i in range(100):
            open_price = base_price + random.uniform(-500, 500)
            high_price = open_price + random.uniform(0, 300)
            low_price = open_price - random.uniform(0, 300)
            close_price = open_price + random.uniform(-200, 200)
            volume = random.uniform(1000, 10000)

            ohlcv.append([
                int(time.time()) - (100 - i) * 900,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ])

        print(f"   ✅ 生成了 {len(ohlcv)} 根模拟 K线")

        print("\n🔢 计算 HAMA 指标...")
        start_time = time.time()

        result = calculate_hama_from_ohlcv(ohlcv)

        elapsed = (time.time() - start_time) * 1000

        if result:
            print(f"   ✅ 计算成功!")
            print(f"   ⏱️  耗时: {elapsed:.2f} ms")
            print(f"   📈 HAMA 值: {result.get('hama_value', 'N/A')}")
            print(f"   🎨 颜色: {result.get('hama_color', 'N/A').upper()}")
            print(f"   📊 趋势: {result.get('trend', 'N/A').upper()}")

            return {
                'method': '本地计算',
                'success': True,
                'elapsed_time_ms': elapsed,
                'data': result
            }
        else:
            return {'method': '本地计算', 'success': False, 'error': '计算返回 None'}

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return {'method': '本地计算', 'success': False, 'error': str(e)}


def test_method_2_ocr_public_widget():
    """测试方法 2: OCR 识别（公开 Widget）"""
    print_separator("方法 2: OCR 识别（公开 Widget）")

    try:
        from playwright.sync_api import sync_playwright
        from app.services.hama_ocr_extractor import HAMAOCRExtractor

        print("✅ OCR 提取器已导入")
        print("\n🌐 启动浏览器...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            symbol = "BTCUSDT"
            interval = "15"
            widget_url = f"https://s.tradingview.com/widgetembed/?symbol=BINANCE:{symbol}&interval={interval}"

            print(f"   访问: {widget_url[:80]}...")

            start_time = time.time()
            page.goto(widget_url, timeout=60000)
            print("   ⏳ 等待图表加载...")
            time.sleep(8)

            screenshot_path = f"screenshot_test_{symbol}_{interval}.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ 截图已保存")

            print("\n🔍 使用 OCR 识别...")
            extractor = HAMAOCRExtractor(ocr_engine='rapidocr')

            ocr_start = time.time()
            result = extractor.extract_hama_with_ocr(screenshot_path)
            ocr_elapsed = time.time() - ocr_start

            browser.close()
            total_elapsed = time.time() - start_time

            if result:
                print(f"   ✅ OCR 识别成功!")
                print(f"   ⏱️  总耗时: {total_elapsed:.2f} 秒")
                print(f"   ⏱️  OCR 耗时: {ocr_elapsed:.2f} 秒")
                print(f"   📈 HAMA 值: {result.get('hama_value', 'N/A')}")
                print(f"   🎨 颜色: {result.get('hama_color', 'N/A').upper()}")

                return {
                    'method': 'OCR (公开 Widget)',
                    'success': True,
                    'elapsed_time_s': total_elapsed,
                    'data': result
                }
            else:
                return {'method': 'OCR (公开 Widget)', 'success': False, 'error': 'OCR 返回 None'}

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return {'method': 'OCR (公开 Widget)', 'success': False, 'error': str(e)}


def test_method_3_direct_api():
    """测试方法 3: 直接 API 提取（使用 Cookie）"""
    print_separator("方法 3: 直接 API 提取（私有图表）")

    try:
        from playwright.sync_api import sync_playwright

        print("✅ Playwright 已导入")

        cookies = get_cookies_from_claude_md()
        if cookies:
            print(f"✅ 已加载 {len(cookies)} 个 Cookie")
        else:
            print("⚠️  未找到 Cookie，尝试无 Cookie 访问")

        print("\n🌐 启动浏览器...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})

            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()

            chart_url = "https://cn.tradingview.com/chart/U1FY2qxO/"
            print(f"\n   访问: {chart_url}")

            start_time = time.time()
            page.goto(chart_url, wait_until='domcontentloaded', timeout=60000)
            print("   ⏳ 等待页面加载...")
            time.sleep(10)

            print("\n🔍 尝试访问 TradingView 内部 API...")

            # 尝试多种方法
            tests = []

            # 测试 1: window.tv_widget
            js_test_1 = '''() => {
                if (typeof window.tv_widget !== 'undefined') {
                    return {found: true, type: 'tv_widget'};
                }
                return {found: false};
            }'''
            result_1 = page.evaluate(js_test_1)
            tests.append(('tv_widget', result_1))

            # 测试 2: 查找所有包含 widget 的对象
            js_test_2 = '''() => {
                const widgets = [];
                for (let key in window) {
                    if (key.toLowerCase().includes('widget') || key.toLowerCase().includes('chart')) {
                        try {
                            const obj = window[key];
                            if (obj && typeof obj === 'object') {
                                widgets.push(key);
                            }
                        } catch (e) {}
                    }
                }
                return {found: widgets.length > 0, widgets: widgets.slice(0, 10)};
            }'''
            result_2 = page.evaluate(js_test_2)
            tests.append(('扫描对象', result_2))

            print("\n   📋 扫描结果:")
            for name, result in tests:
                print(f"      {name}: {result}")

            elapsed = time.time() - start_time

            print("\n💡 提示:")
            print("   1. 浏览器窗口已打开")
            print("   2. 按 F12 打开开发者工具")
            print("   3. 在 Console 中执行:")
            print("      Object.keys(window).filter(k => k.includes('widget'))")
            print("   4. 找到正确的对象后，可以手动提取数据")

            time.sleep(5)

            browser.close()

            return {
                'method': '直接 API',
                'success': False,
                'elapsed_time_s': elapsed,
                'error': '需要手动查找 API',
                'scan_results': tests
            }

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return {'method': '直接 API', 'success': False, 'error': str(e)}


def compare_and_save(results):
    """对比并保存结果"""
    print_separator("📊 测试结果汇总")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\n✅ 成功: {len(successful)}/{len(results)}")
    print(f"❌ 失败: {len(failed)}/{len(results)}\n")

    for r in successful:
        method = r['method']
        print(f"   ⭐ {method}")

        if 'elapsed_time_ms' in r:
            print(f"      耗时: {r['elapsed_time_ms']:.2f} ms")
        elif 'elapsed_time_s' in r:
            print(f"      耗时: {r['elapsed_time_s']:.2f} 秒")

        if 'data' in r and isinstance(r['data'], dict):
            if 'hama_value' in r['data']:
                print(f"      HAMA: {r['data']['hama_value']} ({r['data'].get('hama_color', 'N/A')})")

        print()

    for r in failed:
        print(f"   ❌ {r['method']}: {r.get('error', '未知错误')}")

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hama_test_report_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 报告已保存: {filename}")


def main():
    """主函数"""
    print_separator("🎯 完整测试所有 HAMA 提取方法")

    print("测试方案:")
    print("   1. 本地计算（快速，模拟数据）")
    print("   2. OCR 识别（公开 Widget）")
    print("   3. 直接 API（私有图表，需要 Cookie）")

    print("\n🚀 开始测试...\n")

    results = []

    # 测试 1
    print("\n" + "🔄" * 40)
    results.append(test_method_1_local_calculation())

    # 测试 2
    print("\n" + "🔄" * 40)
    results.append(test_method_2_ocr_public_widget())

    # 测试 3
    print("\n" + "🔄" * 40)
    print("\n⚠️  测试 3 会打开浏览器窗口")
    print("⏳ 3 秒后自动开始...")
    time.sleep(3)
    results.append(test_method_3_direct_api())

    # 汇总结果
    print("\n" + "🔄" * 40)
    compare_and_save(results)

    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)


if __name__ == '__main__':
    main()
