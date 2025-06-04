import time
from urllib.parse import quote_plus

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


def crawl_danawa_keyboards(
    driver, query="키보드", max_count=5, sort=None, page_limit=1
):
    from urllib.parse import quote_plus

    from selenium.webdriver.common.by import By

    results = []
    base_url = "https://search.danawa.com/dsearch.php"

    for page in range(1, page_limit + 1):
        sort_param = f"&listSort={sort}" if sort else ""
        url = f"{base_url}?query={quote_plus(query)}{sort_param}&page={page}&tab=main"

        print(f"\n[PAGE {page}] URL 접속 중: {url}")
        driver.get(url)
        time.sleep(3)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = driver.find_elements(
            By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item"
        )
        print(f"[PAGE {page}] 상품 개수: {len(products)}")

        for idx, p in enumerate(products):
            if len(results) >= max_count:
                break

            print(f"  - [{idx+1}] 상품 정보 수집 중...")

            try:
                name_elem = p.find_element(By.CSS_SELECTOR, "p.prod_name > a")
                name = name_elem.text.strip()
                detail_page_url = name_elem.get_attribute("href")
                print(f"    → 이름: {name}")
                print(f"    → 상세페이지 URL: {detail_page_url}")
            except Exception as e:
                print(f"    → 이름/상세페이지 URL 수집 실패: {e}")
                continue

            try:
                price = (
                    p.find_element(By.CSS_SELECTOR, "p.price_sect > a")
                    .text.strip()
                    .replace(",", "")
                    .replace("원", "")
                )
                print(f"    → 가격: {price}")
            except:
                price = ""
                print("    → 가격 없음")

            try:
                spec_html = p.find_element(
                    By.CSS_SELECTOR, "div.spec_list"
                ).get_attribute("innerHTML")
                spec_keywords = extract_specs_text(spec_html)
                print(f"    → 설명 키워드: {spec_keywords}")
            except:
                spec_keywords = []
                print("    → 설명 없음")

            try:
                thumbnail = p.find_element(
                    By.CSS_SELECTOR, "a.thumb_link > img"
                ).get_attribute("src")
                print(f"    → 썸네일: {thumbnail}")
            except:
                thumbnail = ""
                print("    → 썸네일 없음")

            try:
                options = extract_product_options(p)
                print(f"    → 옵션: {options}")
            except:
                options = []
                print("    → 옵션 없음")

            results.append(
                {
                    "name": name,
                    "price": price,
                    "description": spec_keywords,
                    "thumbnail": thumbnail,
                    "options": options,
                    "detail_page_url": detail_page_url,  # 추가된 부분!
                }
            )

        if len(results) >= max_count:
            print(f"[중단] 최대 수량({max_count}) 도달")
            break

    print(f"\n[완료] 총 {len(results)}개 키보드 상품 수집 완료")
    return results

def crawl_danawa_product_list(driver, query, sort=None, max_items=10, page_limit=1):
    return crawl_danawa_keyboards(
        driver, query=query, sort=sort, max_count=max_items, page_limit=page_limit
    )
