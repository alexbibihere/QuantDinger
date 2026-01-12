"""
直接测试TradingView API
"""
import requests
import json
import os

# TradingView配置
TV_SCAN_URL = "https://scanner.tradingview.com/crypto/scan"
TV_COOKIE = os.getenv('TV_COOKIE', "cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings=%7B%22analytics%22%3Atrue%2C%22advertising%22%3Atrue%7D; _ga=GA1.1.1784921442.1765155922; g_state=%7B%22i_l%22%3A0%2C%22i_ll%22%3A1765155927489%7D; device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; etg=undefined; cachec=undefined; _sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.1.1765156051..4c428878-38af-4b44-a437-10934a3be912..fb5f8db0-6053-41b3-af01-7f64f5f2292e.1765155920221.18; _ga_YVVRYGL0E0=GS2.1.s1765155921%24o1%24g1%24t1765156051%24j60%24l0%24h0")

# 代理配置
proxies = {
    'http': 'socks5h://host.docker.internal:7890',
    'https': 'socks5h://host.docker.internal:7890'
}

def test_futures():
    """测试永续合约"""
    print("=" * 70)
    print("测试TradingView永续合约API")
    print("=" * 70)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': TV_COOKIE,
        'Content-Type': 'application/json'
    }

    payload = {
        "filter": [
            {
                "left": "type",
                "operation": "equal",
                "right": "perpetual"
            }
        ],
        "options": {
            "lang": "en",
            "active_symbols_only": True
        },
        "symbols": {
            "query": {
                "types": []
            },
            "tickers": []
        },
        "columns": [
            "name",
            "close",
            "change",
            "change_abs",
            "high",
            "low",
            "volume",
            "type",
            "description"
        ],
        "sort": {
            "sortBy": "change",
            "sortOrder": "desc"
        },
        "range": [0, 10]
    }

    try:
        print("\n📡 发送请求到TradingView API...")
        response = requests.post(
            TV_SCAN_URL,
            json=payload,
            headers=headers,
            proxies=proxies,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('data'):
                print(f"\n✅ 成功获取数据！共 {len(data['data'])} 条记录")

                # 解析永续合约
                perpetuals = []
                for item in data['data']:
                    symbol_data = item['d']
                    symbol = symbol_data[0]

                    # 检查是否为永续合约
                    is_perpetual = False
                    if len(symbol_data) > 8:
                        symbol_type = symbol_data[8] if len(symbol_data) > 8 else ""
                        if isinstance(symbol_type, str) and 'perpetual' in symbol_type.lower():
                            is_perpetual = True
                        elif 'USDT' in symbol and not any(m in symbol for m in ['MAR', 'JUN', 'SEP', 'DEC']):
                            is_perpetual = True

                    if is_perpetual and 'USDT' in symbol:
                        price = symbol_data[1]
                        change = symbol_data[2]
                        volume = symbol_data[6]

                        perpetuals.append({
                            'symbol': symbol,
                            'price': price,
                            'change': change,
                            'volume': volume
                        })

                print(f"\n📊 永续合约TOP5:")
                for i, p in enumerate(perpetuals[:5], 1):
                    print(f"  {i}. {p['symbol']}: {p['change']:.2f}%")

                return True
            else:
                print("❌ 未获取到数据")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 开始测试TradingView API...\n")

    success = test_futures()

    print("\n" + "=" * 70)
    if success:
        print("✅ TradingView API测试成功！")
    else:
        print("❌ TradingView API测试失败！")
        print("\n可能的原因:")
        print("1. 代理配置问题（检查VPN是否运行）")
        print("2. Cookie已过期")
        print("3. 网络连接问题")
    print("=" * 70 + "\n")
