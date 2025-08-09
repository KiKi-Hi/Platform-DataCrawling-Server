import uvicorn
from fastapi import FastAPI

from app import router as html_router  # HTML 템플릿 라우트
from core.settings import settings  # 설정
from routes.products_api import router as api_router  # API 라우트

app = FastAPI(title="KIKIHI FastAPI App")

# 라우트 등록
app.include_router(api_router, prefix="/routes")          # API
app.include_router(html_router)                           # "/" 템플릿

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)