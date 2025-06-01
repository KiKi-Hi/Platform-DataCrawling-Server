from fastapi import APIRouter,Query
from app.models.product_schema import ProductModel
from app.tasks.product_tasks import crawl_lowest_price_url
from celery.result import AsyncResult
from app.celery_worker import celery_app
from app.tasks.product_tasks import insert_products_task



router = APIRouter()

# 업로드
@router.post("/upload")
async def batch_upload(products: list[ProductModel]):
    product_dicts = [p.dict() for p in products]
    insert_products_task.delay(product_dicts)
    return {"message": "적재 작업 큐에 등록 완료", "item_count": len(product_dicts)}

# 크롤링
# @router.get("/danawa/products")
# def get_products(
#     query: str = Query(..., description="검색어 (예: 키보드(베어본))"),
#     page: int = Query(1, description="페이지 번호")
# ):
#     return {"products": crawl_danawa_products(query, page)}

# 최저가 갱신
@router.get("/products/{product_name}/lowest-price")
async def fetch_lowest_price(product_name: str):
    task = crawl_lowest_price_url.delay(product_name)
    return {"task_id": task.id}

# 작업 상태 조회
@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.status, "result": result.result}