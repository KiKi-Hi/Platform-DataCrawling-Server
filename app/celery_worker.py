# celery 실행 진입점
from celery import Celery
from app.core.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# tasks 등록 (여기서 직접 import)
celery_app.autodiscover_tasks(['app.tasks'])