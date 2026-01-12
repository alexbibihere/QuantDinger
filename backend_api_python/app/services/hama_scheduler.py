#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA分析定时任务
使用APScheduler定时刷新HAMA分析数据

智能更新策略:
1. 检查 Redis 中所有币种的更新时间
2. 如果币种没有缓存,立即更新
3. 如果币种有缓存但更新时间超过 15 分钟,才更新
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.hama_cache import get_cache_manager
from app.services.tradingview_service import TradingViewDataService

logger = logging.getLogger(__name__)


class HamaScheduler:
    """HAMA分析定时任务调度器"""

    def __init__(self, symbols: List[str] = None, interval_minutes: int = 5, cache_ttl_minutes: int = 15):
        """
        初始化调度器

        Args:
            symbols: 要分析的币种列表
            interval_minutes: 刷新间隔(分钟),默认5分钟
            cache_ttl_minutes: 缓存有效期(分钟),默认15分钟,超过这个时间才会更新
        """
        self.symbols = symbols or []
        self.interval_minutes = interval_minutes
        self.cache_ttl_minutes = cache_ttl_minutes
        self.scheduler = BackgroundScheduler()
        self.cache_manager = get_cache_manager()
        self.tv_service = TradingViewDataService()

        self._job_id = 'hama_refresh_job'

    def start(self):
        """启动定时任务"""
        if not self.symbols:
            logger.warning("没有配置币种列表,定时任务未启动")
            return

        try:
            # 先启动调度器
            self.scheduler.start()

            # 立即在后台执行首次刷新
            logger.info(f"HAMA定时任务已启动, 间隔: {self.interval_minutes}分钟, 币种数: {len(self.symbols)}")
            logger.info(f"缓存有效期: {self.cache_ttl_minutes}分钟 (超过此时间才更新)")
            logger.info(f"正在执行首次智能刷新...")

            # 添加定时任务
            self.scheduler.add_job(
                func=self._smart_refresh_hama_data,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id=self._job_id,
                name='HAMA数据智能刷新',
                replace_existing=True
            )

            # 立即执行一次刷新 (不阻塞)
            import threading
            refresh_thread = threading.Thread(target=self._smart_refresh_hama_data, daemon=True)
            refresh_thread.start()

        except Exception as e:
            logger.error(f"启动HAMA定时任务失败: {e}", exc_info=True)

    def stop(self):
        """停止定时任务"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("HAMA定时任务已停止")
        except Exception as e:
            logger.error(f"停止HAMA定时任务失败: {e}")

    def _should_update_symbol(self, symbol: str) -> bool:
        """
        判断币种是否需要更新

        规则:
        1. 如果币种没有缓存,返回 True (需要更新)
        2. 如果币种有缓存但更新时间超过 15 分钟,返回 True (需要更新)
        3. 否则返回 False (不需要更新)

        Args:
            symbol: 币种符号

        Returns:
            是否需要更新
        """
        if not self.cache_manager:
            return True  # 缓存管理器不可用,总是更新

        try:
            # 尝试从 Redis 获取缓存
            cached_data = self.cache_manager.get(symbol)

            if not cached_data:
                logger.debug(f"{symbol}: 无缓存,需要更新")
                return True

            # 检查缓存时间
            timestamp_str = cached_data.get('timestamp')
            if not timestamp_str:
                logger.debug(f"{symbol}: 缓存无时间戳,需要更新")
                return True

            # 解析时间戳
            try:
                cached_time = datetime.fromisoformat(timestamp_str)
                time_diff = datetime.now() - cached_time

                if time_diff > timedelta(minutes=self.cache_ttl_minutes):
                    logger.debug(f"{symbol}: 缓存过期 ({time_diff.total_seconds() // 60}分钟前),需要更新")
                    return True
                else:
                    logger.debug(f"{symbol}: 缓存有效 ({time_diff.total_seconds() // 60}分钟前),跳过")
                    return False

            except ValueError as e:
                logger.warning(f"{symbol}: 无法解析时间戳 '{timestamp_str}': {e}")
                return True

        except Exception as e:
            logger.warning(f"{symbol}: 检查缓存时出错: {e}")
            return True

    def _smart_refresh_hama_data(self):
        """智能刷新策略: 只更新需要更新的币种"""
        if not self.symbols:
            logger.warning("币种列表为空,跳过刷新")
            return

        logger.info(f"=" * 60)
        logger.info(f"开始智能刷新 {len(self.symbols)} 个币种的 HAMA 数据")
        logger.info(f"策略: 无缓存或缓存超过 {self.cache_ttl_minutes} 分钟才更新")
        logger.info(f"=" * 60)
        start_time = datetime.now()

        # 第一阶段: 检查所有币种,判断哪些需要更新
        symbols_to_update = []
        cached_count = 0

        for symbol in self.symbols:
            if self._should_update_symbol(symbol):
                symbols_to_update.append(symbol)
            else:
                cached_count += 1

        logger.info(f"扫描结果: 需要更新 {len(symbols_to_update)} 个币种, 跳过 {cached_count} 个缓存有效的币种")

        if not symbols_to_update:
            logger.info("所有币种缓存都是最新的,无需更新")
            return

        # 第二阶段: 只更新需要更新的币种
        logger.info(f"开始更新 {len(symbols_to_update)} 个币种...")

        success_count = 0
        failed_count = 0
        failed_symbols = []

        for i, symbol in enumerate(symbols_to_update, 1):
            try:
                # 获取HAMA分析
                analysis = self.tv_service.get_hama_cryptocurrency_signals(symbol)
                conditions = self.tv_service.check_hama_conditions(analysis)

                result_data = {
                    'symbol': symbol,
                    'hama_analysis': analysis,
                    'conditions': conditions,
                    'timestamp': datetime.now().isoformat(),
                    'cached': False
                }

                # 保存到Redis
                if self.cache_manager:
                    cache_success = self.cache_manager.set(symbol, result_data)
                    if cache_success:
                        cached_count += 1

                success_count += 1

                # 每10个币种打印一次进度
                if i % 10 == 0:
                    logger.info(f"刷新进度: {i}/{len(symbols_to_update)} ({i*100//len(symbols_to_update)}%)")

            except Exception as e:
                logger.error(f"刷新失败 {symbol}: {e}")
                failed_count += 1
                failed_symbols.append(symbol)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"=" * 60)
        logger.info(
            f"HAMA数据智能刷新完成 - "
            f"扫描: {len(self.symbols)} 个, "
            f"需要更新: {len(symbols_to_update)} 个, "
            f"跳过: {cached_count} 个, "
            f"成功: {success_count}, "
            f"失败: {failed_count}, "
            f"耗时: {duration:.2f}秒"
        )

        if failed_symbols:
            logger.warning(f"失败的币种: {', '.join(failed_symbols[:10])}")
            if len(failed_symbols) > 10:
                logger.warning(f"  ... 还有 {len(failed_symbols) - 10} 个")

        logger.info(f"下次扫描时间: {self.interval_minutes} 分钟后")
        logger.info(f"=" * 60)

    def update_symbols(self, symbols: List[str]):
        """
        更新币种列表

        Args:
            symbols: 新的币种列表
        """
        self.symbols = symbols
        logger.info(f"币种列表已更新, 当前数量: {len(symbols)}")

    def set_interval(self, minutes: int):
        """
        更新刷新间隔

        Args:
            minutes: 新的间隔(分钟)
        """
        self.interval_minutes = minutes

        # 重启任务以应用新间隔
        if self.scheduler.running:
            self.scheduler.remove_job(self._job_id)
            self.scheduler.add_job(
                func=self._refresh_hama_data,
                trigger=IntervalTrigger(minutes=minutes),
                id=self._job_id,
                name='HAMA数据定时刷新',
                replace_existing=True
            )
            logger.info(f"刷新间隔已更新为{minutes}分钟")

    def get_status(self) -> dict:
        """
        获取调度器状态

        Returns:
            状态信息字典
        """
        cache_stats = self.cache_manager.get_stats() if self.cache_manager else {}

        return {
            'running': self.scheduler.running,
            'symbols_count': len(self.symbols),
            'interval_minutes': self.interval_minutes,
            'cache_stats': cache_stats
        }


# 全局调度器实例
_hama_scheduler = None


def get_scheduler() -> HamaScheduler:
    """获取全局调度器实例"""
    global _hama_scheduler
    return _hama_scheduler


def init_scheduler(symbols: List[str] = None, interval_minutes: int = 5, cache_ttl_minutes: int = 15):
    """
    初始化全局调度器

    Args:
        symbols: 币种列表
        interval_minutes: 刷新间隔(分钟)
        cache_ttl_minutes: 缓存有效期(分钟),超过此时间才更新
    """
    global _hama_scheduler
    _hama_scheduler = HamaScheduler(symbols, interval_minutes, cache_ttl_minutes)
    return _hama_scheduler
