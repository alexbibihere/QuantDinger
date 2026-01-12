"""
测试TradingView永续合约API - 完整版
"""
import requests
import json

def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)

def test_futures_top_gainers():
    """测试永续合约涨幅榜"""

    print_separator("🚀 测试TradingView永续合约API")

    print("\n📊 正在获取币安USDT永续合约涨幅榜TOP5...")

    try:
        response = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={'limit': 5, 'market': 'futures'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('code') == 1 and data.get('data'):
                result = data['data']
                gainers = result['symbols']

                print(f"\n✅ 成功获取 {result['count']} 个永续合约涨幅榜币种")
                print(f"🕐 时间戳: {result['timestamp']}")
                print(f"📈 市场: {result['market']}")

                print("\n" + "-" * 70)
                print(f"{'排名':<4} {'币种':<12} {'价格':<12} {'涨跌幅':<10} {'成交量':<15} {'建议':<8} {'置信度':<8}")
                print("-" * 70)

                for i, gainer in enumerate(gainers, 1):
                    symbol = gainer.get('symbol', 'N/A')
                    price = gainer.get('price', 0)
                    change = gainer.get('price_change_percent', 0)
                    volume = gainer.get('volume', 0)

                    hama = gainer.get('hama_analysis', {})
                    recommendation = hama.get('recommendation', 'N/A')
                    confidence = hama.get('confidence', 0)

                    # 格式化
                    change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
                    price_str = f"${price:.4f}" if price < 1 else f"${price:.2f}"
                    volume_str = f"{volume:,.0f}" if volume > 1000000 else f"{volume:,.2f}"
                    confidence_str = f"{confidence*100:.0f}%"

                    # 颜色标记（用符号代替）
                    trend_icon = "📈" if change > 0 else "📉"
                    rec_icon = {"BUY": "✅", "SELL": "❌", "HOLD": "⏸️"}.get(recommendation, "❓")

                    print(f"{i:<4} {symbol:<12} {price_str:<12} {trend_icon} {change_str:<8} {volume_str:<15} {rec_icon} {recommendation:<7} {confidence_str:<8}")

                print("-" * 70)
                print("\n✨ 永续合约API测试成功！")
                return True
            else:
                print(f"❌ API返回错误: {data.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_spot_vs_futures():
    """对比现货和永续合约"""

    print_separator("📊 对比现货 vs 永续合约")

    try:
        # 获取现货数据
        spot_resp = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={'limit': 5, 'market': 'spot'},
            timeout=30
        )

        # 获取永续合约数据
        futures_resp = requests.get(
            'http://localhost:5000/api/gainer-analysis/top-gainers',
            params={'limit': 5, 'market': 'futures'},
            timeout=30
        )

        if spot_resp.status_code == 200 and futures_resp.status_code == 200:
            spot_data = spot_resp.json()['data']['symbols']
            futures_data = futures_resp.json()['data']['symbols']

            print("\n📈 现货市场 TOP5:")
            print(f"{'排名':<4} {'币种':<12} {'涨跌幅':<10} {'数据源':<15}")
            print("-" * 50)
            for i, g in enumerate(spot_data, 1):
                source = g.get('hama_analysis', {}).get('data_source', 'Unknown')
                print(f"{i:<4} {g['symbol']:<12} {g['price_change_percent']:>7.2f}%     {source:<15}")

            print("\n📊 永续合约 TOP5:")
            print(f"{'排名':<4} {'币种':<12} {'涨跌幅':<10} {'数据源':<15}")
            print("-" * 50)
            for i, g in enumerate(futures_data, 1):
                source = g.get('hama_analysis', {}).get('data_source', 'Unknown')
                print(f"{i:<4} {g['symbol']:<12} {g['price_change_percent']:>7.2f}%     {source:<15}")

            print("\n✅ 数据源对比完成！")
            return True
        else:
            print("❌ 获取数据失败")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_hama_monitor_integration():
    """测试HAMA监控是否能使用永续合约"""

    print_separator("🔍 测试HAMA监控集成")

    try:
        # 首先检查HAMA监控状态
        status_resp = requests.get(
            'http://localhost:5000/api/hama-monitor/status',
            timeout=10
        )

        if status_resp.status_code == 200:
            status = status_resp.json()
            print(f"\n📊 HAMA监控状态:")
            print(f"   运行中: {'✅ 是' if status.get('running') else '❌ 否'}")
            print(f"   监控币种数: {status.get('symbol_count', 0)}")
            print(f"   信号总数: {status.get('signal_count', 0)}")

            print("\n💡 提示: 在前端页面可以选择市场类型(现货/永续合约)添加涨幅榜")
            print("   URL: http://localhost:8888/hama-monitor")
            return True
        else:
            print("⚠️  无法获取HAMA监控状态")
            return False

    except Exception as e:
        print(f"⚠️  错误: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  🔥 TradingView永续合约API - 完整测试")
    print("=" * 70)

    results = {}

    # 测试1: 永续合约涨幅榜
    results['futures_api'] = test_futures_top_gainers()

    # 测试2: 现货vs永续合约对比
    results['comparison'] = test_spot_vs_futures()

    # 测试3: HAMA监控集成
    results['hama_monitor'] = test_hama_monitor_integration()

    # 总结
    print_separator("📋 测试总结")

    print(f"\n永续合约API:      {'✅ 通过' if results.get('futures_api') else '❌ 失败'}")
    print(f"数据源对比:       {'✅ 通过' if results.get('comparison') else '❌ 失败'}")
    print(f"HAMA监控集成:     {'✅ 通过' if results.get('hama_monitor') else '❌ 失败'}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 所有测试通过！永续合约功能已成功实现！")
        print("=" * 70)
        print("\n🚀 下一步:")
        print("   1. 访问前端: http://localhost:8888")
        print("   2. 打开HAMA监控: http://localhost:8888/hama-monitor")
        print("   3. 选择市场类型为 '永续合约'")
        print("   4. 点击'添加涨幅榜'开始监控永续合约信号")
        print("=" * 70 + "\n")
    else:
        print("  ⚠️  部分测试失败，请检查后端日志")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
