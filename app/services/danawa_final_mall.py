from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from urllib.parse import quote_plus

def get_final_shop_url(product_name):
    options = Options()
    options.add_argument("--headless")  # 실제 브라우저 안 보이게
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 다나와 검색 페이지 접속
        query = quote_plus(product_name)
        search_url = f"https://search.danawa.com/dsearch.php?query={query}&tab=main"
        driver.get(search_url)
        time.sleep(3)

        # 2. 상품 리스트에서 첫 번째 상품 선택
        items = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item")
        if not items:
            print("상품이 없습니다.")
            return None

        first_item = items[0]

        # 3. 최저가 '구매하기' 버튼 클릭
        buy_button = first_item.find_element(By.CSS_SELECTOR, "a.click_log_product_searched_price_")
        redirect_link = buy_button.get_attribute("href")

        print(f"[중간 링크] 다나와 리다이렉션 URL: {redirect_link}")

        # 4. 리다이렉션 URL 열기 → JavaScript로 실제 쇼핑몰로 이동됨
        driver.get(redirect_link)
        time.sleep(5)  # 쿠팡 등으로 리다이렉트될 시간 대기

        # 5. 최종 URL 확인
        final_url = driver.current_url
        return final_url

    except Exception as e:
        print("오류 발생:", e)
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    product_name = "AULA F108 유무선 독거미 한글 기계식 키보드 펀키스 국내 정품 스카이 블랙, LEOBOG 세이야축"
    final_url = get_final_shop_url(product_name)
    
    if final_url:
        print(f"✅ 최종 쇼핑몰 URL: {final_url}")
    else:
        print("❌ 최종 URL을 가져오지 못했습니다.")
