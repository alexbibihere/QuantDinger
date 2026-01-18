#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 TradingView 私有图表直接提取 HAMA 指标数据

方案分析：
1. WebSocket 数据监听（最佳方案）
2. 浏览器 Console API 执行
3. DOM 元素提取
4. Network 请求拦截
"""

import sys
import os
import json

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


print("=" * 80)
print("  TradingView 私有图表 HAMA 数据提取方案")
print("=" * 80)

print("""
🎯 目标：从你的私有 TradingView 页面直接获取 HAMA 指标数据

📋 可用方案：

方案 1: WebSocket 数据监听 ⭐⭐⭐⭐⭐ (推荐)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原理：监听 TradingView 的 WebSocket 数据流

优势：
  ✅ 实时性最高
  ✅ 数据最准确
  ✅ 不需要截图/OCR
  ✅ 可以获取所有指标数据

实现：
  1. 连接到 TradingView WebSocket
  2. 监听数据包
  3. 解析 HAMA 指标数据
  4. 实时获取更新

WebSocket 端点：
  - wss://data.tradingview.com/socket.io/
  - 需要认证 token

使用工具：
  - 浏览器 DevTools -> Network -> WS
  - Playwright/CDP 协议
  - Python: websockets、playwright

示例代码见下方
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


方案 2: 浏览器 Console API ⭐⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原理：在浏览器 Console 中执行 JavaScript 获取指标数据

优势：
  ✅ 可以访问图表内部 API
  ✅ 不需要逆向工程
  ✅ 相对简单

实现：
  1. 连接到浏览器 (CDP)
  2. 在页面中执行 JS
  3. 调用 TradingView 内部 API
  4. 获取 HAMA 数据

JavaScript API:
  - window.ChartEngine.instance
  - widget.chart()
  - widget.getStudies()

示例代码见下方
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


方案 3: DOM 元素提取 ⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原理：从页面 DOM 中提取显示的指标数值

优势：
  ✅ 简单直接
  ✅ 不需要复杂逻辑

劣势：
  ❌ 数据可能不完整
  ❌ 需要解析 HTML

实现：
  1. 使用 Playwright 连接
  2. 查找 HAMA 指标元素
  3. 提取数值和颜色

示例代码见下方
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


方案 4: Network 请求拦截 ⭐⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
原理：拦截 TradingView 的 HTTP 请求

优势：
  ✅ 可以获取原始数据
  ✅ 支持历史数据

实现：
  1. 使用 Playwright/CDP
  2. 拦截 /history 或 /symbols 请求
  3. 解析响应数据

API 端点：
  - https://symbol-search.tradingview.com/
  - https://data.tradingview.com/
  - 需要认证

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print("\n💡 推荐实施步骤：\n")

print("""
第一步：使用浏览器开发者工具分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 打开你的 TradingView 页面
   https://cn.tradingview.com/chart/U1FY2qxO/

2. 打开开发者工具 (F12)

3. 切换到 Network 标签

4. 过滤 WebSocket (WS) 请求

5. 查找包含 HAMA 数据的消息

6. 记录消息格式和数据结构


第二步：使用 Playwright 连接浏览器
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 以调试模式启动 Chrome:
   chrome.exe --remote-debugging-port=9222

2. 打开你的 TradingView 页面

3. 运行 Python 脚本连接并提取数据


第三步：验证数据准确性
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 对比提取的数据与图表显示
2. 验证时间戳
3. 确认数值一致性
""")

print("\n" + "=" * 80)
print("  示例代码")
print("=" * 80)

print("""
📌 方案 1: WebSocket 监听
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from playwright.sync_api import sync_playwright
import json

def monitor_tradingview_websocket():
    with sync_playwright() as p:
        # 连接到现有浏览器
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # 获取页面
        contexts = browser.contexts
        pages = []
        for ctx in contexts:
            pages.extend(ctx.pages)

        tv_page = None
        for page in pages:
            if 'tradingview.com/chart' in page.url:
                tv_page = page
                break

        if not tv_page:
            print("未找到 TradingView 页面")
            return

        # 监听 WebSocket
        def on_web_socket(ws):
            print(f"WebSocket 连接: {ws.url}")

            def on_message(message):
                try:
                    data = json.loads(message)
                    print(f"收到消息: {data}")
                    # 解析 HAMA 数据
                    # TODO: 根据实际消息格式解析
                except:
                    pass

            ws.on("framesreceived", on_message)

        tv_page.on("websocket", on_web_socket)

        # 保持连接
        input("按 Enter 退出...")

        browser.close()

# 运行
monitor_tradingview_websocket()
""")

print("""
📌 方案 2: Console API 执行
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from playwright.sync_api import sync_playwright

def get_hama_via_console():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # 获取 TradingView 页面
        contexts = browser.contexts
        pages = []
        for ctx in contexts:
            pages.extend(ctx.pages)

        tv_page = None
        for page in pages:
            if 'tradingview.com/chart' in page.url:
                tv_page = page
                break

        if not tv_page:
            print("未找到 TradingView 页面")
            return

        # 执行 JavaScript 获取图表数据
        js_code = '''
        // 获取图表实例
        const widget = window.tv_widget;
        if (!widget) {
            return {error: "Widget not found"};
        }

        // 获取图表对象
        const chart = widget.chart();
        if (!chart) {
            return {error: "Chart not found"};
        }

        // 获取所有指标
        const studies = chart.getAllStudies();

        // 查找 HAMA 指标
        const hamaStudy = studies.find(s =>
            s.name && s.name.includes('HAMA')
        );

        if (!hamaStudy) {
            return {error: "HAMA study not found"};
        }

        // 获取 HAMA 数据
        const hamaData = hamaStudy.data;

        return {
            name: hamaStudy.name,
            data: hamaData,
            price: hamaStudy.price,
            color: hamaStudy.color
        };
        '''

        result = tv_page.evaluate(js_code)
        print("HAMA 数据:", json.dumps(result, indent=2))

        browser.close()

# 运行
get_hama_via_console()
""")

print("""
📌 方案 3: DOM 元素提取
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from playwright.sync_api import sync_playwright

def get_hama_from_dom():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # 获取 TradingView 页面
        contexts = browser.contexts
        pages = []
        for ctx in contexts:
            pages.extend(ctx.pages)

        tv_page = None
        for page in pages:
            if 'tradingview.com/chart' in page.url:
                tv_page = page
                break

        if not tv_page:
            print("未找到 TradingView 页面")
            return

        # 提取 DOM 数据
        js_code = '''
        // 查找所有包含数值的元素
        const elements = document.querySelectorAll('*');
        const hamaElements = [];

        for (let el of elements) {
            const text = el.textContent || '';

            // 查找包含 HAMA 的元素
            if (text.includes('HAMA') || text.includes('hama')) {
                const style = window.getComputedStyle(el);
                hamaElements.push({
                    text: text.trim(),
                    color: style.color,
                    fontSize: style.fontSize
                });
            }
        }

        return hamaElements;
        '''

        result = tv_page.evaluate(js_code)
        print("HAMA 元素:", json.dumps(result, indent=2, ensure_ascii=False))

        browser.close()

# 运行
get_hama_from_dom()
""")

print("\n" + "=" * 80)
print("  下一步行动")
print("=" * 80)

print("""
1. 🔍 分析 WebSocket 消息格式
   ─────────────────────────────────────
   打开浏览器 DevTools -> Network -> WS
   查看包含 HAMA 数据的消息

2. 📝 创建提取脚本
   ─────────────────────────────────────
   根据消息格式编写 Python 脚本
   使用上面的示例代码

3. ✅ 验证数据准确性
   ─────────────────────────────────────
   对比提取的数据与图表显示
   确保数据一致

4. 🚀 集成到生产
   ─────────────────────────────────────
   定时监控或实时监听
   保存到数据库或发送通知
""")

print("\n" + "=" * 80)
