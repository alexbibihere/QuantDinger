#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA OCR 服务

⚠️ 已废弃 — 由 tv-bridge (hama_tv_service.py) 替代

保留此文件仅为兼容旧代码引用。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.warning("⚠️ hama_ocr_service.py 已废弃，使用 hama_tv_service.py 替代")


def get_ocr_service(*args, **kwargs):
    return None
