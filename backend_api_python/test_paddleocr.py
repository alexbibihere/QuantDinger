#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 PaddleOCR 安装
"""
import sys
import io

# 设置 stdout 编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR 安装成功!")

    # 初始化 PaddleOCR (首次运行会下载模型)
    print("正在初始化 PaddleOCR (首次运行会下载模型文件,请耐心等待)...")
    ocr = PaddleOCR(lang='ch')
    print("✅ PaddleOCR 初始化成功!")

    print("\n🎉 OCR 功能已就绪!")
    print("\n您现在可以使用以下功能:")
    print("1. 识别 TradingView 图表中的 HAMA 指标")
    print("2. 提取图片中的文字信息")
    print("3. 转换文档为 Markdown 格式")

except ImportError as e:
    print(f"❌ PaddleOCR 未安装: {e}")
    print("\n请运行: pip install paddleocr paddlepaddle")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
