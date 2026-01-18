#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 截图静态文件服务 Blueprint
"""
from flask import Blueprint, send_from_directory, send_file
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 创建 Blueprint
bp = Blueprint('static_files', __name__)

# 获取截图目录
def get_screenshot_dir():
    """获取截图目录的绝对路径"""
    # 获取 static_files.py 所在目录 (app/routes/)
    routes_dir = os.path.dirname(os.path.abspath(__file__))
    # 上一级到 app 目录
    app_dir = os.path.dirname(routes_dir)
    # 截图在 app/screenshots/ 目录
    screenshot_dir = os.path.join(app_dir, 'screenshots')
    logger.info(f"截图目录: {screenshot_dir}")
    return screenshot_dir

@bp.route('/screenshot/<path:filename>')
def serve_screenshot(filename):
    """
    提供 HAMA 截图静态文件服务

    Args:
        filename: 截图文件名 (例如: hama_brave_BTCUSDT_1768723554.png)

    Returns:
        截图文件的二进制数据
    """
    screenshot_dir = get_screenshot_dir()

    logger.info(f"访问截图: {filename}, 截图目录: {screenshot_dir}")

    try:
        # 检查文件是否存在
        file_path = os.path.join(screenshot_dir, filename)
        logger.info(f"完整文件路径: {file_path}, 存在: {os.path.exists(file_path)}")

        if not os.path.exists(file_path):
            # 列出目录中的所有文件用于调试
            if os.path.exists(screenshot_dir):
                files = os.listdir(screenshot_dir)[:5]  # 只显示前5个
                logger.info(f"目录中的文件: {files}")
            return f"File not found: {filename}", 404

        # 返回文件
        return send_file(file_path, mimetype='image/png')
    except Exception as e:
        logger.error(f"服务截图文件失败: {e}")
        return f"Error serving file: {str(e)}", 500
