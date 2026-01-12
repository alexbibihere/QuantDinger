#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA分析Redis缓存管理
"""
import json
import logging
from datetime import timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HamaCacheManager:
    """HAMA分析Redis缓存管理器"""

    def __init__(self, redis_client=None, default_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            redis_client: Redis客户端实例
            default_ttl: 默认缓存过期时间(秒),默认300秒(5分钟)
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.prefix = "hama:analysis:"

    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis不可用: {e}")
            return False

    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        从Redis获取币种的HAMA分析缓存

        Args:
            symbol: 币种符号

        Returns:
            缓存数据或None
        """
        if not self.is_available():
            return None

        try:
            key = self._make_key(symbol)
            data = self.redis_client.get(key)

            if data:
                result = json.loads(data)
                logger.debug(f"Redis缓存命中: {symbol}")
                return result

            return None

        except Exception as e:
            logger.error(f"Redis获取失败 {symbol}: {e}")
            return None

    def set(self, symbol: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        设置币种的HAMA分析缓存到Redis

        Args:
            symbol: 币种符号
            data: 要缓存的数据
            ttl: 过期时间(秒),默认使用default_ttl

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            key = self._make_key(symbol)
            ttl = ttl or self.default_ttl

            # 添加缓存时间戳
            data['cached_at'] = json.dumps({'timestamp': data.get('timestamp')})
            data['is_cached'] = True

            json_data = json.dumps(data, ensure_ascii=False)

            self.redis_client.setex(key, ttl, json_data)
            logger.debug(f"Redis缓存已设置: {symbol}, TTL={ttl}秒")
            return True

        except Exception as e:
            logger.error(f"Redis设置失败 {symbol}: {e}")
            return False

    def delete(self, symbol: str) -> bool:
        """
        删除指定币种的缓存

        Args:
            symbol: 币种符号

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            key = self._make_key(symbol)
            self.redis_client.delete(key)
            logger.debug(f"Redis缓存已删除: {symbol}")
            return True

        except Exception as e:
            logger.error(f"Redis删除失败 {symbol}: {e}")
            return False

    def clear_all(self) -> bool:
        """
        清空所有HAMA分析缓存

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            # 查找所有HAMA缓存key
            keys = []
            for key in self.redis_client.scan_iter(f"{self.prefix}*"):
                keys.append(key)

            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"已清空{len(keys)}个HAMA缓存")

            return True

        except Exception as e:
            logger.error(f"Redis清空失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.is_available():
            return {
                'available': False,
                'cached_symbols': 0,
                'cache_ttl_seconds': self.default_ttl
            }

        try:
            keys = []
            for key in self.redis_client.scan_iter(f"{self.prefix}*"):
                keys.append(key)

            return {
                'available': True,
                'cached_symbols': len(keys),
                'cache_ttl_seconds': self.default_ttl,
                'cache_ttl_minutes': int(self.default_ttl / 60)
            }

        except Exception as e:
            logger.error(f"获取Redis统计失败: {e}")
            return {
                'available': False,
                'cached_symbols': 0,
                'cache_ttl_seconds': self.default_ttl,
                'error': str(e)
            }

    def get_cached_symbols(self) -> list:
        """
        获取所有已缓存的币种列表

        Returns:
            币种符号列表
        """
        if not self.is_available():
            return []

        try:
            symbols = []
            for key in self.redis_client.scan_iter(f"{self.prefix}*"):
                # 提取symbol (去掉前缀)
                symbol = key.decode('utf-8').replace(self.prefix, '')
                symbols.append(symbol)

            return sorted(symbols)

        except Exception as e:
            logger.error(f"获取缓存列表失败: {e}")
            return []

    def _make_key(self, symbol: str) -> str:
        """生成Redis key"""
        return f"{self.prefix}{symbol}"


# 全局缓存管理器实例
_cache_manager = None


def get_cache_manager() -> HamaCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    return _cache_manager


def init_cache_manager(redis_client=None, ttl: int = 300):
    """
    初始化全局缓存管理器

    Args:
        redis_client: Redis客户端实例
        ttl: 默认缓存过期时间(秒)
    """
    global _cache_manager
    _cache_manager = HamaCacheManager(redis_client, ttl)
    logger.info(f"HAMA缓存管理器已初始化, TTL={ttl}秒")
