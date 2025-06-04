import datetime
import os
import re
import time
from pprint import pprint  # For pretty printing results
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from danawa_list import crawl_danawa_product_list
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# MongoDB 접속 정보
MONGO_URI = "mongodb://localhost:27017"  # 필요 시 환경에 맞게 변경
DB_NAME = "kikihi"
COLLECTION_NAME = "products"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


# --- 1. Helper: Selenium WebDriver Setup ---
def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )  # To avoid bot detection
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Use a common user agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        print(
            "Please ensure you have ChromeDriver installed and in your PATH, or provide the executable_path."
        )
        raise

    options_texts = []
    try:
        # More specific selector for options, often within spec_list
        option_elements = product_li_element.find_elements(
            By.CSS_SELECTOR,
            "div.spec_list dd > a, div.spec_list span.cmpr_txt, div.spec_list span.spec_item_val",
        )
        for el in option_elements:
            text = el.text.strip()
            if text and text not in options_texts:
                options_texts.append(text)
    except Exception as e:
        print(f"  List options extraction error: {e}")
    return options_texts


# 최저가 링크
def get_final_purchase_url(driver):
    try:
        buy_link = driver.find_element(By.CSS_SELECTOR, "a.buy_link")
        return buy_link.get_attribute("href")
    except:
        return ""


# spec table


# 스펙 테이블
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
                    print(f"  Clicking spec tab: {selector}")
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
            print("  Spec table not found.")
            return specs

        current_category = ""
        for row in spec_table.find_all("tr", recursive=False):
            if not hasattr(row, "find_all"):
                continue

            header_cells = row.find_all("th", recursive=False)
            data_cells = row.find_all("td", recursive=False)

            # Category row
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

        print(f"  Extracted {len(specs)} spec items.")

    except Exception as e:
        print(f"  Error extracting specs: {e}")

    return specs


# 상세 이미지들
def get_all_detail_images(driver):
    images = []
    try:
        # Ensure "상세설명" tab is active
        try:
            detail_tab_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "li#danawaProdDetailTabDetail a, "
                        "ul.info_hd a[href*='#productDescription'], "
                        "a.tab_anchor[name='productDescription']",  # Tab might be an anchor
                    )
                )
            )
            print("  Ensuring '상세설명' tab is active for images.")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                detail_tab_button,
            )
            time.sleep(3)  # Wait for images to potentially load/relayout
        except Exception as tab_e:
            print(
                f"  Detail description tab not found or clickable for images, proceeding: {tab_e}"
            )

        # Scroll through the detail section to trigger lazy loading
        print("  Scrolling to load all detail images...")
        scroll_pause_time = 0.5  # Faster scroll for images
        last_height = driver.execute_script("return document.body.scrollHeight")

        # Target specific content areas for scrolling if possible
        scroll_target_selectors = [
            "div#detail_info_wrap div.detail_cont",
            "div#productDescription",
            "div.product_detail_content_area",
            "body",  # Fallback to body
        ]
        scroll_element_js = "return arguments[0].scrollHeight"
        scroll_js = "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;"

        scroll_target_found = False
        for sel in scroll_target_selectors:
            try:
                target_element = driver.find_element(By.CSS_SELECTOR, sel)
                if target_element:
                    print(f"  Scrolling within element: {sel}")
                    element_height = driver.execute_script(
                        scroll_element_js, target_element
                    )
                    current_element_scroll = 0
                    while current_element_scroll < element_height:
                        driver.execute_script(scroll_js, target_element)
                        time.sleep(scroll_pause_time)
                        current_element_scroll += driver.execute_script(
                            "return arguments[0].clientHeight;", target_element
                        )
                        new_element_height = driver.execute_script(
                            scroll_element_js, target_element
                        )
                        if new_element_height > element_height:  # Content expanded
                            element_height = new_element_height
                        else:  # Check if we are at the bottom
                            scrolled_val = driver.execute_script(
                                "return arguments[0].scrollTop", target_element
                            )
                            if (
                                scrolled_val
                                + driver.execute_script(
                                    "return arguments[0].clientHeight;", target_element
                                )
                                >= element_height - 10
                            ):  # Allow small diff
                                break
                    scroll_target_found = True
                    break
            except:
                continue

        if (
            not scroll_target_found
        ):  # Fallback to body scroll if no specific target worked
            print("  Fallback to body scroll for images.")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

        print("  Finished scrolling for images.")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Common selectors for detail images section
        image_containers = soup.select(
            "div#detail_info_wrap div.detail_cont img, "  # Primary location
            "div#productDescription img, "  # Inside product description anchor
            "div.product_detail_content_area img, "  # Another common content area
            "div.detail_area img"  # General detail area
        )
        for img_tag in image_containers:
            src = img_tag.get("src")
            # Prioritize 'data-original' or other lazy-load attributes if 'src' is a placeholder
            lazy_src = (
                img_tag.get("data-original")
                or img_tag.get("data-src")
                or img_tag.get("_src")
            )
            # Ensure lazy_src is a string before using startswith
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
                if (
                    "spacer.gif" not in final_src and "loading.gif" not in final_src
                ):  # Filter out placeholders
                    images.append(final_src)
        print(f"  Extracted {len(images)} unique detail images.")
    except Exception as e:
        print(f"  Error extracting detail images: {e}")
    return images


# 연관 상품
def get_related_products(driver):
    related = []
    try:
        # Related products might not need a specific tab click, often at bottom of page or sidebar
        # Scroll to bottom to ensure they are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.8);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Common selectors for related product lists (these can vary a lot)
        related_sections_selectors = [
            "div.rel_prod_list ul li",
            "div.relation_goods_list ul li",
            "div.recommend_product_list ul li",
            "div.another_goods ul li",
            "div.prod_rel_list ul li",
            "div.rel_goods_area ul.goods_list li",
        ]

        related_items_elements = []
        for selector in related_sections_selectors:
            elements = soup.select(selector)
            if elements:
                related_items_elements = elements
                print(f"  Found related products section with selector: {selector}")
                break

        if not related_items_elements:
            print("  No related products section found with common selectors.")
            return []

        for item_el in related_items_elements:
            link_tag = item_el.find("a")
            if not link_tag:
                continue

            name = ""
            link = link_tag.get("href", "")
            link_str = str(link)
            if link_str and not link_str.startswith("http"):  # Ensure absolute URL
                if link_str.startswith("//"):
                    link = "https:" + link_str
                elif link_str.startswith("/"):
                    link = "https://prod.danawa.com" + link_str  # Assuming danawa links
                else:
                    link = link_str
            else:
                link = link_str

            # Try to get name from a dedicated text element, often more reliable
            name_selectors = [".txt_link", ".prod_name", ".tit", ".name", ".shrt_desc"]
            for sel in name_selectors:
                name_element = item_el.select_one(sel)
                if name_element and name_element.get_text(strip=True):
                    name = name_element.get_text(strip=True)
                    break

            price_selectors = [
                ".price_sect .price",
                "span.price",
                "em.num_c",
                ".prc_c",
                ".curr_price",
            ]
            price = ""
            for sel in price_selectors:
                price_element = item_el.select_one(sel)
                if price_element:
                    price = (
                        price_element.get_text(strip=True)
                        .replace(",", "")
                        .replace("원", "")
                    )
                    break

            if name and link:
                related.append(
                    {"name": name, "price": price, "link": link, "image_url": img_src}
                )
        print(f"  Extracted {len(related)} related products.")
    except Exception as e:
        print(f"  Error extracting related products: {e}")
    return related


# 가격 추이
def get_price_trend_image_url(driver):
    url = ""
    try:
        # Click "가격비교" or "가격추이" tab
        price_tab_selectors = [
            "li#danawaProdDetailTabPriceCompare a",  # Price Comparison tab
            "li#danawaProdDetailTabPrice a",  # Price Trend tab
            "ul.info_hd a[href*='#priceCompare']",
            "ul.info_hd a[href*='#priceHistory']",
            "a.tab_anchor[name='priceCompare']",
        ]
        price_tab_button = None
        for selector in price_tab_selectors:
            try:
                button = driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed() and button.is_enabled():
                    price_tab_button = button
                    break
            except:
                continue

        if price_tab_button:
            print("  Clicking price trend/comparison tab.")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                price_tab_button,
            )
            time.sleep(2.5)  # Wait for graph to load
        else:
            print(
                "  Price trend/comparison tab not found, graph might be visible by default or not present."
            )

        # Selector for price graph image
        graph_img_selectors = [
            "img#priceGraphImg",  # Most common ID
            "div.chart_area img",  # Image within a chart area
            "img.price_graph_img",
            "div#price_graph_area img",
        ]
        graph_img_element = None
        for selector in graph_img_selectors:
            try:
                graph_img_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if graph_img_element:
                    break
            except:
                continue

        if graph_img_element:
            url = graph_img_element.get_attribute("src")
            if url and url.startswith("//"):
                url = "https:" + url  # Ensure absolute URL
            print(f"  Extracted price trend image URL: {url if url else 'Not found'}")
        else:
            print("  Price trend graph image not found.")
    except Exception as e:
        print(f"  Error extracting price trend image: {e}")
    return url


# detail로 접근
def crawl_danawa_product_detail(driver, detail_url):
    print(f"Navigating to detail page: {detail_url}")
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)  # Extra pause for any late JS
    except Exception as page_load_err:
        print(f"  Error loading detail page {detail_url}: {page_load_err}")
        return {
            "detail_page_url": detail_url,
            "error": f"Page load error: {page_load_err}",
        }

    detail_data = {}

    detail_data["final_purchase_url"] = get_final_purchase_url(driver)
    detail_data["spec_table"] = get_spec_table(driver)
    detail_data["all_detail_images"] = get_all_detail_images(driver)
    detail_data["related_products"] = get_related_products(driver)
    detail_data["price_trend_image_url"] = get_price_trend_image_url(driver)

    return detail_data


# --- 4. Main Orchestration ---
def crawl_products(
    query: str,
    sort: str = "accuracy",
    max_items: int = 1,
    save_format: str = "json",
    page_limit: int = 1,
    headless: bool = True,
):
    # 드라이버 생성
    list_driver = get_driver(headless=headless)
    all_product_data = []

    try:
        print(
            f"\n--- [LIST PAGE] '{query}' 검색, 정렬: {sort}, 최대 {max_items}개, 페이지 제한: {page_limit} ---"
        )
        list_products = crawl_danawa_product_list(
            list_driver,
            query=query,
            sort=sort,
            max_items=max_items,
            page_limit=page_limit,
        )
    except Exception as e:
        print(f"!! 리스트 페이지 크롤링 중 오류 발생: {e}")
        list_products = []
    finally:
        print("[LIST PAGE] 드라이버 종료")
        if list_driver:
            list_driver.quit()

    if not list_products:
        print(f"[LIST PAGE] '{query}'에 대해 상품이 없습니다. 상세 페이지 크롤링 생략.")
        return []

    print(
        f"\n--- [DETAIL PAGE] 총 {len(list_products)}개 상품에 대해 상세정보 수집 ---"
    )
    detail_page_driver = get_driver(headless=headless)

    for i, item in enumerate(list_products):
        name = item.get("name", "Unknown Product")
        print(f"\n상세정보 수집 중 {i+1}/{len(list_products)}: {name}")
        url = item.get("detail_page_url")

        if not url:
            print(f" - 상세 페이지 URL 없음. '{name}' 생략")
            all_product_data.append(
                {**item, "detail_crawl_error": "Missing detail page URL"}
            )
            continue

        try:
            product_details = crawl_danawa_product_detail(detail_page_driver, url)
            combined_data = {**item, **product_details}
            all_product_data.append(combined_data)
            print(f" - 수집 성공: {name}")
        except Exception as e:
            print(f"!! 상세정보 수집 오류: {e}")
            all_product_data.append({**item, "detail_crawl_error": str(e)})

        if i < len(list_products) - 1:
            time.sleep(2)

    print("[DETAIL PAGE] 드라이버 종료")
    if detail_page_driver:
        detail_page_driver.quit()

    # MongoDB 저장
    try:

        # insert_many 대신 insert_one으로 반복해 저장해도 됨
        if all_product_data:
            collection.insert_many(all_product_data)
            print(f"[MONGODB] 총 {len(all_product_data)}개 상품 데이터 저장 완료")
        client.close()
    except Exception as e:
        print(f"[MONGODB] 저장 중 오류 발생: {e}")

    # JSON 저장 옵션

    return all_product_data


# 테스트용 메인 함수
def danawa_crawling():
    query = "풀배열 키보드(베어본)"
    sort = "accuracy"
    max_items = 3
    page_limit = 1
    print("[TEST] Danawa 크롤링 시작")
    data = crawl_products(
        query=query,
        sort=sort,
        max_items=max_items,
        page_limit=page_limit,
        headless=True,
    )
    print(f"[TEST] 크롤링 완료: 총 {len(data)}개 상품 수집됨")
    for i, item in enumerate(data, 1):
        print(f"\n[{i}] 제품명: {item.get('name')}")
        print(f"가격: {item.get('price')}")
        print(f"옵션: {item.get('options')}")
        print(f"설명: {item.get('description')}")


if __name__ == "__main__":
    danawa_crawling()
