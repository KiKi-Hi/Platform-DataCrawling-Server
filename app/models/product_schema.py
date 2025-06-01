from pydantic import BaseModel
from typing import Optional

from pydantic import BaseModel

class ProductModel(BaseModel):
    상품명: str
    브랜드명: str | None = None
    썸네일: str | None = None
    상세이미지: str | None = None
    원가: int | None = None
    최저가: int | None = None
    관련태그: list[str] | None = []
    카테고리: str
