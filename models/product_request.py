from typing import List, Optional

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    keyword: str = Field(..., description="검색어")
    sort: Optional[str] = Field(
        "인기순", description="정렬 기준 (예: 인기순, 최신순, 가격낮은순, 가격높은순)"
    )
    max_items: Optional[int] = Field(50, description="최대 크롤링 개수")
    save_format: Optional[str] = Field(
        "json", description="저장 포맷 (json, csv, db 등)"
    )
    page_limit: Optional[int] = Field(
        None, description="최대 페이지 수 (미지정 시 전체 대상)"
    )

    class Config:
        schema_extra = {
            "example": {
                "keyword": "노트북",
                "sort": "인기순",
                "max_items": 100,
                "save_format": "json",
                "page_limit": 5,
            }
        }
