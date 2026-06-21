"""
Futures Gainers Ranking API routes.
Provides real-time futures gainers data from multiple exchanges (Binance, OKX).
Automatically records symbols to gainer history for tracking.

Change log:
  2026-05-23: Added today's change calculation (UTC 00:00 based) via klines API.
              Uses ThreadPoolExecutor for parallel klines requests (top 10 symbols only).
"""
from flask import Blueprint, request, jsonify
import subprocess
import json
import time
import os
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.logger import get_logger
from app.services.futures_gainers_history import get_futures_gainers_history

logger = get_logger(__name__)

# 禁用所有代理设置（Windows 系统代理可能干扰）
for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    if var in os.environ:
        del os.environ[var]

futures_gainers_bp = Blueprint('futures_gainers', __name__)
executor = ThreadPoolExecutor(max_workers=5)

# API endpoints
BINANCE_FUTURES_API = "https://testnet.binancefuture.com/fapi/v1/ticker/24hr"
BINANCE_KLINES_API = "https://testnet.binancefuture.com/fapi/v1/klines"
OKX_API = "https://www.okx.com/api/v5/market/tickers?instType=SWAP"
OKX_CANDLES_API = "https://www.okx.com/api/v5/market/candles"
CRYPTOBUBBLES_API = "https://cryptobubbles.net/backend/data/bubbles1000.usd.json"

# Number of top symbols to calculate today's change for (top 30 to ensure enough data)
TODAY_CHANGE_TOP_N = 30


def get_today_open_price(symbol, proxies):
    """
    获取合约今天的开盘价（UTC 0点的第一根1分钟K线开盘价）
    返回 (today_open_price, current_price) 或 None 失败
    """
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
        today_start_ms = int(today_start.timestamp() * 1000)

        resp = requests.get(
            BINANCE_KLINES_API,
            params={"symbol": symbol, "interval": "1m", "startTime": today_start_ms, "limit": 2},
            proxies=proxies,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'close'}
        )
        resp.raise_for_status()
        klines = resp.json()
        if klines and len(klines) > 0:
            today_open = float(klines[0][1])  # open price of first kline (UTC 00:00)
            current_price = float(klines[-1][4])  # close of last kline
            return today_open, current_price
        return None
    except Exception as e:
        logger.debug(f"Klines fetch failed for {symbol}: {e}")
        return None


def get_proxies():
    """从环境变量获取代理配置"""
    proxy_url = os.getenv('PROXY_URL')
    if proxy_url:
        return {'http': proxy_url, 'https': proxy_url}

    # 尝试其他代理环境变量，跳过 socks5 协议（requests 默认不支持）
    for key in ['HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY']:
        proxy_url = os.getenv(key)
        if proxy_url and not proxy_url.startswith('socks'):
            return {'http': proxy_url, 'https': proxy_url}

    # 默认使用本地代理
    return {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}


def get_binance_proxies():
    """获取Binance专用代理（必须使用代理）"""
    return get_proxies()


def get_okx_proxies():
    """获取OKX代理配置"""
    return {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}


def get_binance_futures_gainers(proxy=None):
    """获取币安U本位合约涨幅榜（同时返回24h涨跌幅和当天涨跌幅）"""
    try:
        # testnet可以直接访问，不需要代理
        proxies = None
        if proxy:
            proxies = {'http': proxy, 'https': proxy}
            logger.info(f"Fetching Binance with custom proxy: {proxy}")
        elif 'testnet' in BINANCE_FUTURES_API:
            # testnet直接访问，不使用代理
            proxies = None
            logger.info("Fetching Binance testnet (direct, no proxy)")
        else:
            # 正式环境需要代理
            proxy_url = os.getenv('PROXY_URL') or os.getenv('ALL_PROXY') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
            if proxy_url:
                proxies = {'http': proxy_url, 'https': proxy_url}
                logger.info(f"Fetching Binance futures with proxy: {proxy_url}")
            else:
                proxies = None
                logger.info("Fetching Binance futures (direct, no proxy)")

        # 使用 Python requests，禁用环境变量代理
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            BINANCE_FUTURES_API,
            proxies=proxies,
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'close'}
        )
        response.raise_for_status()
        data = response.json()

        # 筛选USDT合约并按24h涨幅排序取前N名
        usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)

        # 只取前 N 名并行计算当天涨跌幅
        top_candidates = sorted_pairs[:TODAY_CHANGE_TOP_N]
        today_open_map = {}

        # 用 ThreadPoolExecutor 并行请求 klines
        with ThreadPoolExecutor(max_workers=10)        as kline_executor:
            futures_map = {
                kline_executor.submit(get_today_open_price, item['symbol'], proxies): item['symbol']
                for item in top_candidates
            }
            for future in as_completed(futures_map):
                symbol = futures_map[future]
                try:
                    result = future.result()
                    if result:
                        today_open, current_price = result
                        if today_open > 0:
                            today_change = round(((current_price - today_open) / today_open) * 100, 2)
                        else:
                            today_change = 0
                        today_open_map[symbol] = {
                            'change_pct_today': today_change,
                            'today_open': str(today_open)
                        }
                except Exception as e:
                    logger.debug(f"Klines future failed for {symbol}: {e}")

        # 合并当天涨跌幅到数据中
        enriched_pairs = []
        for item in sorted_pairs:
            enriched = dict(item)
            today_info = today_open_map.get(item['symbol'], {})
            enriched['change_pct_today'] = today_info.get('change_pct_today', None)
            enriched['today_open'] = today_info.get('today_open', None)
            enriched_pairs.append(enriched)

        # 按当天涨跌幅重新排序（有当天数据的优先，无当天数据按24h排序）
        sorted_today = sorted(
            enriched_pairs,
            key=lambda x: (
                x['change_pct_today'] if x['change_pct_today'] is not None else float('-inf'),
                float(x['priceChangePercent'])
            ),
            reverse=True
        )

        # 自动记录到涨幅榜历史（只记录前10名）
        top_10_pairs = sorted_today[:10]
        _record_binance_gainers_to_history(top_10_pairs)

        return {
            'exchange': 'binance',
            'data': sorted_today,
            'timestamp': int(time.time())
        }
    except Exception as e:
        logger.error(f"Binance futures API error: {e}")
        return {
            'exchange': 'binance',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        }


def get_okx_today_open_price(symbol, proxies):
    """
    获取OKX合约今天的开盘价（UTC 0点日K线开盘价）
    返回 (today_open_price, current_price) 或 None
    """
    try:
        now = datetime.datetime.now(datetime.timezone.utc)

        resp = requests.get(
            OKX_CANDLES_API,
            params={"instId": symbol, "bar": "1Dutc", "limit": "2"},
            proxies=proxies,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'close'}
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get('code') != '0':
            return None
        candles = body.get('data', [])
        if not candles or len(candles) < 1:
            return None

        # candles[0] 是最新的日K线
        today_candle = candles[0]
        ts = int(today_candle[0])
        dt = datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc)
        if dt.date() != now.date():
            # 最新的日K线不是今天的（可能刚过UTC 0点）
            return None

        today_open = float(today_candle[1])
        current_price = float(today_candle[4])
        return today_open, current_price
    except Exception as e:
        logger.debug(f"OKX Klines fetch failed for {symbol}: {e}")
        return None


def get_okx_proxies():
    """获取OKX代理配置"""
    return {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}


def get_okx_futures_gainers():
    """获取OKX U本位合约涨幅榜（同时返回24h涨跌幅和当天涨跌幅）"""
    try:
        logger.info(f"Fetching OKX futures via requests + Clash proxy")
        proxies = get_okx_proxies()

        session = requests.Session()
        session.trust_env = False
        resp = session.get(
            OKX_API,
            proxies=proxies,
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'close'}
        )
        resp.raise_for_status()

        body = resp.json()
        if body.get('code') != '0':
            return {
                'exchange': 'okx',
                'error': f'OKX API error: {body.get("msg", "unknown")}',
                'data': [],
                'timestamp': int(time.time())
            }

        data = body.get('data', [])

        # 计算涨跌幅并排序
        for item in data:
            open24h = float(item.get('open24h', 0))
            last = float(item.get('last', 0))
            if open24h > 0:
                change_pct = ((last - open24h) / open24h) * 100
                item['change_pct'] = change_pct
            else:
                item['change_pct'] = 0

        # 按24h涨幅排序取前N名用于当天涨跌幅计算
        sorted_pairs = sorted(data, key=lambda x: x['change_pct'], reverse=True)
        top_candidates = sorted_pairs[:TODAY_CHANGE_TOP_N]

        # 用 ThreadPoolExecutor 并行请求日K线获取当天开盘价
        today_open_map = {}
        with ThreadPoolExecutor(max_workers=10) as kline_executor:
            futures_map = {
                kline_executor.submit(get_okx_today_open_price, item['instId'], proxies): item['instId']
                for item in top_candidates
            }
            for future in as_completed(futures_map):
                symbol = futures_map[future]
                try:
                    result = future.result()
                    if result:
                        today_open, current_price = result
                        if today_open > 0:
                            today_change = round(((current_price - today_open) / today_open) * 100, 2)
                        else:
                            today_change = 0
                        today_open_map[symbol] = {
                            'change_pct_today': today_change,
                            'today_open': str(today_open)
                        }
                except Exception as e:
                    logger.debug(f"OKX Klines future failed for {symbol}: {e}")

        # 合并当天涨跌幅到数据中
        enriched_pairs = []
        for item in sorted_pairs:
            enriched = dict(item)
            today_info = today_open_map.get(item['instId'], {})
            enriched['change_pct_today'] = today_info.get('change_pct_today', None)
            enriched['today_open'] = today_info.get('today_open', None)
            enriched_pairs.append(enriched)

        # 按当天涨跌幅重新排序（有当天数据的优先，无当天数据按24h排序）
        sorted_today = sorted(
            enriched_pairs,
            key=lambda x: (
                x['change_pct_today'] if x['change_pct_today'] is not None else float('-inf'),
                x['change_pct']
            ),
            reverse=True
        )

        # 自动记录到涨幅榜历史（只记录前10名）——用当天涨跌幅排序后的前10名
        top_10_pairs = sorted_today[:10]
        logger.info(f"准备调用记录函数，数据量: {len(top_10_pairs)}")
        _record_okx_gainers_to_history(top_10_pairs)

        return {
            'exchange': 'okx',
            'data': sorted_today,  # 返回按当天涨跌幅排序的数据给前端
            'timestamp': int(time.time())
        }
    except Exception as e:
        logger.error(f"OKX futures API error: {e}")
        return {
            'exchange': 'okx',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        }


def format_binance_item(item, hama_data=None):
    """格式化币安数据项（包含HAMA指标）"""
    result = {
        'symbol': item['symbol'],
        'price': item['lastPrice'],
        'change_pct': float(item['priceChangePercent']),
        'today_change_pct': item.get('change_pct_today'),  # 当天涨跌幅
        'today_open': item.get('today_open'),              # 当天开盘价
        'high_24h': item['highPrice'],
        'low_24h': item['lowPrice'],
        'volume_24h': item['quoteVolume'],
        'open_24h': item['openPrice']
    }

    # 添加HAMA指标数据
    if hama_data and item['symbol'] in hama_data:
        hama = hama_data[item['symbol']]
        result['hama'] = {
            'color': hama.get('hama_color'),
            'trend': hama.get('hama_trend'),
            'candle_close': hama.get('candle_close'),
            'ma': hama.get('ma'),
            'candle_ma_status': hama.get('candle_ma_status'),
            'bb_status': hama.get('bb_status'),
            'bb_upper': hama.get('bb_upper'),
            'bb_lower': hama.get('bb_lower'),
            'last_cross_type': hama.get('last_cross_type'),
            'last_cross_time': hama.get('last_cross_time')
        }

    return result


def format_okx_item(item):
    """格式化OKX数据项（包含当天涨跌幅）"""
    return {
        'symbol': item['instId'],
        'price': item['last'],
        'change_pct': round(item.get('change_pct', 0), 2),
        'today_change_pct': item.get('change_pct_today'),  # 当天涨跌幅
        'today_open': item.get('today_open'),              # 当天开盘价
        'high_24h': item['high24h'],
        'low_24h': item['low24h'],
        'volume_24h': item.get('volCcy24h', '0'),
        'open_24h': item.get('open24h', '0')
    }


def format_cryptobubbles_item(item):
    """格式化Crypto Bubbles数据项"""
    perf = item.get('performance', {})
    return {
        'symbol': item['symbol'],
        'name': item['name'],
        'slug': item['slug'],
        'price': item['price'],
        'marketcap': item.get('marketcap', 0),
        'volume': item.get('volume', 0),
        'change_pct_1h': perf.get('hour'),
        'change_pct_4h': perf.get('hour4'),
        'change_pct_24h': perf.get('day'),
        'change_pct_7d': perf.get('week'),
        'change_pct_30d': perf.get('month'),
        'rank': item.get('rank'),
        'dominance': item.get('dominance'),
        'exchange_prices': item.get('exchangePrices', {}),
        'image': f"https://cryptobubbles.net/backend/{item.get('image', '')}"
    }


def get_cryptobubbles_gainers(limit=30):
    """
    获取 Crypto Bubbles 涨幅榜数据（现货市场，基于 CoinGecko 数据）
    支持多种时间维度：1h, 4h, 24h, 7d, 30d
    """
    try:
        logger.info("Fetching Crypto Bubbles data")

        # Crypto Bubbles API 不需要代理，直接访问
        # 使用 http.client 直接发送请求，避免任何代理干扰
        import http.client
        import json
        import urllib.parse

        parsed_url = urllib.parse.urlparse(CRYPTOBUBBLES_API)
        host = parsed_url.netloc
        path = parsed_url.path

        logger.info(f"Requesting {CRYPTOBUBBLES_API} (direct connection via http.client)")

        # 使用 HTTPS 连接
        if parsed_url.scheme == 'https':
            conn = http.client.HTTPSConnection(host, timeout=30)
        else:
            conn = http.client.HTTPConnection(host, timeout=30)

        try:
            conn.request('GET', path, headers={
                'User-Agent': 'Mozilla/5.0',
                'Connection': 'close',
                'Accept': 'application/json'
            })
            response = conn.getresponse()
            data = json.loads(response.read().decode('utf-8'))
            logger.info(f"✅ Crypto Bubbles data fetched: {len(data)} items")

            return {
                'exchange': 'cryptobubbles',
                'data': data,
                'timestamp': int(time.time())
            }
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Crypto Bubbles API error in get_cryptobubbles_gainers: {e}, type={type(e).__name__}")
        return {
            'exchange': 'cryptobubbles',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        }


def _record_okx_gainers_to_history(gainers_data):
    """
    自动记录OKX涨幅榜数据到历史（使用数据库）

    Args:
        gainers_data: OKX涨幅榜数据列表
    """
    try:
        logger.info(f"开始准备记录OKX涨幅榜数据，共 {len(gainers_data)} 个币种")

        # 构造记录数据
        record_data = []
        for rank, item in enumerate(gainers_data, 1):
            # 只记录涨幅>0的币种
            change_pct = item.get('change_pct', 0)
            if change_pct > 0:
                record_data.append({
                    'symbol': item.get('instId'),
                    'price': float(item.get('last', 0)),
                    'change_percentage': change_pct,
                    'volume': float(item.get('volCcy24h', 0)),
                    'high_24h': float(item.get('high24h', 0)),
                    'low_24h': float(item.get('low24h', 0)),
                    'open_24h': float(item.get('open24h', 0)),
                    'rank': rank
                })

        logger.info(f"筛选后需记录 {len(record_data)} 个涨幅>0的币种")

        from app.services.futures_gainers_history import get_futures_gainers_history
        history_service = get_futures_gainers_history()
        history_service.batch_record(record_data, 'okx')
        logger.info(f"已记录 {len(record_data)} 个OKX涨幅榜币种到历史")
    except Exception as e:
        logger.error(f"记录OKX涨幅榜历史失败: {e}")


def _record_binance_gainers_to_history(gainers_data):
    """
    自动记录Binance涨幅榜数据到历史

    Args:
        gainers_data: Binance涨幅榜数据列表（带change_pct_today）
    """
    try:
        record_data = []
        for rank, item in enumerate(gainers_data, 1):
            change_pct = float(item.get('priceChangePercent', 0))
            if change_pct > 0:
                final_change = float(item.get('change_pct_today', item.get('priceChangePercent', 0)))
                record_data.append({
                    'symbol': item.get('symbol'),
                    'price': float(item.get('lastPrice', 0)),
                    'change_percentage': final_change,
                    'volume': float(item.get('quoteVolume', 0)),
                    'high_24h': float(item.get('highPrice', 0)),
                    'low_24h': float(item.get('lowPrice', 0)),
                    'open_24h': float(item.get('openPrice', 0)),
                    'rank': rank
                })

        from app.services.futures_gainers_history import get_futures_gainers_history
        history_service = get_futures_gainers_history()
        history_service.batch_record(record_data, 'binance')
        logger.info(f"已记录 {len(record_data)} 个Binance涨幅榜币种到历史")
    except Exception as e:
        logger.error(f"记录Binance涨幅榜历史失败: {e}")



def _record_cryptobubbles_to_history(gainers_data):
    """
    自动记录Crypto Bubbles涨幅榜数据到历史（只记录有Binance价格的币种，取前10名）

    Args:
        gainers_data: Crypto Bubbles数据列表
    """
    try:
        # 筛选有 Binance 价格的币种，按24h涨幅降序取前10
        binance_coins = [item for item in gainers_data
                         if item.get('exchangePrices', {}).get('binance') is not None]

        perf_key = 'day'  # 24h performance
        binance_coins.sort(key=lambda x: x.get('performance', {}).get(perf_key, -9999) or -9999, reverse=True)
        top10 = binance_coins[:10]

        record_data = []
        for rank, item in enumerate(top10, 1):
            change_pct = item.get('performance', {}).get(perf_key)
            if change_pct is not None and change_pct > 0:
                symbol = f"{item['symbol']}USDT"
                record_data.append({
                    'symbol': symbol,
                    'price': float(item.get('price', 0)),
                    'change_percentage': change_pct,
                    'volume': float(item.get('volume', 0)),
                    'high_24h': None,
                    'low_24h': None,
                    'open_24h': None,
                    'rank': rank
                })

        if record_data:
            from app.services.futures_gainers_history import get_futures_gainers_history
            history_service = get_futures_gainers_history()
            history_service.batch_record(record_data, 'cryptobubbles')
            logger.info(f"已记录 {len(record_data)} 个Crypto Bubbles涨幅榜币种到历史")
        else:
            logger.info("Crypto Bubbles无符合条件的涨幅币种需要记录")
    except Exception as e:
        logger.error(f"记录Crypto Bubbles涨幅榜历史失败: {e}")


@futures_gainers_bp.route('/futures-gainers/hama/<symbols>', methods=['GET'])
def get_batch_hama(symbols):
    """批量获取HAMA指标数据"""
    try:
        from app.services.hama_binance_calculator import get_hama_calculator
        calc = get_hama_calculator(use_futures=True)
        symbol_list = symbols.split(',')
        logger.info(f"批量计算HAMA: {len(symbol_list)} 个币种")
        results = calc.calculate_batch(symbol_list, interval='15m', max_workers=5)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        logger.error(f"批量计算HAMA失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@futures_gainers_bp.route('/futures-gainers/cryptobubbles', methods=['GET'])
def get_futures_gainers_cryptobubbles():
    """获取Crypto Bubbles涨幅榜"""
    try:
        limit = int(request.args.get('limit', 30))
        result = get_cryptobubbles_gainers(limit)

        # 自动记录到涨幅榜历史（只记录有 Binance 价格的币种，取前10名）
        _record_cryptobubbles_to_history(result.get('data', []))

        return jsonify(result)
    except Exception as e:
        logger.error(f"Crypto Bubbles error: {e}")
        return jsonify({
            'exchange': 'cryptobubbles',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        })


@futures_gainers_bp.route('/futures-gainers/binance', methods=['GET'])
def get_futures_gainers_binance():
    """获取Binance涨幅榜"""
    try:
        proxy = request.args.get('proxy')
        result = get_binance_futures_gainers(proxy)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Binance gainers error: {e}")
        return jsonify({
            'exchange': 'binance',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        })


@futures_gainers_bp.route('/futures-gainers/okx', methods=['GET'])
def get_futures_gainers_okx():
    """获取OKX涨幅榜"""
    try:
        result = get_okx_futures_gainers()
        return jsonify(result)
    except Exception as e:
        logger.error(f"OKX gainers error: {e}")
        return jsonify({
            'exchange': 'okx',
            'error': str(e),
            'data': [],
            'timestamp': int(time.time())
        })


@futures_gainers_bp.route('/futures-gainers/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'futures_gainers'})


@futures_gainers_bp.route('/futures-gainers/debug/hama-test', methods=['GET'])
def debug_hama_test():
    """调试端点：直接测试 HAMA 计算器"""
    import traceback
    try:
        from app.services.hama_binance_calculator import get_hama_calculator
        calc = get_hama_calculator(use_futures=True)
        result = calc.calculate_for_symbol('BTCUSDT', interval='15m')
        return jsonify({
            'success': True,
            'api_url': calc.base_url,
            'result': {
                'error': result.get('error'),
                'price': result.get('price'),
                'hama_color': result.get('hama_color'),
                'ma': result.get('ma')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
