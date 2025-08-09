# import re
# import time
# from urllib.parse import parse_qsl, quote_plus, unquote, urlencode, urlparse, urlunparse

# from bs4 import BeautifulSoup
# from numpy import double
# from selenium import webdriver
# from selenium.common.exceptions import StaleElementReferenceException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# # --- 크롬 옵션 ---
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--ignore-certificate-errors")
# chrome_options.add_argument("--ignore-ssl-errors")
# chrome_options.add_argument("--headless=new")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")
# driver = webdriver.Chrome(options=chrome_options)

# # --- 유틸 ---
# def normalize_thumbnail_url(url: str):
#     if not url:
#         return ""
#     if url.startswith("//"):
#         url = "https:" + url
#     return get_highres_thumbnail(url)

# def get_highres_thumbnail(url):
#     if not url:
#         return ""
#     parsed = urlparse(url)
#     query = dict(parse_qsl(parsed.query))
#     if 'shrink' in query:
#         query['shrink'] = '500:500'
#     new_query = urlencode(query, doseq=True)
#     rebuilt = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
#                           parsed.params, new_query, parsed.fragment))
#     return unquote(rebuilt)
# # --- spec ---
# def extract_specs_text(spec_html: str):
#     soup = BeautifulSoup(spec_html, "html.parser")
#     return [a.get_text(strip=True) for a in soup.find_all("a") if a.get_text(strip=True)]
# #0809 최종 URL
# from selenium.webdriver.support.ui import WebDriverWait


# def get_final_redirect_url(driver, bridge_url, timeout=10):
#     try:
#         original_url = bridge_url
#         driver.get(bridge_url)
#         # 최종 URL로 리다이렉션 될 때까지 대기
#         WebDriverWait(driver, timeout).until(lambda d: d.current_url != original_url)
#         final_url = driver.current_url
#         return final_url
#     except Exception as e:
#         print(f"최종 URL 변환 실패: {e}")
#         return bridge_url  # 실패 시 원본 URL 반환


# ## 0809 브릿지 URL을 최종 구매 URL로 변환하는 함수
# def resolve_bridge_urls(driver, bridge_urls):
#     final_urls = {}
#     for url in bridge_urls:
#         try:
#             final_url = get_final_redirect_url(driver, url)
#             final_urls[url] = final_url
#         except Exception as e:
#             final_urls[url] = url
#     return final_urls

# # ---하나 옵션 ---
# def extract_single_option(option_li, driver):
#     option_info = {}
#     try:
#         option_info["option_name"] = option_li.find_element(By.CSS_SELECTOR, "span.text").text.strip()
#     except:
#         option_info["option_name"] = ""
#     try:
#         price_elem = option_li.find_element(By.CSS_SELECTOR, "p.price_sect a strong")
#         option_info["main_price"] = int(price_elem.text.replace(",", "").replace("원", ""))
#     except:
#         option_info["main_price"] = None

#     vendors = []
#     try:
#         price_info_button = option_li.find_element(By.CSS_SELECTOR, "button.i_more")
#         driver.execute_script("arguments[0].click();", price_info_button)
#         popup_id_suffix = option_li.get_attribute('id').split('_')[-1]
#         popup_selector = f"span#layer_price_more_{popup_id_suffix}"

#         WebDriverWait(driver, 7).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"{popup_selector} span.lpm_wrap"))
#         )
#         popup = driver.find_element(By.CSS_SELECTOR, popup_selector)
#         vendor_blocks = popup.find_elements(By.CSS_SELECTOR, "span.lpm_wrap")

#         if vendor_blocks:  # 첫 번째 벤더만 처리
#             block = vendor_blocks[0]
#             try:
#                 # 쇼핑몰 이름
#                 try:
#                     logo_img = block.find_element(By.CSS_SELECTOR, "a.lpm_logo img")
#                     shop_name = logo_img.get_attribute("alt").strip()
#                 except:
#                     shop_name = block.find_element(By.CSS_SELECTOR, "a.lpm_logo").text.strip()
#                 # 가격
#                 try:
#                     price_span = block.find_element(By.CSS_SELECTOR, "a.lpm_price > span")
#                     price_val_raw = price_span.text.replace(",", "").replace("원", "").strip()
#                     price_val = int(price_val_raw) if price_val_raw else None
#                 except:
#                     price_val = None
#                 # URL
#                 bridge_url = block.find_element(By.CSS_SELECTOR, "a.lpm_price").get_attribute("href")
                
#                 vendors.append({
#                     "shop": shop_name,
#                     "price": price_val,
#                     "url": bridge_url
#                 })
#             except Exception as e:
#                 print(f"[WARN] 첫 번째 벤더 파싱 실패: {e}")

#     except Exception as e:
#         print(f"[WARN] 팝업 가격 정보 가져오기 실패: {e}")

#     option_info["vendors"] = vendors
#     return option_info

# # --- 전체 옵션 ---

# def extract_product_options(product_li, driver):
#     options = []
#     try:
#         option_lis = product_li.find_elements(By.CSS_SELECTOR, "div.prod_pricelist ul > li")
#         target_lis = option_lis if option_lis else [product_li]
#         for opt_li in target_lis:
#             opt_info = extract_single_option(opt_li, driver)
#               # option_name이 '중고'(혹은 유사 단어 포함)면 건너뜀
#             opt_name = (opt_info.get('option_name') or '').strip()
#             if opt_name == '중고' or ('중고' in opt_name):
#                 continue
#             if opt_info and (opt_info.get('option_name') or opt_info.get('main_price') or opt_info.get('vendors')):
#                 options.append(opt_info)

#     except Exception as e:
#         print(f"[ERROR] 상품 내 옵션 추출 실패: {e}")
#     return options

# # --- 메인 ---
# def crawl_danawa_keyboards(driver, query, max_count, sort, start_page=1, end_page=1):
#     results = []
#     all_bridge_urls = []  # 변환할 모든 bridge_url 모아두는 리스트

#     base_url = "https://search.danawa.com/dsearch.php"

#     for page in range(start_page, end_page + 1):
#         sort_param = f"&listSort={sort}" if sort else ""
#         url = f"{base_url}?query={quote_plus(query)}&sort={sort_param}&page={page}&tab=main"
#         driver.get(url)
#         time.sleep(1)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(1)

#         products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item")
#         if not products:
#             products = driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")
#         print(f"[DEBUG] PAGE {page} - 상품 개수: {len(products)}")

#         for idx in range(len(products)):
#             if len(results) >= max_count:
#                 break

#             # 최신 DOM에서 참조
#             try:
#                 products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item") or \
#                            driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")
#                 p = products[idx]
#             except IndexError:
#                 break

#             try:
#                 name_elem = p.find_element(By.CSS_SELECTOR, ".prod_name > a")
#                 name = name_elem.text.strip()
#                 detail_page_url = name_elem.get_attribute("href")
#             except StaleElementReferenceException:
#                 print(f"[WARN] stale element in name/url, retrying idx={idx}")
#                 time.sleep(0.5)
#                 continue
#             except Exception as e:
#                 print(f"[WARN] 상품명/URL 추출 실패: {e}")
#                 continue

#             # 가격, 스펙, 썸네일
#             try:
#                 price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect strong")
#                 price_val = double(price_elem.text.replace(",", "").replace("원", ""))
#             except:
#                 price_val = 0
#             try:
#                 spec_elem = p.find_element(By.CSS_SELECTOR, ".spec_list")
#                 spec_html = spec_elem.get_attribute("innerHTML")
#                 spec_keywords = extract_specs_text(spec_html)
#             except:
#                 spec_keywords = []
#             try:
#                 img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
#                 thumb = img_elem.get_attribute("data-original") or img_elem.get_attribute("src")
#                 thumbnail = normalize_thumbnail_url(thumb)
#             except:
#                 thumbnail = ""

#             # 옵션 추출
#             options = extract_product_options(p, driver)
#             for opt in options:
#                 for v in opt.get('vendors', []):
#                     if v.get('url'):
#                         v['bridge_url'] = v['url']  
#                         all_bridge_urls.append(v['bridge_url'])
#                         v.pop('url', None)  # url 비움 (나중에 채움)


#             results.append({
#                 "name": name,
#                 "price": price_val,
#                 "category": "keyboard",
#                 "description": spec_keywords,
#                 "thumbnail": thumbnail,
#                 "options": options,
#                 "detail_page_url": detail_page_url
#             })
#             print(f"[INFO] 저장: {name} (옵션 {len(options)}개)")
#              # --- 후처리: 한번에 브리지 URL 변환 ---
#     print(f"[INFO] 변환할 bridge URL 총 {len(all_bridge_urls)}개")
#     final_url_map = resolve_bridge_urls(driver, all_bridge_urls)

#     for product in results:
#         for opt in product['options']:
#             for v in opt.get('vendors', []):
#                 bridge_url = v.get('bridge_url')
#                 if bridge_url:
#                     v['url'] = final_url_map.get(bridge_url, bridge_url)
#                     v.pop('bridge_url', None)

#     return results

# def crawl_danawa_product_list(driver, query, sort, max_items, start_page, end_page):
#     return crawl_danawa_keyboards(
#         driver=driver,
#         query=query,
#         sort=sort,
#         max_count=max_items,
#         start_page=start_page,
#         end_page=end_page
#     )
import re
import time
from urllib.parse import parse_qsl, quote_plus, unquote, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup
from numpy import double
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# --- 크롬 옵션 & 로그 억제 ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")  # 크롬 로그 출력 최소화
service = Service(log_path='NUL')  # (윈도우: 'NUL', 리눅스: '/dev/null')

driver = webdriver.Chrome(service=service, options=chrome_options)

# --- 유틸 ---
def normalize_thumbnail_url(url: str):
    if not url: return ""
    if url.startswith("//"):
        url = "https:" + url
    return get_highres_thumbnail(url)

def get_highres_thumbnail(url):
    if not url: return ""
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    if 'shrink' in query:
        query['shrink'] = '500:500'
    new_query = urlencode(query, doseq=True)
    rebuilt = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                          parsed.params, new_query, parsed.fragment))
    return unquote(rebuilt)

def extract_specs_text(spec_html: str):
    soup = BeautifulSoup(spec_html, "html.parser")
    return [a.get_text(strip=True) for a in soup.find_all("a") if a.get_text(strip=True)]

def get_final_redirect_url(driver, bridge_url, timeout=10):
    try:
        original_url = bridge_url
        driver.get(bridge_url)
        WebDriverWait(driver, timeout).until(lambda d: d.current_url != original_url)
        final_url = driver.current_url
        return final_url
    except Exception as e:
        print(f"최종 URL 변환 실패: {e}")
        return bridge_url

def resolve_bridge_urls(driver, bridge_urls):
    final_urls = {}
    for url in bridge_urls:
        try:
            final_url = get_final_redirect_url(driver, url)
            final_urls[url] = final_url
        except Exception as e:
            final_urls[url] = url
    return final_urls

# --- 하나 옵션 ---
def extract_single_option(option_li, driver):
    option_info = {}
    try:
        option_info["option_name"] = option_li.find_element(By.CSS_SELECTOR, "span.text").text.strip()
    except:
        option_info["option_name"] = ""
    try:
        price_elem = option_li.find_element(By.CSS_SELECTOR, "p.price_sect a strong")
        option_info["main_price"] = int(price_elem.text.replace(",", "").replace("원", ""))
    except:
        option_info["main_price"] = None

    vendors = []
    try:
        price_info_button = option_li.find_element(By.CSS_SELECTOR, "button.i_more")
        driver.execute_script("arguments[0].click();", price_info_button)
        popup_id_suffix = option_li.get_attribute('id').split('_')[-1]
        popup_selector = f"span#layer_price_more_{popup_id_suffix}"
        WebDriverWait(driver, 7).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"{popup_selector} span.lpm_wrap"))
        )
        popup = driver.find_element(By.CSS_SELECTOR, popup_selector)
        vendor_blocks = popup.find_elements(By.CSS_SELECTOR, "span.lpm_wrap")
        if vendor_blocks:
            block = vendor_blocks[0]
            try:
                try:
                    logo_img = block.find_element(By.CSS_SELECTOR, "a.lpm_logo img")
                    shop_name = logo_img.get_attribute("alt").strip()
                except:
                    shop_name = block.find_element(By.CSS_SELECTOR, "a.lpm_logo").text.strip()
                try:
                    price_span = block.find_element(By.CSS_SELECTOR, "a.lpm_price > span")
                    price_val_raw = price_span.text.replace(",", "").replace("원", "").strip()
                    price_val = int(price_val_raw) if price_val_raw else None
                except:
                    price_val = None
                bridge_url = block.find_element(By.CSS_SELECTOR, "a.lpm_price").get_attribute("href")
                vendors.append({
                    "shop": shop_name,
                    "price": price_val,
                    "url": bridge_url
                })
            except Exception as e:
                print(f"[WARN] 첫 번째 벤더 파싱 실패: {e}")
    except Exception as e:
        print(f"[WARN] 팝업 가격 정보 가져오기 실패: {e}")

    option_info["vendors"] = vendors
    return option_info

# --- 전체 옵션 ---
def extract_product_options(product_li, driver):
    options = []
    try:
        option_lis = product_li.find_elements(By.CSS_SELECTOR, "div.prod_pricelist ul > li")
        target_lis = option_lis if option_lis else [product_li]
        for opt_li in target_lis:
            opt_info = extract_single_option(opt_li, driver)
            opt_name = (opt_info.get('option_name') or '').strip()
            # "중고" 텍스트 있으면 continue~!
            if ('중고' in opt_name) or (opt_name == ''):
                continue
            if opt_info and (opt_info.get('option_name') or opt_info.get('main_price') or opt_info.get('vendors')):
                options.append(opt_info)
    except Exception as e:
        print(f"[ERROR] 상품 내 옵션 추출 실패: {e}")
    return options

# --- 메인 ---
def crawl_danawa_keyboards(driver, query, max_count, sort, start_page=1, end_page=1):
    results = []
    all_bridge_urls = []

    base_url = "https://search.danawa.com/dsearch.php"
    for page in range(start_page, end_page + 1):
        sort_param = f"&listSort={sort}" if sort else ""
        url = f"{base_url}?query={quote_plus(query)}&sort={sort_param}&page={page}&tab=main"
        driver.get(url)
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item")
        if not products:
            products = driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")
        print(f"[DEBUG] PAGE {page} - 상품 개수: {len(products)}")

        for idx in range(len(products)):
            if len(results) >= max_count:
                break
            try:
                products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item") \
                           or driver.find_elements(By.CSS_SELECTOR, "div.prod_main_info")
                p = products[idx]
            except IndexError:
                break
            try:
                name_elem = p.find_element(By.CSS_SELECTOR, ".prod_name > a")
                name = name_elem.text.strip()
                detail_page_url = name_elem.get_attribute("href")
            except StaleElementReferenceException:
                print(f"[WARN] stale element in name/url, retrying idx={idx}")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"[WARN] 상품명/URL 추출 실패: {e}")
                continue

            # 가격, 스펙, 썸네일
            try:
                price_elem = p.find_element(By.CSS_SELECTOR, ".price_sect strong")
                price_val = double(price_elem.text.replace(",", "").replace("원", ""))
            except:
                price_val = 0
            try:
                spec_elem = p.find_element(By.CSS_SELECTOR, ".spec_list")
                spec_html = spec_elem.get_attribute("innerHTML")
                spec_keywords = extract_specs_text(spec_html)
            except:
                spec_keywords = []
            try:
                img_elem = p.find_element(By.CSS_SELECTOR, "a.thumb_link img")
                thumb = img_elem.get_attribute("data-original") or img_elem.get_attribute("src")
                thumbnail = normalize_thumbnail_url(thumb)
            except:
                thumbnail = ""
            # 옵션 추출 및 bridge_url 저장
            options = extract_product_options(p, driver)
            for opt in options:
                for v in opt.get('vendors', []):
                    if v.get('url'):
                        v['bridge_url'] = v['url']
                        all_bridge_urls.append(v['bridge_url'])
                        v.pop('url', None)  # url 비워두고 후처리에서 추가
            results.append({
                "name": name,
                "price": price_val,
                "category": "keyboard",
                "description": spec_keywords,
                "thumbnail": thumbnail,
                "options": options,
                "detail_page_url": detail_page_url
            })
            print(f"[INFO] 저장: {name} (옵션 {len(options)}개)")

    # --- 후처리: bridge URL → 실제 URL 변환 ---
    print(f"[INFO] 변환할 bridge URL 총 {len(all_bridge_urls)}개")
    final_url_map = resolve_bridge_urls(driver, all_bridge_urls)
    for product in results:
          for opt in product.get('options', []):
                 if 'vendors' in opt and isinstance(opt['vendors'], list):
                    if len(opt['vendors']) == 1:
                        vendor_dict = opt['vendors'][0]
                        bridge_url = vendor_dict.get('bridge_url')
                        if bridge_url:
                            vendor_dict['url'] = final_url_map.get(bridge_url, bridge_url)
                            vendor_dict.pop('bridge_url', None)
                        opt['vendors'] = vendor_dict  # 리스트 → dict 변환
                    else:
                        for v in opt['vendors']:
                            bridge_url = v.get('bridge_url')
                            if bridge_url:
                                v['url'] = final_url_map.get(bridge_url, bridge_url)
                                v.pop('bridge_url', None)
    return results

def crawl_danawa_product_list(driver, query, sort, max_items, start_page, end_page):
    return crawl_danawa_keyboards(
        driver=driver,
        query=query,
        sort=sort,
        max_count=max_items,
        start_page=start_page,
        end_page=end_page
    )
