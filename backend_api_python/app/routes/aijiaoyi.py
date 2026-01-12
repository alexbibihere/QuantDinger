#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爱交易(aijiaoyi.xyz) API路由
使用Selenium爬取加密货币数据
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Optional

logger = logging.getLogger(__name__)

aijiaoyi_bp = Blueprint('aijiaoyi', __name__)


@aijiaoyi_bp.route('/crypto-list', methods=['GET'])
def get_crypto_list():
    """
    获取加密货币列表

    GET /api/aijiaoyi/crypto-list?limit=50

    Args:
        limit: 限制返回数量(默认50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # 最多200个

        logger.info(f"正在获取爱交易加密货币列表, limit={limit}")

        from app.services.aijiaoyi_selenium import AijiaoyiSeleniumService

        service = AijiaoyiSeleniumService()
        crypto_list = service.get_crypto_list(limit=limit)

        if crypto_list:
            logger.info(f"✅ 成功获取 {len(crypto_list)} 个币种")

            return jsonify({
                'success': True,
                'count': len(crypto_list),
                'data': crypto_list
            })
        else:
            return jsonify({
                'success': False,
                'message': '未获取到数据'
            }), 500

    except Exception as e:
        logger.error(f"获取加密货币列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@aijiaoyi_bp.route('/top-gainers', methods=['GET'])
def get_top_gainers():
    """
    获取涨幅榜

    GET /api/aijiaoyi/top-gainers?limit=20

    Args:
        limit: 返回数量(默认20)
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 最多100个

        logger.info(f"正在获取爱交易涨幅榜, limit={limit}")

        from app.services.aijiaoyi_selenium import AijiaoyiSeleniumService

        service = AijiaoyiSeleniumService()
        gainers = service.get_top_gainers(limit=limit)

        if gainers:
            logger.info(f"✅ 成功获取涨幅榜 {len(gainers)} 个币种")

            return jsonify({
                'success': True,
                'count': len(gainers),
                'gainers': gainers
            })
        else:
            return jsonify({
                'success': False,
                'message': '未获取到涨幅榜数据'
            }), 500

    except Exception as e:
        logger.error(f"获取涨幅榜失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@aijiaoyi_bp.route('/login', methods=['POST'])
def login_and_get_data():
    """
    登录后获取数据(需要账号密码)

    POST /api/aijiaoyi/login
    Body:
        {
            "username": "your_username",
            "password": "your_password",
            "limit": 50
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        limit = data.get('limit', 50)

        if not username or not password:
            return jsonify({
                'success': False,
                'message': '缺少用户名或密码'
            }), 400

        logger.info(f"正在使用账号 {username} 登录爱交易...")

        from app.services.aijiaoyi_selenium import AijiaoyiSeleniumService

        service = AijiaoyiSeleniumService(username, password)

        # 尝试登录
        if not service.login(username, password):
            return jsonify({
                'success': False,
                'message': '登录失败,请检查用户名和密码'
            }), 401

        # 登录成功,获取数据
        crypto_list = service.get_crypto_list(limit=limit)

        if crypto_list:
            logger.info(f"✅ 登录成功,获取到 {len(crypto_list)} 个币种")

            return jsonify({
                'success': True,
                'message': '登录成功',
                'count': len(crypto_list),
                'data': crypto_list,
                'logged_in': True
            })
        else:
            return jsonify({
                'success': False,
                'message': '登录成功但未获取到数据'
            }), 500

    except Exception as e:
        logger.error(f"登录或获取数据失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500
