"""
测试所有页面接口
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_api(name, url, params=None, method="GET"):
    """测试单个API"""
    try:
        full_url = f"{BASE_URL}{url}"
        if method == "GET":
            response = requests.get(full_url, params=params, timeout=10)
        else:
            response = requests.post(full_url, json=params, timeout=10)

        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {name}")
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('code') == 1:
                    print(f"   返回: 成功")
                else:
                    print(f"   返回: {data.get('msg', 'Unknown error')}")
            except:
                print(f"   返回: HTML页面 (正常)")
        else:
            print(f"   错误: {response.text[:100]}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {name}")
        print(f"   错误: {str(e)}")
        print()
        return False

def main():
    print("=" * 70)
    print("QuantDinger 所有页面接口测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    results = []

    # 1. 健康检查
    print("🔍 基础服务")
    results.append(("健康检查", test_api("健康检查", "/api/health")))
    print()

    # 2. 认证相关
    print("🔐 认证服务")
    # results.append(("登录", test_api("登录", "/api/user/login", {"username": "alexbibihere", "password": "iam5323.."}, "POST")))
    print()

    # 3. 市场数据
    print("📊 市场数据")
    results.append(("市场搜索", test_api("市场搜索", "/api/market/search", {"query": "BTC"})))
    print()

    # 4. K线数据
    print("📈 K线数据")
    results.append(("K线数据", test_api("K线数据", "/api/kline", {"symbol": "BTCUSDT", "interval": "1h", "limit": 10})))
    print()

    # 5. 指标管理
    print("📊 指标管理")
    results.append(("获取指标列表", test_api("获取指标列表", "/api/indicator/list")))
    print()

    # 6. 策略相关
    print("💼 策略管理")
    results.append(("获取策略列表", test_api("获取策略列表", "/api/strategy/list")))
    print()

    # 7. 回测
    print("🔬 回测服务")
    results.append(("回测配置", test_api("回测配置", "/api/backtest/config")))
    print()

    # 8. AI分析
    print("🤖 AI分析")
    results.append(("AI聊天历史", test_api("AI聊天历史", "/api/ai/chat/history")))
    print()

    # 9. 涨幅榜分析
    print("📈 涨幅榜分析")
    results.append(("涨幅榜TOP5", test_api("涨幅榜TOP5", "/api/gainer-analysis/top-gainers", {"limit": 5, "market": "futures"})))
    print()

    # 10. HAMA监控
    print("🔔 HAMA监控")
    results.append(("HAMA监控状态", test_api("HAMA监控状态", "/api/hama-monitor/status")))
    print()

    # 11. 多交易所对比
    print("💱 多交易所对比")
    results.append(("交易所对比", test_api("交易所对比", "/api/multi-exchange/compare", {"market": "futures", "limit": 5})))
    results.append(("Binance涨幅榜", test_api("Binance涨幅榜", "/api/multi-exchange/binance", {"market": "futures", "limit": 3})))
    results.append(("OKX涨幅榜", test_api("OKX涨幅榜", "/api/multi-exchange/okx", {"market": "futures", "limit": 3})))
    print()

    # 12. 仪表板
    print("📊 仪表板")
    results.append(("仪表板数据", test_api("仪表板数据", "/api/dashboard/overview")))
    print()

    # 13. 系统设置
    print("⚙️ 系统设置")
    results.append(("系统配置", test_api("系统配置", "/api/settings/config")))
    print()

    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)

    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    print(f"\n总计: {total_count} 个接口")
    print(f"成功: {success_count} 个 ✅")
    print(f"失败: {total_count - success_count} 个 ❌")
    print(f"成功率: {success_count/total_count*100:.1f}%")

    print("\n详细结果:")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
