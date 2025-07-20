# core/config.py
from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import settings

client = AsyncIOMotorClient(settings.mongo_uri)

def get_mongo_collection(collection_name: str):
    db = client[settings.mongo_db]
    return db[collection_name]
