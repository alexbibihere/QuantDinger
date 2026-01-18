"""
TradingView Scanner API路由
提供无需登录的大规模加密货币数据获取接口
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.services.tradingview_scanner_service import (
    TradingViewScannerAPI,
    get_top_perpetuals,
    get_default_watchlist,
    get_top_gainers
)
from app.services.tradingview_cache import get_cache_manager as get_tv_cache_manager_impl
from app import get_tv_cache_manager
from app.utils.logger import get_logger
from app import get_redis_client
from app.services.hama_calculator import calculate_hama_from_ohlcv
from app.services.screenshot_cache import get_screenshot_cache
import json
import os
import threading
import time

logger = get_logger(__name__)

tradingview_scanner_bp = Blueprint('tradingview_scanner', __name__)

# 关注列表缓存
_watchlist_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=5)  # 缓存5分钟
}

# HAMA 缓存 TTL (5分钟)
_HAMA_CACHE_TTL = 300

# 截图缓存 TTL (10分钟)
_SCREENSHOT_CACHE_TTL = 600

# 截图缓存 Worker 线程
_screenshot_worker_thread = None
_screenshot_worker_running = False


def _get_hama_from_cache(symbol: str) -> dict:
    """从 Redis 缓存获取 HAMA 状态"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return None

        cache_key = f"hama_status:{symbol}"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            logger.info(f"✅ {symbol} 从 Redis 缓存获取 HAMA 状态")
            return json.loads(cached_data)

        return None
    except Exception as e:
        logger.error(f"从 Redis 获取 HAMA 缓存失败: {e}")
        return None


def _set_hama_to_cache(symbol: str, hama_data: dict):
    """将 HAMA 状态存入 Redis 缓存"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return

        cache_key = f"hama_status:{symbol}"
        redis_client.setex(
            cache_key,
            _HAMA_CACHE_TTL,
            json.dumps(hama_data, ensure_ascii=False)
        )
        logger.info(f"✅ {symbol} HAMA 状态已缓存")
    except Exception as e:
        logger.error(f"设置 HAMA 缓存失败: {e}")


def _get_screenshot_from_cache(symbol: str, interval: str = '15m') -> str:
    """从数据库缓存获取截图 base64 数据 (优先数据库,备用Redis)"""
    try:
        # 优先从数据库获取
        screenshot_cache = get_screenshot_cache()
        cached_data = screenshot_cache.get_screenshot(symbol, interval)

        if cached_data and cached_data.get('image_base64'):
            logger.info(f"✅ {symbol} 从数据库缓存获取截图")
            return cached_data['image_base64']

        # 如果数据库没有,尝试从Redis获取 (兼容旧版本)
        redis_client = get_redis_client()
        if redis_client:
            cache_key = f"chart_screenshot:{symbol}:{interval}"
            cached_data = redis_client.get(cache_key)

            if cached_data:
                logger.info(f"✅ {symbol} 从 Redis 缓存获取截图 (备用)")
                # 将Redis数据迁移到数据库
                screenshot_cache.save_screenshot(symbol, interval, cached_data.decode('utf-8'))
                return cached_data.decode('utf-8')

        return None
    except Exception as e:
        logger.error(f"从缓存获取截图失败: {e}")
        return None


def _save_screenshot_to_cache(symbol: str, interval: str, image_base64: str,
                              file_size: int = None, screenshot_url: str = None) -> bool:
    """保存截图 base64 数据到数据库缓存 (同时保存到Redis作为快速缓存)"""
    try:
        # 保存到数据库 (永久存储,直到手动清理)
        screenshot_cache = get_screenshot_cache()
        success = screenshot_cache.save_screenshot(symbol, interval, image_base64, file_size, screenshot_url)

        if success:
            # 同时保存到Redis作为快速缓存 (TTL 10分钟)
            redis_client = get_redis_client()
            if redis_client:
                cache_key = f"chart_screenshot:{symbol}:{interval}"
                redis_client.setex(cache_key, _SCREENSHOT_CACHE_TTL, image_base64)
                logger.info(f"✅ {symbol} 截图已缓存到数据库 + Redis (TTL: {_SCREENSHOT_CACHE_TTL}秒)")
            else:
                logger.info(f"✅ {symbol} 截图已缓存到数据库")

        return success
    except Exception as e:
        logger.error(f"保存截图到缓存失败: {e}")
        return False


def _parse_cookie_string(cookie_string: str) -> list:
    """
    解析 cookie 字符串为 Playwright 所需的格式
    
    Args:
        cookie_string: 从 CLAUDE.md 中读取的 cookie 字符串
    
    Returns:
        格式化后的 cookie 列表
    """
    cookies = []
    for cookie_pair in cookie_string.split(';'):
        cookie_pair = cookie_pair.strip()
        if not cookie_pair:
            continue
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.tradingview.com',
                'path': '/',
                'expires': -1,
                'httpOnly': True,
                'secure': True
            })
    return cookies


def _get_tradingview_cookies() -> list:
    """
    从 CLAUDE.md 文件中获取 TradingView cookie
    
    Returns:
        格式化后的 cookie 列表
    """
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        claude_md_path = os.path.join(project_root, 'CLAUDE.md')
        
        with open(claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找 cookie 部分
        cookie_start = content.find('# cookie')
        if cookie_start == -1:
            logger.warning("CLAUDE.md 中未找到 cookie 部分")
            return []
        
        # 提取 cookie 字符串
        cookie_section = content[cookie_start:]
        cookie_lines = cookie_section.split('\n')
        cookie_string = ''
        for line in cookie_lines[1:]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('```'):
                cookie_string = line
                break
        
        if not cookie_string:
            logger.warning("CLAUDE.md 中未找到有效的 cookie 字符串")
            return []
        
        # 解析 cookie
        cookies = _parse_cookie_string(cookie_string)
        logger.info(f"✅ 从 CLAUDE.md 中加载了 {len(cookies)} 个 cookie")
        return cookies
    except Exception as e:
        logger.error(f"读取或解析 cookie 失败: {e}")
        return []


def _capture_and_cache_screenshot(symbol: str, interval: str = '15') -> tuple[bool, str | None]:
    """
    截图并缓存到 Redis (不使用 OCR,仅截图)
    """
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth.stealth import Stealth
        import base64
        import os

        logger.info(f"正在截取 {symbol} 图表...")

        # 转换 interval 格式: 15m -> 15, 1h -> 60, 1d -> 1D
        interval_mapping = {
            '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
            '1d': 'D', '1w': 'W', '1M': 'M'
        }
        tv_interval = interval_mapping.get(interval, interval)

        # 构建 TradingView 图表 URL - 使用 widget embed URL (不需要登录)
        # 格式: https://s.tradingview.com/widgetembed/?frameElementId=tradingview_76d87&symbol=BINANCE%3ABTCUSDT&interval=15
        chart_url = f"https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol=BINANCE:{symbol}&interval={tv_interval}&hidesidetoolbar=1&symboledit=1&saveimage=0&toolbarbg=f1f3f6&studies=%5B%5D&theme=light&style=1&timezone=Etc%2FUTC"

        # 截图路径 - 修改为保存到项目根目录的 screenshot 目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshot_dir = os.path.join(project_root, 'screenshot')
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{symbol}_{interval}_chart.png")
        logger.info(f"截图将保存到: {screenshot_path}")

        logger.info(f"TradingView Widget URL: {chart_url}")

        # 从 CLAUDE.md 获取 cookie
        cookies = _get_tradingview_cookies()

        # 使用 Playwright 直接截图,不初始化 OCR
        with sync_playwright() as p:
            # 配置代理
            proxy_url = os.environ.get('PROXY_URL')

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    f'--proxy-server={proxy_url}' if proxy_url else ''
                ]
            )

            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 设置 cookie
            if cookies:
                context.add_cookies(cookies)
                logger.info(f"✅ 已设置 {len(cookies)} 个 TradingView cookie")
            
            page = context.new_page()

            # 应用 stealth 模式
            stealth_config = Stealth()
            stealth_config.apply_stealth_sync(page)

            # 访问图表 - 使用更宽松的超时设置
            logger.info(f"正在加载 {symbol} 图表...")
            try:
                # 先等待 DOMContentLoaded,不等待所有资源加载
                page.goto(chart_url, timeout=90000, wait_until='domcontentloaded')

                # 等待图表容器出现
                logger.info(f"等待 {symbol} 图表容器加载...")
                try:
                    page.wait_for_selector('div[class*="chart-container"]', timeout=15000)
                except:
                    # 如果找不到 chart-container,等待任意 div 出现
                    logger.warning(f"{symbol} 未找到 chart-container,等待页面元素...")
                    page.wait_for_selector('body', timeout=10000)

                # 额外等待图表渲染完成 - 增加等待时间到15秒
                logger.info(f"等待 {symbol} 图表渲染...")
                page.wait_for_timeout(15000)

            except Exception as e:
                logger.warning(f"{symbol} 页面加载警告: {e},继续尝试截图...")
                # 即使等待失败也继续,尝试截图

            # 截图 - 截取页面右侧图表区域
            logger.info(f"截取 {symbol} 图表到: {screenshot_path}")

            try:
                # 先尝试截取完整页面,便于调试
                logger.info(f"截取 {symbol} 完整页面...")
                page.screenshot(path=screenshot_path, full_page=False)
                logger.info(f"✅ {symbol} 完整页面截图完成")
            except Exception as e:
                logger.error(f"{symbol} 截图失败: {e}")
                browser.close()
                return False

            browser.close()

        # 检查截图文件是否存在且有内容
        if not os.path.exists(screenshot_path):
            logger.error(f"{symbol} 截图文件不存在")
            return False

        file_size = os.path.getsize(screenshot_path)
        if file_size < 1000:  # 小于1KB认为截图失败
            logger.error(f"{symbol} 截图文件过小: {file_size} bytes")
            return False

        # 将截图转换为 base64
        with open(screenshot_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 保存到数据库 + Redis 缓存
        _save_screenshot_to_cache(symbol, interval, image_base64, file_size, chart_url)
        logger.info(f"✅ {symbol} 截图并缓存成功 (大小: {file_size} bytes)")
        return True

    except Exception as e:
        logger.error(f"截图并缓存失败: {e}", exc_info=True)
        return False


def _cache_all_gainers_screenshots():
    """缓存所有涨幅榜币种的截图"""
    try:
        logger.info("🚀 开始缓存涨幅榜所有币种截图...")

        # 获取涨幅榜前10
        gainers = get_top_gainers(limit=10)
        if not gainers:
            logger.error("❌ 获取涨幅榜数据失败")
            return

        logger.info(f"📊 涨幅榜币种数量: {len(gainers)}")

        # 为每个币种截图并缓存
        success_count = 0
        failed_count = 0

        for coin in gainers:
            symbol = coin.get('symbol')
            if not symbol:
                continue

            try:
                if _capture_and_cache_screenshot(symbol, '15m'):
                    success_count += 1
                else:
                    failed_count += 1

                # 避免请求过快,等待1秒
                time.sleep(1)

            except Exception as e:
                logger.error(f"处理 {symbol} 截图时出错: {e}")
                failed_count += 1

        logger.info(f"✅ 缓存完成 - 成功: {success_count}, 失败: {failed_count}")

    except Exception as e:
        logger.error(f"缓存所有截图失败: {e}", exc_info=True)


def _screenshot_worker():
    """截图缓存 Worker 线程 - 每10分钟刷新一次"""
    global _screenshot_worker_running

    logger.info("🔄 截图缓存 Worker 已启动")

    while _screenshot_worker_running:
        try:
            # 执行缓存
            _cache_all_gainers_screenshots()

            # 等待10分钟
            logger.info("⏰ 下次刷新将在10分钟后...")
            for _ in range(600):  # 10分钟 = 600秒
                if not _screenshot_worker_running:
                    break
                time.sleep(1)

        except Exception as e:
            logger.error(f"截图缓存 Worker 出错: {e}", exc_info=True)
            # 出错后等待1分钟再试
            for _ in range(60):
                if not _screenshot_worker_running:
                    break
                time.sleep(1)

    logger.info("🛑 截图缓存 Worker 已停止")


def start_screenshot_worker():
    """启动截图缓存 Worker"""
    global _screenshot_worker_thread, _screenshot_worker_running

    if _screenshot_worker_running:
        logger.warning("⚠️ 截图缓存 Worker 已经在运行")
        return

    _screenshot_worker_running = True
    _screenshot_worker_thread = threading.Thread(target=_screenshot_worker, daemon=True)
    _screenshot_worker_thread.start()
    logger.info("✅ 截图缓存 Worker 已启动")


def stop_screenshot_worker():
    """停止截图缓存 Worker"""
    global _screenshot_worker_running

    _screenshot_worker_running = False
    logger.info("🛑 截图缓存 Worker 停止信号已发送")


def _estimate_hama_status(coin_data: dict, use_cache: bool = True) -> dict:
    """
    空函数 - 已移除 HAMA 状态计算

    Args:
        coin_data: 币种数据
        use_cache: 是否使用缓存 (默认 True)

    Returns:
        空字典
    """
    # 不再计算 HAMA 状态,直接返回空字典
    return {}


def _estimate_hama_status_simple(coin_data: dict) -> dict:
    """
    基于价格数据简单估算 HAMA 状态 (备用方案)

    Args:
        coin_data: 币种数据

    Returns:
        HAMA 状态字典
    """
    change_pct = coin_data.get('change_percentage', 0)
    volume = coin_data.get('volume', 0)

    # 简单规则
    if change_pct > 3 and volume > 1000000:
        status = 'strong_uptrend'
        trend = 'up'
        color = 'green'
        confidence = 'low'  # 估算的置信度低
    elif change_pct > 1:
        status = 'uptrend'
        trend = 'up'
        color = 'green'
        confidence = 'low'
    elif change_pct < -3:
        status = 'strong_downtrend'
        trend = 'down'
        color = 'red'
        confidence = 'low'
    elif change_pct < -1:
        status = 'downtrend'
        trend = 'down'
        color = 'red'
        confidence = 'low'
    else:
        status = 'sideways'
        trend = 'neutral'
        color = 'gray'
        confidence = 'low'

    return {
        'status': status,
        'trend': trend,
        'color': color,
        'cross_signal': 'none',
        'confidence': confidence,
        'method': 'estimated',
        'timestamp': datetime.now().isoformat()
    }


def _redis_available():
    """检查Redis是否可用"""
    redis_client = get_redis_client()
    if not redis_client:
        return False
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def _redis_get(key):
    """从Redis获取数据"""
    if not _redis_available():
        return None
    try:
        redis_client = get_redis_client()
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Redis获取失败: {e}")
        return None


def _redis_set(key, data, ttl=300):
    """设置数据到Redis"""
    if not _redis_available():
        return False
    try:
        redis_client = get_redis_client()
        redis_client.setex(key, ttl, json.dumps(data))
        return True
    except Exception as e:
        logger.warning(f"Redis设置失败: {e}")
        return False


# 内存缓存 (备用,当Redis不可用时)
_top_gainers_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=3)
}

_perpetuals_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=5)
}

_watchlist_mem_cache = {
    'data': None,
    'timestamp': None,
    'duration': timedelta(minutes=5)
}


@tradingview_scanner_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    """
    获取默认关注列表 (带5分钟缓存)

    查询参数:
    - limit: 限制返回数量 (默认20)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 20,
        "data": [...],
        "cached": true
    }
    """
    global _watchlist_cache

    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 最多100个

        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'
        current_time = datetime.now()

        # 检查缓存
        if not force_refresh and _watchlist_cache['data'] is not None:
            cache_age = current_time - _watchlist_cache['timestamp']
            if cache_age < _watchlist_cache['duration']:
                logger.info(f"使用缓存的watchlist数据 (缓存时间: {cache_age.seconds}秒)")
                watchlist = _watchlist_cache['data'][:limit]

                return jsonify({
                    'success': True,
                    'count': len(watchlist),
                    'data': watchlist,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Default Watchlist (Cached)'
                })

        # 重新获取数据
        logger.info(f"获取默认关注列表, limit={limit}")

        # 获取完整数据并缓存
        full_watchlist = get_default_watchlist(limit=100)
        _watchlist_cache['data'] = full_watchlist
        _watchlist_cache['timestamp'] = current_time

        watchlist = full_watchlist[:limit]

        return jsonify({
            'success': True,
            'count': len(watchlist),
            'data': watchlist,
            'cached': False,
            'source': 'TradingView Default Watchlist'
        })

    except Exception as e:
        logger.error(f"获取默认关注列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/perpetuals', methods=['GET'])
def get_perpetuals():
    """
    获取币安永续合约列表 (使用Redis缓存)

    查询参数:
    - limit: 限制返回数量 (默认50)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 50,
        "data": [...],
        "cached": true
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # 最多200个

        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'
        current_time = datetime.now()

        # 获取币种级别缓存管理器
        tv_cache = get_tv_cache_manager() or get_tv_cache_manager_impl()

        # 优先使用币种级别 Redis 缓存
        if not force_refresh and tv_cache and tv_cache.is_available():
            try:
                # 获取所有已缓存的币种
                cached_symbols = tv_cache.get_all_cached_symbols()

                if cached_symbols and len(cached_symbols) > 0:
                    # 批量获取币种数据
                    cached_coins = tv_cache.get_coins(cached_symbols)

                    if cached_coins and len(cached_coins) > 0:
                        # 转换为列表
                        perpetuals = list(cached_coins.values())

                        # 按成交量排序
                        perpetuals.sort(key=lambda x: x.get('volume', 0), reverse=True)

                        # 限制返回数量
                        perpetuals = perpetuals[:limit]

                        logger.info(f"使用币种级别 Redis 缓存: {len(perpetuals)} 个币种")

                        return jsonify({
                            'success': True,
                            'count': len(perpetuals),
                            'data': perpetuals,
                            'cached': True,
                            'cache_age_seconds': 0,
                            'source': 'TradingView Perpetuals (Coin-level Redis Cache)'
                        })
            except Exception as e:
                logger.warning(f"读取币种级别缓存失败: {e}")

        # 检查内存缓存 (备用)
        if not force_refresh and _perpetuals_mem_cache['data'] is not None:
            cache_age = current_time - _perpetuals_mem_cache['timestamp']
            if cache_age < _perpetuals_mem_cache['duration']:
                logger.info(f"使用内存缓存的永续合约数据 (缓存时间: {cache_age.seconds}秒)")
                perpetuals = _perpetuals_mem_cache['data'][:limit]

                return jsonify({
                    'success': True,
                    'count': len(perpetuals),
                    'data': perpetuals,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Perpetuals (Memory Cache)'
                })

        # 重新获取数据
        logger.info(f"获取永续合约列表, limit={limit}")

        # 获取完整数据并缓存(最多200个)
        full_perpetuals = get_top_perpetuals(limit=200)

        # 存入币种级别 Redis 缓存
        try:
            if tv_cache and tv_cache.is_available():
                cached_count = tv_cache.set_coins(full_perpetuals, ttl=300)
                logger.info(f"永续合约数据已存入币种级别 Redis 缓存: {cached_count} 个币种")
            else:
                logger.warning("币种级别缓存管理器不可用")
        except Exception as e:
            logger.warning(f"存入币种级别 Redis 缓存失败: {e}")

        # 存入内存缓存
        _perpetuals_mem_cache['data'] = full_perpetuals
        _perpetuals_mem_cache['timestamp'] = current_time

        perpetuals = full_perpetuals[:limit]

        return jsonify({
            'success': True,
            'count': len(perpetuals),
            'data': perpetuals,
            'cached': False,
            'source': 'TradingView Perpetuals'
        })

    except Exception as e:
        logger.error(f"获取永续合约列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/top-gainers', methods=['GET'])
def get_gainers():
    """
    获取涨幅榜 (使用Redis缓存)

    查询参数:
    - limit: 限制返回数量 (默认20)
    - min_change: 最小涨跌幅百分比 (可选)
    - refresh: 强制刷新缓存 (默认false)

    返回:
    {
        "success": true,
        "count": 20,
        "data": [...],
        "cached": true
    }
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 最多100个

        min_change = request.args.get('min_change', type=float)
        force_refresh = request.args.get('refresh', 'false', type=str).lower() == 'true'

        current_time = datetime.now()

        # 获取币种级别缓存管理器
        tv_cache = get_tv_cache_manager() or get_tv_cache_manager_impl()

        # 优先使用币种级别 Redis 缓存
        if not force_refresh and tv_cache and tv_cache.is_available():
            try:
                # 获取所有已缓存的币种
                cached_symbols = tv_cache.get_all_cached_symbols()

                if cached_symbols and len(cached_symbols) > 0:
                    # 批量获取币种数据
                    cached_coins = tv_cache.get_coins(cached_symbols)

                    if cached_coins and len(cached_coins) > 0:
                        # 转换为列表
                        gainers = list(cached_coins.values())

                        # 按涨跌幅排序
                        gainers.sort(key=lambda x: x.get('change_percentage', 0), reverse=True)

                        # 应用过滤
                        if min_change is not None:
                            gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

                        # 限制返回数量
                        gainers = gainers[:limit]

                        logger.info(f"使用币种级别 Redis 缓存: {len(gainers)} 个币种")

                        return jsonify({
                            'success': True,
                            'count': len(gainers),
                            'data': gainers,
                            'cached': True,
                            'cache_age_seconds': 0,
                            'source': 'TradingView Scanner - Top Gainers (Coin-level Redis Cache)'
                        })
            except Exception as e:
                logger.warning(f"读取币种级别缓存失败: {e}")

        # 检查内存缓存 (备用)
        if not force_refresh and _top_gainers_mem_cache['data'] is not None:
            cache_age = current_time - _top_gainers_mem_cache['timestamp']
            if cache_age < _top_gainers_mem_cache['duration']:
                logger.info(f"使用内存缓存的涨幅榜数据 (缓存时间: {cache_age.seconds}秒)")
                gainers = _top_gainers_mem_cache['data'].copy()

                # 应用过滤
                if min_change is not None:
                    gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

                gainers = gainers[:limit]

                logger.info(f"使用内存缓存,准备为 {len(gainers)} 个币种添加 HAMA 状态...")

                # 添加 HAMA 状态字段 (使用 OCR 识别)
                for i, gainer in enumerate(gainers):
                    logger.info(f"正在为第 {i+1}/{len(gainers)} 个币种 {gainer.get('symbol')} 添加 HAMA 状态...")
                    hama_status = _estimate_hama_status(gainer)
                    gainer['hama_status'] = hama_status
                    logger.info(f"✅ {gainer.get('symbol')} HAMA 状态: {hama_status.get('status', 'N/A')}, 方法: {hama_status.get('method', 'N/A')}")

                return jsonify({
                    'success': True,
                    'count': len(gainers),
                    'data': gainers,
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds()),
                    'source': 'TradingView Scanner - Top Gainers (Memory Cache)'
                })

        # 缓存失效或强制刷新,重新获取数据
        logger.info(f"获取涨幅榜, limit={limit}, min_change={min_change}")

        gainers = get_top_gainers(limit=100)  # 获取更多然后过滤

        # 存入币种级别 Redis 缓存
        try:
            if tv_cache and tv_cache.is_available():
                cached_count = tv_cache.set_coins(gainers, ttl=180)
                logger.info(f"涨幅榜数据已存入币种级别 Redis 缓存: {cached_count} 个币种")
            else:
                logger.warning("币种级别缓存管理器不可用")
        except Exception as e:
            logger.warning(f"存入币种级别 Redis 缓存失败: {e}")

        # 存入内存缓存
        _top_gainers_mem_cache['data'] = gainers
        _top_gainers_mem_cache['timestamp'] = current_time

        # 应用过滤
        if min_change is not None:
            gainers = [g for g in gainers if g.get('change_percentage', 0) >= min_change]

        gainers = gainers[:limit]

        logger.info(f"重新获取数据,准备为 {len(gainers)} 个币种添加 HAMA 状态...")

        # 添加 HAMA 状态字段 (使用 OCR 识别)
        for i, gainer in enumerate(gainers):
            logger.info(f"正在为第 {i+1}/{len(gainers)} 个币种 {gainer.get('symbol')} 添加 HAMA 状态...")
            hama_status = _estimate_hama_status(gainer)
            gainer['hama_status'] = hama_status
            logger.info(f"✅ {gainer.get('symbol')} HAMA 状态: {hama_status.get('status', 'N/A')}, 方法: {hama_status.get('method', 'N/A')}")

        return jsonify({
            'success': True,
            'count': len(gainers),
            'data': gainers,
            'cached': False,
            'source': 'TradingView Scanner - Top Gainers'
        })

    except Exception as e:
        logger.error(f"获取涨幅榜失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/symbols', methods=['POST'])
def get_symbols_data():
    """
    获取指定币种的数据

    请求体:
    {
        "symbols": ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", ...]
    }

    返回:
    {
        "success": true,
        "count": 2,
        "data": [...]
    }
    """
    try:
        data = request.get_json()

        if not data or 'symbols' not in data:
            return jsonify({
                'success': False,
                'error': '请提供symbols列表'
            }), 400

        symbols = data['symbols']

        if not isinstance(symbols, list):
            return jsonify({
                'success': False,
                'error': 'symbols必须是数组'
            }), 400

        symbols = symbols[:100]  # 最多100个

        logger.info(f"获取指定币种数据, 数量={len(symbols)}")

        api = TradingViewScannerAPI()
        result = api.get_crypto_data(symbols)

        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'source': 'TradingView Scanner'
        })

    except Exception as e:
        logger.error(f"获取指定币种数据失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    获取统计信息

    返回:
    {
        "success": true,
        "data": {
            "total_perpetuals": 200,
            "top_gainers": [...]
        }
    }
    """
    try:
        logger.info("获取统计信息")

        # 获取一些统计数据
        api = TradingViewScannerAPI()

        # 获取前20个作为样本
        sample = api.get_default_watchlist(limit=20)

        # 计算统计
        if sample:
            avg_change = sum(c.get('change_percentage', 0) for c in sample) / len(sample)
            gainers_count = sum(1 for c in sample if c.get('change_percentage', 0) > 0)
            losers_count = sum(1 for c in sample if c.get('change_percentage', 0) < 0)

            stats_data = {
                'sample_size': len(sample),
                'avg_change': round(avg_change, 2),
                'gainers_count': gainers_count,
                'losers_count': losers_count,
                'top_gainer': max(sample, key=lambda x: x.get('change_percentage', 0)) if sample else None,
                'top_loser': min(sample, key=lambda x: x.get('change_percentage', 0)) if sample else None
            }
        else:
            stats_data = {}

        return jsonify({
            'success': True,
            'data': stats_data,
            'source': 'TradingView Scanner'
        })

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/chart-screenshot', methods=['GET'])
def get_chart_screenshot():
    """
    获取 TradingView 图表截图

    Parameters:
        symbol: 币种符号 (如 BTCUSDT)
        interval: 时间周期 (默认 15m)
        force_refresh: 强制刷新 (默认 false)

    Returns:
        JSON with screenshot base64 data
    """
    try:
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '15m')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        logger.info(f"正在获取 {symbol} 的图表截图... (force_refresh={force_refresh})")

        # 如果不是强制刷新,先尝试从缓存获取
        if not force_refresh:
            cached_image = _get_screenshot_from_cache(symbol, interval)
            if cached_image:
                logger.info(f"✅ {symbol} 从缓存获取截图成功")
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'interval': interval,
                    'image_base64': cached_image,
                    'content_type': 'image/png',
                    'cached': True
                })

        # 强制刷新或缓存未命中,实时截图
        if force_refresh:
            logger.info(f"🔄 {symbol} 强制刷新,正在实时截图...")
        else:
            logger.info(f"⚠️ {symbol} 缓存未命中,正在实时截图...")

        # 使用截图函数
        success = _capture_and_cache_screenshot(symbol, interval)

        if success:
            # 从缓存读取刚刚保存的截图
            cached_image = _get_screenshot_from_cache(symbol, interval)
            if cached_image:
                logger.info(f"✅ {symbol} 实时截图成功")
                return jsonify({
                    'success': True,
                    'symbol': symbol,
                    'interval': interval,
                    'image_base64': cached_image,
                    'content_type': 'image/png',
                    'cached': False
                })
            else:
                logger.error(f"❌ {symbol} 截图成功但缓存读取失败")
                return jsonify({
                    'success': False,
                    'error': '截图成功但缓存读取失败'
                }), 500
        else:
            logger.error(f"❌ {symbol} 截图失败")
            return jsonify({
                'success': False,
                'error': '截图失败'
            }), 500

    except Exception as e:
        logger.error(f"获取图表截图失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/screenshot-cache/stats', methods=['GET'])
def get_screenshot_cache_stats():
    """
    获取截图缓存统计信息

    Returns:
        JSON with cache statistics
    """
    try:
        screenshot_cache = get_screenshot_cache()
        stats = screenshot_cache.get_stats()

        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取截图缓存统计失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tradingview_scanner_bp.route('/screenshot-cache/cleanup', methods=['POST'])
def cleanup_screenshot_cache():
    """
    清理旧截图缓存

    Parameters:
        days: 保留天数 (默认 7)

    Returns:
        JSON with cleanup results
    """
    try:
        from flask import request
        data = request.get_json() or {}
        days = data.get('days', 7)

        screenshot_cache = get_screenshot_cache()
        deleted_count = screenshot_cache.cleanup_old_screenshots(days)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'已清理 {deleted_count} 条超过 {days} 天的截图'
        })
    except Exception as e:
        logger.error(f"清理截图缓存失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
