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
    from app.routes.aijiaoyi import aijiaoyi_bp
    from app.routes.sse import sse_bp
    from app.routes.gainer_stats import gainer_stats_bp

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
    app.register_blueprint(tradingview_bp, url_prefix='/api/tradingview')
    app.register_blueprint(tradingview_selenium_bp, url_prefix='/api/tradingview-selenium')
    app.register_blueprint(tradingview_login_bp, url_prefix='/api/tradingview-login')
    app.register_blueprint(tradingview_scanner_bp, url_prefix='/api/tradingview-scanner')
    app.register_blueprint(aijiaoyi_bp, url_prefix='/api/aijiaoyi')
    app.register_blueprint(sse_bp, url_prefix='/api/sse')
    app.register_blueprint(gainer_stats_bp, url_prefix='/api/gainer-stats')

