"""
爱交易数据源 v2 - 币安永续合约当日涨幅榜
通过 rest-api K线接口直连，用 1h K线合成日线涨跌幅
"""
import logging
import time
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import requests

logger = logging.getLogger(__name__)

TOKEN = "f04995790b694cb3a895eefa8986ee54"
CANDLE_API = "https://rest-api.aijiaoyi.xyz/market/candle/get_since/v2"

BINANCE_PERP_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "TRXUSDT", "LINKUSDT", "DOTUSDT", "SUIUSDT",
    "PEPEUSDT", "LTCUSDT", "BCHUSDT", "NEARUSDT", "APTUSDT", "UNIUSDT",
    "ATOMUSDT", "OPUSDT", "ARBUSDT", "FILUSDT", "INJUSDT", "STXUSDT",
    "TAOUSDT", "SEIUSDT", "MATICUSDT", "AAVEUSDT", "MKRUSDT", "ETCUSDT",
    "XLMUSDT", "ALGOUSDT", "FLOWUSDT", "ICPUSDT", "EGLDUSDT", "RUNEUSDT",
    "AXSUSDT", "SANDUSDT", "MANAUSDT", "CHZUSDT", "GALAUSDT", "ENJUSDT",
    "CRVUSDT", "COMPUSDT", "YFIUSDT", "SUSHIUSDT", "SNXUSDT",
    "WIFUSDT", "PENDLEUSDT", "TIAUSDT", "JUPUSDT", "PYTHUSDT",
    "ONDOUSDT", "STRKUSDT", "ZROUSDT", "EIGENUSDT", "IOUSDT",
    "NOTUSDT", "DOGSUSDT", "HMSTRUSDT", "CATIUSDT",
    "BONKUSDT", "FLOKIUSDT", "SHIBUSDT", "WLDUSDT", "ORDIUSDT",
    "SATSUSDT", "1000PEPEUSDT",
    "FETUSDT", "AGIXUSDT", "OCEANUSDT",
    "RNDRUSDT", "ARUSDT", "LDOUSDT", "SSVUSDT", "BLURUSDT",
    "ALTUSDT", "ETHFIUSDT", "ENAUSDT", "OMUSDT", "TNSRUSDT",
    "WUSDT", "BEAMXUSDT", "DYDXUSDT", "IMXUSDT", "CFXUSDT",
    "KASUSDT", "FTMUSDT", "TONUSDT",
]

_cache = {"data": None, "ts": 0}
CACHE_TTL = 30

TIMEFRAME = "1h"
HOURS_LIMIT = 48


def calc_change_pct(candles: list) -> tuple:
    """
    用 1h K线合成日涨跌幅
    取昨天24h最后一根close为昨收，今天最后一根close为今收
    """
    if not candles or len(candles) < 2:
        return None, [], 0

    sorted_c = sorted(candles, key=lambda c: c.get("ts", 0))

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_ts = int(today_start.timestamp())
    yest_ts = int((today_start - datetime.timedelta(days=1)).timestamp())

    today_candles = [c for c in sorted_c if c.get("ts", 0) >= today_ts]
    yesterday_candles = [c for c in sorted_c if yest_ts <= c.get("ts", 0) < today_ts]

    if not today_candles or not yesterday_candles:
        logger.debug(f"calc: 今天{len(today_candles)}根, 昨天{len(yesterday_candles)}根, "
                      f"candle_ts范围={sorted_c[0].get('ts')}~{sorted_c[-1].get('ts')}, "
                      f"today_ts={today_ts}, yest_ts={yest_ts}")
        return None, [], 0

    y_close = yesterday_candles[-1].get("close")
    t_close = today_candles[-1].get("close")
    if y_close and y_close > 0 and t_close and t_close > 0:
        return round((t_close - y_close) / y_close * 100, 2), today_candles, y_close
    return None, [], 0


def fetch_single_symbol(symbol: str) -> Optional[dict]:
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = int((now - datetime.timedelta(hours=60)).timestamp())

    try:
        url = f"{CANDLE_API}?token={TOKEN}&symbol=BINANCE:{symbol}&timeframe={TIMEFRAME}&limit={HOURS_LIMIT}&ts={ts}"
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get("error", {}).get("code") != 0:
            return None

        candles = data.get("payload", {}).get("candles", [])
        if not candles:
            return None

        change_pct, today_candles, yest_close = calc_change_pct(candles)
        if change_pct is None:
            return None

        today_close = today_candles[-1].get("close", 0)

        return {
            "symbol": symbol,
            "symbol_short": symbol.replace("USDT", ""),
            "price": today_close,
            "prev_close": yest_close,
            "change_pct": change_pct,
            "high": max(c.get("high", 0) for c in today_candles) if today_candles else 0,
            "low": min(c.get("low", 0) for c in today_candles) if today_candles else 0,
            "open": today_candles[0].get("open", 0) if today_candles else 0,
            "vol": sum(c.get("vol", 0) for c in today_candles),
            "source": "aijiaoyi_v2",
        }
    except Exception as e:
        logger.debug(f"爱交易 {symbol} 失败: {e}")
        return None


def fetch_gainers(limit: int = 10) -> list:
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_single_symbol, sym): sym for sym in BINANCE_PERP_SYMBOLS}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception:
                pass

    seen = set()
    unique = []
    for r in sorted(results, key=lambda x: x.get("change_pct", 0), reverse=True):
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)

    top = unique[:limit]
    _cache["data"] = top
    _cache["ts"] = now
    return top
