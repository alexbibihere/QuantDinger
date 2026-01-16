"""
测试所有API接口
"""
import requests
import json
import sys
import io
from datetime import datetime

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"

# 测试结果
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_api(name, method, url, data=None, params=None, auth_token=None):
    """测试单个API"""
    test_results["total"] += 1
    headers = {}

    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        print(f"\n{'='*80}")
        print(f"测试: {name}")
        print(f"方法: {method} {url}")
        if params:
            print(f"参数: {params}")
        if data:
            print(f"数据: {json.dumps(data, ensure_ascii=False)}")

        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", params=params, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{url}", json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{url}", headers=headers, timeout=30)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        print(f"状态码: {response.status_code}")

        if response.status_code < 400:
            test_results["passed"] += 1
            print(f"✅ 通过")

            # 显示部分响应数据
            try:
                resp_data = response.json()
                if isinstance(resp_data, dict):
                    if "success" in resp_data:
                        print(f"响应: success={resp_data.get('success')}, data={str(resp_data.get('data', {}))[:100]}")
                    else:
                        print(f"响应: {json.dumps(resp_data, ensure_ascii=False)[:200]}")
                elif isinstance(resp_data, list) and len(resp_data) > 0:
                    print(f"响应: 数组长度={len(resp_data)}, 第一项={str(resp_data[0])[:100]}")
            except:
                print(f"响应: {response.text[:200]}")
        else:
            test_results["failed"] += 1
            print(f"❌ 失败")
            print(f"错误: {response.text[:200]}")
            test_results["errors"].append({
                "name": name,
                "url": url,
                "status": response.status_code,
                "error": response.text[:200]
            })

    except Exception as e:
        test_results["failed"] += 1
        print(f"❌ 异常: {str(e)}")
        test_results["errors"].append({
            "name": name,
            "url": url,
            "error": str(e)
        })

def main():
    print("="*80)
    print(f"QuantDinger API 测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 获取认证token
    print("\n" + "="*80)
    print("步骤1: 登录获取token")
    print("="*80)
    test_api(
        "用户登录",
        "POST",
        "/api/user/login",
        data={"username": "quantdinger", "password": "123456"}
    )

    # 获取token
    auth_token = None
    try:
        response = requests.post(f"{BASE_URL}/api/user/login",
                                json={"username": "quantdinger", "password": "123456"},
                                timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("token"):
                auth_token = data["data"]["token"]
                print(f"\n✅ 登录成功，Token: {auth_token[:50]}...")
    except:
        print("\n⚠️  登录失败，部分需要认证的API可能无法测试")

    # ==================== 健康检查 ====================
    print("\n\n" + "="*80)
    print("【健康检查】")
    print("="*80)
    test_api("健康检查", "GET", "/api/health")

    # ==================== 市场数据 ====================
    print("\n\n" + "="*80)
    print("【市场数据】")
    print("="*80)
    test_api("获取市场行情", "GET", "/api/market/ticker", params={"symbol": "BTCUSDT"})
    test_api("搜索市场", "GET", "/api/market/search", params={"query": "BTC"})

    # ==================== K线数据 ====================
    print("\n\n" + "="*80)
    print("【K线数据】")
    print("="*80)
    test_api("获取K线数据", "GET", "/api/kline/data",
             params={"symbol": "BTCUSDT", "interval": "1h", "limit": 100})

    # ==================== TradingView Scanner ====================
    print("\n\n" + "="*80)
    print("【TradingView Scanner】")
    print("="*80)
    test_api("获取永续合约", "GET", "/api/tradingview-scanner/perpetuals", params={"limit": 10})
    test_api("获取涨幅榜", "GET", "/api/tradingview-scanner/top-gainers", params={"limit": 10})
    test_api("获取关注列表", "GET", "/api/tradingview-scanner/watchlist", params={"limit": 10})

    # ==================== 涨幅榜统计 ====================
    print("\n\n" + "="*80)
    print("【涨幅榜统计】")
    print("="*80)
    test_api("获取频繁出现币种", "GET", "/api/gainer-stats/frequent-symbols",
             params={"limit": 10, "days": 7})
    test_api("获取今日涨幅榜", "GET", "/api/gainer-stats/today")

    # ==================== 涨幅分析 ====================
    print("\n\n" + "="*80)
    print("【涨幅分析】")
    print("="*80)
    test_api("批量分析涨幅", "POST", "/api/gainer-analysis/analyze-batch",
             data={"symbols": ["BTCUSDT", "ETHUSDT"]})

    # ==================== HAMA监控 ====================
    print("\n\n" + "="*80)
    print("【HAMA监控】")
    print("="*80)
    test_api("获取HAMA信号", "GET", "/api/hama-monitor/signals", params={"limit": 10})
    test_api("获取HAMA状态", "GET", "/api/hama-monitor/status")

    # ==================== 多交易所对比 ====================
    print("\n\n" + "="*80)
    print("【多交易所对比】")
    print("="*80)
    test_api("对比多交易所涨幅", "GET", "/api/multi-exchange/compare", params={"market": "futures", "limit": 10})

    # ==================== SSE实时价格 ====================
    print("\n\n" + "="*80)
    print("【SSE实时价格】")
    print("="*80)
    test_api("SSE价格流", "GET", "/api/sse/prices")

    # ==================== 指标管理 (需要认证) ====================
    if auth_token:
        print("\n\n" + "="*80)
        print("【指标管理】")
        print("="*80)
        test_api("获取指标列表", "GET", "/api/indicator/list", auth_token=auth_token)
        test_api("获取内置指标", "GET", "/api/indicator/builtin", auth_token=auth_token)

        # ==================== 策略管理 (需要认证) ====================
        print("\n\n" + "="*80)
        print("【策略管理】")
        print("="*80)
        test_api("获取策略列表", "GET", "/api/strategy/list", auth_token=auth_token)
        test_api("获取交易状态", "GET", "/api/strategy/trading-status", auth_token=auth_token)

        # ==================== 回测 (需要认证) ====================
        print("\n\n" + "="*80)
        print("【回测】")
        print("="*80)
        test_api("获取回测配置", "GET", "/api/backtest/config", auth_token=auth_token)

        # ==================== 仪表板 (需要认证) ====================
        print("\n\n" + "="*80)
        print("【仪表板】")
        print("="*80)
        test_api("获取仪表板数据", "GET", "/api/dashboard/overview", auth_token=auth_token)

        # ==================== AI分析 (需要认证) ====================
        print("\n\n" + "="*80)
        print("【AI分析】")
        print("="*80)
        test_api("AI多代理分析", "POST", "/api/analysis/multi",
                data={"symbol": "BTCUSDT", "exchange": "binance"},
                auth_token=auth_token)

        # ==================== 设置 (需要认证) ====================
        print("\n\n" + "="*80)
        print("【设置】")
        print("="*80)
        test_api("获取系统设置", "GET", "/api/settings", auth_token=auth_token)

    # ==================== 总结 ====================
    print("\n\n" + "="*80)
    print("【测试总结】")
    print("="*80)
    print(f"总计: {test_results['total']} 个API")
    print(f"✅ 通过: {test_results['passed']} 个")
    print(f"❌ 失败: {test_results['failed']} 个")
    print(f"通过率: {test_results['passed']/test_results['total']*100:.1f}%")

    if test_results["errors"]:
        print("\n失败的API:")
        for err in test_results["errors"]:
            print(f"  - {err['name']}: {err.get('error', err.get('status', ''))}")

    print("="*80)

if __name__ == "__main__":
    main()
