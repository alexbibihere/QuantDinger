"""
爱交易深度检查 - 检查symbol_list的所有121个子元素
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from app.utils.logger import get_logger

logger = get_logger(__name__)


def deep_inspect_symbol_list():
    """深度检查symbol_list的所有子元素"""
    print("=" * 80)
    print("爱交易深度检查 - 检查所有子元素")
    print("=" * 80)

    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    driver = webdriver.Chrome(
        options=chrome_options,
        service=Service(executable_path='/usr/bin/chromedriver')
    )

    try:
        print("\n步骤1: 加载页面并选择币安永续")
        print("-" * 80)

        driver.get("https://aijiaoyi.xyz/chart")
        time.sleep(5)

        driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
        """)

        driver.execute_script('document.getElementById("crypto_currency").click()')
        time.sleep(5)

        driver.execute_script('document.getElementById("binance_perpetual").click()')
        time.sleep(10)

        print("\n步骤2: 获取symbol_list容器的所有子元素")
        print("-" * 80)

        symbol_list = driver.find_element(By.ID, 'symbol_list')

        # 方法1: 所有contenteditable=false的元素
        contenteditable_elems = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
        print(f"contenteditable=false的元素: {len(contenteditable_elems)} 个")

        # 方法2: 所有直接子div元素
        all_children = driver.execute_script("""
            var container = document.getElementById('symbol_list');
            var children = container.children;
            return children.length;
        """)
        print(f"容器子元素总数: {all_children} 个")

        # 方法3: 检查所有可能的元素类型
        all_divs = symbol_list.find_elements(By.TAG_NAME, 'div')
        print(f"容器内div元素: {len(all_divs)} 个")

        all_lis = symbol_list.find_elements(By.TAG_NAME, 'li')
        print(f"容器内li元素: {len(all_lis)} 个")

        all_spans = symbol_list.find_elements(By.TAG_NAME, 'span')
        print(f"容器内span元素: {len(all_spans)} 个")

        print("\n步骤3: 详细检查每个子元素")
        print("-" * 80)

        # 使用JavaScript获取所有子元素的详细信息
        elements_info = driver.execute_script("""
            var container = document.getElementById('symbol_list');
            var children = Array.from(container.children);
            var info = [];

            children.forEach(function(child, index) {
                var elemInfo = {
                    index: index,
                    tagName: child.tagName,
                    id: child.id || '',
                    className: child.className || '',
                    contentEditable: child.contentEditable || 'inherit',
                    textContent: child.textContent ? child.textContent.substring(0, 50) : '',
                    hasText: child.textContent && child.textContent.trim().length > 0,
                    childCount: child.children.length,
                    attributes: []
                };

                // 获取所有属性
                for (var i = 0; i < child.attributes.length; i++) {
                    var attr = child.attributes[i];
                    elemInfo.attributes.push({
                        name: attr.name,
                        value: attr.value ? attr.value.substring(0, 50) : ''
                    });
                }

                info.push(elemInfo);
            });

            return info;
        """)

        # 保存完整信息
        with open('/tmp/symbol_list_children.json', 'w', encoding='utf-8') as f:
            json.dump(elements_info, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存所有子元素信息到 /tmp/symbol_list_children.json")

        # 分析有文本内容的元素
        text_elements = [e for e in elements_info if e['hasText'] and len(e['textContent'].strip()) > 3]
        print(f"\n有文本内容的元素: {len(text_elements)} 个")

        # 显示前30个有内容的元素
        print(f"\n前30个有内容的元素:")
        print("-" * 80)

        crypto_data = []
        for elem in text_elements[:100]:
            text = elem['textContent']
            # 检查是否像币种数据(包含USDT或价格)
            if 'USDT' in text or 'PERP' in text:
                # 尝试解析
                lines = text.split('\n')
                for line in lines:
                    if line.strip() and len(line.strip()) > 3:
                        # 可能是币种符号
                        if 'USDT' in line or 'PERP' in line:
                            if not any(c['symbol'] == line for c in crypto_data):
                                crypto_data.append({
                                    'raw_text': text,
                                    'tag_name': elem['tagName'],
                                    'id': elem['id'],
                                    'class': elem['className']
                                })
                                break

        print(f"\n找到 {len(crypto_data)} 个可能的币种元素")

        # 尝试不同的选择器
        print("\n步骤4: 尝试不同的选择器")
        print("-" * 80)

        selectors = [
            '[contenteditable="false"]',
            'div',
            'li',
            '[class*="symbol"]',
            '[class*="coin"]',
            '[class*="item"]',
            '[id*="symbol"]',
        ]

        for selector in selectors:
            try:
                elems = symbol_list.find_elements(By.CSS_SELECTOR, selector)
                print(f"选择器 '{selector}': {len(elems)} 个元素")

                # 显示前3个元素的文本
                for i, elem in enumerate(elems[:3], 1):
                    try:
                        text = elem.text
                        if text and len(text.strip()) > 3:
                            print(f"  元素{i}: {text[:50]}")
                    except:
                        pass
            except:
                print(f"选择器 '{selector}': 失败")

        # 最重要: 尝试从所有子元素提取数据
        print("\n步骤5: 从所有子元素提取币种数据")
        print("-" * 80)

        all_coins = driver.execute_script("""
            var container = document.getElementById('symbol_list');
            var children = Array.from(container.children);
            var coins = [];

            children.forEach(function(child) {
                var text = child.textContent || '';

                // 检查是否包含币种特征
                if (text.includes('USDT') || text.includes('PERP')) {
                    var lines = text.split('\\n');

                    // 查找币种符号
                    var symbol = '';
                    var price = '';
                    var change = '';

                    for (var i = 0; i < lines.length; i++) {
                        var line = lines[i].trim();

                        if (line.includes('USDT') || line.includes('PERP')) {
                            symbol = line;
                        }
                        // 查找价格(数字格式)
                        else if (/^[0-9,.]+$/.test(line) || /^\\d+\\.\\d+$/.test(line.replace(/,/g, ''))) {
                            price = line;
                        }
                        // 查找涨跌幅
                        else if (line.includes('%') || (line.includes('+') || line.includes('-'))) {
                            change = line;
                        }
                    }

                    if (symbol) {
                        coins.push({
                            symbol: symbol,
                            price: price,
                            change: change,
                            fullText: text.substring(0, 100)
                        });
                    }
                }
            });

            return coins;
        """)

        print(f"从所有子元素提取到 {len(all_coins)} 个币种:\n")

        if all_coins:
            for i, coin in enumerate(all_coins, 1):
                print(f"{i:2d}. {coin['symbol']:30} 价格:{coin['price']:15} 涨跌:{coin['change']:10}")

            # 保存到文件
            with open('/tmp/all_coins_from_children.json', 'w', encoding='utf-8') as f:
                json.dump(all_coins, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已保存到 /tmp/all_coins_from_children.json")
        else:
            print("❌ 未能提取到币种数据")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)


if __name__ == "__main__":
    deep_inspect_symbol_list()
