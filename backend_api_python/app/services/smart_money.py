"""
Binance Smart Money (聪明钱) 数据服务
调用 Binance 内部 API 获取合约聪明钱指标
"""
import requests
import time
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

SMART_MONEY_URL = "https://www.binance.com/bapi/futures/v1/public/future/smart-money/signal/overview"
CACHE_TTL = 600  # 10分钟缓存
_cache = {}

HEADERS = {
    'accept': 'application/json',
    'accept-language': 'zh-CN,zh;q=0.9',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'clienttype': 'web',
    'lang': 'zh-CN',
}


def get_proxies():
    """获取代理配置"""
    import os
    proxy_url = os.getenv('PROXY_URL') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
    if proxy_url:
        return {'http': proxy_url, 'https': proxy_url}
    return None


def get_smart_money_overview(symbol: str) -> Optional[dict]:
    """
    获取单个币种的聪明钱数据

    Returns:
        dict with fields:
        - symbol, ts, totalPositions, totalTraders, longShortRatio
        - longTraders, longTradersQty, longTradersAvgEntryPrice
        - shortTraders, shortTradersQty, shortTradersAvgEntryPrice
        - longWhales, longWhalesQty, longWhalesAvgEntryPrice
        - shortWhales, shortWhalesQty, shortWhalesAvgEntryPrice
        - longProfitTraders, shortProfitTraders
        - longProfitWhales, shortProfitWhales
        - 衍生字段: smartMoneyNotionalUsd, smartMoneyShareOfOI
    """
    global _cache

    # 检查缓存
    cached = _cache.get(symbol)
    if cached and time.time() - cached['fetched_at'] < CACHE_TTL:
        return cached['data']

    proxies = get_proxies()
    try:
        resp = requests.get(
            SMART_MONEY_URL,
            params={'symbol': symbol},
            headers=HEADERS,
            proxies=proxies,
            timeout=10
        )

        if resp.status_code != 200:
            logger.warning(f"Smart Money API 返回 {resp.status_code}: {resp.text[:200]}")
            return cached['data'] if cached else None

        data = resp.json()
        if data.get('code') != '000000' or not data.get('data'):
            logger.warning(f"Smart Money API 返回异常: {data.get('msg', '未知错误')}")
            return cached['data'] if cached else None

        raw = data['data']
        result = {
            'symbol': symbol,
            'ts': int(raw.get('updateTime', time.time() * 1000)),
            'totalPositions': _num(raw.get('totalPositions')),
            'totalTraders': int(raw.get('totalTraders', 0)),
            'longShortRatio': _num(raw.get('longShortRatio')),
            # 所有交易者
            'longTraders': int(raw.get('longTraders', 0)),
            'longTradersQty': _num(raw.get('longTradersQty')),
            'longTradersAvgEntryPrice': _num(raw.get('longTradersAvgEntryPrice')),
            'shortTraders': int(raw.get('shortTraders', 0)),
            'shortTradersQty': _num(raw.get('shortTradersQty')),
            'shortTradersAvgEntryPrice': _num(raw.get('shortTradersAvgEntryPrice')),
            # 鲸鱼 (top 20%)
            'longWhales': int(raw.get('longWhales', 0)),
            'longWhalesQty': _num(raw.get('longWhalesQty')),
            'longWhalesAvgEntryPrice': _num(raw.get('longWhalesAvgEntryPrice')),
            'shortWhales': int(raw.get('shortWhales', 0)),
            'shortWhalesQty': _num(raw.get('shortWhalesQty')),
            'shortWhalesAvgEntryPrice': _num(raw.get('shortWhalesAvgEntryPrice')),
            # 盈利计数
            'longProfitTraders': int(raw.get('longProfitTraders', 0)),
            'shortProfitTraders': int(raw.get('shortProfitTraders', 0)),
            'longProfitWhales': int(raw.get('longProfitWhales', 0)),
            'shortProfitWhales': int(raw.get('shortProfitWhales', 0)),
        }

        # 衍生计算
        result['longProfitPct'] = round(
            result['longProfitTraders'] / result['longTraders'] * 100, 1
        ) if result['longTraders'] > 0 else 0
        result['shortProfitPct'] = round(
            result['shortProfitTraders'] / result['shortTraders'] * 100, 1
        ) if result['shortTraders'] > 0 else 0

        result['whaleLongShortRatio'] = round(
            (result['longWhalesQty'] * result['longWhalesAvgEntryPrice']) /
            max(result['shortWhalesQty'] * result['shortWhalesAvgEntryPrice'], 1), 2
        ) if result['shortWhalesQty'] > 0 else 0

        # 缓存
        _cache[symbol] = {'data': result, 'fetched_at': time.time()}

        return result

    except requests.exceptions.Timeout:
        logger.warning(f"Smart Money API 超时: {symbol}")
        return cached['data'] if cached else None
    except Exception as e:
        logger.error(f"Smart Money API 错误: {e}")
        return cached['data'] if cached else None


def get_batch_smart_money(symbols: list, max_workers: int = 3) -> dict:
    """批量获取聪明钱数据"""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_smart_money_overview, sym): sym
            for sym in symbols
        }
        for future in as_completed(futures):
            sym = futures[future]
            try:
                data = future.result()
                if data:
                    results[sym] = data
            except Exception as e:
                logger.error(f"批量获取 {sym} 失败: {e}")

    return results


def _num(v) -> float:
    """安全转浮点"""
    try:
        n = float(v)
        return n if n == n else 0  # NaN check
    except (TypeError, ValueError):
        return 0
