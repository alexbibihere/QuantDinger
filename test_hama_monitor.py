#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAMA信号监控服务测试脚本
测试监控服务的各项功能
"""

import sys
import os
import time
import requests
from datetime import datetime

# 配置
API_BASE = "http://localhost:5000"
USERNAME = "quantdinger"
PASSWORD = "123456"


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")


def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")


def print_info(text):
    """打印信息"""
    print(f"ℹ️  {text}")


def login():
    """登录获取session"""
    print_header("1. 用户登录")

    try:
        response = requests.post(
            f"{API_BASE}/api/user/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )

        if response.status_code == 200:
            print_success("登录成功")
            # 返回cookies
            return response.cookies
        else:
            print_error(f"登录失败: HTTP {response.status_code}")
            return None

    except Exception as e:
        print_error(f"登录请求失败: {str(e)}")
        return None


def test_get_monitor_status(cookies):
    """测试获取监控状态"""
    print_header("2. 获取监控状态")

    try:
        response = requests.get(
            f"{API_BASE}/api/hama-monitor/status",
            cookies=cookies,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                status = data["data"]
                print_success("获取监控状态成功")
                print(f"   运行状态: {'运行中' if status['running'] else '已停止'}")
                print(f"   监控币种: {status['symbol_count']} 个")
                print(f"   信号总数: {status['total_signals']} 条")
                print(f"   检查间隔: {status['check_interval']} 秒")
                print(f"   冷却时间: {status['signal_cooldown']} 秒")
                return status
            else:
                print_error(f"API返回错误: {data.get('message')}")
                return None
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return None

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return None


def test_start_monitor(cookies):
    """测试启动监控"""
    print_header("3. 启动监控服务")

    try:
        response = requests.post(
            f"{API_BASE}/api/hama-monitor/start",
            cookies=cookies,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success(data.get("message", "监控启动成功"))
                return True
            else:
                print_error(f"启动失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def test_add_top_gainers(cookies):
    """测试添加涨幅榜"""
    print_header("4. 添加涨幅榜币种")

    try:
        response = requests.post(
            f"{API_BASE}/api/hama-monitor/symbols/add-top-gainers",
            cookies=cookies,
            json={"limit": 5, "market": "spot"},
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data["data"]
                print_success(f"添加涨幅榜成功")
                print(f"   总计: {result['total']} 个")
                print(f"   新增: {result['added']} 个")
                print(f"   已存在: {result['already_monitored']} 个")
                return True
            else:
                print_error(f"添加失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def test_get_monitored_symbols(cookies):
    """测试获取监控币种列表"""
    print_header("5. 获取监控币种列表")

    try:
        response = requests.get(
            f"{API_BASE}/api/hama-monitor/symbols",
            cookies=cookies,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                symbols = data["data"]["symbols"]
                print_success(f"获取监控币种列表成功,共 {len(symbols)} 个")

                if symbols:
                    print(f"\n   监控中的币种:")
                    for i, symbol in enumerate(symbols[:10], 1):
                        last_signal = symbol.get('last_signal') or '-'
                        print(f"   {i:2}. {symbol['symbol']:12} {symbol['market_type']:6} 最后信号: {last_signal}")

                    if len(symbols) > 10:
                        print(f"   ... 还有 {len(symbols) - 10} 个币种")

                return True
            else:
                print_error(f"获取失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def test_add_symbol(cookies, symbol="ETHUSDT"):
    """测试添加单个币种"""
    print_header(f"6. 添加监控币种: {symbol}")

    try:
        response = requests.post(
            f"{API_BASE}/api/hama-monitor/symbols/add",
            cookies=cookies,
            json={"symbol": symbol, "market_type": "spot"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success(data.get("message", f"已添加 {symbol}"))
                return True
            else:
                print_error(f"添加失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def test_wait_for_signals(cookies, wait_time=30):
    """等待信号产生"""
    print_header(f"7. 等待信号产生 (等待 {wait_time} 秒)")

    print_info("监控正在运行,等待检测HAMA交叉信号...")
    print_info("提示: 这可能需要较长时间,取决于市场走势")

    for i in range(wait_time):
        remaining = wait_time - i
        print(f"   剩余等待时间: {remaining} 秒...", end="\r")
        time.sleep(1)

    print("\n")

    # 检查是否有新信号
    try:
        response = requests.get(
            f"{API_BASE}/api/hama-monitor/signals",
            cookies=cookies,
            params={"limit": 10},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                signals = data["data"]["signals"]
                print_success(f"当前信号数量: {len(signals)}")

                if signals:
                    print(f"\n   最近的信号:")
                    for i, signal in enumerate(signals[:5], 1):
                        signal_type = signal['signal_type']
                        type_text = "📈 涨" if signal_type == "UP" else "📉 跌"
                        print(f"   {i}. {signal['symbol']:12} {type_text}  "
                              f"价格: {signal['price']:.4f}  "
                              f"时间: {signal['timestamp']}")
                else:
                    print_info("暂无信号产生,这是正常现象")
                    print_info("HAMA信号需要满足交叉条件才会触发")

                return True

        return False

    except Exception as e:
        print_error(f"获取信号失败: {str(e)}")
        return False


def test_get_signals(cookies):
    """测试获取信号历史"""
    print_header("8. 获取信号历史")

    try:
        response = requests.get(
            f"{API_BASE}/api/hama-monitor/signals",
            cookies=cookies,
            params={"limit": 20},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                signals = data["data"]["signals"]
                print_success(f"获取信号历史成功,共 {len(signals)} 条")

                if signals:
                    print(f"\n   信号历史:")
                    for i, signal in enumerate(signals[:10], 1):
                        signal_type = signal['signal_type']
                        type_text = "📈 涨" if signal_type == "UP" else "📉 跌"
                        print(f"   {i:2}. {signal['symbol']:12} {type_text}  "
                              f"价格: {signal['price']:8.4f}  "
                              f"{signal['timestamp']}")

                return True
            else:
                print_error(f"获取失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def test_stop_monitor(cookies):
    """测试停止监控"""
    print_header("9. 停止监控服务")

    try:
        response = requests.post(
            f"{API_BASE}/api/hama-monitor/stop",
            cookies=cookies,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success(data.get("message", "监控停止成功"))
                return True
            else:
                print_error(f"停止失败: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP错误: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print_header("HAMA信号监控服务测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_BASE}")

    # 测试步骤
    cookies = login()
    if not cookies:
        print_error("无法登录,测试终止")
        return False

    # 获取初始状态
    initial_status = test_get_monitor_status(cookies)

    # 启动监控
    test_start_monitor(cookies)

    # 添加涨幅榜
    test_add_top_gainers(cookies)

    # 添加单个币种
    test_add_symbol(cookies, "BTCUSDT")

    # 获取监控列表
    test_get_monitored_symbols(cookies)

    # 等待信号 (可选,注释掉以跳过等待)
    print_info("\n提示: 等待信号测试可能需要较长时间")
    print_info("如需跳过,请按 Ctrl+C 中断测试\n")

    try:
        test_wait_for_signals(cookies, wait_time=30)
    except KeyboardInterrupt:
        print_info("\n用户中断等待,继续测试")

    # 获取信号历史
    test_get_signals(cookies)

    # 停止监控 (可选)
    print_info("\n是否停止监控服务?")
    print_info("监控可以继续运行,在后台检测信号")

    # 总结
    print_header("测试完成")
    print_success("所有基本功能测试完成")
    print_info("\n提示:")
    print_info("1. 如果没有产生信号,是正常现象")
    print_info("2. HAMA信号需要满足蜡烛图与MA线的交叉条件")
    print_info("3. 可以访问前端页面查看实时监控状态:")
    print(f"   {API_BASE.replace(':5000', ':8888')}/hama-monitor")
    print_info("4. 监控服务会在后台持续运行")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_info("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
