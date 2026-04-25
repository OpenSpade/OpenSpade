from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import random

# 爬取币安下架信息页面
def crawl_binance_delisting():
    url = "https://www.binance.com/zh-CN/support/announcement/list/161"
    
    # 配置Chrome选项
    chrome_options = Options()
    # 暂时不使用无头模式，以便查看页面情况
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 初始化浏览器
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 执行JavaScript以隐藏webdriver属性
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    try:
        # 打开页面
        driver.get(url)
        
        # 等待页面加载（使用随机时间）
        time.sleep(random.uniform(3, 5))
        
        # 处理Cookie同意弹窗
        try:
            accept_button = driver.find_element("xpath", "//button[contains(text(), '接受所有 Cookie')]")
            accept_button.click()
            time.sleep(random.uniform(1, 3))
        except:
            pass
        
        # 滚动页面加载更多内容（使用随机时间）
        for i in range(3):
            driver.execute_script(f"window.scrollBy(0, {random.randint(800, 1200)});")
            time.sleep(random.uniform(1.5, 3))
        
        # 获取页面源码
        page_source = driver.page_source
        
        # 保存页面源码到文件以便调试
        with open('binance_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 找到下架信息的公告列表
        delisting_announcements = []
        
        # 查找所有链接元素
        for link in soup.find_all('a'):
            text = link.get_text(strip=True)
            if text and ('下架' in text or '移除' in text):
                href = link.get('href', '')
                if href:
                    if not href.startswith('http'):
                        href = f"https://www.binance.com{href}"
                else:
                    href = url
                
                delisting_announcements.append({
                    "title": text,
                    "url": href
                })
        
        # 去重
        unique_announcements = []
        seen_titles = set()
        for announcement in delisting_announcements:
            if announcement['title'] not in seen_titles:
                seen_titles.add(announcement['title'])
                unique_announcements.append(announcement)
        
        return unique_announcements
        
    finally:
        # 关闭浏览器
        driver.quit()

# 主函数
if __name__ == "__main__":
    print("正在爬取币安下架信息...")
    announcements = crawl_binance_delisting()
    
    print(f"\n共收集到 {len(announcements)} 条下架信息：")
    print("-" * 80)
    
    for i, announcement in enumerate(announcements, 1):
        print(f"{i}. {announcement['title']}")
        print(f"   链接: {announcement['url']}")
        print("-" * 80)
    
    # 保存为JSON文件
    with open('binance_delisting_announcements.json', 'w', encoding='utf-8') as f:
        json.dump(announcements, f, ensure_ascii=False, indent=2)
    
    print("\n下架信息已保存到 binance_delisting_announcements.json 文件中。")