from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from urllib.parse import quote_plus

def get_shop_urls_for_product(product_li):
    shop_urls = []
    try:
        buy_links = product_li.find_elements(By.CSS_SELECTOR, "p.price_sect a[href*='buyer.danawa.com']")
        for link in buy_links:
            href = link.get_attribute("href")
            if href and href not in shop_urls:
                shop_urls.append(href)
    except Exception as e:
        print("[구매 링크 추출 실패]", e)
    return shop_urls
from bs4 import BeautifulSoup


def extract_product_options(product_li):
    options = []
    try:
        # 옵션명이 들어 있는 모든 <span class="text"> 요소 찾기
        option_spans = product_li.find_elements(By.CSS_SELECTOR, "span.text")
        for span in option_spans:
            text = span.text.strip()
            if text and text not in options:
                options.append(text)
    except:
        pass
    return options

def extract_specs_text(spec_html: str):
    soup = BeautifulSoup(spec_html, "html.parser")
    keywords = []

    # 모든 <a> 태그에서 텍스트 추출
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        if text:
            keywords.append(text)
    
    return keywords

def get_final_redirect_url(driver, url):
    # 새 탭에서 열고 최종 리다이렉트 URL 얻기
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)
    time.sleep(5)  # 리다이렉트 대기
    final_url = driver.current_url
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return final_url

def crawl_danawa_keyboards(query="키보드", max_count=5):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless")  # 필요시 활성화

    driver = webdriver.Chrome(options=options)

    try:
        url = f"https://search.danawa.com/dsearch.php?query={quote_plus(query)}&tab=main"
        driver.get(url)
        time.sleep(3)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item")
        result = []

        for idx, p in enumerate(products):
            if idx >= max_count:
                break
            # 광고 등 예외상품은 'prod_name'이 없으므로 건너뜀
            try:
                name = p.find_element(By.CSS_SELECTOR, "p.prod_name > a").text.strip()
            except:
                continue


            # 가격 추출
            try:
                price = p.find_element(By.CSS_SELECTOR, "p.price_sect > a").text.strip().replace(",", "").replace("원", "")
            except:
                price = ""


            # description 추출
            try:
                spec_html = p.find_element(By.CSS_SELECTOR, "div.spec_list").get_attribute("innerHTML")
                spec_keywords = extract_specs_text(spec_html)
                print(f"[사양 추출] {spec_keywords}")
            except:
                spec_keywords = []

            # 썸네일 추출
            try:
                thumbnail = p.find_element(By.CSS_SELECTOR, "a.thumb_link > img").get_attribute("src")
            except:
                thumbnail = ""
            
            # 옵션 추출

            try:
                options = extract_product_options(p)
            except:
                options = []

   
            result.append({
                "name": name,
                "price": price,
                "description": spec_keywords,
                "thumbnail": thumbnail,
                "options": options  # 👉 여기 추가

            })

        return result

    finally:
        driver.quit()

if __name__ == "__main__":
    products_info = crawl_danawa_keyboards(query="풀배열 키보드(베어본)", max_count=2)
    for prod in products_info:
        print(f"제품명: {prod['name']}")
        print(f"가격: {prod['price']}")
        print(f"설명: {prod['description']}")
        print(f"썸네일: {prod['thumbnail']}")
        print(f"옵션: {prod['options']}")
        print("-" * 50)
