"""
AiCoin Open API 数据服务
封装 AiCoin 的 Open API，提供合约聪明钱相关数据
国内直连，无需代理
"""
import hmac
import hashlib
import base64
import os
import time
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# AiCoin Open API 配置
AICOIN_BASE_URL = "https://open.aicoin.com/api"

# 使用环境变量配置 API Key（可选，不配则用内置免费额度但可能受限）
AICOIN_ACCESS_KEY_ID = os.getenv("AICOIN_ACCESS_KEY_ID", "")
AICOIN_ACCESS_SECRET = os.getenv("AICOIN_ACCESS_SECRET", "")

# 如果没配，尝试内置免费Key
if not AICOIN_ACCESS_KEY_ID:
    AICOIN_ACCESS_KEY_ID = "free"
    AICOIN_ACCESS_SECRET = "free"

_CACHE = {}
CACHE_TTL = 60  # 1分钟缓存


def _sign(params: dict) -> dict:
    """生成 AiCoin API 签名"""
    if "AccessKeyId" in params:
        return params  # 已有签名参数

    nonce = base64.b64encode(os.urandom(8)).decode()[:16]
    ts = str(int(time.time()))

    params["AccessKeyId"] = AICOIN_ACCESS_KEY_ID
    params["SignatureNonce"] = nonce
    params["Timestamp"] = ts

    str_to_sign = f"AccessKeyId={AICOIN_ACCESS_KEY_ID}&SignatureNonce={nonce}&Timestamp={ts}"
    signature = base64.b64encode(
        hmac.new(
            AICOIN_ACCESS_SECRET.encode(), str_to_sign.encode(), hashlib.sha1
        ).digest()
    ).decode()
    params["Signature"] = signature
    return params


def _get(path: str, params: dict = None, use_v2: bool = True) -> Optional[dict]:
    """通用 GET 请求"""
    cache_key = f"{path}:{str(params)}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached["ts"] < CACHE_TTL:
        return cached["data"]

    url = f"{AICOIN_BASE_URL}/v2{path}" if use_v2 else f"{AICOIN_BASE_URL}{path}"
    params = _sign(params or {})
    params["AccessKeyId"] = AICOIN_ACCESS_KEY_ID

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"AiCoin API {path} 返回 {resp.status_code}")
            return None
        data = resp.json()
        if data.get("success"):
            _CACHE[cache_key] = {"data": data.get("data"), "ts": time.time()}
            return data.get("data")
        else:
            logger.warning(f"AiCoin API {path} 失败: {data.get('error')}")
            return None
    except Exception as e:
        logger.error(f"AiCoin API {path} 错误: {e}")
        return None


# ============ 公开接口 ============


def get_ticker(coin_list: str = "BTC,ETH") -> Optional[list]:
    """获取币种实时行情"""
    return _get("/coin/ticker", {"coin_list": coin_list})


def get_futures_interest(symbol: str = None, platform: str = None) -> Optional[list]:
    """获取合约持仓数据"""
    params = {}
    if symbol:
        params["symbol"] = symbol
    if platform:
        params["platform"] = platform
    return _get("/futures/interest", params)


def get_long_short_ratio(symbol: str = "BTCUSDT", platform: str = "binance") -> Optional[list]:
    """获取多空比"""
    params = {"symbol": symbol, "platform": platform}
    return _get("/mix/ls-ratio", params)


def get_liquidation(symbol: str = None, platform: str = None) -> Optional[list]:
    """获取强平数据"""
    params = {}
    if symbol:
        params["symbol"] = symbol
    if platform:
        params["platform"] = platform
    return _get("/mix/liq", params)


def get_big_orders(symbol: str = None, platform: str = None) -> Optional[list]:
    """获取主力大单跟踪"""
    params = {}
    if symbol:
        params["symbol"] = symbol
    if platform:
        params["platform"] = platform
    return _get("/order/bigOrder", params)


def get_top_gainer(platform: str = "binance") -> Optional[list]:
    """获取涨幅榜（加密股票）"""
    return _get("/upgrade/v2/crypto_stock/top-gainer", {"platform": platform})


def get_coin_info(coin_list: str = "BTC") -> Optional[list]:
    """获取币种详细信息（含 AI 分析）"""
    return _get("/coin/info", {"coin_list": coin_list})


def get_smart_money_signals() -> Optional[list]:
    """
    获取聪明钱信号（策略胜率信号）
    包括异常价格波动信号、主力动向
    """
    return _get("/signal/strategySignal", {"type": "futures"})


def get_market_overview() -> Optional[dict]:
    """获取市场概览（多空比、强平、灰度等）"""
    result = {}
    nav = _get("/mix/nav")
    if nav:
        result["nav"] = nav
    ls_ratio = _get("/mix/ls-ratio", {"symbol": "BTCUSDT", "platform": "binance"})
    if ls_ratio:
        result["longShortRatio"] = ls_ratio
    return result if result else None


# ============ Binance 交易对 ============


def get_trading_pairs(market: str = "binance", currency: str = None) -> Optional[list]:
    """获取平台所有交易对"""
    params = {"market": market}
    if currency:
        params["currency"] = currency
    return _get("/trading-pair", params)


def get_trading_pair_ticker(key_list: str) -> Optional[list]:
    """获取交易对实时行情
    key_list 格式: "btcusdt:binance,ethusdt:binance"
    """
    return _get("/trading-pair/ticker", {"key_list": key_list})


def get_all_binance_tickers() -> Optional[list]:
    """获取 Binance 所有 USDT 交易对行情"""
    pairs = get_trading_pairs(market="binance", currency="USDT")
    if not pairs:
        return None

    # 取前 100 个交易对的 ticker（AiCoin 单次最多 100 个）
    all_tickers = []
    for i in range(0, len(pairs), 100):
        batch = pairs[i : i + 100]
        key_list = ",".join(
            f"{p.get('coin_key', '').lower()}usdt:binance"
            for p in batch
            if p.get("coin_key")
        )
        if key_list:
            tickers = _get("/trading-pair/ticker", {"key_list": key_list})
            if tickers:
                all_tickers.extend(tickers)
    return all_tickers

