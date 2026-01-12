"""
SSE 实时价格推送 API
"""
from flask import Blueprint, Response, stream_with_context, request
from queue import Queue, Empty
import logging
import json

from app.services.price_broadcaster import get_price_broadcaster
from app.utils.logger import get_logger

logger = get_logger(__name__)

sse_bp = Blueprint('sse', __name__)


@sse_bp.route('/prices')
def price_stream():
    """
    SSE 实时价格推送端点

    连接此端点可接收实时价格更新
    """
    def event_stream():
        client_queue = Queue()
        broadcaster = get_price_broadcaster()

        # 添加客户端到广播器
        broadcaster.add_client(client_queue)

        try:
            # 发送连接成功消息
            yield f"event: connected\ndata: {json.dumps({'message': '已连接到价格推送服务'})}\n\n"

            # 持续发送价格更新
            while True:
                try:
                    # 等待价格更新 (最多60秒)
                    price_data = client_queue.get(timeout=60)

                    # 发送 SSE 事件
                    yield f"event: price\ndata: {json.dumps(price_data)}\n\n"

                except Empty:
                    # 发送心跳,保持连接
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': __import__('time').time()})}\n\n"

        except GeneratorExit:
            logger.info("客户端断开连接")
        finally:
            # 清理客户端
            broadcaster.remove_client(client_queue)

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Connection": "keep-alive"
        }
    )


@sse_bp.route('/test-broadcast', methods=['POST'])
def test_broadcast():
    """
    测试广播价格

    请求体:
        {
            "symbol": "BTCUSDT",
            "price": 90000,
            "change_24h": 2.5
        }
    """
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol', 'BTCUSDT')
        price = data.get('price', 90000)
        change_24h = data.get('change_24h')

        broadcaster = get_price_broadcaster()
        broadcaster.broadcast_price(symbol, price, change_24h)

        return {
            'code': 1,
            'message': f'已广播价格: {symbol} = {price}'
        }

    except Exception as e:
        logger.error(f"测试广播失败: {e}")
        return {
            'code': 0,
            'message': str(e)
        }, 500


@sse_bp.route('/status')
def status():
    """获取 SSE 服务状态"""
    broadcaster = get_price_broadcaster()

    return {
        'code': 1,
        'data': {
            'running': broadcaster._running,
            'connected_clients': len(broadcaster._clients)
        }
    }
