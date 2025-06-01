from fastapi import FastAPI
from app.api import products_api

app = FastAPI()
app.include_router(products_api.router)
