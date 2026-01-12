"""
测试涨幅榜统计功能
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_gainer_stats():
    print("=" * 80)
    print("测试涨幅榜统计功能")
    print("=" * 80)

    # 1. 获取统计数据
    print("\n1. 获取涨幅榜统计数据 (最近7天, 前10个币种)")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/api/gainer-stats/frequent-symbols?limit=10&days=7")
    data = response.json()
    print(f"状态: {data.get('success')}")
    print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

    # 2. 获取涨幅榜数据
    print("\n2. 获取涨幅榜数据 (前10个)")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/api/tradingview-scanner/top-gainers?limit=10")
    data = response.json()
    print(f"状态: {data.get('success')}")
    if data.get('success') and data.get('data'):
        print(f"币种数: {len(data['data'])}")
        for i, coin in enumerate(data['data'][:5], 1):
            print(f"{i}. {coin['symbol']:15} 涨跌: {coin.get('change_percentage', 0):>+6.2f}%")

    # 3. 获取今日涨幅榜
    print("\n3. 获取今日涨幅榜币种")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/api/gainer-stats/today")
    data = response.json()
    print(f"状态: {data.get('success')}")
    print(f"今日币种数: {data.get('count', 0)}")
    if data.get('data'):
        print(f"币种列表: {data['data'][:10]}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_gainer_stats()
