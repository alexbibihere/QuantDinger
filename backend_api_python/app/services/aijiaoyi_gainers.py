"""
爱交易数据源 - 币安永续合约涨幅榜
通过 Playwright 登录后提取 body textContent 获取币安永续合约列表
"""
import asyncio
import json
import logging
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)

_cache = {"data": None, "ts": 0}
CACHE_TTL = 60

TOKEN = "0e7927585fa74c31b6dc3993ca45c72a"
UID = "139563"
PHONE = "15574882481"


async def fetch_binance_perp_gainers(limit: int = 20) -> Optional[list]:
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("请安装 playwright")
        return None

    data = None
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = await context.new_page()

        try:
            # 打开 chart 页（会显示 "You need JavaScript" 页面）
            await page.goto("https://www.aijiaoyi.xyz/chart", timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # 设置 localStorage（此时页面是空白 JS 页面，可以设置）
            await page.evaluate(f"""
            () => {{
                try {{
                    localStorage.setItem('token', '{TOKEN}');
                    localStorage.setItem('uid', '{UID}');
                    localStorage.setItem('user', JSON.stringify({{
                        user_id: 33082, token: '{TOKEN}',
                        uid: {UID}, nickname: '折镜', phone: '{PHONE}'
                    }}));
                }} catch(e) {{}}
            }}
            """)

            # 刷新页面让 React 应用读取 localStorage
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(5)

            # 获取 body textContent
            body_text = await page.evaluate("document.body.textContent")

            # 解析币安永续合约数据
            data = _parse_body_text(body_text, limit)

        except Exception as e:
            logger.error(f"爱交易抓取失败: {e}")

        await browser.close()

    if data:
        _cache["data"] = data
        _cache["ts"] = now
    return data


def _parse_body_text(text: str, limit: int) -> list:
    """从 body textContent 解析币安永续合约"""
    # 按"永续"分割
    parts = text.split("永续")
    results = []

    for i in range(1, len(parts)):
        prev = parts[i - 1]
        after = parts[i]

        # 提取符号名: XXXUSDT
        sym_match = re.search(r'([A-Z][A-Z0-9]*)USDT$', prev)
        if not sym_match:
            continue
        symbol = sym_match.group(1)

        # 提取价格和涨跌幅: 从右往左找
        pct_idx = after.find('%')
        if pct_idx < 0:
            continue

        # 涨跌幅在 % 左边
        chg_start = pct_idx - 1
        while chg_start >= 0 and (after[chg_start].isdigit() or after[chg_start] in '.-'):
            chg_start -= 1
        change_str = after[chg_start + 1:pct_idx]

        # 价格在涨跌幅左边
        price_str = after[:chg_start + 1]

        try:
            change = float(change_str)
            if change > 100 or change < -100:
                continue
            price = float(price_str)

            results.append({
                "symbol": f"{symbol}USDT",
                "symbol_short": symbol,
                "price": price,
                "change_pct": round(change, 2),
                "source": "aijiaoyi",
            })
        except (ValueError, TypeError):
            continue

    # 去重
    seen = set()
    unique = []
    for r in results:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)

    # 按涨跌幅排序
    unique.sort(key=lambda x: x["change_pct"], reverse=True)
    return unique[:limit]


def get_aijiaoyi_gainers(limit: int = 20) -> list:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(fetch_binance_perp_gainers(limit))
        loop.close()
        return data or []
    except Exception as e:
        logger.error(f"爱交易: {e}")
        return []
