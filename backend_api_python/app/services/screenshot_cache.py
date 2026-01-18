#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图缓存服务 - 将截图存储到SQLite数据库
避免重复截图,提升响应速度
"""
import sqlite3
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotCache:
    """截图缓存管理器 (SQLite 存储)"""

    def __init__(self, db_path: str = None):
        """
        初始化截图缓存

        Args:
            db_path: 数据库路径 (默认使用主数据库)
        """
        if db_path is None:
            # 默认使用主数据库
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'data', 'quantdinger.db')

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建截图缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screenshot_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    image_base64 TEXT NOT NULL,
                    file_size INTEGER,
                    screenshot_url TEXT,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval)
                )
            ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screenshot_cache_symbol_interval
                ON screenshot_cache(symbol, interval)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screenshot_cache_captured
                ON screenshot_cache(captured_at)
            ''')

            conn.commit()
            conn.close()

            logger.info("✅ 截图缓存表初始化成功")
        except Exception as e:
            logger.error(f"截图缓存表初始化失败: {e}")

    def get_screenshot(self, symbol: str, interval: str = '15m') -> Optional[Dict[str, Any]]:
        """
        从数据库获取截图

        Args:
            symbol: 币种符号
            interval: 时间周期

        Returns:
            截图数据字典或None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM screenshot_cache
                WHERE symbol = ? AND interval = ?
                ORDER BY captured_at DESC
                LIMIT 1
            ''', (symbol, interval))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'symbol': row['symbol'],
                    'interval': row['interval'],
                    'image_base64': row['image_base64'],
                    'file_size': row['file_size'],
                    'screenshot_url': row['screenshot_url'],
                    'captured_at': row['captured_at'],
                    'cached': True
                }

            return None
        except Exception as e:
            logger.error(f"从数据库获取截图失败 {symbol}: {e}")
            return None

    def save_screenshot(self, symbol: str, interval: str, image_base64: str,
                       file_size: int = None, screenshot_url: str = None) -> bool:
        """
        保存截图到数据库

        Args:
            symbol: 币种符号
            interval: 时间周期
            image_base64: base64编码的图片数据
            file_size: 文件大小
            screenshot_url: 截图URL (可选)

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 使用 INSERT OR REPLACE 更新或插入
            cursor.execute('''
                INSERT OR REPLACE INTO screenshot_cache
                (symbol, interval, image_base64, file_size, screenshot_url, captured_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, interval, image_base64, file_size, screenshot_url, datetime.now()))

            conn.commit()
            conn.close()

            logger.info(f"✅ {symbol} 截图已保存到数据库 ({interval})")
            return True
        except Exception as e:
            logger.error(f"保存截图到数据库失败 {symbol}: {e}")
            return False

    def delete_screenshot(self, symbol: str, interval: str = None) -> bool:
        """
        删除截图

        Args:
            symbol: 币种符号
            interval: 时间周期 (None表示删除所有周期)

        Returns:
            是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if interval:
                cursor.execute('DELETE FROM screenshot_cache WHERE symbol = ? AND interval = ?', (symbol, interval))
            else:
                cursor.execute('DELETE FROM screenshot_cache WHERE symbol = ?', (symbol,))

            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()

            logger.info(f"✅ 删除了 {deleted_count} 条截图记录 ({symbol})")
            return True
        except Exception as e:
            logger.error(f"删除截图失败 {symbol}: {e}")
            return False

    def cleanup_old_screenshots(self, days: int = 7) -> int:
        """
        清理旧截图

        Args:
            days: 保留天数

        Returns:
            删除的数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM screenshot_cache
                WHERE captured_at < datetime('now', '-' || ? || ' days')
            ''', (days,))

            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()

            logger.info(f"✅ 清理了 {deleted_count} 条旧截图 (超过{days}天)")
            return deleted_count
        except Exception as e:
            logger.error(f"清理旧截图失败: {e}")
            return 0

    def get_all_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的币种列表

        Returns:
            币种符号列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT symbol FROM screenshot_cache ORDER BY symbol')
            symbols = [row[0] for row in cursor.fetchall()]

            conn.close()
            return symbols
        except Exception as e:
            logger.error(f"获取缓存币种列表失败: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 总记录数
            cursor.execute('SELECT COUNT(*) FROM screenshot_cache')
            total_count = cursor.fetchone()[0]

            # 总大小
            cursor.execute('SELECT SUM(file_size) FROM screenshot_cache WHERE file_size IS NOT NULL')
            total_size = cursor.fetchone()[0] or 0

            # 按币种统计
            cursor.execute('''
                SELECT symbol, COUNT(*) as count
                FROM screenshot_cache
                GROUP BY symbol
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_symbols = cursor.fetchall()

            conn.close()

            return {
                'total_screenshots': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'top_symbols': top_symbols[:5]
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 全局单例
_screenshot_cache_instance = None


def get_screenshot_cache(db_path: str = None) -> ScreenshotCache:
    """
    获取截图缓存单例

    Args:
        db_path: 数据库路径

    Returns:
        ScreenshotCache 实例
    """
    global _screenshot_cache_instance

    if _screenshot_cache_instance is None:
        _screenshot_cache_instance = ScreenshotCache(db_path)

    return _screenshot_cache_instance
