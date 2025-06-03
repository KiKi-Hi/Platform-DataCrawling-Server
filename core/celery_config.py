from celery.schedules import crontab

beat_schedule = {
    "crawl-all-products-every-day-1am": {
        "task": "tasks.crawl_lowest_price",
        "schedule": crontab(hour=1, minute=0),
        "args": ("17180261",),  # 예시 상품ID, 여러 개면 반복문 등 활용
    },
}
