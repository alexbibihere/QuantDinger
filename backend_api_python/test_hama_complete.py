#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAMA 指标完整功能测试

测试本地 HAMA 计算器与 API 接口
"""
import requests
import json
import random
from datetime import datetime, timedelta


def generate_test_ohlcv_data(count=500, base_price=3000):
    """
    生成测试用的 OHLCV 数据

    Args:
        count: 数据条数
        base_price: 基准价格

    Returns:
        OHLCV 数据列表
    """
    ohlcv_data = []

    for i in range(count):
        timestamp = int((datetime.now() - timedelta(minutes=count-i)).timestamp() * 1000)

        # 随机生成 OHLC
        open_price = base_price + random.uniform(-50, 50)
        close_price = base_price + random.uniform(-50, 50)
        high_price = max(open_price, close_price) + random.uniform(0, 20)
        low_price = min(open_price, close_price) - random.uniform(0, 20)
        volume = random.uniform(100, 1000)

        ohlcv_data.append([timestamp, open_price, high_price, low_price, close_price, volume])

        # 更新基准价格
        base_price = close_price

    return ohlcv_data


def test_hama_api():
    """测试 HAMA API"""
    print('='*60)
    print('HAMA 指标 API 完整功能测试')
    print('='*60)

    # 1. 测试健康检查
    print('\n1. 测试健康检查...')
    try:
        response = requests.get('http://localhost:5000/api/hama/health')
        data = response.json()
        print(f'✅ 健康检查成功: {data}')
    except Exception as e:
        print(f'❌ 健康检查失败: {e}')
        return

    # 2. 生成测试数据
    print('\n2. 生成测试数据...')
    symbol = 'BTCUSDT'
    ohlcv_data = generate_test_ohlcv_data(count=500, base_price=3000)
    print(f'✅ 生成了 {len(ohlcv_data)} 条 {symbol} 的测试数据')

    # 3. 调用 HAMA 计算接口
    print(f'\n3. 调用 HAMA 计算接口...')
    try:
        response = requests.post(
            'http://localhost:5000/api/hama/calculate',
            json={
                'symbol': symbol,
                'ohlcv': ohlcv_data
            },
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()

            if result.get('success'):
                data = result.get('data', {})

                print('\n' + '='*60)
                print('HAMA 指标计算结果:')
                print('='*60)
                print(f"币种: {data.get('symbol')}")
                print(f"当前价格: {data.get('close', 0):.2f}")
                print(f"\nHAMA 蜡烛图:")
                hama = data.get('hama', {})
                print(f"  开盘: {hama.get('open', 0):.2f}")
                print(f"  最高: {hama.get('high', 0):.2f}")
                print(f"  最低: {hama.get('low', 0):.2f}")
                print(f"  收盘: {hama.get('close', 0):.2f}")
                print(f"  MA:   {hama.get('ma', 0):.2f}")
                print(f"  颜色: {hama.get('color', 'unknown')}")

                # 交叉信号
                if hama.get('cross_up'):
                    print(f"  信号: 🟢 金叉（买入信号）")
                elif hama.get('cross_down'):
                    print(f"  信号: 🔴 死叉（卖出信号）")
                else:
                    print(f"  信号: 无交叉")

                # 趋势
                trend = data.get('trend', {})
                direction = trend.get('direction', 'unknown')
                print(f"\n趋势: {direction}")

                if trend.get('rising'):
                    print(f"  MA 线: 上升")
                elif trend.get('falling'):
                    print(f"  MA 线: 下降")

                # 布林带
                bb = data.get('bollinger_bands', {})
                print(f"\n布林带:")
                print(f"  上轨: {bb.get('upper', 0):.2f}")
                print(f"  中轨: {bb.get('basis', 0):.2f}")
                print(f"  下轨: {bb.get('lower', 0):.2f}")
                print(f"  宽度: {bb.get('width', 0):.4f}")

                if bb.get('squeeze'):
                    print(f"  状态: 收缩")
                elif bb.get('expansion'):
                    print(f"  状态: 扩张")
                else:
                    print(f"  状态: 正常")

                print('='*60)
                print('\n✅ 所有测试通过！')

            else:
                print(f"❌ API 返回错误: {result.get('error')}")
        else:
            print(f'❌ HTTP 错误: {response.status_code}')
            print(f'响应: {response.text}')

    except Exception as e:
        print(f'❌ API 调用失败: {e}')


if __name__ == '__main__':
    test_hama_api()
