from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from urllib.parse import quote_plus

def get_final_shopping_url(product_name):
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # 필요시 주석 해제
    
    driver = webdriver.Chrome(options=options)
    
    try:
        query = quote_plus(product_name)
        search_url = f"https://search.danawa.com/dsearch.php?query={query}&tab=main"
        driver.get(search_url)
        
        time.sleep(5)  # 페이지 로딩 대기
        
        items = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist.main_prodlist_list > ul > li.prod_item")
        if not items:
            print("상품을 찾을 수 없습니다.")
            return
        
        first_item = items[0]
        
        # 상품명
        title = first_item.find_element(By.CSS_SELECTOR, "p.prod_name > a").text.strip()
        
        # 상품 URL
        url = first_item.find_element(By.CSS_SELECTOR, "p.prod_name > a").get_attribute("href")
        
        # 최저가 추출 시도 (아래 방법 중 가능한 걸로)
        price = None
        
        # 1) 'p.price_sect strong' 태그 (기존)
        try:
            price = first_item.find_element(By.CSS_SELECTOR, "p.price_sect strong").text.strip()
        except:
            pass
        
        # 2) span[class*='lowest'] 또는 strong[class*='lowest'] 같은 클래스명 탐색
        if not price:
            try:
                price = first_item.find_element(By.CSS_SELECTOR, "span.lowest, strong.lowest").text.strip()
            except:
                pass
        
        # 3) 혹시 없으면 가격 텍스트 모두 출력해보기
        if not price:
            try:
                price = first_item.find_element(By.CSS_SELECTOR, "p.price_sect").text.strip()
            except:
                price = "가격 정보 없음"
        
        print(f"상품명: {title}")
        print(f"URL: {url}")
        print(f"최저가: {price}")
        
    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    product = input("검색할 상품명 입력: ")
    danawa_price_search(product)
