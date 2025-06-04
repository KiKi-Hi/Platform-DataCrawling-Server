from typing import Any, Dict, List

from celery.result import AsyncResult
from fastapi import APIRouter, Body, Query

from celery_worker import celery_app
from core.config import get_mongo_collection
from models.product_request import CrawlRequest
from models.products import ProductModel
from tasks.product_tasks import (crawl_products_task, get_lowest_price,
                                 insert_products_task)

products_col = get_mongo_collection("products")

router = APIRouter()


# 직접 상품 여러러 개 적재 (Bulk Insert)
@router.post("/products/bulk/")
def create_products_bulk(
    products: List[ProductModel] = Body(
        ...,
        example=[
            {
                "productId": "keycap001",
                "categoryId": "keycap",
                "name": "PBT Keycap Set",
                "brand": "KeyCo",
                "thumbnail": "https://cdn.example.com/products/keycap001-thumb.jpg",
                "variants": [
                    {"option": {"color": "화이트"}, "price": 30000},
                    {"option": {"color": "블랙"}, "price": 32000},
                ],
                "attributes": {"material": "PBT", "profile": "OEM"},
                "detailImages": [
                    "https://cdn.example.com/products/keycap001-detail1.jpg"
                ],
                "createdAt": "2025-06-03T12:00:00Z",
                "updatedAt": "2025-06-03T12:00:00Z",
            },
            {
                "productId": "switch001",
                "categoryId": "switch",
                "name": "Linear Switch",
                "brand": "SwitchCo",
                "thumbnail": "https://cdn.example.com/products/switch001-thumb.jpg",
                "variants": [
                    {"option": {"type": "리니어"}, "price": 5000},
                    {"option": {"type": "클릭"}, "price": 5500},
                ],
                "attributes": {"actuationForce": "45g", "travelDistance": "4mm"},
                "detailImages": [
                    "https://cdn.example.com/products/switch001-detail1.jpg"
                ],
                "createdAt": "2025-06-03T12:00:00Z",
                "updatedAt": "2025-06-03T12:00:00Z",
            },
            # ... 이하 생략
        ],
    )
):
    docs = [p.dict() for p in products]
    result = products_col.insert_many(docs)
    return {"inserted_ids": [str(_id) for _id in result.inserted_ids]}


# health check
@router.get("/health")
def health_check():
    return {"status": "ok"}


# 그냥 데이터 크롤링
@router.post("/crawl/")
def crawl_products(request: CrawlRequest):
    task = crawl_products_task.delay(
        search_queries=[request.keyword],
        sorted_by=request.sort,
        max_list_items_per_query=request.max_items or 50,
        save_format=request.save_format,
        page_limit=request.page_limit,
    )
    return {"task_id": task.id, "message": "크롤링 작업이 큐에 등록되었습니다."}


# 그냥 크롤링한 데이터 mongoDB에 삽입
@router.post("/insert-products-manual")
async def insert_products_manual(products: list[ProductModel]):
    product_dicts = [p.dict() for p in products]
    task = insert_products_task.delay(product_dicts)
    return {
        "message": "적재 작업 큐에 등록 완료",
        "task_id": task.id,
        "item_count": len(product_dicts),
    }


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
