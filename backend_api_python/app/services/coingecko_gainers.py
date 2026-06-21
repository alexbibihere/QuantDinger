"""
CoinGecko 涨幅榜数据源 - 现货市场 24h 涨跌幅
"""
import logging
from typing import Optional
import requests
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://api.coingecko.com/api/v3"

# 代理配置（国内环境需要 Clash/V2Ray）
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
USE_PROXY = True

_cache = {"data": None, "ts": 0}
CACHE_TTL = 60  # 60秒缓存

# 按成交量排序获取前 100 个币种
PER_PAGE = 100
SORT_ORDER = "volume_desc"


def _get(url: str) -> Optional[dict]:
    """发起 GET 请求"""
    try:
        sess = requests.Session()
        sess.trust_env = False
        kwargs = {"timeout": 15}
        if USE_PROXY:
            kwargs["proxies"] = PROXIES
        r = sess.get(url, **kwargs)
        if r.status_code == 200:
            return r.json()
        logger.warning(f"CoinGecko {url} 返回 {r.status_code}")
        return None
    except Exception as e:
        logger.debug(f"CoinGecko 请求失败: {e}")
        return None


def fetch_gainers(limit: int = 10) -> list:
    """获取 CoinGecko 24h 涨幅榜"""
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    url = (f"{BASE_URL}/coins/markets"
           f"?vs_currency=usd"
           f"&order={SORT_ORDER}"
           f"&per_page={PER_PAGE}"
           f"&page=1"
           f"&sparkline=false"
           f"&price_change_percentage=24h")

    data = _get(url)
    if not data or not isinstance(data, list):
        logger.error(f"CoinGecko 返回异常: {type(data)}")
        return []

    # 过滤有效数据并计算字段
    results = []
    for coin in data:
        chg = coin.get("price_change_percentage_24h")
        if chg is None:
            continue

        price = coin.get("current_price") or 0
        # 部分低价币 price 可能为 0
        if price == 0:
            continue

        results.append({
            "symbol": coin.get("symbol", "").upper() + "USDT",
            "symbol_short": coin.get("symbol", "").upper(),
            "name": coin.get("name", ""),
            "price": price,
            "change_pct": round(chg, 2),
            "market_cap": coin.get("market_cap") or 0,
            "volume_24h": coin.get("total_volume") or 0,
            "high_24h": coin.get("high_24h") or 0,
            "low_24h": coin.get("low_24h") or 0,
            "rank": coin.get("market_cap_rank") or 0,
            "image": coin.get("image", ""),
            "source": "coingecko",
        })

    # 按涨跌幅降序排列
    sorted_data = sorted(results, key=lambda x: x["change_pct"], reverse=True)

    top = sorted_data[:limit]
    _cache["data"] = top
    _cache["ts"] = now
    return top


def fetch_all() -> dict:
    """获取涨幅榜+跌幅榜完整数据"""
    now = time.time()
    if _cache["data"]:
        cached = _cache["data"]
    else:
        cached = fetch_gainers(limit=PER_PAGE)

    gainers = sorted([c for c in cached if c["change_pct"] >= 0],
                     key=lambda x: x["change_pct"], reverse=True)
    losers = sorted([c for c in cached if c["change_pct"] < 0],
                    key=lambda x: x["change_pct"])

    return {
        "gainers": gainers[:20],
        "losers": losers[:20],
        "total": len(cached),
    }
