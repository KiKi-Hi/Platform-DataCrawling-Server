from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()
# Jinja2 템플릿 폴더 설정
templates = Jinja2Templates(directory="templates")

# MongoDB 클라이언트 설정
MONGO_URL = "mongodb://localhost:27017"
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["kikihi"]
collection = db["keyboard"]

@app.get("/", response_class=HTMLResponse)
async def read_products(request: Request):
    # MongoDB에서 전체 상품 데이터 찾기
    products_cursor = collection.find({})
    products = []
    async for product in products_cursor:
        product["_id"] = str(product["_id"])  # ObjectId 문자열 변환
        products.append(product)
    return templates.TemplateResponse("kikihi.html",
                                     {"request": request, "products": products})