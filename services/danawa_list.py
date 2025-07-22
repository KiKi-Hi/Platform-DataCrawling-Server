import re
import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from numpy import double
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
    

import re
import time
from urllib.parse import parse_qsl, quote_plus, unquote, urlencode, urlparse, urlunparse


def get_highres_thumbnail(url):
    if not url:
        return ""
    if "noImg" in url:
        return ""  # 이미지 없는 상품은 무시
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    if 'shrink' in query:
        query['shrink'] = '500:500'
    new_query = urlencode(query, doseq=True)
    rebuilt = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return unquote(rebuilt)



def crawl_danawa_keyboards(driver, query, max_count, sort, page_limit):
    from numpy import double
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
        # 대체 구조: 일부 제품군
        if not products:
            products = driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")

        print(f"[DEBUG] 상품 개수: {len(products)}")

        for idx, p in enumerate(products or []):  # 혹시라도 products가 None이면 []로
            if len(results) >= max_count:
                break

            # 안전하게 name/detail_page_url 추출
            try:
                name_elem = p.find_element(By.CSS_SELECTOR, ".prod_name > a")
                name = name_elem.text.strip() if name_elem and name_elem.text else ""
                detail_page_url = name_elem.get_attribute("href") if name_elem else ""
            except Exception:
                continue

            # price 추출 및 double 변환
            price_str = ""
            try:
                try:
                    price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > a")
                except:
                    try:
                        price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect strong > em")
                    except:
                        price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > strong")
                price_str = price_elem.get_attribute("innerText")
            except Exception:
                price_str = ""
            # 가격 후처리 및 double 변환 안정화
            price_str = str(price_str or "").strip().replace(",", "").replace("원", "")
            try:
                price_val = double(price_str) if price_str and price_str.isdigit() else 0
            except Exception:
                price_val = 0

            # 스펙 추출
            try:
                spec_elem = p.find_element(By.CSS_SELECTOR, ".spec_list")
                spec_html = spec_elem.get_attribute("innerHTML")
                spec_keywords = extract_specs_text(spec_html or "")
                if spec_keywords is None:
                    spec_keywords = []
            except Exception:
                spec_keywords = []

            # 썸네일 추출 및 고해상도 변환
            try:
                img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
                thumbnail = img_elem.get_attribute("src") or img_elem.get_attribute("data-original")
                thumbnail = get_highres_thumbnail(thumbnail)
            except Exception:
                thumbnail = ""

            # 옵션 추출
            try:
                options = extract_product_options(p)
                if options is None:
                    options = []
            except Exception:
                options = []

            # 구매 링크
            try:
                final_url = get_final_redirect_url(driver, detail_page_url)
                if final_url is None:
                    final_url = ""
            except Exception:
                final_url = ""

            # 카테고리 처리
            q = (query or "").lower()
            if "키보드 케이스" in q or "keyboard case" in q:
                category = "case"
            elif "키캡" in q or "keycap" in q:
                category = "keycap"
            elif "베어본" in q or "하우징" in q or "housing" in q:
                category = "housing"
            elif "스위치" in q or "switch" in q:
                category = "switch"
            elif "케이스" in q or "case" in q:
                category = "case"
            elif "키보드" in q or "keyboard" in q:
                category = "keyboard"
            else:
                category = "accessory"

            results.append({
                "name": name,
                "price": price_val,
                "category": category,
                "description": spec_keywords,
                "thumbnail": thumbnail,
                "options": options,
                "detail_page_url": detail_page_url,
                "final_purchase_url": final_url,
            })


        if results is None:
                results = []
        return results

#이거지예
# def crawl_danawa_keyboards(driver, query, max_count, sort, page_limit):
#     results = []
#     base_url = "https://search.danawa.com/dsearch.php"

#     for page in range(1, page_limit + 1):
#         sort_param = f"&listSort={sort}" if sort else ""
#         url = f"{base_url}?query={quote_plus(query)}{sort_param}&page={page}&tab=main"

#         driver.get(url)
#         time.sleep(3)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(2)

#         products = driver.find_elements(
#             By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item"
#         )


#         # 대체 구조: 키캡이나 액세서리형
#         if len(products) == 0:
#             products = driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")

#         print(f"[DEBUG] 상품 개수: {len(products)}")
        
#         for idx, p in enumerate(products):
#             if len(results) >= max_count:
#                 break

#             try:
#                 name_elem = p.find_element(By.CSS_SELECTOR, ".prod_name > a")
#                 name = name_elem.text.strip()
#                 detail_page_url = name_elem.get_attribute("href")
#             except:
#                 continue

#             try:
#                 try:
#                     price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > a")
#                 except:
#                     try:
#                         price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect strong > em")
#                     except:
#                         price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect > strong")
#                 price = price_elem.get_attribute("innerText").strip().replace(",", "").replace("원", "")
#             except:
#                 price = ""

#             try:
#                 spec_elem = p.find_element(By.CSS_SELECTOR, ".spec_list")
#                 spec_html = spec_elem.get_attribute("innerHTML")
#                 spec_keywords = extract_specs_text(spec_html)
#             except:
#                 spec_keywords = []

#             # try:
#             #     img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
#             #     thumbnail = img_elem.get_attribute("src") or img_elem.get_attribute("data-original")
#             # except:
#             #     thumbnail = ""
#             try:
#                 img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
#                 thumbnail = img_elem.get_attribute("src") or img_elem.get_attribute("data-original")
#                 thumbnail = get_highres_thumbnail(thumbnail)
#             except:
#                 thumbnail = ""
                
#             try:
#                 options = extract_product_options(p)
#             except:
#                 options = []

#             try:
#                 final_url = get_final_redirect_url(driver, detail_page_url)
#             except:
#                 final_url = ""

#             # 카테고리 처리
#             query = query.lower()  # 영어 처리를 위한 소문자 변환

#             if "키보드 케이스" in query or "keyboard case" in query:
#                 category = "case"
#             elif "키캡" in query or "keycap" in query:
#                 category = "keycap"
#             elif "베어본" in query or "하우징" in query or "housing" in query:
#                 category = "housing"
#             elif "스위치" in query or "switch" in query:
#                 category = "switch"
#             elif "케이스" in query or "case" in query:
#                 category = "case"
#             elif "키보드" in query or "keyboard" in query:
#                 category = "keyboard"
#             else:
#                 category = "accessory"

#             results.append({
#                 "name": str(name),
#                 "price": double(price), 
#                 "category": str(category),
#                 "description": str(spec_keywords),
#                 "thumbnail": str(thumbnail),
#                 "options": options,
#                 ""
#                 "detail_page_url": detail_page_url,
#                 "final_purchase_url": str(final_url),
#             })


#         if len(results) >= max_count:
#             break

#     return results

def crawl_danawa_product_list(driver, query, sort, max_items, page_limit):
    try:
        return crawl_danawa_keyboards(driver, query=query, sort=sort, max_count=max_items, page_limit=page_limit)
    except Exception as e:
        print("에러:", e)
        return []
    # 마지막 방어
    if result is None:
        result = []
    return result
