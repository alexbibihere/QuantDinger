"""
API 路由模块
"""
from flask import Flask


def register_routes(app: Flask):
    """注册所有 API 路由蓝图"""
    from app.routes.kline import kline_bp
    from app.routes.analysis import analysis_bp
    from app.routes.backtest import backtest_bp
    from app.routes.health import health_bp
    from app.routes.market import market_bp
    from app.routes.strategy import strategy_bp
    from app.routes.credentials import credentials_bp
    from app.routes.auth import auth_bp
    from app.routes.ai_chat import ai_chat_bp
    from app.routes.indicator import indicator_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.settings import settings_bp
    from app.routes.gainer_analysis import gainer_analysis_bp
    from app.routes.hama_monitor import hama_monitor_bp
    from app.routes.multi_exchange import multi_exchange_bp
    from app.routes.tradingview import tradingview_bp
    from app.routes.tradingview_selenium import tradingview_selenium_bp
    from app.routes.tradingview_login import tradingview_login_bp
    from app.routes.tradingview_scanner import tradingview_scanner_bp
    # from app.routes.aijiaoyi import aijiaoyi_bp  # 旧的爱交易蓝图，下面用新的
    from app.routes.sse import sse_bp
    from app.routes.gainer_stats import gainer_stats_bp
    from app.routes.tradingview_hama import tradingview_hama_bp
    from app.routes.tradingview_pyppeteer import tradingview_pyppeteer_bp
    from app.routes.tradingview_playwright import tradingview_playwright_bp
    from app.routes.hama_indicator import hama_bp
    app.register_blueprint(hama_bp, url_prefix='/api/hama-indicator')
    from app.routes.hama_vision import hama_vision_bp
    from app.routes.hama_ocr import hama_ocr_bp
    from app.routes.hama_market import hama_market_bp
    from app.routes.futures_gainers import futures_gainers_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/user')  # 兼容前端 /api/user/login
    app.register_blueprint(kline_bp, url_prefix='/api')  # /api/kline

    # 添加兼容性路由：/api/indicator/kline -> /api/kline
    from flask import url_for
    from werkzeug.exceptions import NotFound

    @app.route('/api/indicator/kline', methods=['GET', 'POST'])
    def kline_compatibility():
        """兼容性路由：将 /api/indicator/kline 转发到 kline_bp"""
        from app.routes.kline import get_kline
        return get_kline()

    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(backtest_bp, url_prefix='/api/backtest')  # 修复：回测接口应该是 /api/backtest
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(ai_chat_bp, url_prefix='/api/ai')
    app.register_blueprint(indicator_bp, url_prefix='/api/indicator')
    app.register_blueprint(strategy_bp, url_prefix='/api')
    app.register_blueprint(credentials_bp, url_prefix='/api/credentials')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(gainer_analysis_bp, url_prefix='/api/gainer-analysis')
    app.register_blueprint(hama_monitor_bp, url_prefix='/api/hama-monitor')
    app.register_blueprint(multi_exchange_bp, url_prefix='/api/multi-exchange')
    # from app.routes.tradingview_login import tradingview_login_bp
    # app.register_blueprint(tradingview_login_bp, url_prefix='/api/tradingview-login')
    # 已废弃：tradingview_login 使用 Selenium 浏览器登录 TV，已被 tv-bridge 替代

    app.register_blueprint(tradingview_scanner_bp, url_prefix='/api/tradingview-scanner')
    # app.register_blueprint(aijiaoyi_bp, url_prefix='/api/aijiaoyi')
    app.register_blueprint(sse_bp, url_prefix='/api/sse')
    app.register_blueprint(gainer_stats_bp, url_prefix='/api/gainer-stats')
    app.register_blueprint(tradingview_hama_bp, url_prefix='/api/tradingview-hama')
    app.register_blueprint(tradingview_pyppeteer_bp, url_prefix='/api/tradingview-pyppeteer')
    app.register_blueprint(tradingview_playwright_bp, url_prefix='/api/tradingview-playwright')
    app.register_blueprint(hama_vision_bp)
    app.register_blueprint(hama_ocr_bp)
    app.register_blueprint(hama_market_bp, url_prefix='/api/hama-market')
    app.register_blueprint(futures_gainers_bp, url_prefix='/api/futures')

    # 注册聪明钱路由（合约聪明钱）
    from app.routes.smart_money import smart_money_bp
    app.register_blueprint(smart_money_bp)

    # 注册链上聪明钱路由
    from app.routes.chain_smart_money import chain_smart_money_bp
    app.register_blueprint(chain_smart_money_bp)

    # 注册呱呱选币路由
    from app.routes.guagua_market import guagua_bp
    app.register_blueprint(guagua_bp)

    # 注册 AiCoin 开放 API 路由
    from app.routes.aicoin import aicoin_bp
    app.register_blueprint(aicoin_bp)

    # 注册 AiCoin 涨幅榜路由
    from app.routes.aicoin_gainers import aicoin_gainers_bp
    app.register_blueprint(aicoin_gainers_bp)

    # 注册爱交易涨幅榜路由
    from app.routes.aijiaoyi import aijiaoyi_gainers_bp
    app.register_blueprint(aijiaoyi_gainers_bp)

    # 注册爱交易涨幅榜 v2 路由（K线直连版）
    from app.routes.aijiaoyi_v2 import aijiaoyi_v2_bp
    app.register_blueprint(aijiaoyi_v2_bp)

    # 注册 CoinGecko 涨幅榜路由
    from app.routes.coingecko import coingecko_bp
    app.register_blueprint(coingecko_bp)

    # 注册 BrowserAct 路由
    from app.routes.hama_browseract import register_browseract_routes
    register_browseract_routes(app)

    # 注册双币种监控路由
    from app.routes.hama_dual_monitor import register_dual_monitor_routes
    register_dual_monitor_routes(app)

    # 注册 HAMA-TV 路由（通过 tv-bridge WebSocket 获取数据，替代 OCR）
    from app.routes.hama_tv import hama_tv_bp
    app.register_blueprint(hama_tv_bp)

    # 注册 HAMA 行情路由（原有 OCR/浏览器方式，前端 hama-market 已默认走 tv-bridge）
    # 原注册在 hama_market_bp 保留：第 79 行 app.register_blueprint(hama_market_bp, url_prefix='/api/hama-market')

    # 注册 TV 关注列表路由（登录 TV + 获取关注品种 + 截图）
    from app.routes.tv_watchlist import tv_watchlist_bp
    app.register_blueprint(tv_watchlist_bp)

    # 添加静态文件 Blueprint
    from app.routes.static_files import bp as static_files_bp
    app.register_blueprint(static_files_bp, url_prefix='')  # 注册在根路径
