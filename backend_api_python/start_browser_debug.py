#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动以调试模式启动浏览器

功能：
1. 自动关闭所有 Chrome/Edge 浏览器
2. 以调试模式启动浏览器
3. 自动打开 TradingView 图表页面
"""

import sys
import os
import subprocess
import time

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def find_browser_path():
    """查找浏览器路径"""
    possible_paths = [
        # Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
        # Edge
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def close_all_browsers():
    """关闭所有浏览器"""
    print("\n🔴 关闭所有浏览器...")

    try:
        # 关闭 Chrome
        subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'],
                      capture_output=True)
        # 关闭 Edge
        subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'],
                      capture_output=True)

        print("✅ 浏览器已关闭")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️  关闭浏览器时出错: {e}")


def start_browser_debug():
    """以调试模式启动浏览器"""
    print("=" * 80)
    print("🚀 自动以调试模式启动浏览器")
    print("=" * 80)

    # 查找浏览器
    browser_path = find_browser_path()

    if not browser_path:
        print("\n❌ 未找到浏览器")
        print("\n💡 请手动安装 Chrome 或 Edge")
        return False

    print(f"\n✅ 找到浏览器: {browser_path}")

    # 关闭现有浏览器
    close_all_browsers()

    # 启动调试模式
    print("\n🚀 以调试模式启动浏览器...")
    print("   端口: 9222")

    try:
        # 启动浏览器（调试模式）
        cmd = [
            browser_path,
            '--remote-debugging-port=9222',
            '--user-data-dir=/tmp/chrome-debug-profile'
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("✅ 浏览器已启动")

        # 等待浏览器启动
        time.sleep(3)

        # 自动打开 TradingView
        print("\n📡 打开 TradingView...")
        import webbrowser
        webbrowser.open("https://cn.tradingview.com/chart/U1FY2qxO/")

        print("\n" + "=" * 80)
        print("✅ 准备完成!")
        print("=" * 80)

        print("\n📝 下一步:")
        print("   1. 在打开的浏览器中登录 TradingView")
        print("   2. 运行命令: python hama_from_existing_browser.py")
        print("   3. 脚本会自动连接到这个浏览器")

        print("\n💡 提示:")
        print("   - 浏览器会保持打开状态")
        print("   - 可以看到页面自动切换币种")
        print("   - 所有操作在您已登录的浏览器中进行")

        print("\n" + "=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    try:
        success = start_browser_debug()

        if success:
            print("\n⏸️  按 Enter 键退出，或直接运行 HAMA 监控脚本...")
            input()

    except KeyboardInterrupt:
        print("\n\n👋 用户取消")


if __name__ == '__main__':
    main()
