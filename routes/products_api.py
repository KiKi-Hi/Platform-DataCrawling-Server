from typing import Any, Dict, List

from bson import ObjectId
from celery.result import AsyncResult
from fastapi import APIRouter, Body, Query

from celery_worker import celery_app
from core.config import get_mongo_collection
from models.product_request import CrawlRequest
from models.products import CrawlingResponse, ProductModel
from services.danawa_crawling import crawl_products
from tasks.product_tasks import (
    crawl_products_task,
    get_lowest_price,
    insert_products_task,
)

products_col = get_mongo_collection("products")

router = APIRouter()


# 직접 상품 여러 개 적재 (Bulk Insert)
@router.post("/api/crawl", response_model=CrawlingResponse)
async def crawl_danawa_products(
    query: str = Query(..., description="검색어를 입력하세요"),
    sort: str = Query("saveDESC", description="정렬 방식"),
    max_items: int = Query(50, description="최대 아이템 수"),
    page_limit: int = Query(50, description="페이지 제한"),
    headless: bool = Query(True, description="헤드리스 모드")
):
    """
    다나와 상품 크롤링 API (query 파라미터로 직접 검색어 입력)
    """
    try:
        data = crawl_products(
            query=query,
            sort=sort,
            max_items=max_items,
            page_limit=page_limit,
            headless=headless,
        )
        
        # ObjectId -> str로 변환
        safe_data = convert_object_ids(data)
        
        return CrawlingResponse(
            success=True,
            data=safe_data,
            message="크롤링이 성공적으로 완료되었습니다."
        )
    except Exception as e:
        return CrawlingResponse(
            success=False,
            data=[],
            message=f"크롤링 중 오류 발생: {str(e)}"
        )


# 전처리하는 코드 


# health check
@router.get("/health")
def health_check():
    return {"status": "ok"}


# 그냥 데이터 크롤링한한 데이터 mongoDB에 삽입
# @router.post("/crawl/")
# def crawl_products(request: CrawlRequest):
#     task = crawl_products_task.delay(
#         search_queries=[request.keyword],
#         sorted_by=request.sort,
#         max_list_items_per_query=request.max_items or 50,
#         save_format=request.save_format,
#         page_limit=request.page_limit,
#     )
#     return {"task_id": task.id, "message": "크롤링 작업이 큐에 등록되었습니다."}


# 매주 새로운 데이터 mongoDB에 삽입
@router.post("/insert-products")
async def batch_upload(products: list[ProductModel]):
    product_dicts = [p.dict() for p in products]
    insert_products_task.delay(product_dicts)
    return {"message": "적재 작업 큐에 등록 완료", "item_count": len(product_dicts)}


# 최저가 갱신
# @router.get("/products/{product_name}/lowest-price")
# async def fetch_lowest_price(product_name: str):
#     task = crawl_lowest_price_url.delay(product_name)
#     return {"task_id": task.id}

# # 작업 상태 조회
# @router.get("/tasks/{task_id}/status")
# async def get_task_status(task_id: str):
#     result = AsyncResult(task_id, app=celery_app)
#     return {"task_id": task_id, "status": result.status, "result": result.result}


# ObjectId를 문자열로 바꾸는 함수
def convert_object_ids(data: list):
    for item in data:
        if "_id" in item and isinstance(item["_id"], ObjectId):
            item["_id"] = str(item["_id"])
    return data