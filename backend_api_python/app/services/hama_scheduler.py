#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 调度器

⚠️ 已废弃 — OCR/浏览器监控已禁用
定时任务功能保留但不会实际触发浏览器操作。
持续监控由 tv-bridge + Flask 后端健康检查线程替代。
"""

import logging

logger = logging.getLogger(__name__)
logger.warning("⚠️ hama_scheduler.py 已废弃，监控由 tv-bridge 后台线程替代")


class HAMAScheduler:
    """已废弃 — 由 tv-bridge 替代"""

    def __init__(self, *args, **kwargs):
        self.enabled = False

    def start(self):
        logger.info("HAMA 调度器已禁用 (tv-bridge 模式)")

    def stop(self):
        pass

    def is_running(self):
        return False
