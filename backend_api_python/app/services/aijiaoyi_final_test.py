"""
爱交易最终综合测试
尝试所有可能的方法获取币种数据
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.utils.logger import get_logger

logger = get_logger(__name__)


def final_comprehensive_test():
    """最终综合测试"""
    print("=" * 80)
    print("爱交易最终综合测试")
    print("=" * 80)

    # 最优化的Chrome配置
    chrome_options = ChromeOptions()

    # Headless模式
    chrome_options.add_argument('--headless')

    # 基本配置
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # 反检测措施
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 设置真实User-Agent
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    # 添加其他真实浏览器特征
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--profile-directory=Default')

    # 启用性能日志
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(
        options=chrome_options,
        service=Service(executable_path='/usr/bin/chromedriver')
    )

    driver.implicitly_wait(15)

    try:
        print("\n步骤1: 访问网站并执行反检测脚本")
        print("-" * 80)

        # 执行反检测脚本
        anti_detection_script = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });

        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });

        // 修改屏幕属性
        Object.defineProperty(screen, 'availWidth', {
            get: () => 1920
        });
        Object.defineProperty(screen, 'availHeight', {
            get: () => 1080
        });
        """

        driver.execute_script(anti_detection_script)

        driver.get("https://aijiaoyi.xyz/chart")
        time.sleep(8)

        print("✅ 页面加载完成")

        print("\n步骤2: 点击加密货币按钮")
        print("-" * 80)

        try:
            # 等待按钮出现并点击
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'crypto_currency'))
            )
            driver.execute_script('document.getElementById("crypto_currency").click()')
            print("✅ 已点击加密货币按钮")
            time.sleep(8)
        except Exception as e:
            print(f"⚠️ 点击加密货币按钮失败: {e}")

        print("\n步骤3: 点击币安永续")
        print("-" * 80)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'binance_perpetual'))
            )
            driver.execute_script('document.getElementById("binance_perpetual").click()')
            print("✅ 已点击币安永续")
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ 点击币安永续失败: {e}")

        print("\n步骤4: 检查初始币种数量")
        print("-" * 80)

        try:
            symbol_list = driver.find_element(By.ID, 'symbol_list')
            initial_symbols = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
            print(f"初始币种数量: {len(initial_symbols)}")
        except:
            print("❌ 无法获取初始币种")
            initial_symbols = []

        print("\n步骤5: 多策略滚动(尝试触发懒加载)")
        print("-" * 80)

        max_symbols = len(initial_symbols)
        best_symbols = initial_symbols

        # 策略1: 快速滚动到底部并返回
        print("策略1: 快速滚动到底部")
        for i in range(30):
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(0.3)

            if i % 10 == 0:
                try:
                    current_symbols = driver.find_element(By.ID, 'symbol_list').find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
                    if len(current_symbols) > max_symbols:
                        max_symbols = len(current_symbols)
                        best_symbols = current_symbols
                        print(f"  滚动第{i}次: 发现 {len(current_symbols)} 个币种 ⬆️")
                except:
                    pass

        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(3)

        # 策略2: 慢速滚动,每屏停留
        print("\n策略2: 慢速滚动")
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        for scroll_pos in range(0, scroll_height, int(viewport_height / 2)):
            driver.execute_script(f'window.scrollTo(0, {scroll_pos});')
            time.sleep(1)

            try:
                current_symbols = driver.find_element(By.ID, 'symbol_list').find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
                if len(current_symbols) > max_symbols:
                    max_symbols = len(current_symbols)
                    best_symbols = current_symbols
                    print(f"  位置 {scroll_pos}: 发现 {len(current_symbols)} 个币种 ⬆️")
            except:
                pass

        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(3)

        # 策略3: 点击"加载更多"类型的按钮
        print("\n策略3: 查找并点击可能的加载按钮")
        load_more_texts = ['加载更多', 'Load More', '查看更多', 'Show More', '下一页', 'Next', '>', 'more']

        for text in load_more_texts:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for elem in elements:
                    if elem.is_displayed():
                        driver.execute_script("arguments[0].click();", elem)
                        print(f"  ✅ 点击了按钮: {text}")
                        time.sleep(3)

                        current_symbols = driver.find_element(By.ID, 'symbol_list').find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
                        if len(current_symbols) > max_symbols:
                            max_symbols = len(current_symbols)
                            best_symbols = current_symbols
            except:
                pass

        print(f"\n✅ 最终找到 {len(best_symbols)} 个币种")

        print("\n步骤6: 提取并显示币种数据")
        print("-" * 80)

        crypto_data = []
        for i, elem in enumerate(best_symbols, 1):
            try:
                symbol_id = elem.get_attribute('id')
                text = elem.text

                if not text or '\n' not in text:
                    continue

                parts = text.split('\n')
                if len(parts) >= 3:
                    name = parts[0] if parts[0] else symbol_id
                    price_str = parts[1].replace(',', '').replace('N/A', '0')
                    change = parts[2]

                    try:
                        price = float(price_str)
                    except:
                        price = 0

                    clean_symbol = symbol_id.replace('BINANCE:', '') if 'BINANCE:' in symbol_id else symbol_id

                    crypto_data.append({
                        'rank': i,
                        'symbol': clean_symbol,
                        'full_symbol': symbol_id,
                        'name': name,
                        'price': price,
                        'change_percent': change
                    })
            except:
                continue

        if crypto_data:
            print(f"\n{'='*80}")
            print(f"成功获取 {len(crypto_data)} 个币种:")
            print(f"{'='*80}\n")

            for coin in crypto_data:
                print(f"{coin['rank']:2d}. {coin['symbol']:25} {coin['name']:20} "
                      f"价格:{coin['price']:12.2f} 涨跌:{coin['change_percent']}")

            # 保存到文件
            with open('/tmp/aijiaoyi_final_result.json', 'w', encoding='utf-8') as f:
                json.dump(crypto_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 数据已保存到 /tmp/aijiaoyi_final_result.json")
        else:
            print("❌ 未能提取到币种数据")

        print("\n步骤7: 检查页面中的其他可能数据源")
        print("-" * 80)

        # 检查localStorage
        local_storage = driver.execute_script("""
            let items = {};
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        """)

        if local_storage:
            print(f"发现 {len(local_storage)} 个localStorage项:")
            for key, value in list(local_storage.items())[:10]:
                print(f"  {key}: {value[:100]}")

        # 检查所有可能的列表容器
        all_divs = driver.find_elements(By.TAG_NAME, 'div')
        print(f"\n页面共有 {len(all_divs)} 个div元素")

        # 查找可能包含币种数据的div
        potential_containers = 0
        for div in all_divs:
            try:
                div_id = div.get_attribute('id')
                div_class = div.get_attribute('class')

                if div_id and ('list' in div_id.lower() or 'symbol' in div_id.lower()):
                    children = div.find_elements(By.TAG_NAME, 'div')
                    if len(children) > 10:
                        potential_containers += 1
                        print(f"发现容器 {div_id}: {len(children)} 个子元素")
            except:
                pass

        if potential_containers == 0:
            print("未发现其他可能的币种容器")

    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)


if __name__ == "__main__":
    final_comprehensive_test()
