import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def get_shop_urls_for_product(product_li):
    shop_urls = []
    try:
        buy_links = product_li.find_elements(
            By.CSS_SELECTOR, "p.price_sect a[href*='buyer.danawa.com']"
        )
        for link in buy_links:
            href = link.get_attribute("href")
            if href and href not in shop_urls:
                shop_urls.append(href)
    except:
        pass
    return shop_urls

def extract_product_options(product_li):
    options = []
    try:
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
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        if text:
            keywords.append(text)
    return keywords

def get_final_redirect_url(driver, url):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(url)
        time.sleep(5)
        final_url = driver.current_url
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return final_url
    except:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return ""

def crawl_danawa_keyboards(driver, query="키보드", max_count=5, sort=None, page_limit=1):
    results = []
    base_url = "https://search.danawa.com/dsearch.php"

    for page in range(1, page_limit + 1):
        sort_param = f"&listSort={sort}" if sort else ""
        url = f"{base_url}?query={quote_plus(query)}{sort_param}&page={page}&tab=main"

        driver.get(url)
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = driver.find_elements(
            By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item"
        )

        for idx, p in enumerate(products):
            if len(results) >= max_count:
                break

            try:
                name_elem = p.find_element(By.CSS_SELECTOR, ".prod_name > a")
                name = name_elem.text.strip()
                detail_page_url = name_elem.get_attribute("href")
            except:
                continue

            try:
                try:
                    price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > a")
                except:
                    try:
                        price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect strong > em")
                    except:
                        price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > strong")
                price = price_elem.get_attribute("innerText").strip().replace(",", "").replace("원", "")
            except:
                price = ""

            try:
                spec_elem = p.find_element(By.CSS_SELECTOR, ".spec_list")
                spec_html = spec_elem.get_attribute("innerHTML")
                spec_keywords = extract_specs_text(spec_html)
            except:
                spec_keywords = []

            try:
                img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
                thumbnail = img_elem.get_attribute("src") or img_elem.get_attribute("data-original")
            except:
                thumbnail = ""

            try:
                options = extract_product_options(p)
            except:
                options = []

            try:
                final_url = get_final_redirect_url(driver, detail_page_url)
            except:
                final_url = ""

            results.append(
                {
                    "name": name,
                    "price": price,
                    "description": spec_keywords,
                    "thumbnail": thumbnail,
                    "options": options,
                    "detail_page_url": detail_page_url,
                    "final_purchase_url": final_url,  # ← 이 필드에 저장
                }
            )

        if len(results) >= max_count:
            break

    return results

def crawl_danawa_product_list(driver, query, sort=None, max_items=10, page_limit=1):
    return crawl_danawa_keyboards(driver, query=query, sort=sort, max_count=max_items, page_limit=page_limit)
