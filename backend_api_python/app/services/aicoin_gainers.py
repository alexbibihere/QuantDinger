"""
AiCoin 币安合约涨幅榜 - 直接调 AiCoin 开放 API（国内直连）
通过 coin_info/ticker 接口获取主流币种Binance价格
"""
import hashlib
import hmac
import base64
import json
import logging
import os
import time
from typing import Optional
import requests

logger = logging.getLogger(__name__)

_cache = {"data": None, "ts": 0}
CACHE_TTL = 120

# AiCoin 免费 API Key（内置）
AICOIN_KEY = os.getenv("AICOIN_ACCESS_KEY_ID", "free")
AICOIN_SECRET = os.getenv("AICOIN_ACCESS_SECRET", "free")
BASE_URL = "https://open.aicoin.com/api/v2"

HOT_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
    "UNI", "SHIB", "LTC", "ATOM", "ETC", "XLM", "BCH", "FIL", "NEAR",
    "APT", "SUI", "ARB", "OP", "PEPE", "INJ", "TIA", "SEI", "WIF", "JUP",
    "RENDER", "FET", "TAO", "ONDO", "STRK", "ZRO", "ENA", "JTO", "WLD",
    "AAVE", "MKR", "CRV", "SNX", "RUNE", "ALGO", "FLOW", "SAND",
    "MANA", "AXS", "BLUR", "PYTH", "LDO", "AGIX", "GALA", "CHZ",
    "KAVA", "MINA", "ZEC", "DASH", "EOS", "TRX", "VET", "ICP", "HBAR",
    "NOT", "HMSTR", "DOGS", "NEIRO", "CATI", "EIGEN", "SAGA", "PIXEL",
    "PORTAL", "TNSR", "AEVO", "ETHFI", "OMNI", "REZ", "ZK",
]


def _sign(params: dict) -> dict:
    """生成签名"""
    if "AccessKeyId" in params:
        return params
    nonce = base64.b64encode(os.urandom(8)).decode()[:16]
    ts = str(int(time.time()))
    params["AccessKeyId"] = AICOIN_KEY
    params["SignatureNonce"] = nonce
    params["Timestamp"] = ts
    str_to_sign = f"AccessKeyId={AICOIN_KEY}&SignatureNonce={nonce}&Timestamp={ts}"
    sig = base64.b64encode(
        hmac.new(AICOIN_SECRET.encode(), str_to_sign.encode(), hashlib.sha1).digest()
    ).decode()
    params["Signature"] = sig
    return params


def _get(path: str, params: dict = None) -> Optional[dict]:
    """GET 请求"""
    url = f"{BASE_URL}{path}"
    params = _sign(params or {})

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("success"):
            return data.get("data")
        return None
    except Exception as e:
        logger.debug(f"AiCoin GET {path} 失败: {e}")
        return None


def search_coin(keyword: str) -> Optional[dict]:
    """搜索币种，返回第一个有 Binance 价格的"""
    data = _get("/coin/info", {"coin_list": keyword})
    if not data:
        return None
    for c in (data if isinstance(data, list) else []):
        if c.get("coin_code", "").upper() == keyword.upper():
            return c
    return None


def get_binance_gainers(limit: int = 20) -> list:
    """
    获取币安合约涨幅榜：
    1. 先用 coin/ticker 批量获取热门币种数据
    2. 过滤有 Binance 数据的币种
    3. 按24h涨跌幅排序
    """
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    results = []

    # 方式1：用 ticker 批量获取（coin_list 支持最多100个）
    coin_list = ",".join(HOT_COINS[:50])
    ticker_data = _get("/coin/ticker", {"coin_list": coin_list})
    if ticker_data and isinstance(ticker_data, list):
        for c in ticker_data:
            try:
                price = float(c.get("price_usd", 0) or 0)
                change = float(c.get("degree_24h_usd", 0) or 0)
                vol = float(c.get("trade_24h_usd", 0) or 0)
                sym = c.get("coin_key", "").upper()
                results.append({
                    "symbol": f"{sym}USDT",
                    "symbol_short": sym,
                    "name": c.get("coin_name", ""),
                    "price": price,
                    "change_pct": change,
                    "volume": vol,
                    "source": "aicoin",
                })
            except (ValueError, TypeError):
                continue

    # 方式2：如果 ticker 拿不到数据（免费Key受限），用搜索
    if len(results) == 0:
        for coin in HOT_COINS:
            data = _get("/coin/info", {"coin_list": coin})
            if not data or not isinstance(data, list):
                continue
            for c in data:
                if c.get("coin_code", "").upper() != coin.upper():
                    continue
                try:
                    price = float(c.get("price_usd", 0) or 0)
                    change = float(c.get("degree_24h_usd", 0) or 0)
                    vol = float(c.get("trade_24h_usd", 0) or 0)
                    results.append({
                        "symbol": f"{coin}USDT",
                        "symbol_short": coin,
                        "name": c.get("coin_name", ""),
                        "price": price,
                        "change_pct": change,
                        "volume": vol,
                        "source": "aicoin",
                    })
                except (ValueError, TypeError):
                    continue

    # 去重排序
    seen = set()
    unique = []
    for r in results:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)

    unique.sort(key=lambda x: x["change_pct"], reverse=True)
    result = unique[:limit]

    _cache["data"] = result
    _cache["ts"] = now
    return result


def get_aicoin_gainers_api(limit: int = 20) -> list:
    try:
        return get_binance_gainers(limit)
    except Exception as e:
        logger.error(f"AiCoin 涨幅榜: {e}")
        return []
