#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 OCR 识别
"""
import sys
import os
import io

# Windows 控制台编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend_api_python'))

def main():
    from app.services.hama_ocr_extractor import HAMAOCRExtractor

    print("=" * 80)
    print("调试 OCR 识别")
    print("=" * 80)
    print()

    # 初始化 OCR 提取器
    extractor = HAMAOCRExtractor(ocr_engine='paddleocr')

    # 测试图片
    image_path = 'backend_api_python/app/screenshots/hama_brave_BTCUSDT_1768873755.png'

    if not os.path.exists(image_path):
        print(f"❌ 图片不存在: {image_path}")
        return 1

    print(f"📷 图片路径: {image_path}")
    print()

    # 执行 OCR
    print("🔍 正在执行 OCR...")
    print()

    try:
        # 直接调用 PaddleOCR
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='en')
        result = ocr.ocr(image_path)

        print(f"OCR 结果类型: {type(result)}")
        if result is not None:
            print(f"OCR 结果长度: {len(result) if isinstance(result, list) else 'N/A'}")
        if result and len(result) > 0:
            print(f"第一项类型: {type(result[0])}")
            print(f"第一项长度: {len(result[0]) if isinstance(result[0], list) else 'N/A'}")
        print()

        # 新版 PaddleOCR 返回 OCRResult 对象
        if result and len(result) > 0:
            ocr_result = result[0]
            print("✅ OCR 识别成功")
            print()

            # 尝试直接打印结果内容
            print("OCRResult 内容:")
            print("-" * 80)

            # 检查是否有 rec_texts 键
            if 'rec_texts' in ocr_result:
                texts = ocr_result['rec_texts']
                scores = ocr_result.get('rec_scores', [])
                for i, text in enumerate(texts):
                    score = scores[i] if i < len(scores) else 0.0
                    print(f"[{score:.2f}] {text}")
                print("-" * 80)
                print()
                print(f"共识别到 {len(texts)} 行文本")
            else:
                # 打印所有键值对
                print("可用的键:")
                for key in ocr_result.keys():
                    print(f"  {key}: {type(ocr_result[key])}")
                print()
                print("尝试打印所有数据:")
                for key, value in ocr_result.items():
                    if isinstance(value, (list, str)):
                        print(f"{key}: {value}")
                    else:
                        print(f"{key}: {type(value)}")
        else:
            print("❌ OCR 未识别到任何文本")
            print(f"result = {result}")

    except Exception as e:
        print(f"❌ OCR 识别失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
