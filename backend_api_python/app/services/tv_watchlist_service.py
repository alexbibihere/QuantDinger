#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView 关注列表服务 — 通过 Playwright 登录获取关注列表

流程:
  1. 用 TV 账号密码通过 Playwright 登录 cn.tradingview.com
  2. 获取登录后的 cookies (sessionid, sessionid_sign)
  3. 调用 TV API 获取关注列表中的品种
  4. 返回品种列表

使用场景:
  用户在 hama-market 页面输入 TV 账号密码 → 获取自己的关注列表
  → 对每个品种使用 tv-bridge 获取 HAMA 数据 + 生成 SVG 截图
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TradingViewWatchlistService:
    """TradingView 关注列表服务"""

    # TV API 端点
    WATCHLIST_API = "https://www.tradingview.com/accounts/{account_id}/watchlists/"
    WATCHLIST_DETAIL_API = "https://www.tradingview.com/accounts/{account_id}/watchlists/{wl_id}/"

    def __init__(self):
        self.cookies = {}  # 登录后的 cookies
        self.is_logged_in = False

    def login(self, username: str, password: str) -> bool:
        """
        使用 Playwright 登录 TradingView

        Args:
            username: TV 邮箱
            password: TV 密码

        Returns:
            是否登录成功
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright 未安装，请运行: pip install playwright && playwright install chromium")
            return False

        logger.info(f"📡 登录 TradingView: {username}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                # 访问 TV 登录页
                logger.info("  访问登录页面...")
                page.goto("https://cn.tradingview.com/accounts/signin/", wait_until="networkidle")
                page.wait_for_timeout(3000)

                # 输入邮箱
                logger.info("  输入邮箱...")
                email_input = page.locator('input[name="email"], input[type="email"], input[placeholder*="邮箱"], input[placeholder*="Email"]').first
                if email_input.is_visible():
                    email_input.fill(username)
                else:
                    # 尝试按 class 查找
                    page.fill('input[type="text"]', username)

                page.wait_for_timeout(1000)

                # 输入密码
                logger.info("  输入密码...")
                password_input = page.locator('input[name="password"], input[type="password"]').first
                if password_input.is_visible():
                    password_input.fill(password)
                else:
                    page.fill('input[type="password"]', password)

                page.wait_for_timeout(1000)

                # 点击登录按钮
                logger.info("  点击登录按钮...")
                submit_btn = page.locator('button[type="submit"], button:has-text("登录"), button:has-text("Sign in")').first
                if submit_btn.is_visible():
                    submit_btn.click()
                else:
                    page.keyboard.press("Enter")

                # 等待登录完成
                page.wait_for_timeout(5000)
                page.wait_for_load_state("networkidle")

                # 检查是否登录成功
                current_url = page.url
                if "signin" in current_url and "error" in current_url:
                    logger.error("❌ 登录失败: 账号或密码错误")
                    browser.close()
                    return False

                # 获取 cookies
                cookies = context.cookies()
                for c in cookies:
                    if c["name"] in ("sessionid", "sessionid_sign", "uid"):
                        self.cookies[c["name"]] = c["value"]

                logger.info(f"  获取到 {len(self.cookies)} 个 cookies: {list(self.cookies.keys())}")

                # 尝试获取用户信息
                try:
                    # 访问 TV 设置页获取 account_id
                    page.goto("https://www.tradingview.com/settings/", wait_until="networkidle")
                    page.wait_for_timeout(2000)

                    # 从页面提取 account_id
                    account_info = page.evaluate("""() => {
                        try {
                            return window.__INITIAL_STATE__ || {};
                        } catch(e) { return {}; }
                    }""")

                    # 也可以通过 API 获取
                    watchlist_cookies = {}
                    for c in cookies:
                        watchlist_cookies[c["name"]] = c["value"]

                    self.cookies_dict = watchlist_cookies

                    # 尝试获取关注列表
                    watchlists = self._fetch_watchlists()
                    if watchlists:
                        logger.info(f"✅ 登录成功! 获取到 {len(watchlists)} 个关注列表")
                        self.is_logged_in = True
                        browser.close()
                        return True

                except Exception as e:
                    logger.warning(f"  获取关注列表失败: {e}")

                browser.close()

                # 只要有 cookies 就算成功
                if len(self.cookies) >= 2:
                    logger.info(f"✅ 登录成功 (cookies 获取到 {len(self.cookies)} 个)")
                    self.is_logged_in = True
                    return True

                logger.error("❌ 登录失败: 未能获取有效的 cookies")
                return False

        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False

    def _fetch_watchlists(self) -> List[Dict]:
        """
        通过 TV API 获取关注列表
        """
        import requests as req

        # 构建 cookies 字符串
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies_dict.items()])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_str,
            "Referer": "https://www.tradingview.com/",
            "Origin": "https://www.tradingview.com",
        }

        try:
            # 先获取用户信息
            resp = req.get("https://www.tradingview.com/accounts/", headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"获取账户信息失败: {resp.status_code}")
                return []

            accounts = resp.json()
            if not accounts:
                return []

            account_id = accounts[0].get("id")
            if not account_id:
                return []

            # 获取关注列表
            resp = req.get(
                f"https://www.tradingview.com/accounts/{account_id}/watchlists/",
                headers=headers,
                timeout=10
            )
            if resp.status_code != 200:
                logger.warning(f"获取关注列表失败: {resp.status_code}")
                return []

            return resp.json()

        except Exception as e:
            logger.warning(f"TV API 请求失败: {e}")
            return []

    def get_watchlist_symbols(self) -> List[str]:
        """
        获取关注列表中的所有品种

        Returns:
            品种列表，如 ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"]
        """
        if not self.cookies_dict:
            logger.warning("未登录，无法获取关注列表")
            return []

        watchlists = self._fetch_watchlists()
        all_symbols = []

        for wl in watchlists:
            wl_id = wl.get("id")
            if not wl_id:
                continue

            symbols = wl.get("symbols", [])
            name = wl.get("name", "未命名")
            logger.info(f"  关注列表 '{name}': {len(symbols)} 个品种")
            all_symbols.extend(symbols)

        # 去重
        seen = set()
        unique = []
        for s in all_symbols:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique

    def get_watchlist_hama_data(self, timeframe: str = "D") -> List[Dict[str, Any]]:
        """
        获取关注列表所有品种的 HAMA 数据

        Args:
            timeframe: 时间周期

        Returns:
            每个品种的 HAMA 数据列表
        """
        from app.services.hama_tv_service import hama_tv_service

        symbols = self.get_watchlist_symbols()
        if not symbols:
            return []

        # 提取品种名（去掉 BINANCE: 前缀）
        clean_symbols = []
        for s in symbols:
            if ":" in s:
                s = s.split(":")[1]
            clean_symbols.append(s.upper())

        logger.info(f"📡 获取 {len(clean_symbols)} 个关注品种的 HAMA 数据...")

        result = hama_tv_service.batch_get_hama(
            symbols=clean_symbols,
            timeframe=timeframe,
        )

        return result.get("results", {})


# 全局单例
_watchlist_service = None


def get_watchlist_service():
    global _watchlist_service
    if _watchlist_service is None:
        _watchlist_service = TradingViewWatchlistService()
    return _watchlist_service
