# app/tasks/product_tasks.py

import logging
import time
from typing import Dict, List

from celery_worker import celery_app
from services.danawa_crawling import crawl_products
from services.danawa_lowest_price import get_lowest_price
# from services.danawa_lowest_price import update_lowest_prices
from services.product_service import insert_products as insert_many_products

# 선택적으로 사용할 설정값 (필요시 상단에서 import하거나 설정에서 가져오세요)
detail_page_headless = True
pause_between_queries = 1  # 예: 1초 쉬기


@celery_app.task(name="insert_products_task")
def insert_products_task(products: List[Dict]) -> str:
    """
    MongoDB에 크롤링된 제품 리스트 저장하는 Task
    """
    try:
        count = insert_many_products(products)
        logging.info(f"[Celery] 총 {count}개 제품 저장 완료")
        return f"{count} products inserted"
    except Exception as e:
        logging.error(f"[insert_products_task] 저장 실패: {e}")
        return "insert failed"


@celery_app.task(name="crawl_products_task")
def crawl_products_task(
    search_queries: List[str],
    sorted_by: str,
    max_list_items_per_query: int,
    save_format: str,
    page_limit: int,
) -> str:
    try:
        logging.info(
            f"[Celery] 크롤링 시작: {search_queries}, 정렬: {sorted_by}, 저장형식: {save_format}, 페이지 제한: {page_limit}"
        )

        for query in search_queries:
            logging.info(f"[Celery] '{query}' 검색어에 대해 크롤링 중...")

            # 크롤링 실행 함수 (내부에서 sorted_by, max_items 등을 사용할 수 있도록 수정 필요)
            crawl_products(
                query=query,
                sort=sorted_by,
                max_items=max_list_items_per_query,
                save_format=save_format,
                page_limit=page_limit,
                headless=detail_page_headless,
            )

            if pause_between_queries > 0:
                time.sleep(pause_between_queries)

        logging.info("[Celery] 크롤링 완료")
        return "Crawling completed"

    except Exception as e:
        logging.error(f"[Celery] 크롤링 실패: {e}", exc_info=True)
        return "Crawling failed"


# @celery_app.task(name="crawl_lowest_price_url")
# def crawl_lowest_price_url(product_name: str, product_id: str) -> str:
#     """
#     네이버 쇼핑에서 최저가 URL 및 가격 추출 후 DB에 저장
#     """
#     try:
#         logging.info(f"[Celery] '{product_name}' 크롤링 시작")


#         lowest_price = get_lowest_price(final_url)
#         logging.info(f"[{product_name}] 최저가 추출 완료: {lowest_price}원")

#         result = {
#             "_id": product_id,
#             "상품명": product_name,
#             "최저가": lowest_price,
#         }

#         # MongoDB 저장
#         update_lowest_prices([result])  # 이 함수는 내부에서 upsert 또는 update_many 등 처리한다고 가정
#         logging.info(f"[{product_name}] MongoDB 저장 완료")

#         return final_url
#     except Exception as e:
#         logging.error(f"[{product_name}] 최저가 크롤링 실패: {e}")
#         return "crawl failed"
