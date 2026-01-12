#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量获取加密货币的HAMA信号
使用TradingView HAMA API
"""
import requests
import json
import time
import sys
import io
from typing import List, Dict, Optional

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# API配置
API_BASE = "http://localhost:5000"
HAMA_ENDPOINT = "/api/tradingview/hama"


def get_hama_signal(symbol: str) -> Optional[Dict]:
    """
    获取单个币种的HAMA信号

    Args:
        symbol: 币种符号,如 BTCUSDT

    Returns:
        HAMA信号数据字典,失败返回None
    """
    try:
        url = f"{API_BASE}{HAMA_ENDPOINT}/{symbol}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('data')
            else:
                print(f"  ❌ {symbol}: {data.get('message')}")
                return None
        else:
            print(f"  ❌ {symbol}: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
        return None


def format_signal_display(symbol: str, data: Dict) -> str:
    """格式化显示HAMA信号"""
    trend_emoji = {
        'uptrend': '📈',
        'downtrend': '📉',
        'sideways': '➡️'
    }

    recommend_emoji = {
        'BUY': '🟢',
        'SELL': '🔴',
        'HOLD': '🟡'
    }

    trend = data.get('trend', 'unknown')
    recommend = data.get('recommendation', 'HOLD')
    confidence = data.get('confidence', 0) * 100

    output = [
        f"\n{trend_emoji.get(trend, '')} {symbol}",
        f"  趋势: {trend}",
        f"  建议: {recommend_emoji.get(recommend, '')} {recommend}",
        f"  置信度: {confidence:.0f}%",
        f"  形态: {data.get('candle_pattern', 'N/A')}",
    ]

    # 技术指标
    ti = data.get('technical_indicators', {})
    output.extend([
        f"  RSI: {ti.get('rsi', 0):.1f}",
        f"  MACD: {ti.get('macd', 'N/A')}",
        f"  EMA20: {ti.get('ema_20', 0):,.2f}",
        f"  EMA50: {ti.get('ema_50', 0):,.2f}",
    ])

    # 关键价位
    support = ti.get('support_level', 0)
    resistance = ti.get('resistance_level', 0)
    if support > 0:
        output.append(f"  支撑位: ${support:,.2f}")
    if resistance > 0:
        output.append(f"  阻力位: ${resistance:,.2f}")

    # 总结
    conditions = data.get('conditions', {})
    summary = conditions.get('summary', 'N/A')
    output.append(f"  总结: {summary}")

    return '\n'.join(output)


def batch_get_signals(
    symbols: List[str],
    show_details: bool = True,
    group_by_recommendation: bool = True
) -> Dict[str, List[Dict]]:
    """
    批量获取多个币种的HAMA信号

    Args:
        symbols: 币种列表
        show_details: 是否显示详细信息
        group_by_recommendation: 是否按建议分组

    Returns:
        按建议分组的币种字典
    """
    print(f"正在获取 {len(symbols)} 个币种的HAMA信号...")
    print("=" * 60)

    results = {
        'BUY': [],
        'SELL': [],
        'HOLD': [],
        'ERROR': []
    }

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}...", end=' ')

        data = get_hama_signal(symbol)

        if data:
            recommend = data.get('recommendation', 'HOLD')
            results[recommend].append({symbol: data})

            if show_details:
                print(f"\033[92m✓\033[0m {data.get('recommendation')} ({data.get('confidence', 0)*100:.0f}%)")
                if show_details:
                    print(format_signal_display(symbol, data))
            else:
                print(f"\033[92m✓\033[0m {data.get('recommendation')}")
        else:
            results['ERROR'].append(symbol)
            print()

        # 避免请求过快
        time.sleep(0.5)

    # 按建议分组显示
    if group_by_recommendation:
        print("\n" + "=" * 60)
        print("📊 信号汇总")
        print("=" * 60)

        for recommend in ['BUY', 'SELL', 'HOLD']:
            items = results[recommend]
            if items:
                emoji = '🟢' if recommend == 'BUY' else '🔴' if recommend == 'SELL' else '🟡'
                print(f"\n{emoji} {recommend} 信号 ({len(items)}个):")

                for item in items:
                    for symbol, data in item.items():
                        confidence = data.get('confidence', 0) * 100
                        print(f"  - {symbol:15} 置信度: {confidence:.0f}%")

    if results['ERROR']:
        print(f"\n❌ 获取失败 ({len(results['ERROR'])}个):")
        for symbol in results['ERROR']:
            print(f"  - {symbol}")

    return results


def find_buy_signals(
    symbols: List[str],
    min_confidence: float = 0.7
) -> List[Dict]:
    """
    查找高置信度的买入信号

    Args:
        symbols: 币种列表
        min_confidence: 最低置信度(0-1)

    Returns:
        符合条件的买入信号列表
    """
    print(f"正在查找高置信度买入信号(>{min_confidence*100:.0f}%)...")
    print("=" * 60)

    buy_signals = []

    for i, symbol in enumerate(symbols, 1):
        data = get_hama_signal(symbol)

        if data and data.get('recommendation') == 'BUY':
            confidence = data.get('confidence', 0)

            if confidence >= min_confidence:
                buy_signals.append({
                    'symbol': symbol,
                    'confidence': confidence,
                    'data': data
                })
                print(f"✓ {symbol:15} 置信度: {confidence*100:.0f}%")

        time.sleep(0.5)

    if buy_signals:
        # 按置信度排序
        buy_signals.sort(key=lambda x: x['confidence'], reverse=True)

        print(f"\n找到 {len(buy_signals)} 个高置信度买入信号:\n")

        for i, signal in enumerate(buy_signals, 1):
            print(f"{i}. {signal['symbol']}")
            print(f"   置信度: {signal['confidence']*100:.0f}%")
            print(f"   形态: {signal['data'].get('candle_pattern', 'N/A')}")
            print()

    return buy_signals


def main():
    """主函数"""
    # 常用币种列表
    popular_symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT',
        'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'BCHUSDT', 'ATOMUSDT'
    ]

    print("=" * 60)
    print("HAMA信号批量获取工具")
    print("=" * 60)

    import sys

    if len(sys.argv) > 1:
        # 命令行指定币种
        symbols = [s.upper() + 'USDT' if not s.endswith('USDT') else s.upper()
                   for s in sys.argv[1:]]
    else:
        # 使用默认列表
        symbols = popular_symbols

    # 获取所有信号
    results = batch_get_signals(
        symbols,
        show_details=False,  # 不显示每个币种的详细信息
        group_by_recommendation=True
    )

    # 查找买入信号
    print("\n" + "=" * 60)
    print("🔍 高置信度买入信号(>70%)")
    print("=" * 60)

    buy_signals = find_buy_signals(symbols, min_confidence=0.7)

    if not buy_signals:
        print("当前没有高置信度买入信号")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
