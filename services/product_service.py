# 복합 비즈니스 로직 (crud+ 유효성 검사)
import datetime
from typing import Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient, UpdateOne

from core.config import get_mongo_collection
from services.danawa_detail import crawl_danawa_detail
from services.danawa_list import crawl_danawa_keyboards


# 그냥 크롤링해서 mongoDB에 삽입하는 함수
def insert_products(products: List[Dict], collection_name: str = "switch") -> int:
    if not products:
        return 0

    for prod in products:
        prod["created_at"] = datetime.datetime.today()

    collection = get_mongo_collection(collection_name)
    result = collection.insert_many(products)
    return len(result.inserted_ids)


# 매주 최신 데이터 MongoDB에 삽입 - 스케쥴러
def scheduled_crawling_job():
    print(f"[{datetime.datetime.now()}] 🟡 크롤링 시작")

    products = crawl_danawa_keyboards(query="풀배열 키보드(베어본)", max_count=2)

    if products:
        inserted_count = insert_products(products, collection_name="switch")
        print(f"🟢 {inserted_count}건 MongoDB에 저장 완료")
    else:
        print("🔴 크롤링 결과 없음")

    print(f"[{datetime.datetime.now()}] 🔵 크롤링 종료\n")


# 매일 최저가 MongoDB 갱신
def update_lowest_prices(products: list[dict]):
    collection = get_mongo_collection("switch")
    operations = []
    for product in products:
        operations.append(
            UpdateOne(
                {"_id": product["_id"]},  # 또는 {"상품명": product["상품명"]}
                {"$set": {"최저가": product["최저가"], "최저가_URL": product["url"]}},
                upsert=True,
            )
        )
    if operations:
        collection.bulk_write(operations)


# MongoDB에서 모든 상품의 ID와 이름을 가져오는 함수
# def get_all_products():
#     products = collection.find({}, {"_id": 1, "상품명": 1})
#     return [{"_id": str(p["_id"]), "name": p.get("상품명")} for p in products]


# 테스트
if __name__ == "__main__":
    # 예시 신제품 데이터
    new_products = [
        {"product_id": "20240601", "name": "신제품A", "created_at": "2024-06-01"},
        {"product_id": "20240602", "name": "신제품B", "created_at": "2024-06-01"},
    ]
    insert_products(new_products)
