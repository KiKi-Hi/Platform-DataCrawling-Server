# 복합 비즈니스 로직 (crud+ 유효성 검사)
from pymongo import MongoClient
from app.core.config import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db["switch"]

def get_all_products():
    products = collection.find({}, {"_id": 1, "상품명": 1})
    return [{"_id": str(p["_id"]), "name": p.get("상품명")} for p in products]

def insert_products(products: list[dict]):
    collection.insert_many(products)
