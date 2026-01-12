#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时价格获取和推送服务
"""
import logging
import asyncio
import json
import threading
import time
from typing import Dict, List
from datetime import datetime

import redis
import ccxt
import websockets

from app.services.price_broadcaster import get_price_broadcaster

logger = logging.getLogger(__name__)


class RealtimePriceService:
    """实时价格服务"""

    def __init__(self, redis_host='localhost', redis_port=6379):
        """
        初始化实时价格服务

        Args:
            redis_host: Redis 主机
            redis_port: Redis 端口
        """
        import os

        # 从环境变量读取 Redis 配置
        self.redis_host = os.getenv('REDIS_HOST', redis_host)
        self.redis_port = int(os.getenv('REDIS_PORT', redis_port))

        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=0,
            decode_responses=True
        )
        self.broadcaster = get_price_broadcaster()
        self._running = False
        self._ws_thread = None

    def start_binance_websocket(self, symbols: List[str] = None):
        """
        启动 Binance WebSocket 价格推送

        Args:
            symbols: 币种列表,如 ['BTCUSDT', 'ETHUSDT']
        """
        if self._running:
            return

        self._running = True

        # 如果没有指定币种,使用热门币种
        if not symbols:
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
                'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
                'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'ATOMUSDT'
            ]

        # 保存监控的币种列表,用于定期轮询
        self._monitored_symbols = symbols

        # 启动 WebSocket 线程
        self._ws_thread = threading.Thread(
            target=self._run_binance_websocket,
            args=(symbols,),
            daemon=True
        )
        self._ws_thread.start()

        logger.info(f"Binance WebSocket 已启动, 监控 {len(symbols)} 个币种")

        # 启动定期轮询线程 (每 10 秒轮询一次,提供更频繁的更新)
        self._polling_thread = threading.Thread(
            target=self._run_price_polling,
            daemon=True
        )
        self._polling_thread.start()
        logger.info("价格定期轮询已启动 (间隔: 10秒 - 提供接近实时的价格更新)")

    def stop(self):
        """停止 WebSocket"""
        self._running = False
        if self._ws_thread:
            self._ws_thread.join(timeout=5)
        logger.info("Binance WebSocket 已停止")

    def _run_binance_websocket(self, symbols: List[str]):
        """
        运行 Binance WebSocket (在独立线程中)

        Args:
            symbols: 币种列表
        """
        # 转换为小写格式
        streams = [s.lower().replace('usdt', 'usdt') for s in symbols]

        # 构建 Binance WebSocket URL
        symbols_str = '/'.join(streams)
        url = f"wss://stream.binance.com:9443/ws/{symbols_str}@ticker"

        logger.info(f"连接到 Binance WebSocket: {url}")

        # 使用 asyncio 运行 WebSocket
        asyncio.run(self._websocket_handler(url))

    async def _websocket_handler(self, url: str):
        """WebSocket 处理器"""
        retry_count = 0
        max_retries = 5

        while self._running and retry_count < max_retries:
            try:
                async with websockets.connect(url, ping_interval=20) as websocket:
                    logger.info("Binance WebSocket 已连接")
                    retry_count = 0  # 重置重试计数

                    while self._running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)

                            # 解析价格数据
                            if 'e' in data and data['e'] == '24hrTicker':
                                self._handle_ticker(data)
                            else:
                                # 调试: 记录非 ticker 消息
                                logger.info(f"收到非 ticker 消息: {data.get('e', 'unknown')}, 数据: {str(data)[:200]}")

                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket 连接已关闭")
                            break

            except Exception as e:
                logger.error(f"WebSocket 错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"重连中... ({retry_count}/{max_retries})")
                    await asyncio.sleep(5)

        logger.info("WebSocket 线程已退出")

    def _handle_ticker(self, ticker_data: Dict):
        """
        处理 24小时价格数据

        Args:
            ticker_data: Binance ticker 数据
        """
        try:
            symbol = ticker_data.get('s', '').upper()
            price = float(ticker_data.get('c', 0))  # 当前价格
            change_24h = float(ticker_data.get('P', 0))  # 24小时涨跌幅(%)

            if not symbol or not price:
                logger.debug(f"跳过无效数据: symbol={symbol}, price={price}")
                return

            # 调试日志: 记录每个价格更新 (使用 INFO 级别以便查看)
            logger.info(f"价格更新: {symbol} = {price} ({change_24h:.2f}%)")

            # 广播价格更新
            self.broadcaster.broadcast_price(symbol, price, change_24h)

            # 缓存到 Redis (1分钟过期)
            cache_key = f"price:{symbol}"
            price_data = {
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h,
                'timestamp': datetime.now().isoformat()
            }

            self.redis_client.setex(
                cache_key,
                60,  # 60秒过期
                json.dumps(price_data)
            )

        except Exception as e:
            logger.error(f"处理价格数据失败: {e}")

    def batch_broadcast_prices(self, symbols: List[str]):
        """
        批量广播价格 (通过 REST API)

        Args:
            symbols: 币种列表
        """
        try:
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'timeout': 10000
            })

            # 批量获取价格
            tickers = exchange.fetch_tickers(symbols)

            broadcast_count = 0
            for symbol, ticker in tickers.items():
                price = ticker.get('last', 0)
                change_24h = ticker.get('percentage', 0)

                if price:
                    # 转换 CCXT 格式 (BTC/USDT) 为 Binance 格式 (BTCUSDT)
                    symbol_binance = symbol.replace('/', '')
                    self.broadcaster.broadcast_price(symbol_binance, price, change_24h)
                    broadcast_count += 1
                    # 添加日志,显示批量广播的价格
                    logger.info(f"[批量] 价格更新: {symbol_binance} = {price} ({change_24h:.2f}%)")

            logger.info(f"已批量广播 {broadcast_count}/{len(symbols)} 个币种的价格")

        except Exception as e:
            logger.error(f"批量获取价格失败: {e}")

    def _run_price_polling(self):
        """
        定期轮询价格 (在独立线程中)
        补充 WebSocket 未推送的币种价格
        """
        polling_interval = 10  # 10 秒 - 更频繁的更新

        while self._running:
            try:
                # 等待指定间隔
                for _ in range(polling_interval):
                    if not self._running:
                        break
                    time.sleep(1)

                if not self._running:
                    break

                # 轮询所有监控的币种
                if hasattr(self, '_monitored_symbols') and self._monitored_symbols:
                    logger.info(f"开始定期轮询 {len(self._monitored_symbols)} 个币种的价格...")
                    self.batch_broadcast_prices(self._monitored_symbols)

            except Exception as e:
                logger.error(f"价格轮询错误: {e}")
                if self._running:
                    time.sleep(5)  # 出错后等待 5 秒再重试

        logger.info("价格轮询线程已退出")


# 全局服务实例
_realtime_price_service = None


def get_realtime_price_service() -> RealtimePriceService:
    """获取实时价格服务实例"""
    global _realtime_price_service
    if _realtime_price_service is None:
        _realtime_price_service = RealtimePriceService()
    return _realtime_price_service


def start_realtime_price_service(symbols: List[str] = None):
    """
    启动实时价格服务

    Args:
        symbols: 要监控的币种列表
    """
    service = get_realtime_price_service()

    # 启动价格广播器
    service.broadcaster.start()

    # 启动 Binance WebSocket
    if symbols:
        service.start_binance_websocket(symbols)

    return service
