# app/worker/celery_app.py
from celery import Celery

from app.config import REDIS_URL

celery_app = Celery("product_intelligence", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)

celery_app.autodiscover_tasks(["app.worker"])
