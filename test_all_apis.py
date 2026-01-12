#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantDinger API 全接口测试脚本
测试所有页面的 API 接口
"""
import requests
import json
import sys
import io
from typing import Dict, Any, List, Tuple

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置
BASE_URL = "http://localhost:5000"
DEFAULT_USER = "quantdinger"
DEFAULT_PASSWORD = "123456"

# 全局变量存储 token
auth_token = None
user_id = None


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg: str):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}[FAIL] {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")


def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def make_request(method: str, endpoint: str, data: Dict = None,
                 params: Dict = None, need_auth: bool = True) -> Tuple[bool, Any]:
    """
    发送 HTTP 请求

    Args:
        method: HTTP 方法 (GET, POST, PUT, DELETE)
        endpoint: API 端点
        data: 请求体数据
        params: URL 参数
        need_auth: 是否需要认证

    Returns:
        (是否成功, 响应数据)
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}

    if need_auth and auth_token:
        headers['Authorization'] = f"Bearer {auth_token}"

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, params=params, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=10)
        else:
            return False, f"不支持的 HTTP 方法: {method}"

        # 尝试解析 JSON
        try:
            response_data = response.json()
        except:
            response_data = response.text

        if response.status_code in [200, 201]:
            return True, response_data
        else:
            return False, f"HTTP {response.status_code}: {response_data}"

    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, "连接失败"
    except Exception as e:
        return False, str(e)


def test_health_check():
    """测试健康检查接口"""
    print_section("1. 健康检查")

    # 测试 /health
    success, data = make_request('GET', '/health', need_auth=False)
    if success:
        print_success("GET /health")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print_error(f"GET /health - {data}")

    # 测试 /api/health
    success, data = make_request('GET', '/api/health', need_auth=False)
    if success:
        print_success("GET /api/health")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print_error(f"GET /api/health - {data}")


def test_auth():
    """测试认证相关接口"""
    global auth_token, user_id

    print_section("2. 认证接口")

    # 登录
    login_data = {
        "username": DEFAULT_USER,
        "password": DEFAULT_PASSWORD
    }

    success, data = make_request('POST', '/api/user/login', data=login_data, need_auth=False)
    if success:
        print_success("POST /api/user/login (登录)")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # 提取 token - 支持多种响应格式
        if isinstance(data, dict):
            # 格式1: { code: 1, data: { token: ..., userinfo: {...} } }
            if 'data' in data and isinstance(data['data'], dict):
                auth_token = data['data'].get('token')
                user_info = data['data'].get('userinfo', {})
                user_id = user_info.get('id') or user_info.get('username')
            # 格式2: { result: { token: ..., id: ... } }
            elif 'result' in data and isinstance(data['result'], dict):
                auth_token = data['result'].get('token') or data['result'].get('id')
                user_id = data['result'].get('id')
            # 格式3: { token: ..., id: ... }
            elif 'token' in data:
                auth_token = data['token']
                user_id = data.get('id')
            else:
                auth_token = None
                user_id = None

        if auth_token:
            print_info(f"获取到 Token: {auth_token[:20]}...")
            print_info(f"用户 ID: {user_id}")
        else:
            print_error("未能从响应中提取 token")
            print_info(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return False
    else:
        print_error(f"POST /api/user/login - {data}")
        return False

    # 获取用户信息
    if auth_token:
        success, data = make_request('GET', '/api/user/info')
        if success:
            print_success("GET /api/user/info (获取用户信息)")
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
        else:
            print_error(f"GET /api/user/info - {data}")

    return True


def test_dashboard():
    """测试仪表板接口"""
    print_section("3. 仪表板接口")

    # 获取仪表板摘要
    success, data = make_request('GET', '/api/dashboard/summary')
    if success:
        print_success("GET /api/dashboard/summary")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/dashboard/summary - {data}")

    # 获取待处理订单
    success, data = make_request('GET', '/api/dashboard/pendingOrders')
    if success:
        print_success("GET /api/dashboard/pendingOrders")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/dashboard/pendingOrders - {data}")


def test_market():
    """测试市场数据接口"""
    print_section("4. 市场数据接口")

    # 获取市场类型
    success, data = make_request('GET', '/api/market/types')
    if success:
        print_success("GET /api/market/types")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/market/types - {data}")

    # 获取配置
    success, data = make_request('GET', '/api/market/config')
    if success:
        print_success("GET /api/market/config")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/market/config - {data}")

    # 获取热门标的 (加密货币)
    success, data = make_request('POST', '/api/market/symbols/hot',
                                 data={"market": "Crypto", "limit": 10})
    if success:
        print_success("POST /api/market/symbols/hot (热门标的)")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"POST /api/market/symbols/hot - {data}")

    # 搜索标的
    success, data = make_request('POST', '/api/market/symbols/search',
                                 data={"market": "Crypto", "keyword": "BTC", "limit": 5})
    if success:
        print_success("POST /api/market/symbols/search (搜索标的)")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"POST /api/market/symbols/search - {data}")

    # 获取自选股列表
    if user_id:
        success, data = make_request('POST', '/api/market/watchlist/get',
                                     data={"userid": user_id})
        if success:
            print_success("POST /api/market/watchlist/get (自选股)")
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        else:
            print_error(f"POST /api/market/watchlist/get - {data}")


def test_kline():
    """测试 K 线数据接口"""
    print_section("5. K 线数据接口")

    # 获取 K 线数据
    kline_params = {
        "market": "Crypto",
        "symbol": "BTC/USDT",
        "interval": "1d",
        "limit": 10
    }

    success, data = make_request('GET', '/api/kline/data', params=kline_params)
    if success:
        print_success("GET /api/kline/data (K线数据)")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/kline/data - {data}")


def test_indicator():
    """测试指标相关接口"""
    print_section("6. 指标管理接口")

    # 获取指标列表
    success, data = make_request('GET', '/api/indicator/list')
    if success:
        print_success("GET /api/indicator/list")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/indicator/list - {data}")

    # 获取内置指标
    success, data = make_request('GET', '/api/indicator/builtin')
    if success:
        print_success("GET /api/indicator/builtin")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/indicator/builtin - {data}")


def test_backtest():
    """测试回测接口"""
    print_section("7. 回测接口")

    # 获取回测历史
    success, data = make_request('GET', '/api/backtest/history')
    if success:
        print_success("GET /api/backtest/history")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/backtest/history - {data}")


def test_strategy():
    """测试策略相关接口"""
    print_section("8. 策略管理接口")

    # 获取策略列表
    success, data = make_request('GET', '/api/strategies')
    if success:
        print_success("GET /api/strategies")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/strategies - {data}")

    # 获取策略通知
    success, data = make_request('GET', '/api/strategies/notifications')
    if success:
        print_success("GET /api/strategies/notifications")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/strategies/notifications - {data}")


def test_analysis():
    """测试 AI 分析接口"""
    print_section("9. AI 分析接口")

    # 获取分析历史
    if user_id:
        success, data = make_request('POST', '/api/analysis/getHistoryList',
                                     data={"userid": user_id, "page": 1, "pagesize": 10})
        if success:
            print_success("POST /api/analysis/getHistoryList")
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        else:
            print_error(f"POST /api/analysis/getHistoryList - {data}")

    # 获取聊天历史
    if user_id:
        success, data = make_request('POST', '/api/ai/chat/history',
                                     data={"userid": user_id})
        if success:
            print_success("POST /api/ai/chat/history")
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
        else:
            print_error(f"POST /api/ai/chat/history - {data}")


def test_credentials():
    """测试交易所凭证接口"""
    print_section("10. 交易所凭证接口")

    # 获取凭证列表
    success, data = make_request('GET', '/api/credentials/list')
    if success:
        print_success("GET /api/credentials/list")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/credentials/list - {data}")


def test_settings():
    """测试系统设置接口"""
    print_section("11. 系统设置接口")

    # 获取配置 schema
    success, data = make_request('GET', '/api/settings/schema')
    if success:
        print_success("GET /api/settings/schema")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/settings/schema - {data}")

    # 获取配置值
    success, data = make_request('GET', '/api/settings/values')
    if success:
        print_success("GET /api/settings/values")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"GET /api/settings/values - {data}")

    # 获取菜单底部配置
    success, data = make_request('POST', '/api/market/menuFooterConfig', data={})
    if success:
        print_success("POST /api/market/menuFooterConfig")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"POST /api/market/menuFooterConfig - {data}")


def test_indicator_code():
    """测试指标代码相关接口"""
    print_section("12. 指标代码接口")

    # 验证指标代码
    test_code = """
import pandas as pd
import numpy as np

def calculate(df):
    df = df.copy()
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma60'] = df['close'].rolling(window=60).mean()
    df['signal'] = 'hold'
    df.loc[df['sma20'] > df['sma60'], 'signal'] = 'buy'
    df.loc[df['sma20'] < df['sma60'], 'signal'] = 'sell'
    return df
"""

    success, data = make_request('POST', '/api/indicator/verify',
                                 data={"code": test_code})
    if success:
        print_success("POST /api/indicator/verify (验证指标代码)")
        print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
    else:
        print_error(f"POST /api/indicator/verify - {data}")


def main():
    """主函数"""
    print(f"\n{Colors.BOLD}QuantDinger API 全接口测试{Colors.RESET}")
    print(f"测试地址: {BASE_URL}")
    print(f"默认用户: {DEFAULT_USER}")
    print(f"测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 健康检查
        test_health_check()

        # 2. 认证
        if not test_auth():
            print_error("认证失败，终止测试")
            sys.exit(1)

        # 3. 仪表板
        test_dashboard()

        # 4. 市场数据
        test_market()

        # 5. K 线数据
        test_kline()

        # 6. 指标管理
        test_indicator()

        # 7. 回测
        test_backtest()

        # 8. 策略管理
        test_strategy()

        # 9. AI 分析
        test_analysis()

        # 10. 交易所凭证
        test_credentials()

        # 11. 系统设置
        test_settings()

        # 12. 指标代码
        test_indicator_code()

        # 完成
        print_section("测试完成")
        print_success("所有接口测试完成")
        print_info("请查看上面的输出，确认所有接口都正常工作")

    except KeyboardInterrupt:
        print_error("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
