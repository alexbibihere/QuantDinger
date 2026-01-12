#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试币安永续合约在 TradingView Scanner 中的可用性
"""
import requests
import json
from typing import List, Dict, Set
import time
import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_binance_perpetuals() -> List[str]:
    """获取币安所有USDT永续合约"""
    try:
        print("正在获取币安永续合约列表...")

        response = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo', timeout=10)
        data = response.json()

        # 筛选USDT永续合约
        perpetuals = []
        if 'symbols' in data:
            for s in data['symbols']:
                if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING':
                    perpetuals.append(s['symbol'])

        print(f"从币安获取到 {len(perpetuals)} 个USDT永续合约")
        return perpetuals

    except Exception as e:
        print(f"获取币安永续合约失败: {e}")
        return []


def test_tradingview_available(symbols: List[str], batch_size: int = 20) -> Dict[str, bool]:
    """
    测试币种在 TradingView Scanner 中是否可用

    Args:
        symbols: 币种列表
        batch_size: 每批测试的数量

    Returns:
        字典: {symbol: available}
    """
    available_map = {}

    logger.info(f"开始测试 {len(symbols)} 个币种在 TradingView Scanner 中的可用性...")
    logger.info(f"每批测试 {batch_size} 个币种,共 {(len(symbols) + batch_size - 1) // batch_size} 批")

    url = "https://scanner.tradingview.com/crypto/scan"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://cn.tradingview.com',
        'Referer': 'https://cn.tradingview.com/'
    }

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        logger.info(f"正在测试第 {batch_num}/{total_batches} 批 ({len(batch)} 个币种)...")

        try:
            # 构建 TradingView Scanner 请求
            tv_symbols = [f"BINANCE:{s}" for s in batch]

            payload = {
                "symbols": {
                    "tickers": tv_symbols,
                    "query": {
                        "types": []
                    }
                },
                "columns": [
                    "Recommend.All|1",
                    "name",
                    "close",
                    "change|abs"
                ]
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # 检查返回的数据
                if 'data' in data and isinstance(data['data'], list):
                    # TradingView 返回的数据格式: [[values...], [values...], ...]
                    # 每个 values 数组的索引对应 tv_symbols 的索引
                    for idx, symbol_data in enumerate(data['data']):
                        if symbol_data and len(symbol_data) > 0:
                            # 有数据返回,说明可用
                            symbol = batch[idx]
                            available_map[symbol] = True
                        else:
                            # 无数据,说明不可用
                            symbol = batch[idx]
                            available_map[symbol] = False

                    # 标记未返回的币种为不可用
                    for idx in range(len(data['data']), len(batch)):
                        symbol = batch[idx]
                        available_map[symbol] = False

                    available_count = sum(1 for s in batch if available_map.get(s, False))
                    logger.info(f"✅ 第 {batch_num} 批完成: {available_count}/{len(batch)} 个可用")
                else:
                    # 数据格式错误,标记为不可用
                    for symbol in batch:
                        available_map[symbol] = False
                    logger.warning(f"⚠️ 第 {batch_num} 批数据格式错误")
            else:
                # 请求失败,标记为不可用
                for symbol in batch:
                    available_map[symbol] = False
                logger.warning(f"⚠️ 第 {batch_num} 批请求失败: {response.status_code}")

        except Exception as e:
            # 异常,标记为不可用
            for symbol in batch:
                available_map[symbol] = False
            logger.error(f"❌ 第 {batch_num} 批测试失败: {e}")

        # 避免请求过快
        if i + batch_size < len(symbols):
            time.sleep(0.5)

    return available_map


def main():
    """主函数"""
    print("=" * 80)
    print("币安永续合约 TradingView Scanner 可用性测试")
    print("=" * 80)

    # 1. 获取币安永续合约
    binance_symbols = get_binance_perpetuals()

    if not binance_symbols:
        print("❌ 未能获取到币安永续合约列表")
        return

    print(f"\n✅ 获取到 {len(binance_symbols)} 个币安永续合约\n")

    # 2. 测试可用性
    available_map = test_tradingview_available(binance_symbols, batch_size=20)

    # 3. 统计结果
    available_symbols = [s for s, avail in available_map.items() if avail]
    unavailable_symbols = [s for s, avail in available_map.items() if not avail]

    print("\n" + "=" * 80)
    print("测试结果统计")
    print("=" * 80)
    print(f"总计: {len(binance_symbols)} 个币种")
    print(f"✅ 可用: {len(available_symbols)} 个 ({len(available_symbols)/len(binance_symbols)*100:.1f}%)")
    print(f"❌ 不可用: {len(unavailable_symbols)} 个 ({len(unavailable_symbols)/len(binance_symbols)*100:.1f}%)")

    # 4. 保存结果
    result = {
        'total': len(binance_symbols),
        'available_count': len(available_symbols),
        'unavailable_count': len(unavailable_symbols),
        'available_symbols': sorted(available_symbols),
        'unavailable_symbols': sorted(unavailable_symbols)
    }

    output_file = 'binance_available_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 结果已保存到: {output_file}")

    # 5. 显示可用币种列表(前50个)
    print(f"\n✅ 可用币种列表 (前50个):")
    for i, symbol in enumerate(sorted(available_symbols)[:50], 1):
        print(f"  {i:3d}. {symbol}")

    if len(available_symbols) > 50:
        print(f"  ... 还有 {len(available_symbols) - 50} 个")

    # 6. 显示不可用币种列表(前20个)
    if unavailable_symbols:
        print(f"\n❌ 不可用币种列表 (前20个):")
        for i, symbol in enumerate(sorted(unavailable_symbols)[:20], 1):
            print(f"  {i:3d}. {symbol}")

        if len(unavailable_symbols) > 20:
            print(f"  ... 还有 {len(unavailable_symbols) - 20} 个")


if __name__ == "__main__":
    main()
