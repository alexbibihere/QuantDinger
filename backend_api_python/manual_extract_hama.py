#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动提取 HAMA 数据工具

使用方法：
1. 先手动打开浏览器并登录 TradingView
2. 以调试模式启动 Chrome：chrome.exe --remote-debugging-port=9222
3. 运行此脚本连接到浏览器并提取数据
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


def connect_and_extract():
    """连接到浏览器并提取 HAMA 数据"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright 未安装")
        print("   安装: pip install playwright")
        return

    print_separator("🔗 连接到浏览器并提取 HAMA")

    print("💡 使用说明:")
    print("   1. 打开 Chrome 浏览器")
    print("   2. 以调试模式启动:")
    print("      chrome.exe --remote-debugging-port=9222")
    print("   3. 访问你的 TradingView 页面")
    print("   4. 运行此脚本")

    print("\n⏳ 5 秒后自动开始连接...")
    time.sleep(5)

    with sync_playwright() as p:
        try:
            print("\n🔗 连接到浏览器 (localhost:9222)...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")

            # 获取所有上下文和页面
            contexts = browser.contexts
            all_pages = []
            for ctx in contexts:
                all_pages.extend(ctx.pages)

            print(f"✅ 找到 {len(all_pages)} 个页面")

            # 查找 TradingView 页面
            tv_pages = []
            for page in all_pages:
                print(f"\n📄 页面: {page.url[:80]}...")
                if 'tradingview.com' in page.url:
                    tv_pages.append(page)
                    print(f"   ✅ 这是 TradingView 页面")

            if not tv_pages:
                print("\n❌ 未找到 TradingView 页面")
                print("   请确保:")
                print("   1. 浏览器已以调试模式启动")
                print("   2. 已打开 TradingView 页面")
                return

            # 使用第一个 TradingView 页面
            page = tv_pages[0]
            print(f"\n✅ 使用页面: {page.url}")

            # 提取数据
            print_separator("🔍 提取 HAMA 数据")

            # 方法 1: 检查常见的对象
            print("\n📋 方法 1: 扫描常见的对象...")

            js_scan = '''() => {
                const results = {};

                // 检查常见对象
                const objects_to_check = [
                    'tv_widget',
                    'ChartApiInstance',
                    '_exposed_chartWidgetCollection',
                    'widget',
                    'chartWidget',
                    'tradingView'
                ];

                for (let obj_name of objects_to_check) {
                    if (typeof window[obj_name] !== 'undefined') {
                        try {
                            const obj = window[obj_name];
                            results[obj_name] = {
                                type: obj.constructor ? obj.constructor.name : typeof obj,
                                methods: Object.getOwnPropertyNames(obj).slice(0, 20)
                            };
                        } catch (e) {
                            results[obj_name] = {error: String(e)};
                        }
                    }
                }

                // 扫描所有包含 widget 或 chart 的对象
                const all_objects = [];
                for (let key in window) {
                    if (key.toLowerCase().includes('widget') ||
                        key.toLowerCase().includes('chart') ||
                        key.toLowerCase().includes('trading')) {

                        try {
                            const obj = window[key];
                            if (obj && typeof obj === 'object') {
                                all_objects.push({
                                    name: key,
                                    type: obj.constructor ? obj.constructor.name : 'unknown'
                                });
                            }
                        } catch (e) {}
                    }
                }

                results.all_objects = all_objects;

                return results;
            }'''

            scan_result = page.evaluate(js_scan)

            print(f"\n✅ 扫描完成!")
            print(f"\n📊 找到的对象:")

            for obj_name, obj_data in scan_result.items():
                if obj_name != 'all_objects':
                    print(f"\n   🔹 {obj_name}")
                    if 'error' in obj_data:
                        print(f"      错误: {obj_data['error']}")
                    else:
                        print(f"      类型: {obj_data['type']}")
                        if 'methods' in obj_data:
                            print(f"      方法: {', '.join(obj_data['methods'][:10])}")

            print(f"\n📋 所有相关对象 ({len(scan_result['all_objects'])} 个):")
            for obj in scan_result['all_objects']:
                print(f"   - {obj['name']}: {obj['type']}")

            # 方法 2: 尝试获取图表数据
            print_separator("🎯 方法 2: 尝试获取图表数据")

            js_get_data = '''() => {
                // 尝试通过 ChartApiInstance 获取数据
                if (typeof window.ChartApiInstance !== 'undefined') {
                    try {
                        const api = window.ChartApiInstance;
                        return {
                            source: 'ChartApiInstance',
                            data: JSON.parse(JSON.stringify(api)),
                            keys: Object.keys(api)
                        };
                    } catch (e) {
                        return {error: String(e)};
                    }
                }

                // 尝试通过 _exposed_chartWidgetCollection
                if (typeof window._exposed_chartWidgetCollection !== 'undefined') {
                    try {
                        const collection = window._exposed_chartWidgetCollection;
                        const keys = Object.keys(collection);

                        return {
                            source: '_exposed_chartWidgetCollection',
                            keys: keys,
                            length: keys.length
                        };
                    } catch (e) {
                        return {error: String(e)};
                    }
                }

                return {error: 'No suitable API found'};
            }'''

            data_result = page.evaluate(js_get_data)

            print(f"\n📊 数据提取结果:")
            print(json.dumps(data_result, indent=2, ensure_ascii=False))

            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hama_manual_extract_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'page_url': page.url,
                    'scan_result': scan_result,
                    'data_result': data_result
                }, f, ensure_ascii=False, indent=2)

            print(f"\n💾 结果已保存: {filename}")

            # 给出建议
            print_separator("💡 下一步建议")

            print("\n1. 在浏览器 Console 中手动检查对象:")
            print("   按 F12 打开开发者工具，切换到 Console 标签")
            print("   执行以下命令:")

            if scan_result.get('all_objects'):
                print(f"\n   // 检查找到的对象")
                for obj in scan_result['all_objects'][:5]:
                    print(f"   console.log(window.{obj['name']})")

            print("\n2. 查找 HAMA 相关数据:")
            print("   // 搜索包含 hama 的对象")
            print("   Object.keys(window).filter(k => k.toLowerCase().includes('hama'))")
            print("   Object.keys(window).filter(k => k.toLowerCase().includes('study'))")

            print("\n3. 检查图表数据:")
            print("   // 如果找到 chart 对象")
            print("   const chart = window.ChartApiInstance")
            print("   console.log(chart)")
            print("   console.log(Object.keys(chart))")

            print("\n" + "=" * 80)
            input("\n按 Enter 键断开连接...")

            browser.close()
            print("✅ 已断开连接")

        except Exception as e:
            print(f"\n❌ 错误: {e}")
            print("\n💡 请确保:")
            print("   1. Chrome 浏览器正在运行")
            print("   2. 以调试模式启动: chrome.exe --remote-debugging-port=9222")
            print("   3. 已打开 TradingView 页面")

            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    print_separator("🔧 手动提取 HAMA 数据工具")

    print("\n这个工具帮助你:")
    print("   1. 连接到已打开的 Chrome 浏览器")
    print("   2. 扫描 TradingView 页面的所有对象")
    print("   3. 尝试找到 HAMA 指标数据")
    print("   4. 给出下一步操作建议")

    print("\n" + "=" * 80)

    connect_and_extract()

    print("\n" + "=" * 80)
    print("✅ 完成!")
    print("=" * 80)


if __name__ == '__main__':
    main()
