#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA 双币种监控 API 路由
提供 BTCUSDT 和 ETHUSDT 的监控控制接口
"""

from flask import Blueprint, jsonify, request
from app.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint('hama_dual_monitor', __name__)


@bp.route('/api/dual-monitor/status', methods=['GET'])
def get_status():
    """
    获取双币种监控状态

    Returns:
        JSON: 监控状态信息
    """
    try:
        from app.services.hama_dual_monitor import get_dual_monitor

        monitor = get_dual_monitor()
        status = monitor.get_status()

        return jsonify({
            'success': True,
            'data': status
        })

    except Exception as e:
        logger.error(f"获取双币种监控状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/dual-monitor/start', methods=['POST'])
def start_monitor():
    """
    启动双币种监控

    Returns:
        JSON: 启动结果
    """
    try:
        from app.services.hama_dual_monitor import get_dual_monitor

        monitor = get_dual_monitor()

        if monitor.is_running:
            return jsonify({
                'success': True,
                'message': '双币种监控已在运行中',
                'data': monitor.get_status()
            })

        monitor.start()

        return jsonify({
            'success': True,
            'message': '双币种监控已启动',
            'data': monitor.get_status()
        })

    except Exception as e:
        logger.error(f"启动双币种监控失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/dual-monitor/stop', methods=['POST'])
def stop_monitor():
    """
    停止双币种监控

    Returns:
        JSON: 停止结果
    """
    try:
        from app.services.hama_dual_monitor import get_dual_monitor

        monitor = get_dual_monitor()

        if not monitor.is_running:
            return jsonify({
                'success': True,
                'message': '双币种监控未在运行'
            })

        monitor.stop()

        return jsonify({
            'success': True,
            'message': '双币种监控已停止'
        })

    except Exception as e:
        logger.error(f"停止双币种监控失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/dual-monitor/monitor-now', methods=['POST'])
def monitor_now():
    """
    立即执行一次监控

    Returns:
        JSON: 监控结果
    """
    try:
        from app.services.hama_dual_monitor import get_dual_monitor

        monitor = get_dual_monitor()
        results = monitor.monitor_now()

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"立即监控失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/dual-monitor/check-trend', methods=['POST'])
def check_trend():
    """
    检查指定币种的趋势状态

    Request Body:
        {
            "symbol": "BTCUSDT"
        }

    Returns:
        JSON: 趋势状态
    """
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT').upper()

        # 验证币种
        valid_symbols = ['BTCUSDT', 'ETHUSDT']
        if symbol not in valid_symbols:
            return jsonify({
                'success': False,
                'error': f'无效的币种，仅支持: {", ".join(valid_symbols)}'
            }), 400

        # 从数据库获取最新状态
        import sqlite3
        import os

        db_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'quantdinger.db'
        )
        db_path = os.path.abspath(db_path)

        if not os.path.exists(db_path):
            return jsonify({
                'success': True,
                'symbol': symbol,
                'status': 'no_data',
                'message': '暂无数据'
            })

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 查询最新状态
        cursor.execute('''
            SELECT hama_color, hama_trend, hama_value, price, monitored_at
            FROM hama_monitor_cache
            WHERE symbol = ?
            ORDER BY monitored_at DESC
            LIMIT 1
        ''', (symbol,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({
                'success': True,
                'symbol': symbol,
                'status': 'no_data',
                'message': '暂无数据'
            })

        # 查询上次邮件发送状态
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT hama_color, sent_at
            FROM email_send_log
            WHERE symbol = ? AND status = 'success'
            ORDER BY sent_at DESC
            LIMIT 1
        ''', (symbol,))

        email_row = cursor.fetchone()
        conn.close()

        last_email_color = email_row['hama_color'] if email_row else None
        last_email_time = email_row['sent_at'] if email_row else None

        # 判断是否需要发送邮件
        current_color = row['hama_color'] or ''
        should_send_email = False

        if last_email_color is None:
            # 从未发送过邮件
            should_send_email = current_color in ['green', 'red']
        elif last_email_color != current_color:
            # 颜色发生变化
            should_send_email = current_color in ['green', 'red']

        return jsonify({
            'success': True,
            'symbol': symbol,
            'status': 'ok',
            'data': {
                'hama_color': row['hama_color'],
                'hama_trend': row['hama_trend'],
                'hama_value': float(row['hama_value']) if row['hama_value'] else None,
                'price': float(row['price']) if row['price'] else None,
                'monitored_at': row['monitored_at'],
                'last_email_color': last_email_color,
                'last_email_time': last_email_time,
                'should_send_email': should_send_email
            }
        })

    except Exception as e:
        logger.error(f"检查趋势失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_dual_monitor_routes(app):
    """注册双币种监控路由"""
    app.register_blueprint(bp)
    logger.info("✅ 双币种监控 API 路由已注册")
