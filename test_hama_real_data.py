"""
测试真实 HAMA 指标数据获取
"""
import sys
import io

# Windows 终端 UTF-8 编码支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000'

def test_login():
    """登录获取 token"""
    print("\n[1] 登录系统...")
    response = requests.post(f'{BASE_URL}/api/user/login', json={
        'username': 'quantdinger',
        'password': '123456'
    })

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 登录成功")

        # 提取 token
        token = None
        if 'data' in data and isinstance(data['data'], dict):
            token = data['data'].get('token')
        elif 'result' in data and isinstance(data['result'], dict):
            token = data['result'].get('token')
        elif 'token' in data:
            token = data['token']

        if token:
            print(f"[OK] Token: {token[:20]}...")
            return token
        else:
            print("[FAIL] 未找到 token")
            return None
    else:
        print(f"[FAIL] 登录失败: {response.status_code}")
        return None

def test_top_gainers_with_hama(token):
    """测试涨幅榜 + HAMA 分析"""
    print("\n[2] 测试涨幅榜 + HAMA 分析...")

    headers = {'Authorization': f'Bearer {token}'} if token else {}

    try:
        response = requests.get(
            f'{BASE_URL}/api/gainer-analysis/top-gainers',
            params={'limit': 5, 'market': 'spot'},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                symbols = data['data']['symbols']
                print(f"[OK] 获取成功! 共 {len(symbols)} 个币种\n")

                # 显示前3个币种的分析结果
                for i, item in enumerate(symbols[:3], 1):
                    print(f"{'='*80}")
                    print(f"#{i} {item['symbol']} - {item['base_asset']}")
                    print(f"{'='*80}")
                    print(f"价格: ${item['price']:,.2f}")
                    print(f"涨跌幅: {item['price_change_percent']:.2f}%")
                    print(f"成交量: ${item['volume']:,.0f}")
                    print(f"\n--- HAMA 分析 ---")
                    print(f"趋势: {item['hama_analysis']['trend']}")
                    print(f"蜡烛形态: {item['hama_analysis']['candle_pattern']}")
                    print(f"交易建议: {item['hama_analysis']['recommendation']}")
                    print(f"置信度: {item['hama_analysis']['confidence']*100:.1f}%")
                    print(f"趋势强度: {item['hama_analysis']['signals']['trend_strength']}")
                    print(f"成交量确认: {'是' if item['hama_analysis']['signals']['volume_confirmation'] else '否'}")
                    print(f"\n--- 技术指标 ---")
                    ti = item['hama_analysis']['technical_indicators']
                    print(f"RSI: {ti['rsi']:.2f}")
                    print(f"MACD: {ti['macd']}")
                    print(f"EMA 20: ${ti['ema_20']:,.2f}")
                    print(f"EMA 50: ${ti['ema_50']:,.2f}")
                    print(f"支撑位: ${ti['support_level']:,.2f}")
                    print(f"阻力位: ${ti['resistance_level']:,.2f}")
                    print(f"\n--- 条件判断 ---")
                    cond = item['conditions']
                    print(f"满足买入: {'是' if cond['meets_buy_criteria'] else '否'}")
                    print(f"满足卖出: {'是' if cond['meets_sell_criteria'] else '否'}")
                    print(f"综合判断: {cond['summary']}")
                    print()

                return True
            else:
                print(f"[FAIL] API 返回错误: {data.get('msg')}")
                return False
        else:
            print(f"[FAIL] 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("[FAIL] 请求超时 (30秒)")
        print("提示: HAMA 分析需要从 TradingView 和交易所获取数据,可能需要较长时间")
        return False
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False

def test_single_symbol_analysis(token, symbol='BTCUSDT'):
    """测试单个币种分析"""
    print(f"\n[3] 测试单个币种分析 ({symbol})...")

    headers = {'Authorization': f'Bearer {token}'} if token else {}

    try:
        response = requests.post(
            f'{BASE_URL}/api/gainer-analysis/analyze-symbol',
            json={'symbol': symbol},
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                analysis = data['data']
                print(f"[OK] 分析成功!\n")

                print(f"--- {analysis['symbol']} HAMA 详细分析 ---")
                print(f"趋势: {analysis['hama_analysis']['trend']}")
                print(f"蜡烛形态: {analysis['hama_analysis']['candle_pattern']}")
                print(f"交易建议: {analysis['hama_analysis']['recommendation']}")
                print(f"置信度: {analysis['hama_analysis']['confidence']*100:.1f}%")
                print(f"\n--- 条件判断 ---")
                cond = analysis['conditions']
                print(f"上升趋势: {'是' if cond['is_uptrend'] else '否'}")
                print(f"下降趋势: {'是' if cond['is_downtrend'] else '否'}")
                print(f"置信度>70%: {'是' if cond['confidence_above_70'] else '否'}")
                print(f"看涨形态: {'是' if cond['is_bullish_pattern'] else '否'}")
                print(f"满足买入条件: {'是' if cond['meets_buy_criteria'] else '否'}")
                print(f"满足卖出条件: {'是' if cond['meets_sell_criteria'] else '否'}")

                return True
            else:
                print(f"[FAIL] API 返回错误: {data.get('msg')}")
                return False
        else:
            print(f"[FAIL] 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False

def test_refresh_analysis(token):
    """测试刷新数据"""
    print("\n[4] 测试刷新数据...")

    headers = {'Authorization': f'Bearer {token}'} if token else {}

    try:
        response = requests.post(
            f'{BASE_URL}/api/gainer-analysis/refresh',
            json={'limit': 3, 'market': 'spot'},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 1:
                print(f"[OK] 刷新成功! 获取到 {data['data']['count']} 个币种")
                return True
            else:
                print(f"[FAIL] API 返回错误: {data.get('msg')}")
                return False
        else:
            print(f"[FAIL] 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False

def test_tradingview_direct():
    """直接测试 TradingView API (不需要后端)"""
    print("\n[5] 直接测试 TradingView Scanner API...")

    scan_url = "https://scanner.tradingview.com/crypto/scan"

    payload = {
        "symbols": {
            "tickers": ["BINANCE:BTCUSDT"],
            "query": {"types": []}
        },
        "columns": [
            "Recommend.All|1D",
            "RSI|14|0",
            "MACD.macd|12|26|9",
            "EMA|20|0",
            "EMA|50|0"
        ]
    }

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(scan_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                values = data['data'][0].get('d', [])
                print(f"[OK] TradingView API 连接成功!")
                print(f"原始数据: {values[:5]}...")
                return True
            else:
                print("[FAIL] TradingView 返回空数据")
                return False
        else:
            print(f"[FAIL] TradingView 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] TradingView 请求异常: {e}")
        print("提示: 可能需要配置代理才能访问 TradingView")
        return False

def main():
    """主测试函数"""
    print("=" * 80)
    print("HAMA 指标真实数据测试")
    print("=" * 80)

    results = []

    # 测试 TradingView 直连
    results.append(('TradingView API', test_tradingview_direct()))

    # 登录
    token = test_login()
    results.append(('登录', token is not None))

    if token:
        # 测试涨幅榜 + HAMA
        results.append(('涨幅榜 + HAMA 分析', test_top_gainers_with_hama(token)))

        # 测试单个币种分析
        results.append(('单个币种分析', test_single_symbol_analysis(token, 'ETHUSDT')))

        # 测试刷新
        results.append(('刷新数据', test_refresh_analysis(token)))
    else:
        print("\n[SKIP] 跳过需要认证的测试")

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print("=" * 80)
    print(f"总计: {passed}/{total} 通过 ({passed*100//total}%)")
    print("=" * 80)

    if passed == total:
        print("\n[SUCCESS] 所有测试通过! HAMA 真实数据分析功能正常工作")
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")
        print("\n常见问题:")
        print("1. TradingView API 连接失败 - 检查网络连接或代理配置")
        print("2. 交易所数据获取失败 - 检查 CCXT 配置和代理设置")
        print("3. 请求超时 - HAMA 分析需要较长时间,可增加超时时间")

if __name__ == '__main__':
    main()
