#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证涨幅榜API是否正常工作
"""

import requests
import json
import sys

def test_backend_health():
    """测试后端健康检查"""
    print("1️⃣ 测试后端健康检查...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ 后端正常运行")
            return True
        else:
            print(f"   ❌ 后端返回错误: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 后端连接失败: {str(e)}")
        return False

def test_login():
    """测试登录"""
    print("\n2️⃣ 测试用户登录...")
    try:
        response = requests.post(
            "http://localhost:5000/api/user/login",
            json={"username": "quantdinger", "password": "123456"},
            timeout=5
        )
        if response.status_code == 200:
            print("   ✅ 登录成功")
            return response.cookies.get_dict()
        else:
            print(f"   ❌ 登录失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ 登录请求失败: {str(e)}")
        return None

def test_gainer_analysis_api(cookies=None):
    """测试涨幅榜API"""
    print("\n3️⃣ 测试涨幅榜分析API...")
    try:
        headers = {}
        if cookies:
            headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])

        response = requests.get(
            "http://localhost:5000/api/gainer-analysis/top-gainers?limit=3&market=spot",
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                symbols = data.get("data", {}).get("symbols", [])
                print(f"   ✅ API正常工作 (获取到 {len(symbols)} 个币种)")

                if symbols:
                    print(f"\n   示例数据:")
                    for i, symbol in enumerate(symbols[:2], 1):
                        print(f"   {i}. {symbol.get('symbol')}: {symbol.get('price_change_percent', 0):.2f}%")

                return True
            else:
                print(f"   ⚠️ API返回错误: {data.get('message')}")
                return False
        elif response.status_code == 404:
            print(f"   ❌ API未找到(404) - 可能后端未重启以加载新路由")
            print(f"   💡 解决方法: 运行 docker compose restart backend")
            return False
        else:
            print(f"   ❌ API请求失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API请求异常: {str(e)}")
        return False

def test_single_symbol_analysis(cookies=None):
    """测试单个币种分析"""
    print("\n4️⃣ 测试单个币种分析API...")
    try:
        headers = {}
        if cookies:
            headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])

        response = requests.post(
            "http://localhost:5000/api/gainer-analysis/analyze-symbol",
            headers=headers,
            json={"symbol": "BTCUSDT"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data.get("data", {})
                print(f"   ✅ 单个币种分析成功")
                print(f"   币种: {result.get('symbol')}")
                print(f"   趋势: {result.get('hama_trend')}")
                print(f"   形态: {result.get('candle_pattern')}")
                print(f"   建议: {result.get('recommendation')}")
                print(f"   置信度: {result.get('confidence', 0)*100:.1f}%")
                return True
            else:
                print(f"   ⚠️ 分析返回错误: {data.get('message')}")
                return False
        else:
            print(f"   ❌ 分析请求失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 分析请求异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("QuantDinger 涨幅榜API快速验证")
    print("=" * 60)

    # 测试序列
    results = {}

    results["health"] = test_backend_health()

    if not results["health"]:
        print("\n❌ 后端未运行,请先启动服务")
        print("   运行: 一键部署.bat")
        return False

    cookies = test_login()
    results["login"] = cookies is not None

    if results["login"]:
        results["gainer_api"] = test_gainer_analysis_api(cookies)
        results["single_analysis"] = test_single_symbol_analysis(cookies)
    else:
        results["gainer_api"] = False
        results["single_analysis"] = False

    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有测试通过! 涨幅榜功能正常工作")
        print("\n📱 现在可以访问前端使用:")
        print("   http://localhost:8888/gainer-analysis")
    else:
        print("\n⚠️ 部分测试未通过")
        if not results.get("gainer_api"):
            print("\n💡 如果API返回404,说明后端未重启以加载新路由")
            print("   请执行: docker compose restart backend")

    print()
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
