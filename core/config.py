# core/config.py

from motor.motor_asyncio import AsyncIOMotorClient

from core.settings import settings


def get_mongo_collection(collection_name: str):
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    return db[collection_name]