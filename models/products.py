from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class Variant(BaseModel):
    option: Dict[str, Any]
    price: int


class ProductModel(BaseModel):
    productId: str
    categoryId: str
    name: str
    brand: str
    thumbnail: str
    variants: List[Variant]
    attributes: Dict[str, Any]
    detailImages: List[str]
    createdAt: datetime
    updatedAt: datetime

class CrawlingRequest(BaseModel):
    query: str = "60 커스텀 키보드 하우징"
    sort: str = "accuracy"
    max_items: int = 50
    page_limit: int = 50
    headless: bool = True

class CrawlingResponse(BaseModel):
    success: bool
    data: list
    message: str