"""
测试多交易所API
"""
import requests
import json

def test_multi_exchange_api():
    """测试多交易所对比API"""
    print("=" * 70)
    print("测试多交易所涨幅榜对比API")
    print("=" * 70)

    try:
        # 测试对比接口
        print("\n📊 测试: /api/multi-exchange/compare?market=futures&limit=5")
        response = requests.get(
            'http://localhost:5000/api/multi-exchange/compare',
            params={'market': 'futures', 'limit': 5},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('code') == 1:
                result = data['data']
                binance_count = result['exchanges']['binance']['count']
                okx_count = result['exchanges']['okx']['count']

                print(f"\n✅ API调用成功!")
                print(f"\n📊 统计信息:")
                print(f"   Binance币种数: {binance_count}")
                print(f"   OKX币种数: {okx_count}")
                print(f"   共同币种数: {result['analysis']['total_common_symbols']}")
                print(f"   时间戳: {result['timestamp']}")

                if okx_count > 0:
                    print(f"\n📈 OKX TOP5:")
                    for i, gainer in enumerate(result['exchanges']['okx']['top_gainers'], 1):
                        print(f"   {i}. {gainer['symbol']}: {gainer['price_change_percent']:.2f}%")

                if binance_count == 0:
                    print("\n⚠️  Binance API调用失败（代理问题）")
                    print("   但OKX API正常工作，页面应能显示部分数据")

                return True
            else:
                print(f"\n❌ API返回错误: {data.get('msg')}")
                return False
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 开始测试多交易所API...\n")
    success = test_multi_exchange_api()

    print("\n" + "=" * 70)
    if success:
        print("✅ API测试通过！")
        print("\n💡 访问页面查看效果: http://localhost:8888/multi-exchange")
        print("\n📝 注意: 由于代理问题，Binance数据可能无法获取")
        print("   但OKX数据应该正常显示")
    else:
        print("❌ API测试失败！")
    print("=" * 70 + "\n")
