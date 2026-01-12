"""
爱交易直接API调用尝试
尝试找到并调用网站内部API
"""
import requests
import json
import re
from app.utils.logger import get_logger

logger = get_logger(__name__)


def try_direct_api():
    """尝试直接调用爱交易的API"""
    print("=" * 80)
    print("爱交易直接API调用测试")
    print("=" * 80)

    session = requests.Session()

    # 设置headers模拟真实浏览器
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://aijiaoyi.xyz',
        'Referer': 'https://aijiaoyi.xyz/chart',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })

    print("\n步骤1: 访问主页获取cookies")
    print("-" * 80)

    try:
        response = session.get('https://aijiaoyi.xyz/chart', timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"Cookies: {session.cookies.get_dict()}")

        # 从页面中提取可能的API端点
        page_content = response.text

        # 查找API调用
        api_patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.[a-z]+\(["\']([^"\']+)["\']',
            r'api["\']:\s*["\']([^"\']+)["\']',
            r'["\']https://[^"\']+/api/[^"\']+["\']',
            r'["\']https://[^"\']+/v1/[^"\']+["\']',
        ]

        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, page_content)
            found_apis.update(matches)

        if found_apis:
            print(f"\n发现 {len(found_apis)} 个可能的API端点:")
            for api in list(found_apis)[:20]:
                print(f"  - {api}")
        else:
            print("\n未在页面中发现明显的API端点")

    except Exception as e:
        print(f"访问主页失败: {e}")
        return

    print("\n步骤2: 尝试常见的API路径")
    print("-" * 80)

    # 尝试常见的API路径
    api_paths = [
        '/api/symbols',
        '/api/symbols/list',
        '/api/coins',
        '/api/coins/list',
        '/api/crypto',
        '/api/crypto/list',
        '/api/binance/perpetual',
        '/api/binance/perpetual/symbols',
        '/api/market/symbols',
        '/api/market/coins',
        '/api/trading/symbols',
        '/api/v1/symbols',
        '/api/v1/coins',
        '/api/data/symbols',
        '/api/data/coins',
        '/chart/api/symbols',
        '/chart/api/coins',
    ]

    working_apis = []

    for path in api_paths:
        url = f'https://aijiaoyi.xyz{path}'
        try:
            response = session.get(url, timeout=5)
            if response.status_code == 200 and len(response.text) > 100:
                try:
                    data = response.json()
                    if isinstance(data, dict) or (isinstance(data, list) and len(data) > 0):
                        working_apis.append((url, data))
                        print(f"✅ {url}")
                        print(f"   数据类型: {type(data)}, 内容长度: {len(str(data))}")
                    else:
                        print(f"⚠️ {url} - 返回无效数据")
                except:
                    print(f"⚠️ {url} - 非JSON响应")
        except Exception as e:
            pass

    if working_apis:
        print(f"\n🎉 发现 {len(working_apis)} 个可用的API!")

        # 显示每个API的数据
        for url, data in working_apis[:5]:
            print(f"\n{'='*60}")
            print(f"API: {url}")
            print(f"{'='*60}")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
            if len(str(data)) > 500:
                print("... (数据被截断)")
    else:
        print("\n❌ 未发现可用的API端点")

    print("\n步骤3: 检查WebSocket连接")
    print("-" * 80)

    # 检查页面中是否有WebSocket连接
    ws_patterns = [
        r'new WebSocket\(["\']([^"\']+)["\']',
        r'ws://[^"\']+',
        r'wss://[^"\']+',
    ]

    ws_urls = set()
    for pattern in ws_patterns:
        matches = re.findall(pattern, page_content)
        ws_urls.update(matches)

    if ws_urls:
        print(f"发现 {len(ws_urls)} 个WebSocket端点:")
        for ws in ws_urls:
            print(f"  - {ws}")
    else:
        print("未发现WebSocket连接")

    print("\n步骤4: 尝试通过特殊请求头获取数据")
    print("-" * 80)

    # 尝试添加特殊请求头
    special_headers = {
        'X-Requested-With': 'XMLHttpRequest',
    }

    session.headers.update(special_headers)

    for path in ['/api/symbols', '/api/coins', '/chart/api/symbols']:
        url = f'https://aijiaoyi.xyz{path}'
        try:
            response = session.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - 状态码: {response.status_code}")
                try:
                    data = response.json()
                    print(f"   数据: {str(data)[:200]}")
                except:
                    print(f"   响应: {response.text[:200]}")
        except:
            pass

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

    return working_apis


if __name__ == "__main__":
    try_direct_api()
