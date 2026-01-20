#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis截图缓存管理器 - 专为高频刷新场景优化
适用于Brave监控(10分钟刷新)、TradingView实时截图等场景

优势:
- 读取极快(内存级,毫秒响应)
- 自动过期清理(无需手动维护)
- 支持base64直接存储(前端直接使用)
- 独立部署,不影响主数据库
"""
import json
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotRedisCache:
    """Redis截图缓存管理器 - 专为高频刷新优化"""

    def __init__(self, redis_client=None, default_ttl: int = 600):
        """
        初始化Redis缓存管理器

        Args:
            redis_client: Redis客户端实例
            default_ttl: 默认缓存过期时间(秒),默认600秒(10分钟)
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.prefix = "screenshot:"  # 截图缓存前缀

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

    def _make_key(self, symbol: str, interval: str) -> str:
        """生成Redis key"""
        return f"{self.prefix}{symbol}:{interval}"

    def get_screenshot(self, symbol: str, interval: str = '15m') -> Optional[Dict[str, Any]]:
        """
        从Redis获取截图

        Args:
            symbol: 币种符号
            interval: 时间周期

        Returns:
            截图数据字典或None
            {
                'symbol': 'BTCUSDT',
                'interval': '15m',
                'image_base64': 'iVBORw0KG...',
                'file_size': 123456,
                'captured_at': '2025-01-20 10:30:00',
                'cached': True
            }
        """
        if not self.is_available():
            return None

        try:
            key = self._make_key(symbol, interval)
            data = self.redis_client.get(key)

            if data:
                result = json.loads(data)
                logger.debug(f"✅ Redis缓存命中: {symbol} {interval}")
                return result

            logger.debug(f"❌ Redis缓存未命中: {symbol} {interval}")
            return None

        except Exception as e:
            logger.error(f"Redis获取截图失败 {symbol}: {e}")
            return None

    def save_screenshot(self,
                       symbol: str,
                       interval: str,
                       image_base64: str,
                       file_size: int = None,
                       screenshot_url: str = None,
                       ttl: int = None) -> bool:
        """
        保存截图到Redis

        Args:
            symbol: 币种符号
            interval: 时间周期
            image_base64: base64编码的图片数据
            file_size: 文件大小(字节)
            screenshot_url: 截图URL(可选)
            ttl: 过期时间(秒),默认使用default_ttl

        Returns:
            是否成功
        """
        if not self.is_available():
            logger.warning("Redis不可用,无法保存截图")
            return False

        try:
            key = self._make_key(symbol, interval)
            ttl = ttl or self.default_ttl

            # 构建缓存数据
            cache_data = {
                'symbol': symbol,
                'interval': interval,
                'image_base64': image_base64,
                'file_size': file_size,
                'screenshot_url': screenshot_url,
                'captured_at': datetime.now().isoformat(),
                'cached': True,
                'cache_ttl': ttl
            }

            # 保存到Redis
            self.redis_client.setex(key, ttl, json.dumps(cache_data))

            logger.info(f"✅ 截图已缓存到Redis: {symbol} {interval} (TTL={ttl}秒, 大小={file_size or 0}字节)")
            return True

        except Exception as e:
            logger.error(f"Redis保存截图失败 {symbol}: {e}")
            return False

    def save_screenshot_bytes(self,
                             symbol: str,
                             interval: str,
                             image_bytes: bytes,
                             screenshot_url: str = None,
                             ttl: int = None) -> bool:
        """
        保存截图(二进制格式)到Redis

        Args:
            symbol: 币种符号
            interval: 时间周期
            image_bytes: 图片二进制数据
            screenshot_url: 截图URL(可选)
            ttl: 过期时间(秒)

        Returns:
            是否成功
        """
        try:
            # 转换为base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            file_size = len(image_bytes)

            return self.save_screenshot(symbol, interval, image_base64, file_size, screenshot_url, ttl)

        except Exception as e:
            logger.error(f"保存二进制截图失败 {symbol}: {e}")
            return False

    def delete_screenshot(self, symbol: str, interval: str = None) -> bool:
        """
        删除截图缓存

        Args:
            symbol: 币种符号
            interval: 时间周期 (None表示删除所有周期)

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            if interval:
                # 删除指定周期的缓存
                key = self._make_key(symbol, interval)
                self.redis_client.delete(key)
                logger.debug(f"✅ Redis缓存已删除: {symbol} {interval}")
            else:
                # 删除该币种所有周期的缓存
                pattern = f"{self.prefix}{symbol}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.debug(f"✅ Redis缓存已删除: {symbol} 所有周期 ({len(keys)}个)")

            return True

        except Exception as e:
            logger.error(f"Redis删除缓存失败 {symbol}: {e}")
            return False

    def get_all_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的币种列表

        Returns:
            币种符号列表
        """
        if not self.is_available():
            return []

        try:
            # 获取所有screenshot相关的key
            keys = self.redis_client.keys(f"{self.prefix}*")

            # 提取唯一的币种符号
            symbols = set()
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                # key格式: screenshot:BTCUSDT:15m
                parts = key.replace(self.prefix, '').split(':')
                if len(parts) >= 1:
                    symbols.add(parts[0])

            return sorted(list(symbols))

        except Exception as e:
            logger.error(f"获取缓存币种列表失败: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.is_available():
            return {
                'available': False,
                'cached_screenshots': 0,
                'cache_ttl_seconds': self.default_ttl
            }

        try:
            keys = self.redis_client.keys(f"{self.prefix}*")

            # 计算总大小
            total_size = 0
            for key in keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        # 估算JSON字符串大小
                        total_size += len(data)
                except:
                    pass

            return {
                'available': True,
                'cached_screenshots': len(keys),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'cache_ttl_seconds': self.default_ttl,
                'cache_ttl_minutes': int(self.default_ttl / 60),
                'redis_type': 'memory'
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'available': False,
                'error': str(e)
            }

    def clear_all(self) -> int:
        """
        清空所有截图缓存

        Returns:
            删除的数量
        """
        if not self.is_available():
            return 0

        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"✅ 已清空所有截图缓存: {count}个")
                return count
            return 0

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return 0

    def batch_get_screenshots(self, symbols: List[str], interval: str = '15m') -> Dict[str, Dict[str, Any]]:
        """
        批量获取截图

        Args:
            symbols: 币种符号列表
            interval: 时间周期

        Returns:
            币种->截图数据的字典
        """
        if not self.is_available():
            return {}

        try:
            results = {}
            for symbol in symbols:
                data = self.get_screenshot(symbol, interval)
                if data:
                    results[symbol] = data

            logger.info(f"批量获取截图: {len(results)}/{len(symbols)} 个命中")
            return results

        except Exception as e:
            logger.error(f"批量获取截图失败: {e}")
            return {}

    def batch_save_screenshots(self,
                              screenshots: List[Dict[str, Any]],
                              ttl: int = None) -> int:
        """
        批量保存截图

        Args:
            screenshots: 截图列表
                [{
                    'symbol': 'BTCUSDT',
                    'interval': '15m',
                    'image_base64': 'iVBORw0KG...',
                    'file_size': 123456
                }, ...]
            ttl: 过期时间(秒)

        Returns:
            成功保存的数量
        """
        if not self.is_available():
            return 0

        try:
            success_count = 0
            for screenshot in screenshots:
                symbol = screenshot.get('symbol')
                interval = screenshot.get('interval', '15m')
                image_base64 = screenshot.get('image_base64')
                file_size = screenshot.get('file_size')
                screenshot_url = screenshot.get('screenshot_url')

                if symbol and image_base64:
                    if self.save_screenshot(symbol, interval, image_base64, file_size, screenshot_url, ttl):
                        success_count += 1

            logger.info(f"批量保存截图: {success_count}/{len(screenshots)} 个成功")
            return success_count

        except Exception as e:
            logger.error(f"批量保存截图失败: {e}")
            return 0

    def extend_ttl(self, symbol: str, interval: str = '15m', extra_ttl: int = None) -> bool:
        """
        延长缓存过期时间

        Args:
            symbol: 币种符号
            interval: 时间周期
            extra_ttl: 额外的TTL时间(秒),默认使用default_ttl

        Returns:
            是否成功
        """
        if not self.is_available():
            return False

        try:
            key = self._make_key(symbol, interval)
            extra_ttl = extra_ttl or self.default_ttl

            # Redis EXPIRE命令会延长现有TTL
            self.redis_client.expire(key, extra_ttl)
            logger.debug(f"✅ 延长缓存TTL: {symbol} {interval} (+{extra_ttl}秒)")
            return True

        except Exception as e:
            logger.error(f"延长TTL失败 {symbol}: {e}")
            return False


# 全局单例
_screenshot_redis_cache_instance = None


def get_screenshot_redis_cache(redis_client=None, default_ttl: int = 600) -> ScreenshotRedisCache:
    """
    获取Redis截图缓存单例

    Args:
        redis_client: Redis客户端
        default_ttl: 默认TTL(秒)

    Returns:
        ScreenshotRedisCache 实例
    """
    global _screenshot_redis_cache_instance

    if _screenshot_redis_cache_instance is None:
        _screenshot_redis_cache_instance = ScreenshotRedisCache(redis_client, default_ttl)

    return _screenshot_redis_cache_instance


def init_screenshot_redis_cache(redis_client, default_ttl: int = 600) -> ScreenshotRedisCache:
    """
    初始化全局Redis截图缓存

    Args:
        redis_client: Redis客户端
        default_ttl: 默认TTL(秒)

    Returns:
        ScreenshotRedisCache 实例
    """
    global _screenshot_redis_cache_instance
    _screenshot_redis_cache_instance = ScreenshotRedisCache(redis_client, default_ttl)
    logger.info(f"✅ Redis截图缓存已初始化, TTL={default_ttl}秒 ({default_ttl//60}分钟)")
    return _screenshot_redis_cache_instance