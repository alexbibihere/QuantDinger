#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试 OCR 功能
"""
import sys
import io

# 设置 stdout 编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_ocr_import():
    """测试 OCR 导入"""
    try:
        from app.services.hama_ocr_extractor import extract_hama_with_ocr
        print("✅ OCR 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ OCR 模块导入失败: {e}")
        return False

def test_paddleocr_available():
    """测试 PaddleOCR 是否可用"""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='ch')
        print("✅ PaddleOCR 可用")
        return True
    except Exception as e:
        print(f"❌ PaddleOCR 不可用: {e}")
        return False

def main():
    print("=" * 60)
    print("OCR 功能快速测试")
    print("=" * 60)

    # 测试 1: PaddleOCR
    print("\n1. 测试 PaddleOCR:")
    paddleocr_ok = test_paddleocr_available()

    # 测试 2: OCR 模块导入
    print("\n2. 测试 OCR 模块:")
    ocr_module_ok = test_ocr_import()

    # 总结
    print("\n" + "=" * 60)
    if paddleocr_ok and ocr_module_ok:
        print("🎉 所有测试通过! OCR 功能已就绪!")
        print("\n您可以使用以下功能:")
        print("- 识别 TradingView 图表中的 HAMA 指标")
        print("- 调用 /api/hama-ocr/extract API")
        print("- 使用 extract_hama_with_ocr() 函数")
    else:
        print("⚠️ 部分测试失败,请检查错误信息")
    print("=" * 60)

if __name__ == '__main__':
    main()
