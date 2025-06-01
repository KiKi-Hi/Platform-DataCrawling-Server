from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import time

def get_driver():
    chrome_options = Options()
    # headless로 원하면 추가 (지금은 창 띄움)
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def crawl_product_detail(driver, product_url: str):
    driver.get(product_url)
    time.sleep(3)  # 페이지 로딩 대기
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # id는 URL에서 추출
    id_match = re.search(r'pcode=(\d+)', product_url)
    product_id = int(id_match.group(1)) if id_match else None

    product_name = soup.select_one('div.top_summary > h3 > span')
    product_name = product_name.get_text(strip=True) if product_name else ""

    seller = ""
    seller_tag = soup.select_one('div.prod_mall_area > div.mall_list > ul > li > p.mall_name')
    if seller_tag:
        seller = seller_tag.get_text(strip=True)
    else:
        seller_tag = soup.select_one('div.prod_mall_area > div.mall_list > ul > li > a.mall_name')
        if seller_tag:
            seller = seller_tag.get_text(strip=True)

    thumbnail = ""
    thumb_tag = soup.select_one('div.big_thumb > img')
    if thumb_tag and thumb_tag.has_attr('src'):
        thumbnail = thumb_tag['src']

    original_price = ""
    price_tag = soup.select_one('p.price_sect > a > strong')
    if price_tag:
        original_price = price_tag.get_text(strip=True).replace(",", "")

    related_tags = []
    tag_tags = soup.select('div.tag_list > a')
    if tag_tags:
        related_tags = [tag.get_text(strip=True) for tag in tag_tags]

    detail_imgs = []
    img_tags = soup.select('div#productDetailDiv img')
    for img in img_tags:
        if img.has_attr('src'):
            detail_imgs.append(img['src'])

    layout = layout_type = material = ""
    spec_table = soup.select('table#product_spec > tbody > tr')
    for tr in spec_table:
        th = tr.select_one('th')
        td = tr.select_one('td')
        if not th or not td:
            continue
        key = th.get_text(strip=True)
        value = td.get_text(strip=True)
        if "레이아웃" in key:
            layout = value
        if "레이아웃 타입" in key or "배열" in key:
            layout_type = value
        if "재질" in key or "소재" in key:
            material = value

    return {
        "id": product_id,
        "productName": product_name,
        "seller": seller,
        "productThumbnail": thumbnail,
        "originalPrice": original_price,
        "relatedTags": related_tags if related_tags else None,
        "productDetailImages": detail_imgs,
        "productURL": product_url,
        "layout": layout,
        "layoutType": layout_type,
        "material": material
    }

def crawl_danawa_list_and_details(list_url: str):
    driver = get_driver()
    driver.get(list_url)
    time.sleep(3)  # 페이지 로딩 대기

    # 상품 리스트에서 상세 URL 추출
    products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist > ul > li")
    product_urls = []
    for p in products[0:2]:
        try:
            a_tag = p.find_element(By.CSS_SELECTOR, "p.prod_name > a")
            href = a_tag.get_attribute("href")
            if href:
                product_urls.append(href)
        except:
            continue

    print(f"총 {len(product_urls)}개 상품 상세 URL 수집됨")

    results = []
    for url in product_urls:
        print(f"크롤링 중: {url}")
        detail = crawl_product_detail(driver, url)
        results.append(detail)

    driver.quit()
    return results


if __name__ == "__main__":
    danawa_list_url = "https://search.danawa.com/dsearch.php?query=키보드&tab=main"
    data = crawl_danawa_list_and_details(danawa_list_url)
    for item in data:
        print(item)
