#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 视觉识别功能测试脚本

使用前请配置 OPENROUTER_API_KEY
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.hama_vision_extractor import extract_hama_with_vision


def test_vision_extraction():
    """测试视觉识别功能"""
    print("="*60)
    print("HAMA 视觉识别功能测试")
    print("="*60)

    # 检查 API 密钥
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("\n❌ OPENROUTER_API_KEY 未配置")
        print("\n请按照以下步骤配置：")
        print("1. 访问 https://openrouter.ai/ 获取 API 密钥")
        print("2. 在 backend_api_python/.env 文件中添加：")
        print("   OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("   OPENROUTER_MODEL=openai/gpt-4o")
        print("3. 重启容器：docker-compose restart backend")
        print("\n获取 API 密钥：https://openrouter.ai/keys")
        return

    print(f"\n✅ API 密钥已配置: {api_key[:20]}...")

    # 测试图表 URL
    chart_url = "https://cn.tradingview.com/chart/U1FY2qxO/"

    print(f"\n开始测试图表: {chart_url}")
    print("预计需要 60-90 秒（包括加载图表和 AI 识别）...")

    # 调用视觉识别
    result = extract_hama_with_vision(
        chart_url=chart_url,
        symbol='ETHUSD',
        interval='15'
    )

    if result:
        print("\n" + "="*60)
        print("✅ 识别成功！")
        print("="*60)
        print(f"HAMA 数值: {result.get('hama_value')}")
        print(f"HAMA 颜色: {result.get('hama_color')}")
        print(f"趋势: {result.get('trend')}")
        print(f"当前价格: {result.get('current_price')}")
        print(f"置信度: {result.get('confidence')}")

        # 布林带
        bb = result.get('bollinger_bands', {})
        if any(bb.values()):
            print(f"\n布林带:")
            print(f"  上轨: {bb.get('upper')}")
            print(f"  中轨: {bb.get('middle')}")
            print(f"  下轨: {bb.get('lower')}")

        # 备注
        if result.get('note'):
            print(f"\n备注: {result.get('note')}")

        print(f"\n截图路径: {result.get('screenshot_path')}")
        print(f"数据源: {result.get('source')}")

        print("\n" + "="*60)
        print("✅ 测试完成")
        print("="*60)

        # 显示原始响应（用于调试）
        if result.get('raw_response'):
            print("\n原始响应（调试）:")
            import json
            print(json.dumps(result['raw_response'], indent=2, ensure_ascii=False))

    else:
        print("\n❌ 识别失败")
        print("\n可能的原因：")
        print("1. API 密钥无效或额度不足")
        print("2. 网络连接问题")
        print("3. 图表加载失败")
        print("4. AI 模型识别失败")
        print("\n请查看日志获取详细信息：")
        print("docker logs quantdinger-backend --tail 50")


if __name__ == '__main__':
    test_vision_extraction()
