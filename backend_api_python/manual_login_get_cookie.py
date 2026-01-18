#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动登录辅助工具 - 帮助您快速获取 TradingView Cookie

使用方法：
1. 运行此脚本
2. 在自动打开的浏览器中手动登录（如果自动登录失败）
3. 登录成功后，按 Enter 键
4. 脚本会自动获取 Cookie 并更新到 CLAUDE.md
"""

import sys
import os
import re

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_and_update_cookie():
    """手动登录后获取并更新 Cookie"""
    print("=" * 80)
    print("🍪 TradingView Cookie 获取工具（手动登录辅助版）")
    print("=" * 80)

    print("\n使用步骤:")
    print("   1. 浏览器窗口会自动打开")
    print("   2. 如果未登录，请手动登录 TradingView")
    print("   3. 登录成功后，回到此窗口按 Enter 键")
    print("   4. 脚本会自动获取 Cookie 并更新到 CLAUDE.md\n")

    input("⏸️  按 Enter 键打开浏览器...")

    try:
        from playwright.sync_api import sync_playwright

        print("\n🌐 启动浏览器...")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            # 访问 TradingView 首页
            print("   📡 打开 TradingView 首页...")
            page.goto("https://www.tradingview.com/", timeout=60000)

            print("\n" + "=" * 80)
            print("💡 请在浏览器中完成以下操作:")
            print("   1. 如果未登录，点击右上角 'Sign in' 按钮")
            print("   2. 输入账号密码登录")
            print("   3. 如果需要二次验证，请完成验证")
            print("   4. 确保已成功登录（可以看到用户名）")
            print("=" * 80)

            input("\n⏸️  登录成功后，按 Enter 键继续...")

            # 访问图表页面以确保所有 Cookie 都已设置
            print("\n   📡 访问图表页面...")
            page.goto("https://cn.tradingview.com/chart/U1FY2qxO/", timeout=60000)

            import time
            time.sleep(3)

            # 获取所有 Cookie
            print("\n🍪 获取 Cookie...")
            cookies = context.cookies()

            # 格式化为 Cookie 字符串
            cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

            print(f"   ✅ 已获取 {len(cookies)} 个 Cookie")

            # 检查关键 Cookie
            has_sessionid = any(c['name'] == 'sessionid' for c in cookies)
            has_sessionid_sign = any(c['name'] == 'sessionid_sign' for c in cookies)

            print(f"\n📋 Cookie 检查:")
            print(f"   sessionid: {'✅' if has_sessionid else '❌'}")
            print(f"   sessionid_sign: {'✅' if has_sessionid_sign else '❌'}")

            if not has_sessionid or not has_sessionid_sign:
                print(f"\n⚠️  缺少关键 Cookie，可能登录未完成")
                print(f"💡 建议重新获取 Cookie")

            # 保存到 CLAUDE.md
            print(f"\n💾 更新 CLAUDE.md...")

            claude_md_path = os.path.join(os.path.dirname(__file__), '..', 'CLAUDE.md')
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替换 Cookie 部分
            start_marker = '## TradingView Cookie'
            end_marker = '## tv account'

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx != -1 and end_idx != -1:
                new_cookie_section = f"{start_marker}\n```\n{cookie_string}\n```\n\n"
                content = content[:start_idx] + new_cookie_section + content[end_idx:]

                with open(claude_md_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"   ✅ Cookie 已更新到 CLAUDE.md")
            else:
                print(f"   ⚠️  未找到 Cookie 配置区域")
                print(f"\n📝 请手动复制以下内容到 CLAUDE.md:")
                print(f"\n## TradingView Cookie")
                print(f"```")
                print(cookie_string)
                print(f"```")

            print(f"\n{'=' * 80}")
            print(f"✅ 完成!")
            print(f"{'=' * 80}")

            print(f"\n📋 Cookie 信息:")
            print(f"   数量: {len(cookies)} 个")
            print(f"   长度: {len(cookie_string)} 字符")

            if len(cookies) >= 10 and has_sessionid and has_sessionid_sign:
                print(f"\n🎉 Cookie 完整，可以开始批量监控！")
                print(f"\n运行命令:")
                print(f"   python batch_hama_final.py")
            else:
                print(f"\n⚠️  Cookie 可能不完整")
                print(f"💡 建议重新运行此脚本获取 Cookie")

            print(f"\n💾 浏览器将在 5 秒后关闭...")
            time.sleep(5)

            browser.close()

    except Exception as e:
        print(f"\n❌ 获取 Cookie 失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    get_and_update_cookie()
