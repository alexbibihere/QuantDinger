#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证接口修复的脚本
在重启后端后运行此脚本验证修复是否成功
"""
import requests
import json
import sys
import io

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def test_kline_fix():
    """测试 K 线接口修复"""
    print_section("测试 K 线接口修复")

    # 首先登录获取 token
    login_resp = requests.post(f"{BASE_URL}/api/user/login",
                                json={"username": "quantdinger", "password": "123456"})
    if login_resp.status_code != 200:
        print_error("登录失败")
        return False

    token = login_resp.json().get('data', {}).get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    # 测试 K 线接口
    kline_data = {
        "market": "Crypto",
        "symbol": "BTC/USDT",
        "timeframe": "1D",
        "limit": 10
    }

    response = requests.post(f"{BASE_URL}/api/kline",
                            json=kline_data,
                            headers=headers,
                            timeout=10)

    if response.status_code == 200:
        print_success("K 线接口修复成功！")
        data = response.json()
        print_info(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        return True
    else:
        print_error(f"K 线接口仍然失败: HTTP {response.status_code}")
        print_error(f"响应: {response.text[:200]}")
        return False


def test_backtest_fix():
    """测试回测接口修复"""
    print_section("测试回测接口修复")

    # 首先登录获取 token
    login_resp = requests.post(f"{BASE_URL}/api/user/login",
                                json={"username": "quantdinger", "password": "123456"})
    if login_resp.status_code != 200:
        print_error("登录失败")
        return False

    token = login_resp.json().get('data', {}).get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    # 测试回测历史接口
    response = requests.post(f"{BASE_URL}/api/backtest/history",
                            json={"page": 1, "pageSize": 10},
                            headers=headers,
                            timeout=10)

    if response.status_code == 200:
        print_success("回测接口修复成功！")
        data = response.json()
        print_info(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        return True
    else:
        print_error(f"回测接口仍然失败: HTTP {response.status_code}")
        print_error(f"响应: {response.text[:200]}")
        return False


def test_indicator_fix():
    """测试指标接口修复"""
    print_section("测试指标接口修复")

    # 首先登录获取 token
    login_resp = requests.post(f"{BASE_URL}/api/user/login",
                                json={"username": "quantdinger", "password": "123456"})
    if login_resp.status_code != 200:
        print_error("登录失败")
        return False

    token = login_resp.json().get('data', {}).get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    # 测试指标列表接口 - 传递字符串类型的用户名（之前会失败）
    response = requests.post(f"{BASE_URL}/api/indicator/getIndicators",
                            json={"userid": "quantdinger"},  # 传入字符串而不是整数
                            headers=headers,
                            timeout=10)

    if response.status_code == 200:
        print_success("指标接口修复成功！")
        data = response.json()
        print_info(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        return True
    else:
        print_error(f"指标接口仍然失败: HTTP {response.status_code}")
        print_error(f"响应: {response.text[:200]}")
        return False


def main():
    print(f"\n{Colors.BOLD}QuantDinger 接口修复验证{Colors.RESET}")
    print(f"验证时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 测试 K 线接口
    results.append(("K 线接口", test_kline_fix()))

    # 测试回测接口
    results.append(("回测接口", test_backtest_fix()))

    # 测试指标接口
    results.append(("指标接口", test_indicator_fix()))

    # 汇总结果
    print_section("验证结果汇总")

    for name, success in results:
        status = f"{Colors.GREEN}✓ 通过{Colors.RESET}" if success else f"{Colors.RED}✗ 失败{Colors.RESET}"
        print(f"{name:20s} {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n总计: {passed}/{total} 个接口修复成功")

    if passed == total:
        print_success("\n🎉 所有接口修复成功！")
        return 0
    else:
        print_error("\n❌ 部分接口修复失败，请检查后端日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
