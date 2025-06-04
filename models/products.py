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
