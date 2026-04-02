# app/api/routes.py
from fastapi import APIRouter, Query

from app.config import KEYWORDS
from app.models import ScoredProduct
from app.store import RedisStore
from app.worker.tasks import scrape_keyword_task

router = APIRouter()
store = RedisStore()


@router.get("/products", response_model=list[ScoredProduct])
def get_products(keyword: str | None = Query(None)):
    return store.get_products(keyword)


@router.get("/top-products", response_model=list[ScoredProduct])
def get_top_products():
    return store.get_top_products(3)


@router.post("/scrape")
def trigger_scrape():
    task_ids = []
    for keyword in KEYWORDS:
        result = scrape_keyword_task.delay(keyword)
        task_ids.append({"keyword": keyword, "task_id": str(result.id)})
    return {"status": "started", "tasks": task_ids}
