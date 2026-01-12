"""
测试TradingView关注列表API
"""
import requests
import json

def test_watchlist_api():
    """测试关注列表API"""

    # 您提供的cookie（完整版）
    cookie = "cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings=%7B%22analytics%22%3Atrue%2C%22advertising%22%3Atrue%7D; _ga=GA1.1.1784921442.1765155922; g_state=%7B%22i_l%22%3A0%2C%22i_ll%22%3A1765155927489%7D; device_t=OThMTjow.XawaJW5HLwqFI6JkR15zrkE9x6ZGXQP2BZW7q8cc6RE; sessionid=wg1tnp6dz2go7vjz7kkwi1jqu3ssn7lp; sessionid_sign=v3:mBnL6tXBwTesxw8lpnbM0uX2v5zKAeywYIGL8rNeEKs=; etg=undefined; cachec=undefined; _sp_id.cf1a=9e6106ce-373a-4412-9001-6025b357df38.1765155918.1.1765156051..4c428878-38af-4b44-a437-10934a3be912..fb5f8db0-6053-41b3-af01-7f64f5f2292e.1765155920221.18; _ga_YVVRYGL0E0=GS2.1.s1765155921%24o1%24g1%24t1765156051%24j60%24l0%24h0"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Referer': 'https://www.tradingview.com/'
    }

    print("=" * 70)
    print("测试TradingView关注列表API")
    print("=" * 70)

    # 测试方法1: 直接API
    print("\n方法1: 直接访问关注列表API")
    try:
        response = requests.get(
            'https://www.tradingview.com/api/v1/symbols_list/custom/104353945',
            headers=headers,
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！获取到 {len(data)} 个币种")
            if len(data) > 0:
                print("\n前3个币种:")
                for i, item in enumerate(data[:3], 1):
                    print(f"  {i}. {item.get('symbol', 'N/A')}")
        else:
            print(f"❌ 失败: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试方法2: Scanner API
    print("\n方法2: 使用Scanner API获取所有币种")
    try:
        payload = {
            "filter": [],
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": ["name", "description", "close", "change", "change_abs", "volume", "market_cap"],
            "sort": {"sortBy": "change", "sortOrder": "desc"},
            "range": [0, 10]
        }

        response = requests.post(
            'https://scanner.tradingview.com/crypto/scan',
            json=payload,
            headers=headers,
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            print(f"✅ 成功！获取到 {count} 个币种")
            if count > 0:
                print("\nTOP3:")
                for i, item in enumerate(data['data'][:3], 1):
                    d = item['d']
                    print(f"  {i}. {d[0]}: {d[2]:.2f}%")
        else:
            print(f"❌ 失败: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_watchlist_api()
