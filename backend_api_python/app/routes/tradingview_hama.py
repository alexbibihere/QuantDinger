#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView HAMA指标读取API路由
使用Selenium模拟浏览器从TradingView读取HAMA指标
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Optional

from app.services.tradingview_hama_selenium import TradingViewHamaSelenium, load_cookies_from_config

logger = logging.getLogger(__name__)

tradingview_hama_bp = Blueprint('tradingview_hama', __name__)


@tradingview_hama_bp.route('/get-hama', methods=['POST'])
def get_hama_from_tradingview():
    """
    从TradingView获取HAMA指标

    POST /api/tradingview-hama/get-hama
    Body: {
        "symbol": "BTCUSDT",
        "interval": "15",  // 可选,默认15
        "headless": true,  // 可选,是否无头模式
        "cookies": {  // 可选,TradingView的cookies
            "sessionid": "xxx",
            "sessionid_sign": "xxx"
        }
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        interval = data.get('interval', '15')
        headless = data.get('headless', True)
        cookies = data.get('cookies')

        # 如果没有提供cookies,尝试从配置加载
        if not cookies:
            cookies = load_cookies_from_config()
            if cookies:
                logger.info("✅ 已从配置加载TradingView cookies")
            else:
                logger.warning("⚠️ 未提供cookies且配置文件中未找到,将以未登录状态访问")

        logger.info(f"开始从TradingView获取 {symbol} 的HAMA指标 (interval={interval})")

        # 创建Selenium服务实例
        service = TradingViewHamaSelenium(headless=headless, cookies=cookies)

        # 获取HAMA指标
        result = service.get_hama_from_tradingview(
            symbol=symbol,
            interval=interval,
            wait_for_load=10
        )

        if result:
            logger.info(f"✅ 成功从TradingView获取 {symbol} 的HAMA指标")
            return jsonify({
                'success': True,
                'message': '成功获取HAMA指标',
                'data': result
            })
        else:
            logger.error(f"❌ 从TradingView获取 {symbol} 的HAMA指标失败")
            return jsonify({
                'success': False,
                'message': '获取HAMA指标失败'
            }), 500

    except Exception as e:
        logger.error(f"获取HAMA指标异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tradingview_hama_bp.route('/get-price', methods=['POST'])
def get_price_from_tradingview():
    """
    从TradingView获取价格

    POST /api/tradingview-hama/get-price
    Body: {
        "symbol": "BTCUSDT",
        "headless": true,  // 可选
        "cookies": {}  // 可选
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        headless = data.get('headless', True)
        cookies = data.get('cookies')

        logger.info(f"开始从TradingView获取 {symbol} 的价格")

        # 创建Selenium服务实例
        service = TradingViewHamaSelenium(headless=headless, cookies=cookies)

        # 获取价格
        result = service.get_price_from_tradingview(symbol=symbol, wait_for_load=5)

        if result:
            logger.info(f"✅ 成功从TradingView获取 {symbol} 的价格: {result.get('price')}")
            return jsonify({
                'success': True,
                'message': '成功获取价格',
                'data': result
            })
        else:
            logger.error(f"❌ 从TradingView获取 {symbol} 的价格失败")
            return jsonify({
                'success': False,
                'message': '获取价格失败'
            }), 500

    except Exception as e:
        logger.error(f"获取价格异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tradingview_hama_bp.route('/with-custom-script', methods=['POST'])
def get_hama_with_custom_script():
    """
    使用自定义Pine Script从TradingView获取HAMA指标

    POST /api/tradingview-hama/with-custom-script
    Body: {
        "symbol": "BTCUSDT",
        "interval": "15",
        "hama_script": "indicator(...)",  // 可选,Pine Script代码
        "headless": true,
        "cookies": {}
    }
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({
                'success': False,
                'message': '请提供币种符号'
            }), 400

        interval = data.get('interval', '15')
        hama_script = data.get('hama_script')
        headless = data.get('headless', True)
        cookies = data.get('cookies')

        logger.info(f"开始使用自定义脚本从TradingView获取 {symbol} 的HAMA指标")

        # 创建Selenium服务实例
        service = TradingViewHamaSelenium(headless=headless, cookies=cookies)

        # 获取HAMA指标
        result = service.get_hama_with_custom_script(
            symbol=symbol,
            interval=interval,
            hama_script=hama_script,
            wait_for_load=10
        )

        if result:
            logger.info(f"✅ 成功从TradingView获取 {symbol} 的HAMA指标")
            return jsonify({
                'success': True,
                'message': '成功获取HAMA指标',
                'data': result
            })
        else:
            logger.error(f"❌ 从TradingView获取 {symbol} 的HAMA指标失败")
            return jsonify({
                'success': False,
                'message': '获取HAMA指标失败'
            }), 500

    except Exception as e:
        logger.error(f"获取HAMA指标异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@tradingview_hama_bp.route('/batch-get-hama', methods=['POST'])
def batch_get_hama():
    """
    批量从TradingView获取多个币种的HAMA指标

    POST /api/tradingview-hama/batch-get-hama
    Body: {
        "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "interval": "15",
        "headless": true,
        "cookies": {}
    }
    """
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])

        if not symbols:
            return jsonify({
                'success': False,
                'message': '请提供币种列表'
            }), 400

        interval = data.get('interval', '15')
        headless = data.get('headless', True)
        cookies = data.get('cookies')

        results = []
        errors = []

        logger.info(f"开始批量获取 {len(symbols)} 个币种的HAMA指标")

        for symbol in symbols:
            try:
                symbol = symbol.upper()
                logger.info(f"正在处理 {symbol}...")

                # 创建Selenium服务实例
                service = TradingViewHamaSelenium(headless=headless, cookies=cookies)

                # 获取HAMA指标
                result = service.get_hama_from_tradingview(
                    symbol=symbol,
                    interval=interval,
                    wait_for_load=8
                )

                if result:
                    results.append(result)
                    logger.info(f"✅ {symbol} 获取成功")
                else:
                    errors.append({'symbol': symbol, 'error': '获取失败'})
                    logger.warning(f"⚠️ {symbol} 获取失败")

            except Exception as e:
                errors.append({'symbol': symbol, 'error': str(e)})
                logger.error(f"❌ {symbol} 处理异常: {e}")

        logger.info(f"批量获取完成: 成功 {len(results)}, 失败 {len(errors)}")

        return jsonify({
            'success': True,
            'message': f'批量获取完成: 成功 {len(results)}, 失败 {len(errors)}',
            'data': {
                'results': results,
                'errors': errors,
                'total': len(symbols),
                'success_count': len(results),
                'error_count': len(errors)
            }
        })

    except Exception as e:
        logger.error(f"批量获取HAMA指标异常: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'批量获取失败: {str(e)}'
        }), 500


@tradingview_hama_bp.route('/cookies-info', methods=['GET'])
def get_cookies_info():
    """
    获取如何获取TradingView Cookies的说明

    GET /api/tradingview-hama/cookies-info
    """
    info = {
        'title': '如何获取TradingView Cookies',
        'description': '访问TradingView需要登录才能查看自定义指标和关注列表',
        'steps': [
            '1. 在浏览器中打开 https://cn.tradingview.com/',
            '2. 登录您的TradingView账号',
            '3. 按F12打开浏览器开发者工具',
            '4. 切换到 "Application" 或 "存储" 标签',
            '5. 在左侧找到 "Cookies" -> "https://cn.tradingview.com"',
            '6. 复制以下重要的cookies:',
            '   - sessionid',
            '   - sessionid_sign',
            '   - uid',
            '7. 将这些cookies保存到系统设置中'
        ],
        'example': {
            "cookies": {
                "sessionid": "您的sessionid值",
                "sessionid_sign": "您的sessionid_sign值",
                "uid": "您的uid值"
            }
        },
        'note': 'Cookies通常有过期时间,如果获取失败请重新获取'
    }

    return jsonify({
        'success': True,
        'data': info
    })
