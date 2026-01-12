#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SSE (Server-Sent Events) 实时价格推送服务
"""
import json
import logging
import time
import threading
from queue import Queue, Empty
from typing import Set, Dict, Any
from datetime import datetime

import redis
from flask import Response, stream_with_context

logger = logging.getLogger(__name__)


class PriceBroadcaster:
    """价格广播器 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._clients: Set[Queue] = set()
        self._redis_client = None
        self._subscriber_thread = None
        self._running = False

    def start(self, redis_host='localhost', redis_port=6379):
        """启动广播器"""
        if self._running:
            return

        try:
            # 连接 Redis
            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )

            # 启动订阅线程
            self._running = True
            self._subscriber_thread = threading.Thread(
                target=self._subscribe_redis,
                daemon=True
            )
            self._subscriber_thread.start()

            logger.info("价格广播器已启动")

        except Exception as e:
            logger.error(f"启动价格广播器失败: {e}")
            self._running = False

    def stop(self):
        """停止广播器"""
        self._running = False
        if self._subscriber_thread:
            self._subscriber_thread.join(timeout=5)
        logger.info("价格广播器已停止")

    def _subscribe_redis(self):
        """订阅 Redis 价格更新"""
        try:
            pubsub = self._redis_client.pubsub()
            pubsub.subscribe('price_updates')

            logger.info("Redis 价格订阅已启动")

            while self._running:
                try:
                    message = pubsub.get_message(timeout=5)
                    if message and message['type'] == 'message':
                        data = json.loads(message['data'])
                        self._broadcast(data)

                except Exception as e:
                    logger.error(f"Redis 订阅错误: {e}")

        except Exception as e:
            logger.error(f"Redis 订阅线程错误: {e}")

    def add_client(self, queue: Queue):
        """添加客户端"""
        self._clients.add(queue)
        logger.debug(f"客户端已连接, 当前连接数: {len(self._clients)}")

    def remove_client(self, queue: Queue):
        """移除客户端"""
        self._clients.discard(queue)
        logger.debug(f"客户端已断开, 当前连接数: {len(self._clients)}")

    def _broadcast(self, data: Dict[str, Any]):
        """广播价格到所有客户端"""
        # 发送到所有连接的客户端
        dead_clients = set()

        for client_queue in self._clients:
            try:
                client_queue.put_nowait(data)
            except:
                dead_clients.add(client_queue)

        # 清理断开的客户端
        for client in dead_clients:
            self.remove_client(client)

    def broadcast_price(self, symbol: str, price: float, change_24h: float = None):
        """广播价格更新"""
        data = {
            'symbol': symbol,
            'price': price,
            'change24h': change_24h,  # 使用驼峰命名,方便前端处理
            'timestamp': datetime.now().isoformat()
        }

        # 发布到 Redis
        if self._redis_client:
            try:
                self._redis_client.publish(
                    'price_updates',
                    json.dumps(data)
                )
            except Exception as e:
                logger.error(f"Redis 发布失败: {e}")

        # 直接广播到本地客户端
        self._broadcast(data)


# 全局广播器实例
_broadcaster = None


def get_price_broadcaster() -> PriceBroadcaster:
    """获取价格广播器实例"""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = PriceBroadcaster()
    return _broadcaster
