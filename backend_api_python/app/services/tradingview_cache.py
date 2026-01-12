#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TradingView Scanner 币种级别 Redis 缓存管理
每个币种的数据独立缓存,便于定时任务增量更新
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TradingViewCacheManager:
    """TradingView Scanner Redis 缓存管理器 (币种级别)"""

    def __init__(self, redis_client=None, default_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            redis_client: Redis 客户端实例
            default_ttl: 默认缓存过期时间(秒),默认300秒(5分钟)
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.prefix = "tvscanner:coin:"  # 币种级别缓存前缀

    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis 不可用: {e}")
            return False

    def get_coin(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从 Redis 获取单个币种的数据

        Args:
            symbol: 币种符号,如 'BTCUSDT'

        Returns:
            币种数据或 None
        """
        if not self.is_available():
            return None

        try:
            key = f"{self.prefix}{symbol}"
            data = self.redis_client.get(key)

            if data:
                result = json.loads(data)
                logger.debug(f"Redis 缓存命中: {symbol}")
                return result

            return None

        except Exception as e:
            logger.error(f"Redis 获取失败 {symbol}: {e}")
            return None

    def set_coin(self, symbol: str, coin_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        设置单个币种的数据到 Redis

        Args:
            symbol: 币种符号,如 'BTCUSDT'
            coin_data: 币种数据
            ttl: 过期时间(秒),默认使用 default_ttl

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            key = f"{self.prefix}{symbol}"
            ttl = ttl or self.default_ttl

            # 添加缓存时间戳
            coin_data['cached_at'] = datetime.now().isoformat()

            self.redis_client.setex(key, ttl, json.dumps(coin_data))
            logger.debug(f"Redis 缓存已设置: {symbol} (TTL={ttl}秒)")
            return True

        except Exception as e:
            logger.error(f"Redis 设置失败 {symbol}: {e}")
            return False

    def get_coins(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取多个币种的数据

        Args:
            symbols: 币种符号列表

        Returns:
            币种数据字典 {symbol: coin_data}
        """
        if not self.is_available():
            return {}

        results = {}
        for symbol in symbols:
            data = self.get_coin(symbol)
            if data:
                results[symbol] = data

        logger.info(f"批量获取 Redis 缓存: {len(results)}/{len(symbols)} 个币种命中")
        return results

    def set_coins(self, coins_data: List[Dict[str, Any]], ttl: Optional[int] = None) -> int:
        """
        批量设置多个币种的数据到 Redis

        Args:
            coins_data: 币种数据列表
            ttl: 过期时间(秒),默认使用 default_ttl

        Returns:
            成功设置的数量
        """
        if not self.is_available():
            return 0

        success_count = 0
        for coin_data in coins_data:
            symbol = coin_data.get('symbol')
            if symbol:
                if self.set_coin(symbol, coin_data, ttl):
                    success_count += 1

        logger.info(f"批量设置 Redis 缓存: {success_count}/{len(coins_data)} 个币种")
        return success_count

    def delete_coin(self, symbol: str) -> bool:
        """
        删除单个币种的缓存

        Args:
            symbol: 币种符号

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            key = f"{self.prefix}{symbol}"
            self.redis_client.delete(key)
            logger.debug(f"Redis 缓存已删除: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Redis 删除失败 {symbol}: {e}")
            return False

    def get_all_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的币种符号列表

        Returns:
            币种符号列表
        """
        if not self.is_available():
            return []

        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            # 处理 Redis 返回的 bytes 类型
            symbols = []
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                symbols.append(key.replace(self.prefix, ''))
            logger.info(f"获取已缓存币种: {len(symbols)} 个")
            return symbols
        except Exception as e:
            logger.error(f"获取已缓存币种失败: {e}")
            return []

    def clear_all(self) -> int:
        """
        清空所有币种缓存

        Returns:
            删除的数量
        """
        if not self.is_available():
            return 0

        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            if keys:
                # 处理 Redis 返回的 bytes 类型
                count = self.redis_client.delete(*keys)
                logger.info(f"清空所有币种缓存: {count} 个")
                return count
            return 0
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return 0


# 全局缓存管理器实例
_cache_manager = None


def get_cache_manager():
    """获取全局缓存管理器实例"""
    global _cache_manager
    return _cache_manager


def init_cache_manager(redis_client, default_ttl: int = 300):
    """
    初始化全局缓存管理器

    Args:
        redis_client: Redis 客户端实例
        default_ttl: 默认缓存过期时间(秒)
    """
    global _cache_manager
    _cache_manager = TradingViewCacheManager(redis_client, default_ttl)
    logger.info(f"TradingView 缓存管理器已初始化, TTL={default_ttl}秒")
    return _cache_manager
