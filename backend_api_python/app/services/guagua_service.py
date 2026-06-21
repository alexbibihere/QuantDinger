"""
鍛卞懕閫夊竵 (yss-signal.com) 鏁版嵁鏈嶅姟
浠庡懕鍛遍€夊竵 API 鑾峰彇楂?涓?浣庢祦鍔ㄦ€у尯鐨勪俊鍙锋暟鎹?
"""
import requests
import json
import os
import time
import random
from typing import Optional, List, Dict, Any
from functools import lru_cache
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 榛樿閰嶇疆
GUAGUA_BASE_URL = "https://ai.yss-signal.com"
GUAGUA_EMAIL = os.environ.get("GUAGUA_EMAIL", "2601732014@qq.com")
GUAGUA_PASSWORD = os.environ.get("GUAGUA_PASSWORD", "")

# Token 缂撳瓨
_token_cache = {"token": None, "expires_at": 0}

# 缂撳瓨 TTL锛堢锛?
CACHE_TTL = 30

# 淇″彿鏁版嵁缂撳瓨
_signal_cache = {"data": None, "fetched_at": 0}

# 鏃犱唬鐞?Session锛堢粫杩囩郴缁熶唬鐞嗭級
_no_proxy_session = requests.Session()
_no_proxy_session.trust_env = False
_no_proxy_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})


def _get_token() -> Optional[str]:
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now:
        return _token_cache["token"]
    if not GUAGUA_PASSWORD:
        logger.warning("GUAGUA_PASSWORD 鏈厤缃紝璺宠繃鍛卞懕閫夊竵鐧诲綍")
        return None
    try:
        time.sleep(random.uniform(3, 8))
        resp = _no_proxy_session.post(
            f"{GUAGUA_BASE_URL}/login",
            json={"email": GUAGUA_EMAIL, "password": GUAGUA_PASSWORD},
            timeout=15,
        )
        data = resp.json()
        if data.get("success") and data.get("token"):
            token = data["token"]
            _token_cache["token"] = token
            _token_cache["expires_at"] = now + 21600
            logger.info("鍛卞懕閫夊竵鐧诲綍鎴愬姛")
            return token
        else:
            logger.error(f"鍛卞懕閫夊竵鐧诲綍澶辫触: {data.get('message', data.get('error', '鏈煡閿欒'))}")
            return None
    except Exception as e:
        logger.error(f"鍛卞懕閫夊竵鐧诲綍寮傚父: {e}")
        return None


def fetch_signals() -> list:
    now = time.time()
    if _signal_cache["data"] and (now - _signal_cache["fetched_at"]) < CACHE_TTL:
        return _signal_cache["data"]
    token = _get_token()
    if not token:
        return []
    try:
        resp = _no_proxy_session.get(
            f"{GUAGUA_BASE_URL}/?data=1",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Cache-Control": "no-cache"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        signals = data.get("signals", [])
        if isinstance(signals, list):
            _signal_cache["data"] = signals
            _signal_cache["fetched_at"] = time.time()
            return signals
        return []
    except Exception as e:
        logger.error(f"鑾峰彇鍛卞懕閫夊竵淇″彿寮傚父: {e}")
        return []


def _parse_ts(ts_val):
    if not ts_val:
        return None
    try:
        ts = int(ts_val)
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return str(ts_val)


def normalize_signal(s):
    zone_map = {3: "楂樻祦鍔ㄦ€у尯", 2: "涓祦鍔ㄦ€у尯", 1: "浣庢祦鍔ㄦ€у尯", 0: "鏈煡"}
    level = s.get("liquidity_level", 0)
    return {
        "symbol": s.get("symbol", ""),
        "price": s.get("price"),
        "first_price": s.get("first_price") or s.get("firstPrice"),
        "gain": s.get("gain", 0),
        "alert_count": s.get("alert_count") or s.get("alertCount", 0),
        "vol_24h": s.get("vol24h", 0),
        "liquidity_level": level,
        "zone": zone_map.get(level, "鏈煡"),
        "first_timestamp": _parse_ts(s.get("first_timestamp") or s.get("firstTimestamp")),
        "updated_at": _parse_ts(s.get("updated_at") or s.get("updatedAt") or s.get("timestamp")),
        "ai_comment": s.get("ai_comment"),
    }


def get_signals_by_zone(zone_level=None):
    raw_signals = fetch_signals()
    if not raw_signals:
        return {"signals": [], "high": [], "mid": [], "low": [], "stats": {}}
    normalized = [normalize_signal(s) for s in raw_signals]
    normalized.sort(key=lambda x: x.get("gain", 0), reverse=True)
    result = {
        "signals": normalized,
        "high": [s for s in normalized if s["liquidity_level"] == 3],
        "mid": [s for s in normalized if s["liquidity_level"] == 2],
        "low": [s for s in normalized if s["liquidity_level"] == 1],
        "stats": {
            "total": len(normalized),
            "high_count": sum(1 for s in normalized if s["liquidity_level"] == 3),
            "mid_count": sum(1 for s in normalized if s["liquidity_level"] == 2),
            "low_count": sum(1 for s in normalized if s["liquidity_level"] == 1),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }
    if zone_level is not None:
        zone_map = {3: "high", 2: "mid", 1: "low"}
        key = zone_map.get(zone_level, "signals")
        result["filtered"] = result[key]
    return result


def fetch_posts(limit=10):
    token = _get_token()
    if not token:
        return []
    try:
        resp = _no_proxy_session.get(
            f"{GUAGUA_BASE_URL}/posts?limit={limit}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        posts = resp.json()
        return posts if isinstance(posts, list) else []
    except Exception as e:
        logger.error(f"鑾峰彇鍛卞懕閫夊竵甯栧瓙寮傚父: {e}")
        return []