"""
Market API routes (local-only).
Provides watchlist, market metadata, symbol search, and pricing helpers for the frontend.
"""
from flask import Blueprint, request, jsonify
import traceback
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.kline import KlineService
from app.utils.logger import get_logger
from app.utils.cache import CacheManager
from app.utils.db import get_db_connection
from app.utils.config_loader import load_addon_config
from app.data.market_symbols_seed import (
    get_hot_symbols as seed_get_hot_symbols,
    search_symbols as seed_search_symbols,
    get_symbol_name as seed_get_symbol_name
)
from app.services.symbol_name import resolve_symbol_name

logger = get_logger(__name__)

market_bp = Blueprint('market', __name__)
kline_service = KlineService()
cache = CacheManager()

# 线程池用于并行获取价格
executor = ThreadPoolExecutor(max_workers=10)

DEFAULT_USER_ID = 1

def _now_ts() -> int:
    return int(time.time())

def _normalize_symbol(symbol: str) -> str:
    return (symbol or '').strip().upper()

def _ensure_watchlist_table():
    # Table is created by db schema init; this is only a sanity hook.
    return True

@market_bp.route('/config', methods=['GET'])
def get_public_config():
    """
    Public config for frontend (local mode).
    Mirrors the old PHP `/addons/quantdinger/index/getConfig` shape.
    """
    try:
        cfg = load_addon_config()
        models = (cfg.get('ai', {}) or {}).get('models')
        if not isinstance(models, dict) or not models:
            # Fallback defaults (offline friendly)
            models = {
                # Keep some legacy defaults
                'openai/gpt-4o': 'GPT-4o',

                # Unified frontend model list (OpenRouter-style ids)
                'x-ai/grok-code-fast-1': 'xAI: Grok Code Fast 1',
                'x-ai/grok-4-fast': 'xAI: Grok 4 Fast',
                'x-ai/grok-4.1-fast': 'xAI: Grok 4.1 Fast',
                'google/gemini-2.5-flash': 'Google: Gemini 2.5 Flash',
                'google/gemini-2.0-flash-001': 'Google: Gemini 2.0 Flash',
                'google/gemini-3-pro-preview': 'Google: Gemini 3 Pro Preview',
                'google/gemini-2.5-flash-lite': 'Google: Gemini 2.5 Flash Lite',
                'google/gemini-2.5-pro': 'Google: Gemini 2.5 Pro',
                'openai/gpt-4o-mini': 'OpenAI: GPT-4o-mini',
                'openai/gpt-5-mini': 'OpenAI: GPT-5 Mini',
                'openai/gpt-oss-120b': 'OpenAI: gpt-oss-120b',
                'deepseek/deepseek-v3.2': 'DeepSeek: DeepSeek V3.2',
                'minimax/minimax-m2': 'MiniMax: MiniMax M2',
                'anthropic/claude-sonnet-4': 'Anthropic: Claude Sonnet 4',
                'anthropic/claude-sonnet-4.5': 'Anthropic: Claude Sonnet 4.5',
                'anthropic/claude-opus-4.5': 'Anthropic: Claude Opus 4.5',
                'anthropic/claude-haiku-4.5': 'Anthropic: Claude Haiku 4.5',
                'z-ai/glm-4.6': 'Z.AI: GLM 4.6',
            }
        return jsonify({'code': 1, 'msg': 'success', 'data': {'models': models, 'qdt_cost': {}}})
    except Exception as e:
        logger.error(f"get_public_config failed: {str(e)}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500

@market_bp.route('/types', methods=['GET'])
def get_market_types():
    """Return supported market types for the add-watchlist modal."""
    desired_order = ['USStock', 'Crypto', 'Forex', 'Futures', 'HShare', 'AShare']
    order_rank = {v: i for i, v in enumerate(desired_order)}

    def _normalize_item(x):
        # Expected: {value: 'USStock', i18nKey: '...'}
        if isinstance(x, dict):
            v = (x.get('value') or '').strip()
            if not v:
                return None
            return {
                'value': v,
                'i18nKey': x.get('i18nKey') or f'dashboard.analysis.market.{v}'
            }
        if isinstance(x, str):
            v = x.strip()
            if not v:
                return None
            return {'value': v, 'i18nKey': f'dashboard.analysis.market.{v}'}
        return None

    def _sort_items(items):
        # Keep unknown market types after known ones, stable by original order.
        out = []
        for it in items or []:
            norm = _normalize_item(it)
            if norm:
                out.append(norm)
        out.sort(key=lambda it: (order_rank.get(it['value'], 10_000)))
        return out

    cfg = load_addon_config()
    data = (cfg.get('market', {}) or {}).get('types')

    # Normalize & force desired order (even if config overrides the list order).
    if isinstance(data, list) and data:
        data = _sort_items(data)
    else:
        data = _sort_items(desired_order)
    return jsonify({'code': 1, 'msg': 'success', 'data': data})


@market_bp.route('/menuFooterConfig', methods=['POST'])
def get_menu_footer_config():
    """
    Compatibility stub for old PHP `getMenuFooterConfig`.
    Frontend can also hardcode this locally; this endpoint remains for completeness.
    """
    data = {
        'contact': {
            'support_url': 'https://github.com/',
            'feature_request_url': 'https://github.com/',
            'email': 'support@example.com',
            'live_chat_url': 'https://github.com/'
        },
        'social_accounts': [
            {'name': 'GitHub', 'icon': 'github', 'url': 'https://github.com/'},
            {'name': 'X', 'icon': 'x', 'url': 'https://x.com/'}
        ],
        'legal': {
            'user_agreement': '',
            'privacy_policy': ''
        },
        'copyright': '© 2025-2026 QuantDinger'
    }
    return jsonify({'code': 1, 'msg': 'success', 'data': data})

@market_bp.route('/symbols/search', methods=['POST'])
def search_symbols():
    """
    Lightweight symbol search.
    In local-only mode we keep this simple; frontend allows manual input when no results.
    """
    try:
        data = request.get_json() or {}
        market = (data.get('market') or '').strip()
        keyword = (data.get('keyword') or '').strip().upper()
        limit = int(data.get('limit') or 20)

        if not market or not keyword:
            return jsonify({'code': 1, 'msg': 'success', 'data': []})

        out = seed_search_symbols(market=market, keyword=keyword, limit=limit)
        return jsonify({'code': 1, 'msg': 'success', 'data': out})
    except Exception as e:
        logger.error(f"search_symbols failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': []}), 500

@market_bp.route('/symbols/hot', methods=['POST'])
def get_hot_symbols():
    """Return a small curated hot list per market (local-only)."""
    try:
        data = request.get_json() or {}
        market = (data.get('market') or '').strip()
        limit = int(data.get('limit') or 10)
        hot = seed_get_hot_symbols(market=market, limit=limit)
        return jsonify({'code': 1, 'msg': 'success', 'data': hot})
    except Exception as e:
        logger.error(f"get_hot_symbols failed: {str(e)}")
        return jsonify({'code': 0, 'msg': str(e), 'data': []}), 500

@market_bp.route('/watchlist/get', methods=['POST'])
def get_watchlist():
    """Get local watchlist for the single user."""
    try:
        _ensure_watchlist_table()
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                "SELECT id, market, symbol, name FROM qd_watchlist WHERE user_id = ? ORDER BY id DESC",
                (DEFAULT_USER_ID,)
            )
            rows = cur.fetchall() or []

            # Backfill display names for legacy rows (name empty or equals symbol).
            # This keeps UI consistent without requiring users to re-add items.
            for row in rows:
                try:
                    market = row.get('market')
                    symbol = row.get('symbol')
                    current_name = (row.get('name') or '').strip()
                    if not market or not symbol:
                        continue
                    if current_name and current_name != symbol:
                        continue
                    resolved = resolve_symbol_name(market, symbol) or seed_get_symbol_name(market, symbol)
                    if resolved and resolved != current_name:
                        row['name'] = resolved
                        cur.execute(
                            "UPDATE qd_watchlist SET name = ?, updated_at = ? WHERE user_id = ? AND market = ? AND symbol = ?",
                            (resolved, _now_ts(), DEFAULT_USER_ID, market, symbol)
                        )
                except Exception:
                    continue
            db.commit()
            cur.close()
        return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"get_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': []}), 500

@market_bp.route('/watchlist/add', methods=['POST'])
def add_watchlist():
    """Add a symbol to local watchlist (no credits/fees in local mode)."""
    try:
        data = request.get_json() or {}
        market = (data.get('market') or '').strip()
        symbol = _normalize_symbol(data.get('symbol'))
        name_in = (data.get('name') or '').strip()
        if not market or not symbol:
            return jsonify({'code': 0, 'msg': 'Missing market or symbol', 'data': None}), 400

        # Prefer frontend-provided name (search results), otherwise resolve via seed/public sources.
        resolved = resolve_symbol_name(market, symbol) or seed_get_symbol_name(market, symbol)
        name = name_in or resolved or symbol

        now = _now_ts()
        with get_db_connection() as db:
            cur = db.cursor()
            # Insert or ignore duplicates.
            cur.execute(
                "INSERT OR IGNORE INTO qd_watchlist (user_id, market, symbol, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (DEFAULT_USER_ID, market, symbol, name, now, now)
            )
            # If already exists, keep it fresh and sync name.
            cur.execute(
                "UPDATE qd_watchlist SET name = ?, updated_at = ? WHERE user_id = ? AND market = ? AND symbol = ?",
                (name, now, DEFAULT_USER_ID, market, symbol)
            )
            db.commit()
            cur.close()

        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"add_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500

@market_bp.route('/watchlist/remove', methods=['POST'])
def remove_watchlist():
    """Remove a symbol from watchlist. Frontend only passes symbol, so we delete across markets."""
    try:
        data = request.get_json() or {}
        symbol = _normalize_symbol(data.get('symbol'))
        if not symbol:
            return jsonify({'code': 0, 'msg': 'Missing symbol', 'data': None}), 400

        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                "DELETE FROM qd_watchlist WHERE user_id = ? AND symbol = ?",
                (DEFAULT_USER_ID, symbol)
            )
            db.commit()
            cur.close()
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"remove_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


def get_single_price(market: str, symbol: str) -> dict:
    """获取单个标的的价格数据"""
    try:
        # 先尝试从缓存获取（60秒缓存）
        cache_key = f"watchlist_price:{market}:{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.debug(f"Cache hit: {market}:{symbol}")
            return {
                'market': market,
                'symbol': symbol,
                'price': cached_data.get('price', 0),
                'change': cached_data.get('change', 0),
                'changePercent': cached_data.get('changePercent', 0)
            }
        
        # 获取最新的一根K线
        klines = kline_service.get_kline(market, symbol, '1D', 2)
        
        if klines and len(klines) > 0:
            latest = klines[-1]
            prev_close = klines[-2]['close'] if len(klines) > 1 else latest.get('open', 0)
            current_price = latest.get('close', 0)
            
            change = round(current_price - prev_close, 4) if prev_close else 0
            change_percent = round(change / prev_close * 100, 2) if prev_close and prev_close > 0 else 0
            
            result = {
                'market': market,
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'changePercent': change_percent
            }
            
            # 缓存60秒
            cache.set(cache_key, result, 60)
            
            return result
        else:
            return {
                'market': market,
                'symbol': symbol,
                'price': 0,
                'change': 0,
                'changePercent': 0
            }
    except Exception as e:
        logger.error(f"Failed to fetch price {market}:{symbol} - {str(e)}")
        return {
            'market': market,
            'symbol': symbol,
            'price': 0,
            'change': 0,
            'changePercent': 0
        }


@market_bp.route('/watchlist/prices', methods=['POST'])
def get_watchlist_prices():
    """
    批量获取自选股价格
    
    请求体:
    {
        "watchlist": [
            {"market": "USStock", "symbol": "AAPL"},
            {"market": "Crypto", "symbol": "BTC"},
            ...
        ]
    }
    
    响应:
    {
        "code": 1,
        "msg": "success",
        "data": [
            {"market": "USStock", "symbol": "AAPL", "price": 150.0, "change": 1.5, "changePercent": 1.0},
            {"market": "Crypto", "symbol": "BTC", "price": 95000.0, "change": 1000, "changePercent": 1.05}
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 0,
                'msg': 'Request body is required',
                'data': []
            }), 400
        
        watchlist = data.get('watchlist', [])
        
        if not watchlist or not isinstance(watchlist, list):
            return jsonify({
                'code': 0,
                'msg': 'Invalid watchlist format',
                'data': []
            }), 400
        
        # logger.info(f"开始获取 {len(watchlist)} 个自选股价格数据")
        
        results = []
        
        # 使用线程池并行获取价格
        futures = {}
        for item in watchlist:
            market = item.get('market', '')
            symbol = item.get('symbol', '')
            
            if market and symbol:
                future = executor.submit(get_single_price, market, symbol)
                futures[future] = (market, symbol)
        
        # 收集结果（保持顺序）
        for future in as_completed(futures, timeout=30):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                market, symbol = futures[future]
                logger.error(f"Price fetch timed out or failed: {market}:{symbol} - {str(e)}")
                results.append({
                    'market': market,
                    'symbol': symbol,
                    'price': 0,
                    'change': 0,
                    'changePercent': 0
                })
        
        success_count = sum(1 for r in results if r.get('price', 0) > 0)
        # logger.info(f"批量获取完成，成功: {success_count}/{len(results)}")
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Batch watchlist price fetch failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 0,
            'msg': f'Failed: {str(e)}',
            'data': []
        }), 500


@market_bp.route('/price', methods=['GET'])
def get_price():
    """
    获取单个标的价格
    
    参数:
        market: 市场类型
        symbol: 交易标的
    """
    try:
        market = request.args.get('market', '')
        symbol = request.args.get('symbol', '')
        
        if not market or not symbol:
            return jsonify({
                'code': 0,
                'msg': 'Missing market or symbol parameter(s)',
                'data': None
            }), 400
        
        result = get_single_price(market, symbol)
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch price: {str(e)}")
        return jsonify({
            'code': 0,
            'msg': f'Failed: {str(e)}',
            'data': None
        }), 500


@market_bp.route('/ticker', methods=['GET'])
def get_ticker():
    """
    获取市场行情数据 (GET接口，用于测试)

    参数:
        symbol: 交易对符号，如 BTCUSDT
    """
    try:
        symbol = request.args.get('symbol', '')
        if not symbol:
            return jsonify({
                'code': 0,
                'msg': 'Missing symbol parameter',
                'data': None
            }), 400

        # 默认使用Crypto市场
        result = get_single_price('Crypto', symbol)

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"get_ticker failed: {str(e)}")
        return jsonify({
            'code': 0,
            'msg': f'Failed: {str(e)}',
            'data': None
        }), 500


@market_bp.route('/search', methods=['GET'])
def search_market():
    """
    搜索市场符号 (GET接口，用于测试)

    参数:
        query: 搜索关键词
        market: 市场类型 (可选，默认 Crypto)
    """
    try:
        query = request.args.get('query', '').upper()
        market = request.args.get('market', 'Crypto')
        limit = int(request.args.get('limit', 10))

        if not query:
            return jsonify({
                'code': 0,
                'msg': 'Missing query parameter',
                'data': []
            }), 400

        # 使用种子数据搜索
        results = seed_search_symbols(market=market, keyword=query, limit=limit)

        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': results
        })
    except Exception as e:
        logger.error(f"search_market failed: {str(e)}")
        return jsonify({
            'code': 0,
            'msg': f'Failed: {str(e)}',
            'data': []
        }), 500


@market_bp.route('/stock/name', methods=['POST'])
def get_stock_name():
    """
    获取股票名称

    请求体:
    {
        "market": "USStock",
        "symbol": "AAPL"
    }

    响应:
    {
        "code": 1,
        "msg": "success",
        "data": {
            "name": "Apple Inc."
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 0,
                'msg': 'Request body is required',
                'data': None
            }), 400
        
        market = data.get('market', '')
        symbol = data.get('symbol', '')
        
        if not market or not symbol:
            return jsonify({
                'code': 0,
                'msg': 'Missing market or symbol parameter(s)',
                'data': None
            }), 400
        
        # 尝试从缓存获取（1天缓存）
        cache_key = f"stock_name:{market}:{symbol}"
        cached_name = cache.get(cache_key)
        
        if cached_name:
            logger.debug(f"Stock name cache hit: {market}:{symbol}")
            return jsonify({
                'code': 1,
                'msg': 'success',
                'data': {'name': cached_name}
            })
        
        # 根据不同市场获取股票名称
        stock_name = symbol  # 默认使用代码
        
        try:
            if market in ['USStock', 'AShare', 'HShare']:
                # 对于股票，尝试获取基本信息
                import yfinance as yf
                
                # 转换symbol格式
                if market == 'USStock':
                    yf_symbol = symbol
                elif market == 'AShare':
                    yf_symbol = symbol + '.SS' if symbol.startswith('6') else symbol + '.SZ'
                elif market == 'HShare':
                    # 港股需要补齐4位数字并添加.HK
                    hk_code = symbol.zfill(4)
                    yf_symbol = hk_code + '.HK'
                else:
                    yf_symbol = symbol
                
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                
                # 尝试获取名称
                stock_name = info.get('longName') or info.get('shortName') or symbol
                
            elif market == 'Crypto':
                # 加密货币，使用交易对格式
                if '/' in symbol:
                    stock_name = symbol
                else:
                    stock_name = f"{symbol}/USDT"
            
            elif market == 'Forex':
                # 外汇
                forex_names = {
                    'XAUUSD': '黄金',
                    'XAGUSD': '白银',
                    'EURUSD': '欧元/美元',
                    'GBPUSD': '英镑/美元',
                    'USDJPY': '美元/日元',
                    'AUDUSD': '澳元/美元',
                    'USDCAD': '美元/加元',
                    'USDCHF': '美元/瑞郎',
                }
                stock_name = forex_names.get(symbol, symbol)
            
            elif market == 'Futures':
                # 期货
                futures_names = {
                    'GC': '黄金期货',
                    'SI': '白银期货',
                    'CL': '原油期货',
                    'NG': '天然气期货',
                    'ZC': '玉米期货',
                    'ZW': '小麦期货',
                    'BTCUSDT': 'BTC永续合约',
                    'ETHUSDT': 'ETH永续合约',
                }
                stock_name = futures_names.get(symbol, symbol)
            
        except Exception as e:
            logger.warning(f"Failed to fetch stock name; falling back to symbol: {market}:{symbol} - {str(e)}")
            stock_name = symbol
        
        # 缓存1天
        cache.set(cache_key, stock_name, 86400)
        
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {'name': stock_name}
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch stock name: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'code': 0,
            'msg': f'Failed: {str(e)}',
            'data': None
        }), 500
