"""
爱交易反爬虫检测脚本
检查网站是否有反自动化检测机制
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from app.utils.logger import get_logger

logger = get_logger(__name__)


def detect_anti_automation():
    """检测网站是否有反自动化机制"""
    print("=" * 80)
    print("爱交易反爬虫检测")
    print("=" * 80)

    # 配置1: 基础配置(可能被检测)
    print("\n测试1: 基础配置(容易被检测)")
    print("-" * 80)

    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver1 = webdriver.Chrome(
        options=chrome_options,
        service=Service(executable_path='/usr/bin/chromedriver')
    )

    driver1.get("https://aijiaoyi.xyz/chart")
    time.sleep(5)

    # 检查WebDriver标识
    webdriver_detected = driver1.execute_script("""
        return {
            'navigator.webdriver': navigator.webdriver,
            'chrome对象': window.chrome ? '存在' : '不存在',
            'permissions': navigator.permissions ? '存在' : '不存在',
            'plugins长度': navigator.plugins.length,
            'languages': navigator.languages,
            'userAgent': navigator.userAgent
        }
    """)

    print("WebDriver检测结果:")
    print(json.dumps(webdriver_detected, ensure_ascii=False, indent=2))

    # 获取页面源码,检查是否有反爬虫提示
    page_source = driver1.page_source
    anti_bot_keywords = ['机器人', 'robot', 'bot', 'captcha', 'verification', '检测', 'blocked']

    found_keywords = []
    for keyword in anti_bot_keywords:
        if keyword.lower() in page_source.lower():
            found_keywords.append(keyword)

    if found_keywords:
        print(f"\n⚠️ 发现反爬虫关键词: {found_keywords}")
    else:
        print("\n✅ 未发现明显的反爬虫关键词")

    # 检查实际获取的币种数量
    try:
        symbol_list = driver1.find_element(By.ID, 'symbol_list')
        symbols = symbol_list.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
        print(f"\n基础配置获取到: {len(symbols)} 个币种")
    except:
        print("\n❌ 未找到币种列表")

    driver1.quit()

    # 配置2: 反检测配置
    print("\n\n测试2: 反检测配置(更难被检测)")
    print("-" * 80)

    chrome_options2 = ChromeOptions()
    chrome_options2.add_argument('--headless')
    chrome_options2.add_argument('--no-sandbox')
    chrome_options2.add_argument('--disable-dev-shm-usage')

    # 反检测措施
    chrome_options2.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options2.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options2.add_experimental_option('useAutomationExtension', False)

    # 设置更真实的User-Agent
    chrome_options2.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    # 添加更多真实浏览器特征
    chrome_options2.add_argument('--disable-infobars')
    chrome_options2.add_argument('--disable-extensions')
    chrome_options2.add_argument('--profile-directory=Default')
    chrome_options2.add_argument('--disable-plugins-discovery')
    chrome_options2.add_argument('--incognito')

    driver2 = webdriver.Chrome(
        options=chrome_options2,
        service=Service(executable_path='/usr/bin/chromedriver')
    )

    # 注入JavaScript修改navigator属性
    driver2.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // 添加chrome对象
        window.chrome = {
            runtime: {}
        };

        // 修改plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // 修改languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });
    """)

    driver2.get("https://aijiaoyi.xyz/chart")
    time.sleep(5)

    # 再次检查WebDriver标识
    webdriver_detected2 = driver2.execute_script("""
        return {
            'navigator.webdriver': navigator.webdriver,
            'chrome对象': window.chrome ? '存在' : '不存在',
            'permissions': navigator.permissions ? '存在' : '不存在',
            'plugins长度': navigator.plugins.length,
            'languages': navigator.languages,
            'userAgent': navigator.userAgent
        }
    """)

    print("WebDriver检测结果:")
    print(json.dumps(webdriver_detected2, ensure_ascii=False, indent=2))

    # 点击加密货币按钮
    try:
        driver2.execute_script('document.getElementById("crypto_currency").click()')
        print("✅ 已点击加密货币按钮")
        time.sleep(5)

        # 点击币安永续
        driver2.execute_script('document.getElementById("binance_perpetual").click()')
        print("✅ 已点击币安永续")
        time.sleep(8)

        # 滚动页面
        for i in range(20):
            driver2.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(0.5)

        # 检查币种数量
        symbol_list2 = driver2.find_element(By.ID, 'symbol_list')
        symbols2 = symbol_list2.find_elements(By.CSS_SELECTOR, '[contenteditable="false"]')
        print(f"\n反检测配置获取到: {len(symbols2)} 个币种")

        if len(symbols2) > 15:
            print(f"\n🎉 成功! 反检测配置获取到更多币种: {len(symbols2)} 个")
        else:
            print(f"\n⚠️ 反检测配置仍然只有 {len(symbols2)} 个币种")

        # 显示前20个币种
        print(f"\n前20个币种:")
        for i, elem in enumerate(symbols2[:20], 1):
            try:
                symbol_id = elem.get_attribute('id')
                text = elem.text
                parts = text.split('\n')
                if len(parts) >= 3:
                    print(f"{i:2d}. {symbol_id:25} {parts[0]:15} 价格:{parts[1]:12} 涨跌:{parts[2]}")
            except:
                continue

    except Exception as e:
        print(f"❌ 出错: {e}")

    driver2.quit()

    # 配置3: 非headless模式对比(如果可能)
    print("\n\n测试3: 检查页面是否有动态加载机制")
    print("-" * 80)

    chrome_options3 = ChromeOptions()
    chrome_options3.add_argument('--headless')
    chrome_options3.add_argument('--no-sandbox')
    chrome_options3.add_argument('--disable-dev-shm-usage')
    chrome_options3.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options3.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options3.add_experimental_option('useAutomationExtension', False)

    driver3 = webdriver.Chrome(
        options=chrome_options3,
        service=Service(executable_path='/usr/bin/chromedriver')
    )

    # 监控网络请求
    chrome_options3.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver3.execute_cdp_cmd('Network.enable', {})

    def request_interceptor(request):
        """拦截网络请求"""
        if 'symbol' in request.get('request', {}).get('url', '').lower():
            logger.info(f"发现币种相关请求: {request['request']['url']}")

    driver3.get("https://aijiaoyi.xyz/chart")
    time.sleep(5)

    # 执行JavaScript检查是否有隐藏的数据
    hidden_data = driver3.execute_script("""
        // 检查所有可能的数据容器
        let results = {};

        // 检查React/Vue状态
        if (window.__STATE__) {
            results.reactState = 'found';
        }

        // 检查所有data属性
        let elementsWithDataset = document.querySelectorAll('[data-symbol], [data-coin], [data-crypto]');
        results.dataElements = elementsWithDataset.length;

        // 检查隐藏的div
        let hiddenDivs = document.querySelectorAll('div[style*="display: none"], div[hidden]');
        results.hiddenDivs = hiddenDivs.length;

        // 检查是否有WebSocket连接
        results.websockets = typeof WebSocket !== 'undefined';

        // 检查localStorage
        try {
            let keys = Object.keys(localStorage);
            results.localStorageKeys = keys.filter(k => k.includes('symbol') || k.includes('coin'));
        } catch(e) {
            results.localStorageError = e.message;
        }

        return results;
    """)

    print("页面数据结构检测:")
    print(json.dumps(hidden_data, ensure_ascii=False, indent=2))

    driver3.quit()

    print("\n" + "=" * 80)
    print("检测完成")
    print("=" * 80)


if __name__ == "__main__":
    detect_anti_automation()
