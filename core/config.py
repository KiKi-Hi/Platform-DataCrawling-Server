from pymongo import MongoClient

from core.settings import settings


def get_mongo_collection(collection_name: str):
    client = MongoClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    return db[collection_name]
