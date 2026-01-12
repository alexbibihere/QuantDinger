"""
TradingView Watchlist登录API路由
支持使用TradingView账号登录并获取关注列表
"""
from flask import Blueprint, request, jsonify
from app.services.tradingview_watchlist_login import TradingViewWatchlistLogin
from app.utils.logger import get_logger
from typing import Dict, Any

logger = get_logger(__name__)

tradingview_login_bp = Blueprint('tradingview_login', __name__)


@tradingview_login_bp.route('/login', methods=['POST'])
def login_and_get_watchlist():
    """
    登录TradingView并获取关注列表

    请求体:
    {
        "username": "tradingview用户名或邮箱",
        "password": "tradingview密码",
        "list_name": "关注列表名称(可选)"
    }

    返回:
    {
        "success": true,
        "count": 15,
        "data": [...]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        username = data.get('username')
        password = data.get('password')
        list_name = data.get('list_name')

        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        logger.info(f"收到TradingView登录请求: {username}")

        # 创建服务实例
        service = TradingViewWatchlistLogin(username, password)

        # 登录
        if not service.login(headless=True):
            return jsonify({
                'success': False,
                'error': '登录失败,请检查用户名和密码'
            }), 401

        # 获取关注列表
        watchlist = service.get_watchlist(list_name)

        logger.info(f"成功获取 {len(watchlist)} 个币种")

        return jsonify({
            'success': True,
            'count': len(watchlist),
            'data': watchlist,
            'source': 'TradingView Watchlist'
        })

    except Exception as e:
        logger.error(f"登录获取watchlist失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@tradingview_login_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    """
    获取TradingView默认crypto watchlist (无需登录)

    查询参数:
    - limit: 限制返回数量 (可选)

    返回:
    {
        "success": true,
        "count": 15,
        "data": [...]
    }
    """
    try:
        limit = request.args.get('limit', type=int)

        logger.info("获取TradingView默认crypto watchlist")

        # 创建服务实例(不登录)
        service = TradingViewWatchlistLogin()

        # 获取默认watchlist
        watchlist = service.get_watchlist()

        if limit and limit > 0:
            watchlist = watchlist[:limit]

        logger.info(f"返回 {len(watchlist)} 个币种")

        return jsonify({
            'success': True,
            'count': len(watchlist),
            'data': watchlist,
            'source': 'TradingView Default Crypto Watchlist'
        })

    except Exception as e:
        logger.error(f"获取watchlist失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@tradingview_login_bp.route('/test', methods=['POST'])
def test_login():
    """
    测试TradingView登录 (不获取watchlist)

    请求体:
    {
        "username": "tradingview用户名或邮箱",
        "password": "tradingview密码"
    }

    返回:
    {
        "success": true,
        "message": "登录成功"
    }
    """
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        logger.info(f"测试TradingView登录: {username}")

        service = TradingViewWatchlistLogin(username, password)

        if service.login(headless=True):
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '登录失败'
            }), 401

    except Exception as e:
        logger.error(f"测试登录失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500
