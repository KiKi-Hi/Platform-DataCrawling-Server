import uvicorn
from fastapi import FastAPI

from core.settings import settings
from routes.products_api import router as api_router

app = FastAPI(title="KIKIHI FastAPI App")

# ✅ 올바른 라우터 등록 방법
app.include_router(api_router, prefix="/routes")


# ✅ FastAPI의 데코레이터 사용
@app.get("/")
def root():
    return {"message": "Welcome!"}


# ✅ 서버 실행 코드
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)
