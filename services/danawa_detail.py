import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def extract_korean(text):
    return "".join(re.findall("[가-힣0-9\s()/.-]+", text))


def get_cheapest_buy_link(driver):
    try:
        buy_link = driver.find_element(By.CSS_SELECTOR, "a.buy_link")
        return buy_link.get_attribute("href")
    except:
        return ""


def get_spec_table(driver):
    spec_table = {}
    current_category = None

    try:
        detail_tab = driver.find_element(
            By.CSS_SELECTOR, "li#danawaProdDetailTabDetail"
        )
        driver.execute_script("arguments[0].click();", detail_tab)
        time.sleep(2)
    except:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    tbody = soup.select_one("table#productDetailSpec > tbody") or soup.select_one(
        "table.spec_view_table > tbody"
    )
    if not tbody:
        return spec_table

    for tr in tbody.find_all("tr"):
        ths = tr.find_all("th")
        tds = tr.find_all("td")

        if len(ths) == 1 and ths[0].get("colspan") == "4":
            current_category = ths[0].get_text(strip=True)
            continue

        for i in range(0, len(ths)):
            key = ths[i].get_text(strip=True)
            value = tds[i].get_text(strip=True) if i < len(tds) else ""
            if key:
                full_key = f"{current_category} > {key}" if current_category else key
                spec_table[full_key] = value

    return spec_table


def get_detail_images(driver):
    try:
        tab_btn = driver.find_element(By.CSS_SELECTOR, "li#danawaProdDetailTabDetail")
        driver.execute_script("arguments[0].click();", tab_btn)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return [
            img.get("data-original") or img.get("src")
            for img in soup.select("div#detailImage img")
            if (img.get("data-original") or img.get("src", "")).startswith("http")
        ]
    except:
        return []


def get_related_products(driver):
    try:
        tab_btn = driver.find_element(By.CSS_SELECTOR, "li#danawaProdDetailTabDetail")
        driver.execute_script("arguments[0].click();", tab_btn)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        related_products = []
        for rel in soup.select("div.rel_prod_list li a"):
            rel_img = rel.select_one("img")
            rel_link = rel.get("href")
            rel_title = rel.get("title") or (
                rel_img["alt"] if rel_img and rel_img.has_attr("alt") else ""
            )
            rel_img_url = rel_img["src"] if rel_img and rel_img.has_attr("src") else ""
            related_products.append(
                {"title": rel_title, "link": rel_link, "img": rel_img_url}
            )
        return related_products
    except:
        return []


def get_price_trend_image(driver):
    try:
        price_tab = driver.find_element(By.CSS_SELECTOR, "li#danawaProdDetailTabPrice")
        driver.execute_script("arguments[0].click();", price_tab)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        price_img = soup.select_one("img#priceGraphImg")
        if price_img and price_img.has_attr("src"):
            return price_img["src"]
    except Exception as e:
        print("가격 추이 이미지 추출 실패:", e)
    return ""


def crawl_danawa_detail(product_detail_url):
    driver = get_driver()
    try:
        driver.get(product_detail_url)
        time.sleep(2)

        return {
            "buy_url": get_cheapest_buy_link(driver),
            "spec": get_spec_table(driver),
            "detail_images": get_detail_images(driver),
            "related_products": get_related_products(driver),
            "price_trend_img": get_price_trend_image(driver),
        }
    finally:
        driver.quit()


# ✅ 테스트
if __name__ == "__main__":
    url = "https://prod.danawa.com/info/?pcode=17180261&cate=112782"
    result = crawl_danawa_detail(url)

    from pprint import pprint

    pprint(result)
