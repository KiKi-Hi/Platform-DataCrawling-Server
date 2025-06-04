import datetime
import os
import re
import time
from pprint import pprint  # For pretty printing results
from urllib.parse import parse_qs, quote_plus, urlparse

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
    import time

    from selenium.webdriver.common.by import By

    try:
        buy_link = driver.find_element(By.CSS_SELECTOR, "a.buy_link")
        redirect_link = buy_link.get_attribute("href")
        print(f"중간 구매 링크: {redirect_link}")

        # 현재 창 핸들 저장
        main_window = driver.current_window_handle
        before_handles = set(driver.window_handles)

        # 링크 클릭(새 창/탭일 수도 있으니 클릭으로 처리)
        driver.execute_script("arguments[0].click();", buy_link)
        time.sleep(5)  # 충분히 대기

        # 새 창/탭이 열렸는지 확인
        after_handles = set(driver.window_handles)
        new_handles = after_handles - before_handles

        if new_handles:
            # 새 창/탭으로 열렸다면, 그 창으로 전환
            new_window = new_handles.pop()
            driver.switch_to.window(new_window)
            time.sleep(2)
            final_url = driver.current_url
            # 새 창 닫고, 원래 창으로 복귀
            driver.close()
            driver.switch_to.window(main_window)
        else:
            # 새 창이 아니라면, 현재 URL 사용
            final_url = driver.current_url

        print(f"최종 구매처 URL: {final_url}")
        return final_url
    except Exception as e:
        print(f"구매처 URL 추출 실패: {e}")
        return ""


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

            header_cells = row.find_all("th", recursive=False) # type: ignore
            data_cells = row.find_all("td", recursive=False) # type: ignore

            # Category row
            if len(header_cells) == 1 and header_cells[0].get("colspan"): # type: ignore
                current_category = header_cells[0].get_text(strip=True)
                if "주요사양" in current_category or "스펙" in current_category:
                    current_category = ""
            elif header_cells and data_cells:
                for i in range(len(header_cells)):
                    key = header_cells[i].get_text(strip=True)
                    if not key and header_cells[i].find("img"): # type: ignore
                        key = header_cells[i].find("img").get("alt", "icon_spec") # type: ignore

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
    import time

    from bs4 import BeautifulSoup
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    images = []
    try:
        # 상세설명 탭 클릭(이미 진입했다면 생략 가능)
        try:
            detail_tab_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "li#danawaProdDetailTabDetail a, ul.info_hd a[href*='#productDescription'], a.tab_anchor[name='productDescription']")
                )
            )
            print("  Ensuring '상세설명' tab is active for images.")
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
                detail_tab_button,
            )
            time.sleep(2)
        except Exception as tab_e:
            print(f"  Detail description tab not found or clickable for images, proceeding: {tab_e}")

        # 스크롤로 이미지 로딩 유도
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        print("  Finished scrolling for images.")
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 상세 이미지가 한 장만 있는 경우, 정확한 selector로 추출
        # (table > tbody > tr > td > div > p > img)
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
        print(f"  Extracted {len(images)} unique detail images.")
    except Exception as e:
        print(f"  Error extracting detail images: {e}")
    return images

# 연관 상품
# def get_related_products(driver):
#     related = []
#     try:
#         # Related products might not need a specific tab click, often at bottom of page or sidebar
#         # Scroll to bottom to ensure they are loaded
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.8);")
#         time.sleep(0.5)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(1)

#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         # Common selectors for related product lists (these can vary a lot)
#         related_sections_selectors = [
#             "div.rel_prod_list ul li",
#             "div.relation_goods_list ul li",
#             "div.recommend_product_list ul li",
#             "div.another_goods ul li",
#             "div.prod_rel_list ul li",
#             "div.rel_goods_area ul.goods_list li",
#         ]

#         related_items_elements = []
#         for selector in related_sections_selectors:
#             elements = soup.select(selector)
#             if elements:
#                 related_items_elements = elements
#                 print(f"  Found related products section with selector: {selector}")
#                 break

#         if not related_items_elements:
#             print("  No related products section found with common selectors.")
#             return []

#         for item_el in related_items_elements:
#             link_tag = item_el.find("a")
#             if not link_tag:
#                 continue

#             name = ""
#             link = link_tag.get("href", "")
#             link_str = str(link)
#             if link_str and not link_str.startswith("http"):  # Ensure absolute URL
#                 if link_str.startswith("//"):
#                     link = "https:" + link_str
#                 elif link_str.startswith("/"):
#                     link = "https://prod.danawa.com" + link_str  # Assuming danawa links
#                 else:
#                     link = link_str
#             else:
#                 link = link_str

#             # Try to get name from a dedicated text element, often more reliable
#             name_selectors = [".txt_link", ".prod_name", ".tit", ".name", ".shrt_desc"]
#             for sel in name_selectors:
#                 name_element = item_el.select_one(sel)
#                 if name_element and name_element.get_text(strip=True):
#                     name = name_element.get_text(strip=True)
#                     break

#             price_selectors = [
#                 ".price_sect .price",
#                 "span.price",
#                 "em.num_c",
#                 ".prc_c",
#                 ".curr_price",
#             ]
#             price = ""
#             for sel in price_selectors:
#                 price_element = item_el.select_one(sel)
#                 if price_element:
#                     price = (
#                         price_element.get_text(strip=True)
#                         .replace(",", "")
#                         .replace("원", "")
#                     )
#                     break

#             if name and link:
#                 related.append(
#                     {"name": name, "price": price, "link": link, "image_url": img_src}
#                 )
#         print(f"  Extracted {len(related)} related products.")
#     except Exception as e:
#         print(f"  Error extracting related products: {e}")
#     return related


# 가격 추이
# def get_price_trend_image_url(driver):
#     url = ""
#     try:
#         # Click "가격비교" or "가격추이" tab
#         price_tab_selectors = [
#             "li#danawaProdDetailTabPriceCompare a",  # Price Comparison tab
#             "li#danawaProdDetailTabPrice a",  # Price Trend tab
#             "ul.info_hd a[href*='#priceCompare']",
#             "ul.info_hd a[href*='#priceHistory']",
#             "a.tab_anchor[name='priceCompare']",
#         ]
#         price_tab_button = None
#         for selector in price_tab_selectors:
#             try:
#                 button = driver.find_element(By.CSS_SELECTOR, selector)
#                 if button.is_displayed() and button.is_enabled():
#                     price_tab_button = button
#                     break
#             except:
#                 continue

#         if price_tab_button:
#             print("  Clicking price trend/comparison tab.")
#             driver.execute_script(
#                 "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
#                 price_tab_button,
#             )
#             time.sleep(2.5)  # Wait for graph to load
#         else:
#             print(
#                 "  Price trend/comparison tab not found, graph might be visible by default or not present."
#             )

#         # Selector for price graph image
#         graph_img_selectors = [
#             "img#priceGraphImg",  # Most common ID
#             "div.chart_area img",  # Image within a chart area
#             "img.price_graph_img",
#             "div#price_graph_area img",
#         ]
#         graph_img_element = None
#         for selector in graph_img_selectors:
#             try:
#                 graph_img_element = WebDriverWait(driver, 5).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#                 )
#                 if graph_img_element:
#                     break
#             except:
#                 continue

#         if graph_img_element:
#             url = graph_img_element.get_attribute("src")
#             if url and url.startswith("//"):
#                 url = "https:" + url  # Ensure absolute URL
#             print(f"  Extracted price trend image URL: {url if url else 'Not found'}")
#         else:
#             print("  Price trend graph image not found.")
#     except Exception as e:
#         print(f"  Error extracting price trend image: {e}")
#     return url

# 상세 페이지 URL
def get_danawa_actual_purchase_link(bridge_url: str) -> str:
    """
    다나와 '최저가 구매하기' bridge URL에서 실제 상품 상세/구매 페이지 URL을 생성
    """
    parsed_url = urlparse(bridge_url)
    query_params = parse_qs(parsed_url.query)
    pcode = query_params.get('pcode', [None])[0]
    if pcode:
        return f"https://prod.danawa.com/info/?pcode={pcode}&keyword=&cate="
    else:
        return f"https://prod.danawa.com/info/?keyword={quote_plus(parsed_url.path)}"

# 상세 페이지로 접근 후 각각 메서드 실행
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
    # detail_data["related_products"] = get_related_products(driver)
    # detail_data["price_trend_image_url"] = get_price_trend_image_url(driver)

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

    # 상세 페이지 크롤링 // 여기서 부터 문제
    for i, item in enumerate(list_products):
        name = item.get("name", "Unknown Product")

        # 상세 페이지 url 
        bridge_url = item.get("detail_page_url")
        if bridge_url:
            actual_url = get_danawa_actual_purchase_link(bridge_url)
            item["actual_purchase_url"] = actual_url
        if not bridge_url:
            print(f" - 상세 페이지 URL 없음. '{name}' 생략")
            all_product_data.append(
                {**item, "detail_crawl_error": "Missing detail page URL"}
            )
            continue

        try:
            # 상세 페이지에서 정보 크롤링
            product_details = crawl_danawa_product_detail(detail_page_driver, bridge_url)
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
        print(f"상세 페이지 URL: {item.get('detail_page_url')}")
        
        print(f"최종 구매 URL: {item.get('final_purchase_url')}")
        print(f"스펙: {item.get('spec_table')}")
        print(f"상세 이미지: {item.get('all_detail_images')}")
        print(f"연관 상품: {item.get('related_products')}")
        print(f"가격 추이 이미지 URL: {item.get('price_trend_image_url')}")
        print(f"저장된 시간: {datetime.datetime.now().isoformat()}")
        print("-" * 40)


if __name__ == "__main__":
    danawa_crawling()
