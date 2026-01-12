#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TradingView Scanner 定时任务
定期刷新永续合约和涨幅榜的币种数据到 Redis
"""
import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.tradingview_scanner_service import get_top_perpetuals, get_top_gainers
from app.services.tradingview_cache import get_cache_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TradingViewScheduler:
    """TradingView Scanner 定时任务管理器"""

    def __init__(
        self,
        cache_manager=None,
        refresh_interval: int = 300,  # 默认5分钟刷新一次
        perpetuals_limit: int = 200,
        gainers_limit: int = 100
    ):
        """
        初始化定时任务管理器

        Args:
            cache_manager: Redis 缓存管理器
            refresh_interval: 刷新间隔(秒),默认300秒(5分钟)
            perpetuals_limit: 永续合约获取数量
            gainers_limit: 涨幅榜获取数量
        """
        self.cache_manager = cache_manager
        self.refresh_interval = refresh_interval
        self.perpetuals_limit = perpetuals_limit
        self.gainers_limit = gainers_limit

        # 创建后台调度器
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

        # 任务运行状态
        self.is_running = False
        self.last_refresh_time = None
        self.last_refresh_count = 0

    def _refresh_perpetuals(self):
        """刷新永续合约数据到 Redis"""
        try:
            logger.info("=" * 60)
            logger.info("开始刷新永续合约数据...")
            start_time = datetime.now()

            # 获取永续合约数据
            perpetuals = get_top_perpetuals(limit=self.perpetuals_limit)

            if perpetuals and len(perpetuals) > 0:
                # 批量缓存到 Redis (每个币种独立存储)
                if self.cache_manager:
                    cached_count = self.cache_manager.set_coins(perpetuals, ttl=300)
                    logger.info(f"✅ 永续合约数据已刷新: {cached_count} 个币种")
                else:
                    logger.warning("缓存管理器不可用,跳过缓存")

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"刷新耗时: {elapsed:.2f} 秒")
            else:
                logger.warning("未获取到永续合约数据")

        except Exception as e:
            logger.error(f"刷新永续合约数据失败: {e}", exc_info=True)

    def _refresh_gainers(self):
        """刷新涨幅榜数据到 Redis"""
        try:
            logger.info("=" * 60)
            logger.info("开始刷新涨幅榜数据...")
            start_time = datetime.now()

            # 获取涨幅榜数据
            gainers = get_top_gainers(limit=self.gainers_limit)

            if gainers and len(gainers) > 0:
                # 批量缓存到 Redis (每个币种独立存储)
                if self.cache_manager:
                    cached_count = self.cache_manager.set_coins(gainers, ttl=180)
                    logger.info(f"✅ 涨幅榜数据已刷新: {cached_count} 个币种")
                else:
                    logger.warning("缓存管理器不可用,跳过缓存")

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"刷新耗时: {elapsed:.2f} 秒")
            else:
                logger.warning("未获取到涨幅榜数据")

        except Exception as e:
            logger.error(f"刷新涨幅榜数据失败: {e}", exc_info=True)

    def _refresh_all(self):
        """刷新所有数据 (永续合约 + 涨幅榜)"""
        try:
            logger.info("=" * 60)
            logger.info(f"TradingView 定时任务开始执行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)

            total_count = 0

            # 刷新永续合约
            try:
                self._refresh_perpetuals()
            except Exception as e:
                logger.error(f"永续合约刷新失败: {e}")

            # 刷新涨幅榜
            try:
                self._refresh_gainers()
            except Exception as e:
                logger.error(f"涨幅榜刷新失败: {e}")

            # 更新状态
            self.last_refresh_time = datetime.now()
            logger.info("=" * 60)
            logger.info("TradingView 定时任务执行完成")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"定时任务执行失败: {e}", exc_info=True)

    def start(self):
        """启动定时任务"""
        if self.is_running:
            logger.warning("定时任务已在运行中")
            return

        try:
            # 添加定时任务
            self.scheduler.add_job(
                self._refresh_all,
                'interval',
                seconds=self.refresh_interval,
                id='tradingview_refresh',
                name='TradingView 数据刷新',
                replace_existing=True
            )

            # 启动调度器
            self.scheduler.start()
            self.is_running = True

            logger.info("=" * 60)
            logger.info("✅ TradingView 定时任务已启动")
            logger.info(f"   刷新间隔: {self.refresh_interval} 秒 ({self.refresh_interval // 60} 分钟)")
            logger.info(f"   永续合约: {self.perpetuals_limit} 个")
            logger.info(f"   涨幅榜: {self.gainers_limit} 个")
            logger.info("=" * 60)

            # 在后台线程中执行首次刷新,避免阻塞应用启动
            import threading
            logger.info("首次数据刷新将在后台执行...")
            refresh_thread = threading.Thread(target=self._refresh_all, daemon=True)
            refresh_thread.start()

        except Exception as e:
            logger.error(f"启动定时任务失败: {e}", exc_info=True)
            raise

    def stop(self):
        """停止定时任务"""
        if not self.is_running:
            logger.warning("定时任务未运行")
            return

        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("TradingView 定时任务已停止")
        except Exception as e:
            logger.error(f"停止定时任务失败: {e}", exc_info=True)

    def refresh_now(self):
        """立即刷新数据 (手动触发)"""
        logger.info("手动触发数据刷新...")
        self._refresh_all()


# 全局定时任务实例
_scheduler = None


def get_scheduler():
    """获取全局定时任务实例"""
    global _scheduler
    return _scheduler


def init_scheduler(cache_manager, refresh_interval: int = 300):
    """
    初始化全局定时任务

    Args:
        cache_manager: Redis 缓存管理器
        refresh_interval: 刷新间隔(秒),默认300秒(5分钟)
    """
    global _scheduler
    _scheduler = TradingViewScheduler(
        cache_manager=cache_manager,
        refresh_interval=refresh_interval,
        perpetuals_limit=700,  # 增加到700,以覆盖所有615个USDT永续合约
        gainers_limit=100
    )
    return _scheduler


def start_scheduler():
    """启动全局定时任务"""
    scheduler = get_scheduler()
    if scheduler:
        scheduler.start()


def stop_scheduler():
    """停止全局定时任务"""
    scheduler = get_scheduler()
    if scheduler:
        scheduler.stop()
