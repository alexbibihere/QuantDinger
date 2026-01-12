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
chrome_options.add_argument('--disable-gpu')

driver = webdriver.Chrome(
    options=chrome_options,
    service=Service(executable_path='/usr/bin/chromedriver')
)

try:
    print("访问爱交易网站...")
    driver.get('https://aijiaoyi.xyz/chart')
    time.sleep(5)

    driver.execute_script('document.getElementById("crypto_currency").click()')
    print("已点击加密货币")
    time.sleep(5)

    driver.execute_script('document.getElementById("binance_perpetual").click()')
    print("已点击币安永续")
    time.sleep(10)

    # 获取symbol_list的所有子元素
    print("\n检查symbol_list的子元素...")

    symbol_list = driver.find_element(By.ID, 'symbol_list')

    # 使用JavaScript获取所有子元素
    all_coins = driver.execute_script("""
        var container = document.getElementById('symbol_list');
        var children = Array.from(container.children);
        var coins = [];

        children.forEach(function(child) {
            var text = child.textContent || "";

            if (text.includes("USDT") || text.includes("PERP")) {
                var lines = text.split("\\n");

                var symbol = "";
                var price = "";
                var change = "";

                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i].trim();

                    if (line.includes("USDT") || line.includes("PERP")) {
                        symbol = line;
                    }
                    else if (line.match(/^\d+\.?\d*$/) || line.match(/^\d+\,\d+\.\d+$/)) {
                        price = line;
                    }
                    else if (line.includes("%")) {
                        change = line;
                    }
                }

                if (symbol) {
                    coins.push({
                        symbol: symbol,
                        price: price,
                        change: change
                    });
                }
            }
        });

        return coins;
    """)

    print(f"\n从所有子元素提取到 {len(all_coins)} 个币种:\n")

    for i, coin in enumerate(all_coins, 1):
        print(f"{i:2d}. {coin['symbol']:35} 价格:{coin['price']:15} 涨跌:{coin['change']:10}")

    print(f"\n{'='*80}")
    print(f"总结: 共获取到 {len(all_coins)} 个币种")
    print(f"{'='*80}")

finally:
    driver.quit()
