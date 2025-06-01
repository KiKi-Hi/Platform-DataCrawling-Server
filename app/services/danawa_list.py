from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# 크롬 브라우저 자동 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # 창 최대화
options.add_argument("--disable-blink-features=AutomationControlled")  # 봇 감지 방지

# 웹드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 다나와 키보드 페이지 접속
url = "https://search.danawa.com/dsearch.php?query=키보드&tab=main"
driver.get(url)

# 페이지 로딩 대기
time.sleep(3)

# 스크롤 다운 (동적 로딩 대응)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# 키보드 상품 리스트 가져오기
products = driver.find_elements(By.CSS_SELECTOR, "div.main_prodlist > ul > li")

# 결과 출력
for p in products:
    try:
        name = p.find_element(By.CSS_SELECTOR, "p.prod_name > a").text
        price = p.find_element(By.CSS_SELECTOR, "p.price_sect > a").text
        print(f"제품명: {name} / 가격: {price}")
    except:
        continue  # 광고 등 예외 항목은 무시

# 크롬 종료
driver.quit()
