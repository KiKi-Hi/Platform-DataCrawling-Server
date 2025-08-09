from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient

# router 객체로 바꿈
router = APIRouter()

# 템플릿 디렉토리
templates = Jinja2Templates(directory="templates")

# MongoDB 연결
MONGO_URL = "mongodb://localhost:27017"
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["kikihi"]
collection = db["keyboard"]

@router.get("/", response_class=HTMLResponse)
async def read_products(request: Request):
    products_cursor = collection.find({})
    products = []
    async for product in products_cursor:
        product["_id"] = str(product["_id"])
        products.append(product)
    return templates.TemplateResponse("kikihi.html", {"request": request, "products": products})
