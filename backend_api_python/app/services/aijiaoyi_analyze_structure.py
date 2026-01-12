"""
分析symbol_list的子元素结构,找出为什么只能获取6-15个币种
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service

chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(
    options=chrome_options,
    service=Service(executable_path='/usr/bin/chromedriver')
)

try:
    driver.get('https://aijiaoyi.xyz/chart')
    time.sleep(5)

    driver.execute_script('document.getElementById("crypto_currency").click()')
    time.sleep(5)

    driver.execute_script('document.getElementById("binance_perpetual").click()')
    time.sleep(10)

    print("=" * 80)
    print("深度分析 - 查看每个币种的子元素结构")
    print("=" * 80)

    # 获取第一个币种元素的详细子元素信息
    first_coin_structure = driver.execute_script("""
        var container = document.getElementById('symbol_list');
        var firstChild = container.children[0];

        if (!firstChild) return null;

        var subChildren = Array.from(firstChild.children);
        var info = [];

        subChildren.forEach(function(sub, index) {
            info.push({
                index: index,
                tagName: sub.tagName,
                className: sub.className || '',
                id: sub.id || '',
                textContent: sub.textContent || ''
            });
        });

        return {
            parentText: firstChild.textContent,
            parentClass: firstChild.className,
            parentId: firstChild.id,
            subChildrenCount: subChildren.length,
            subChildren: info
        };
    """)

    print("\n第一个币种元素的结构:")
    print(f"父元素ID: {first_coin_structure['parentId']}")
    print(f"父元素Class: {first_coin_structure['parentClass'][:100]}")
    print(f"子元素数量: {first_coin_structure['subChildrenCount']}")
    print(f"\n所有文本内容: {first_coin_structure['parentText']}")

    print("\n子元素详情:")
    for sub in first_coin_structure['subChildren']:
        print(f"{sub['index']}: {sub['tagName']:10} class={sub['className'][:40]:40} text={sub['textContent'][:40]}")

    # 现在提取所有币种的正确数据
    print("\n" + "=" * 80)
    print("从所有币种的子元素中提取数据")
    print("=" * 80)

    all_coins = driver.execute_script("""
        var container = document.getElementById('symbol_list');
        var children = Array.from(container.children);
        var coins = [];

        children.forEach(function(child) {
            var subChildren = Array.from(child.children);

            if (subChildren.length === 0) return;

            // 通常子元素的结构是: [name, price, change, ...] 或类似
            // 让我们尝试从子元素中提取

            var coin = {
                id: child.id || '',
                name: '',
                price: '',
                change: '',
                rawData: []
            };

            subChildren.forEach(function(sub) {
                var text = sub.textContent.trim();
                if (text) {
                    coin.rawData.push(text);
                }
            });

            // 分析rawData来提取name, price, change
            if (coin.rawData.length >= 2) {
                // 第一个非空元素通常是name
                coin.name = coin.rawData[0];

                // 查找价格(数字)
                for (var i = 1; i < coin.rawData.length; i++) {
                    var text = coin.rawData[i];
                    // 尝试解析为数字
                    var num = parseFloat(text.replace(/,/g, ''));
                    if (!isNaN(num) && num > 0) {
                        coin.price = text;
                        break;
                    }
                }

                // 查找涨跌幅(包含%)
                for (var i = 1; i < coin.rawData.length; i++) {
                    var text = coin.rawData[i];
                    if (text.includes('%') || text.includes('+') || text.includes('-')) {
                        coin.change = text;
                        break;
                    }
                }
            }

            if (coin.name && (coin.price || coin.change)) {
                coins.push(coin);
            }
        });

        return coins;
    """)

    print(f"\n提取到 {len(all_coins)} 个币种:\n")

    for i, coin in enumerate(all_coins, 1):
        print(f"{i:2d}. {coin['id']:25} {coin['name']:20} 价格:{coin['price']:15} 涨跌:{coin['change']:10}")
        # 显示原始数据用于调试
        if i <= 3:
            print(f"     原始数据: {coin['rawData']}")

finally:
    driver.quit()

print("\n" + "=" * 80)
