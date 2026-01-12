"""
测试TradingView永续合约API
"""
import requests
import json

def test_futures_api():
    """测试获取永续合约涨幅榜"""

    print("=" * 60)
    print("测试TradingView永续合约API")
    print("=" * 60)

    # 测试获取永续合约涨幅榜
    print("\n📊 获取币安USDT永续合约涨幅榜TOP5...")

    try:
        response = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={
                'limit': 5,
                'market': 'futures'  # 测试合约市场
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('success') and data.get('data'):
                gainers = data['data']['gainers']

                print(f"\n✅ 成功获取 {len(gainers)} 个永续合约涨幅榜币种:\n")

                for i, gainer in enumerate(gainers, 1):
                    symbol = gainer.get('symbol', 'N/A')
                    change = gainer.get('price_change_percent', 0)
                    price = gainer.get('price', 0)
                    volume = gainer.get('volume', 0)
                    source = gainer.get('source', 'Unknown')

                    # 格式化涨跌幅显示
                    change_color = "📈" if change > 0 else "📉"
                    change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"

                    print(f"{i}. {symbol}")
                    print(f"   价格: ${price:.4f}")
                    print(f"   涨跌幅: {change_color} {change_str}")
                    print(f"   成交量: {volume:,.0f}")
                    print(f"   数据源: {source}")
                    print()

                print("✨ 测试成功！TradingView永续合约API工作正常！")
                return True
            else:
                print(f"❌ API返回错误: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确认服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_spot_vs_futures():
    """对比现货和合约数据源"""

    print("\n" + "=" * 60)
    print("对比现货 vs 永续合约数据源")
    print("=" * 60)

    try:
        # 获取现货数据
        spot_response = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={'limit': 3, 'market': 'spot'},
            timeout=10
        )

        # 获取合约数据
        futures_response = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={'limit': 3, 'market': 'futures'},
            timeout=10
        )

        if spot_response.status_code == 200 and futures_response.status_code == 200:
            spot_data = spot_response.json()['data']['gainers']
            futures_data = futures_response.json()['data']['gainers']

            print("\n📈 现货市场 TOP3:")
            for i, g in enumerate(spot_data, 1):
                print(f"  {i}. {g['symbol']}: {g['price_change_percent']:.2f}% ({g.get('source', 'N/A')})")

            print("\n📊 永续合约 TOP3:")
            for i, g in enumerate(futures_data, 1):
                print(f"  {i}. {g['symbol']}: {g['price_change_percent']:.2f}% ({g.get('source', 'N/A')})")

            print("\n✅ 数据源对比完成！")
            return True
        else:
            print("❌ 获取数据失败")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == '__main__':
    print("\n🚀 开始测试永续合约API...\n")

    # 测试1: 获取永续合约数据
    test1 = test_futures_api()

    # 测试2: 对比现货和合约
    test2 = test_spot_vs_futures()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"永续合约API: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"数据源对比: {'✅ 通过' if test2 else '❌ 失败'}")
    print("=" * 60)

    if test1 and test2:
        print("\n🎉 所有测试通过！永续合约功能已成功实现！")
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
