# celery 실행 진입점
from celery import Celery

from core.settings import settings

celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# tasks 등록 (여기서 직접 import)
celery_app.autodiscover_tasks(
    [
        "tasks.product_tasks",
        # "app.tasks.another_task",  # 다른 task가 있다면 여기에 추가
    ],
    force=True,  # 강제로 모든 task를 다시 로드
)
