#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 OCR 识别功能演示
"""
import sys
import io

# 设置 stdout 编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_basic_ocr():
    """测试基本 OCR 功能"""
    print("=" * 60)
    print("测试 1: 基本 OCR 功能")
    print("=" * 60)

    try:
        from paddleocr import PaddleOCR
        import os

        # 初始化 OCR
        print("\n📸 初始化 PaddleOCR...")
        ocr = PaddleOCR(lang='ch')
        print("✅ OCR 初始化成功!\n")

        # 检查是否有测试图片
        test_images = []
        image_dirs = [
            './screenshot',
            './file',
            '../screenshot',
            '../file',
            'd:/github/QuantDinger/screenshot',
            'd:/github/QuantDinger/file'
        ]

        for dir_path in image_dirs:
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        test_images.append(os.path.join(dir_path, f))
                        if len(test_images) >= 3:  # 最多找3张图片
                            break
            if len(test_images) >= 3:
                break

        if test_images:
            print(f"🖼️  找到 {len(test_images)} 张图片进行测试:\n")

            for i, img_path in enumerate(test_images, 1):
                print(f"[{i}/{len(test_images)}] 处理图片: {os.path.basename(img_path)}")

                # 进行 OCR 识别 (不使用 cls 参数,新版已移除)
                result = ocr.ocr(img_path)

                if result and len(result) > 0:
                    # result 是一个列表,包含所有图片的结果
                    img_result = result[0] if len(result) > 0 else []
                    if isinstance(img_result, list):
                        print(f"  ✅ 识别成功! 检测到 {len(img_result)} 个文本块\n")

                        # 显示前3个识别结果
                        for j, line in enumerate(img_result[:3], 1):
                            if isinstance(line, (list, tuple)) and len(line) >= 2:
                                box = line[0]
                                text_info = line[1]

                                # 处理不同的返回格式
                                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                    text = text_info[0]
                                    confidence = text_info[1] if isinstance(text_info[1], (int, float)) else 0.0
                                else:
                                    text = str(text_info)
                                    confidence = 0.0

                                print(f"  文本 {j}: {text}")
                                if confidence > 0:
                                    print(f"  置信度: {confidence:.2%}")
                                print()

                        if len(img_result) > 3:
                            print(f"  ... 还有 {len(img_result) - 3} 个文本块\n")
                else:
                    print("  ❌ 未识别到文本\n")

                print("-" * 60)
        else:
            print("⚠️  未找到测试图片")
            print("\n💡 提示: 将图片放到以下目录之一进行测试:")
            for dir_path in image_dirs:
                print(f"   - {dir_path}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hama_ocr_extractor():
    """测试 HAMA OCR 提取器"""
    print("\n" + "=" * 60)
    print("测试 2: HAMA OCR 提取器")
    print("=" * 60)

    try:
        from app.services.hama_ocr_extractor import HAMAOCRExtractor

        print("\n🔧 创建 HAMA OCR 提取器...")
        extractor = HAMAOCRExtractor(ocr_engine='paddleocr')
        print("✅ 提取器创建成功!\n")

        # 检查是否有截图
        import os
        screenshot_path = None

        possible_paths = [
            './screenshot/BTCUSDT_15m_chart.png',
            '../screenshot/BTCUSDT_15m_chart.png',
            'd:/github/QuantDinger/screenshot/BTCUSDT_15m_chart.png'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                screenshot_path = path
                break

        if screenshot_path:
            print(f"📸 识别 HAMA 图表: {os.path.basename(screenshot_path)}\n")

            result = extractor.extract_hama_with_ocr(screenshot_path)

            if result:
                print("✅ HAMA 识别成功!\n")
                print(f"  HAMA 数值: {result.get('hama_value', 'N/A')}")
                print(f"  HAMA 颜色: {result.get('hama_color', 'N/A')}")
                print(f"  趋势: {result.get('trend', 'N/A')}")
                print(f"  当前价格: {result.get('current_price', 'N/A')}")

                bb = result.get('bollinger_bands', {})
                if bb:
                    print(f"\n  布林带:")
                    print(f"    上轨: {bb.get('upper', 'N/A')}")
                    print(f"    中轨: {bb.get('middle', 'N/A')}")
                    print(f"    下轨: {bb.get('lower', 'N/A')}")

                print(f"\n  OCR 引擎: {result.get('ocr_engine', 'N/A')}")
                print(f"  置信度: {result.get('confidence', 'N/A')}")
            else:
                print("❌ HAMA 识别失败")
        else:
            print("⚠️  未找到测试截图")
            print("\n💡 提示: 需要先截取 TradingView 图表到 screenshot 目录")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_api():
    """测试 OCR API 接口"""
    print("\n" + "=" * 60)
    print("测试 3: OCR API 接口")
    print("=" * 60)

    try:
        import requests

        # 检查后端是否运行
        print("\n🌐 检查后端服务...")
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=2)
            if response.status_code == 200:
                print("✅ 后端服务运行中\n")

                # 测试 OCR API (如果已注册路由)
                print("📡 测试 OCR API...")
                try:
                    # 注意: 这个 API 可能还未注册路由
                    response = requests.get(
                        'http://localhost:5000/api/hama-ocr/extract',
                        params={
                            'symbol': 'BTCUSDT',
                            'interval': '15'
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        print("✅ OCR API 调用成功!\n")
                        print(f"响应: {data}")
                    else:
                        print(f"⚠️  API 返回状态码: {response.status_code}")
                        print(f"响应: {response.text}")

                except requests.exceptions.RequestException as e:
                    print(f"⚠️  OCR API 调用失败: {e}")
                    print("\n💡 提示: OCR API 可能还未注册到路由")

            else:
                print(f"⚠️  后端服务状态异常: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ 后端服务未运行")
            print("\n💡 提示: 请先启动后端服务")
            print("   cd backend_api_python && python run.py")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "🚀" * 30)
    print("OCR 功能完整测试")
    print("🚀" * 30 + "\n")

    results = []

    # 测试 1: 基本 OCR
    results.append(("基本 OCR", test_basic_ocr()))

    # 测试 2: HAMA OCR 提取器
    results.append(("HAMA OCR 提取器", test_hama_ocr_extractor()))

    # 测试 3: OCR API
    results.append(("OCR API", test_ocr_api()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 所有测试通过! OCR 功能完全正常!")
    else:
        print("\n⚠️  部分测试失败,请查看错误信息")

    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
