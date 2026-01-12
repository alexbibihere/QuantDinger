#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试预定义币种列表在 TradingView Scanner 中的可用性
"""
import requests
import json
from typing import List, Dict
import time


# 币安USDT永续合约列表(从之前获取的数据)
BINANCE_PERPETUALS = [
    '1INCHUSDT', 'AAVEUSDT', 'ACAUSDT', 'ACHUSDT', 'ACMUSDT', 'ADAUSDT', 'ADXUSDT',
    'AERGOUSDT', 'AGIXUSDT', 'AIUSDT', 'ALGOUSDT', 'ALICEUSDT', 'ALPINEUSDT',
    'ALPHAUSDT', 'AMBUSDT', 'ANKRUSDT', 'APEUSDT', 'APIUSDT', 'APTUSDT',
    'ARBUSDT', 'ARPAUSDT', 'ARUSDT', 'ASRUSDT', 'ATAUSDT', 'ATOMUSDT',
    'AUCTIONUSDT', 'AVAXUSDT', 'AXLUSDT', 'AXSUSDT', 'BAKEUSDT', 'BALUSDT',
    'BANDUSDT', 'BATUSDT', 'BCHUSDT', 'BELUSDT', 'BETAUSDT', 'BGNUSDT',
    'BICOUSDT', 'BLZUSDT', 'BNBUSDT', 'BNXUSDT', 'BNTUSDT', 'BNXUSDT',
    'BTTCUSDT', 'BTSUSDT', 'BTCUSDT', 'BTTUSDT', 'BURGERUSDT', 'BUSDUSDT',
    'C98USDT', 'CELOUSDT', 'CELRUSDT', 'CHRUSDT', 'CHZUSDT', 'CNTRUSDT',
    'COMPUSDT', 'COREUSDT', 'COTIUSDT', 'CRVUSDT', 'CTKUSDT', 'CTSIUSDT',
    'CVCUSDT', 'CVXUSDT', 'DASHUSDT', 'DEFIUSDT', 'DEGOUSDT', 'DENTUSDT',
    'DGBUSDT', 'DUSDT', 'DFUSDT', 'DODOUSDT', 'DOGEUSDT', 'DOTUSDT',
    'DUSDT', 'DYDXUSDT', 'EGLDUSDT', 'ENJUSDT', 'ENSUSDT', 'EONEUSDT',
    'EOSUSDT', 'ETCUSDT', 'ETHUSDT', 'ETHUSDT', 'FETUSDT', 'FILUSDT',
    'FIOUSDT', 'FLOWUSDT', 'FLUXUSDT', 'FORUSDT', 'FORTHUSDT', 'FRONTUSDT',
    'FTMUSDT', 'FXSUSDT', 'GALAUSDT', 'GHSTUSDT', 'GLMUSDT', 'GLMRUSDT',
    'GMTUSDT', 'GMXUSDT', 'GNSUSDT', 'GRTUSDT', 'GTCUSDT', 'GTMUSDT',
    'HARDUSDT', 'HBARUSDT', 'HFTUSDT', 'HIGHUSDT', 'HIFIUSDT', 'HOTUSDT',
    'ICPUSDT', 'ICXUSDT', 'IDEXUSDT', 'IDUSDT', 'IMXUSDT', 'INJUSDT',
    'IOSTUSDT', 'IOTAUSDT', 'IOTXUSDT', 'JASMYUSDT', 'JOEUSDT', 'JUVUSDT',
    'KAVAUSDT', 'KAVAUSDT', 'KEYUSDT', 'KLAYUSDT', 'KSMUSDT', 'LDOUSDT',
    'LENDUSDT', 'LINAUSDT', 'LINKUSDT', 'LISTUSDT', 'LITUSDT', 'LRCUSDT',
    'LQTYUSDT', 'LRCUSDT', 'LTCUSDT', 'LUNAUSDT', 'LUNCUSDT', 'MAGICUSDT',
    'MANAUSDT', 'MASKUSDT', 'MATICUSDT', 'MAVUSDT', 'MDTUSDT', 'MDXUSDT',
    'METISUSDT', 'MINAUSDT', 'MKRUSDT', 'MLNUSDT', 'MOVRUSDT', 'MTLUSDT',
    'MULTIUSDT', 'NANOUSDT', 'NEARUSDT', 'NEBLUSDT', 'NEOUSDT', 'NEOUSDT',
    'NEXOUSDT', 'NKNUSDT', 'NMRUSDT', 'NTRNUSDT', 'OAXUSDT', 'OGUSDT',
    'OGNUSDT', 'OMGUSDT', 'OMNIUSDT', 'ONEUSDT', 'ONTUSDT', 'OPUSDT',
    'ORBSUSDT', 'OXTUSDT', 'PARAUSDT', 'PENDLEUSDT', 'PEPEUSDT', 'PEPEUSDT',
    'PHAUSDT', 'PHBUSDT', 'PIVXUSDT', 'POLSUSDT', 'POLYXUSDT', 'PONDUUSDT',
    'PORTOUSDT', 'POWRUSDT', 'PRIVUSDT', 'PROSUSDT', 'PSGUSDT', 'PUNDIXUSDT',
    'PYRUSDT', 'QIUSDT', 'QNTUSDT', 'QTUMUSDT', 'RAREUSDT', 'RAYUSDT',
    'RDNTUSDT', 'RENDERUSDT', 'RENFILUSDT', 'REPUSDT', 'RETFIUSDT', 'RIFUSDT',
    'RLCUSDT', 'RNDRUSDT', 'ROSEUSDT', 'RPLUSDT', 'RSRUSDT', 'RUNEUSDT',
    'RVNUSDT', 'SANDUSDT', 'SANTOSUSDT', 'SCUSDT', 'SCRTUSDT', 'SFPUSDT',
    'SKLUSDT', 'SLPUSDT', 'SNXUSDT', 'SOLUSDT', 'SPELLUSDT', 'SRMUSDT',
    'SSVUSDT', 'STGUSDT', 'STMXUSDT', 'STORJUSDT', 'STPTUSDT', 'STXUSDT',
    'SUSHIUSDT', 'SYNUSDT', 'THETAUSDT', 'TLMUSDT', 'TMTUSDT', 'TRUUSDT',
    'TRXUSDT', 'TUSDT', 'TUSDUSDT', 'TVKUSDT', 'TYTEUSDT', 'UMAUSDT',
    'UNFIUSDT', 'UNIUSDT', 'USDPUSDT', 'UTKUSDT', 'VETUSDT', 'WAVESUSDT',
    'WAXPUSDT', 'WOOUSDT', 'XECUSDT', 'XEMUSDT', 'XLMUSDT', 'XRPUSDT',
    'XTZUSDT', 'XVGUSDT', 'YFIUSDT', 'YGGUSDT', 'ZECUSDT', 'ZENUSDT',
    'ZILUSDT', 'ZRXUSDT'
]


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

    print(f"开始测试 {len(symbols)} 个币种在 TradingView Scanner 中的可用性...")
    print(f"每批测试 {batch_size} 个币种,共 {(len(symbols) + batch_size - 1) // batch_size} 批\n")

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

        print(f"正在测试第 {batch_num}/{total_batches} 批 ({len(batch)} 个币种)...", end=' ')

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
                    # TradingView 返回的数据格式
                    batch_available = 0
                    for idx, symbol_data in enumerate(data['data']):
                        if idx < len(batch):
                            symbol = batch[idx]
                            if symbol_data and len(symbol_data) > 0:
                                # 有数据返回,说明可用
                                available_map[symbol] = True
                                batch_available += 1
                            else:
                                # 无数据,说明不可用
                                available_map[symbol] = False

                    # 标记未返回的币种为不可用
                    for idx in range(len(data['data']), len(batch)):
                        symbol = batch[idx]
                        available_map[symbol] = False

                    print(f"OK - {batch_available}/{len(batch)} 个可用")
                else:
                    # 数据格式错误,标记为不可用
                    for symbol in batch:
                        available_map[symbol] = False
                    print(f"FAIL - 数据格式错误")
            else:
                # 请求失败,标记为不可用
                for symbol in batch:
                    available_map[symbol] = False
                print(f"FAIL - HTTP {response.status_code}")

        except Exception as e:
            # 异常,标记为不可用
            for symbol in batch:
                available_map[symbol] = False
            print(f"ERROR - {e}")

        # 避免请求过快
        if i + batch_size < len(symbols):
            time.sleep(0.5)

    return available_map


def main():
    """主函数"""
    print("=" * 80)
    print("币安永续合约 TradingView Scanner 可用性测试")
    print("=" * 80)
    print()

    # 测试可用性
    available_map = test_tradingview_available(BINANCE_PERPETUALS, batch_size=20)

    # 统计结果
    available_symbols = [s for s, avail in available_map.items() if avail]
    unavailable_symbols = [s for s, avail in available_map.items() if not avail]

    print("\n" + "=" * 80)
    print("测试结果统计")
    print("=" * 80)
    print(f"总计: {len(BINANCE_PERPETUALS)} 个币种")
    print(f"可用: {len(available_symbols)} 个 ({len(available_symbols)/len(BINANCE_PERPETUALS)*100:.1f}%)")
    print(f"不可用: {len(unavailable_symbols)} 个 ({len(unavailable_symbols)/len(BINANCE_PERPETUALS)*100:.1f}%)")

    # 保存结果
    result = {
        'total': len(BINANCE_PERPETUALS),
        'available_count': len(available_symbols),
        'unavailable_count': len(unavailable_symbols),
        'available_symbols': sorted(available_symbols),
        'unavailable_symbols': sorted(unavailable_symbols)
    }

    output_file = 'binance_available_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n结果已保存到: {output_file}")

    # 显示可用币种列表
    print(f"\n可用币种列表 ({len(available_symbols)} 个):")
    for i, symbol in enumerate(sorted(available_symbols), 1):
        print(f"{i:3d}. {symbol}")

    # 显示不可用币种列表
    if unavailable_symbols:
        print(f"\n不可用币种列表 ({len(unavailable_symbols)} 个):")
        for i, symbol in enumerate(sorted(unavailable_symbols), 1):
            print(f"{i:3d}. {symbol}")


if __name__ == "__main__":
    main()
