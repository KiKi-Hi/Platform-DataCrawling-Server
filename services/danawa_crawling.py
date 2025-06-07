import datetime
import os
import re
import time
from urllib.parse import parse_qs, quote_plus, urlparse

from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from services.danawa_list import crawl_danawa_product_list

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "kikihi"
COLLECTION_NAME = "products"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver

def get_final_purchase_url(driver):
    import time

    from selenium.webdriver.common.by import By

    try:
        buy_link = driver.find_element(By.CSS_SELECTOR, "a.buy_link")
        main_window = driver.current_window_handle
        before_handles = set(driver.window_handles)
        driver.execute_script("arguments[0].click();", buy_link)
        time.sleep(5)
        after_handles = set(driver.window_handles)
        new_handles = after_handles - before_handles

        if new_handles:
            new_window = new_handles.pop()
            driver.switch_to.window(new_window)
            time.sleep(2)
            final_url = driver.current_url
            driver.close()
            driver.switch_to.window(main_window)
        else:
            final_url = driver.current_url
        return final_url
    except Exception:
        return ""

def get_spec_table(driver):
    specs = {}
    try:
        spec_tab_selectors = [
            "li#danawaProdDetailTabDetail a",
            "ul.info_hd a[href*='#productDescription']",
            "div.sub_tab_wrap li a[data-idx='0']",
            "a.tab_anchor[name='productDescription']",
        ]
        for selector in spec_tab_selectors:
            try:
                tab = driver.find_element(By.CSS_SELECTOR, selector)
                if tab.is_displayed() and tab.is_enabled():
                    driver.execute_script("arguments[0].click();", tab)
                    time.sleep(1.5)
                    break
            except:
                continue
        soup = BeautifulSoup(driver.page_source, "html.parser")
        spec_table = soup.select_one(
            "div#productDescription table#productDetailSpec tbody, "
            "div.detail_cont_border table.spec_tbl tbody, "
            "div.spec_box table tbody, "
            "div.prod_spec table tbody"
        )
        if not spec_table:
            return specs
        current_category = ""
        for row in spec_table.find_all("tr", recursive=False):
            if not hasattr(row, "find_all"):
                continue
            header_cells = row.find_all("th", recursive=False)
            data_cells = row.find_all("td", recursive=False)
            if len(header_cells) == 1 and header_cells[0].get("colspan"):
                current_category = header_cells[0].get_text(strip=True)
                if "주요사양" in current_category or "스펙" in current_category:
                    current_category = ""
            elif header_cells and data_cells:
                for i in range(len(header_cells)):
                    key = header_cells[i].get_text(strip=True)
                    if not key and header_cells[i].find("img"):
                        key = header_cells[i].find("img").get("alt", "icon_spec")
                    if not key:
                        continue
                    value = (
                        data_cells[i].get_text(strip=True)
                        if i < len(data_cells)
                        else ""
                    )
                    full_key = (
                        f"{current_category} > {key}" if current_category else key
                    )
                    specs[full_key] = value
    except Exception:
        pass
    return specs

def get_all_detail_images(driver):
    import time

    from bs4 import BeautifulSoup
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    images = []
    try:
        try:
            detail_tab_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "li#danawaProdDetailTabDetail a, ul.info_hd a[href*='#productDescription'], a.tab_anchor[name='productDescription']")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                detail_tab_button,
            )
            time.sleep(2)
        except Exception:
            pass
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tags = soup.select("table tbody tr td div p img")
        for img_tag in img_tags:
            src = img_tag.get("src")
            lazy_src = (
                img_tag.get("data-original")
                or img_tag.get("data-src")
                or img_tag.get("_src")
            )
            if isinstance(lazy_src, list):
                lazy_src = lazy_src[0] if lazy_src else None
            final_src = (
                lazy_src
                if (isinstance(lazy_src, str) and lazy_src.startswith("http"))
                else src
            )
            if (
                final_src
                and isinstance(final_src, str)
                and final_src.startswith("http")
                and final_src not in images
            ):
                if "spacer.gif" not in final_src and "loading.gif" not in final_src:
                    images.append(final_src)
    except Exception:
        pass
    return images

def get_danawa_actual_purchase_link(bridge_url: str) -> str:
    parsed_url = urlparse(bridge_url)
    query_params = parse_qs(parsed_url.query)
    pcode = query_params.get('pcode', [None])[0]
    if pcode:
        return f"https://prod.danawa.com/info/?pcode={pcode}&keyword=&cate="
    else:
        return f"https://prod.danawa.com/info/?keyword={quote_plus(parsed_url.path)}"

def crawl_danawa_product_detail(driver, detail_url):
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)
    except Exception as page_load_err:
        return {
            "detail_page_url": detail_url,
            "error": f"Page load error: {page_load_err}",
        }
    detail_data = {}
    if not detail_data.get("final_purchase_url"):
        detail_data["final_purchase_url"] = get_final_purchase_url(driver)
    # 이미 값이 있으면 기존 값 유지!

    detail_data["spec_table"] = get_spec_table(driver)
    detail_data["all_detail_images"] = get_all_detail_images(driver)
    return detail_data

def crawl_products(
    query: str,
    sort: str = "accuracy",
    max_items: int = 1,
    save_format: str = "json",
    page_limit: int = 1,
    headless: bool = True,
):
    list_driver = get_driver(headless=headless)
    all_product_data = []
    try:
        list_products = crawl_danawa_product_list(
            list_driver,
            query=query,
            sort=sort,
            max_items=max_items,
            page_limit=page_limit,
        )
    except Exception:
        list_products = []
    finally:
        if list_driver:
            list_driver.quit()
    if not list_products:
        return []
    detail_page_driver = get_driver(headless=headless)
    for i, item in enumerate(list_products):
        name = item.get("name", "Unknown Product")
        bridge_url = item.get("detail_page_url")
        if bridge_url:
            actual_url = get_danawa_actual_purchase_link(bridge_url)
        if not bridge_url:
            all_product_data.append(
                {**item, "detail_crawl_error": "Missing detail page URL"}
            )
            continue
        try:
            product_details = crawl_danawa_product_detail(detail_page_driver, bridge_url)
            combined_data = {**item, **product_details}
            all_product_data.append(combined_data)
        except Exception as e:
            all_product_data.append({**item, "detail_crawl_error": str(e)})
        if i < len(list_products) - 1:
            time.sleep(2)
    if detail_page_driver:
        detail_page_driver.quit()
    try:
        if all_product_data:
            collection.insert_many(all_product_data)
        client.close()
    except Exception:
        pass
    return all_product_data

def danawa_crawling():
    query = "60커스텀 키보드 하우징"
    sort = "accuracy"
    max_items = 3
    page_limit = 1
    data = crawl_products(
        query=query,
        sort=sort,
        max_items=max_items,
        page_limit=page_limit,
        headless=True,
    )
  

if __name__ == "__main__":
    danawa_crawling()
