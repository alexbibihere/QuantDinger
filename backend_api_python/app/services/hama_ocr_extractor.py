#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA OCR 提取器

⚠️ 已废弃 — 由 tv-bridge (hama_tv_service.py) 替代

原功能: 使用 Playwright + Brave 浏览器 + RapidOCR 从 TradingView 截图识别 HAMA 指标
替代方案: hama_tv_service.py 通过 tv-bridge WebSocket 获取数据，更快更准更稳

保留此文件仅为兼容旧代码引用。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.warning("⚠️ hama_ocr_extractor.py 已废弃，正在使用 hama_tv_service.py 替代")


class HAMAOCRExtractor:
    """已废弃 — 由 tv-bridge 替代"""

    def __init__(self, *args, **kwargs):
        logger.info("HAMAOCRExtractor 已禁用 (tv-bridge 模式)")

    def extract_hama(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return None

    def capture_screenshot(self, *args, **kwargs) -> Optional[str]:
        return None


def extract_hama_with_ocr(*args, **kwargs):
    return None
